# pylint: disable=no-member
'''
Kata's action overrides.
'''

import datetime
import logging

import re
from pylons import c
from pylons.i18n import _

import ckan.logic.action.get
import ckan.logic.action.create
import ckan.logic.action.update
import ckan.logic.action.delete
from ckan.model import Related, Session, Package, repo
import ckan.model as model
from ckan.lib.search import index_for, rebuild
from ckan.lib.navl.validators import ignore_missing, ignore, not_empty
from ckan.logic.validators import url_validator
from ckan.logic import check_access, NotAuthorized, side_effect_free
from ckanext.kata import utils, settings
from ckan.logic import get_action
import ckan.new_authz


_get_or_bust = ckan.logic.get_or_bust
_authz = model.authz

log = logging.getLogger(__name__)

TITLE_MATCH = re.compile(r'^(title_)?\d?$')


@side_effect_free
def package_show(context, data_dict):
    '''Return the metadata of a dataset (package) and its resources.

    :param id: the id or name of the dataset
    :type id: string

    :rtype: dictionary
    '''

    # Called before showing the dataset in some interface (browser, API),
    # or when adding package to Solr index (no validation / conversions then).

    pkg_dict1 = ckan.logic.action.get.package_show(context, data_dict)
    pkg_dict1 = utils.resource_to_dataset(pkg_dict1)

    # Remove empty agents that come from padding the agent list in converters
    if 'agent' in pkg_dict1:
        agents = filter(None, pkg_dict1.get('agent', []))
        pkg_dict1['agent'] = agents or []

    # Normally logic function should not catch the raised errors
    # but here it is needed so action package_show won't catch it instead
    # Hiding information from API calls
    try:
        check_access('package_update', context)
    except NotAuthorized:
        pkg_dict1 = utils.hide_sensitive_fields(pkg_dict1)

    pkg = Package.get(pkg_dict1['id'])
    if 'erelated' in pkg.extras:
        erelated = pkg.extras['erelated']
        if len(erelated):
            for value in erelated.split(';'):
                if len(Session.query(Related).filter(Related.title == value).all()) == 0:
                    data_dict = {'title': value,
                                 'type': _("Paper"),
                                 'dataset_id': pkg.id}
                    related_create(context, data_dict)

    # Update package.title to match package.extras.title_0
    extras_title = pkg.extras.get(u'title_0')
    if extras_title and extras_title != pkg.title:
        repo.new_revision()
        pkg.title = pkg.extras[u'title_0']
        pkg.save()
        rebuild(pkg.id)  # Rebuild solr-index for this dataset

    return pkg_dict1


def package_create(context, data_dict):
    """
    Creates a new dataset.
    
    Extends ckan's similar method to instantly reindex the SOLR index, 
    so that this newly added package emerges in search results instantly instead of 
    during the next timed reindexing.

    :param context: context
    :param data_dict: data dictionary (package data)

    :rtype: dictionary
    """
    user = model.User.get(context['user'])
    try:
        if data_dict['type'] == 'harvest' and not user.sysadmin:
            ckan.lib.base.abort(401, _('Unauthorized to add a harvest source'))
            
    except KeyError:
        log.debug("Tried to check the package type, but it wasn't present!")
        # TODO: JUHO: Dubious to let pass without checking user.sysadmin
        pass
    # Remove ONKI generated parameters for tidiness
    # They won't exist when adding via API
    try:
        removable = ['field-tags', 'tag_string_tmp', 'field-tags_langs',
                     'geographic_coverage_field_langs', 'geographic_coverage_field',
                     'geographic_coverage_tmp',
                     'discipline_field_langs', 'discipline_field']
        for key in removable:
            del data_dict[key]
    except KeyError:
        pass

    data_dict = utils.dataset_to_resource(data_dict)

    # Get version PID (or generate a new one?)
    new_version_pid = data_dict.get('new_version_pid')

    if not new_version_pid and data_dict.get('generate_version_pid', None) == 'on':
        new_version_pid = utils.generate_pid()

    if new_version_pid:
        data_dict['pids'] = data_dict.get('pids', []) + [{'id': new_version_pid, 'type': 'version', 'provider': 'kata'}]

    # Add current user as a distributor if not already present.
    if user:
        if not 'agent' in data_dict:
            data_dict['agent'] = []

        user_name = user.display_name
        distributor_names = [agent.get('name') for agent in data_dict['agent'] if agent.get('role') == 'distributor']

        if not user_name in distributor_names:
            data_dict['agent'].append(
                {'name': user_name, 'role': 'distributor', 'id': user.id}
            )

    pkg_dict1 = ckan.logic.action.create.package_create(context, data_dict)

    # Logging for production use
    _log_action('Package', 'create', context['user'], pkg_dict1['id'])

    context = {'model': model, 'ignore_auth': True, 'validate': False,
               'extras_as_string': False}
    pkg_dict = ckan.logic.action.get.package_show(context, pkg_dict1)
    index = index_for('package')
    index.index_package(pkg_dict)
    return pkg_dict1


def package_update(context, data_dict):
    '''
    Updates the dataset.

    Extends ckan's similar method to instantly re-index the SOLR index.
    Otherwise the changes would only be added during a re-index (a rebuild of search index,
    to be specific).

    :type context: dict
    :param context: context
    :type data_dict: dict
    :param data_dict: dataset as dictionary

    :rtype: dictionary
    '''
    # Remove ONKI generated parameters for tidiness
    # They won't exist when adding via API
    try:
        removable = ['field-tags', 'tag_string_tmp', 'field-tags_langs',
                     'geographic_coverage_field_langs', 'geographic_coverage_field',
                     'discipline_field_langs', 'discipline_field']
        for key in removable:
            del data_dict[key]
    except KeyError:
        pass

    # Get all resources here since we get only 'dataset' resources from WUI.
    temp_context = {'model': model, 'ignore_auth': True, 'validate': True,
                    'extras_as_string': True}
    temp_pkg_dict = ckan.logic.action.get.package_show(temp_context, data_dict)

    old_resources = temp_pkg_dict.get('resources', [])

    if not 'resources' in data_dict:
        # When this is reached, we are updating a dataset, not creating a new resource
        data_dict['resources'] = old_resources
        data_dict = utils.dataset_to_resource(data_dict)

    # Get all PIDs (except for package.id and package.name) from database and add new relevant PIDS there
    data_dict['pids'] = temp_pkg_dict.get('pids', [])

    new_version_pid = data_dict.get('new_version_pid', None)
    if not new_version_pid and data_dict.get('generate_version_pid', None) == 'on':
        new_version_pid = utils.generate_pid()
        
    if new_version_pid:
        data_dict['pids'] += [{'id': new_version_pid,
                              'type': 'version',
                              'provider': 'kata',
                              }]

    # # Check if data version has changed and if so, generate a new version_PID
    # if not data_dict['version'] == temp_pkg_dict['version']:
    #     data_dict['pids'].append(
    #         {
    #             u'provider': u'kata',
    #             u'id': utils.generate_pid(),
    #             u'type': u'version',
    #         })

    # This fixes extras fields being cleared when adding a resource. This is be because the extras are not properly
    # cleared in show_package_schema conversions. Some fields stay in extras and they cause all other fields to be
    # dropped in package_update(). When updating a dataset via UI or API, the conversion to extras occur in
    # package_update() and popping extras here should have no effect.

    data_dict.pop('extras', None)
    # TODO: MIKKO: Get rid of popping extras here and rather pop the additional extras in converters so we could remove the
    # popping and the above "context['allow_partial_update'] = True" which causes the extras to be processed in a way
    # that nothing gets added to extras from the converters and everything not initially present in extras gets removed.

    # TODO: JUHO: Apply correct schema depending on dataset
    # This is quick resolution. More robust way would be to check through
    # model.Package to which harvest source the dataset belongs and then get the
    # type of the harvester (eg. DDI)
    # if data_dict['name'].startswith('FSD'):
    #     context['schema'] = schemas.update_package_schema_ddi()

    # If distributor isn't present in data_dict, get the old one
    # This fix is made for users using API
    orig_pkg = ckan.logic.action.get.package_show(context, data_dict)
    distributor = False
    for agent in data_dict.get('agent'):
        if agent.get('role') == 'distributor':
            distributor = True
    if not distributor:
        for agent in orig_pkg.get('agent'):
            if agent.get('role') == 'distributor':
                data_dict['agent'].append({'name': agent.get('name'),
                                           'role': u'distributor',
                                           'organisation': agent.get('organisation')})

    pkg_dict1 = ckan.logic.action.update.package_update(context, data_dict)

    # Logging for production use
    _log_action('Package', 'update', context['user'], data_dict['id'])

    context = {'model': model, 'ignore_auth': True, 'validate': False,
               'extras_as_string': True}
    pkg_dict = ckan.logic.action.get.package_show(context, pkg_dict1)
    index = index_for('package')
    # update_dict calls index_package, so it would basically be the same
    index.update_dict(pkg_dict)
    return pkg_dict1


def package_delete(context, data_dict):
    '''
    Deletes a package
    
    Extends ckan's similar method to instantly re-index the SOLR index. 
    Otherwise the changes would only be added during a re-index (a rebuild of search index,
    to be specific).

    :param context: context
    :type context: dictionary
    :param data_dict: package data
    :type data_dict: dictionary

    '''
    # Logging for production use
    _log_action('Package', 'delete', context['user'], data_dict['id'])

    index = index_for('package')
    index.remove_dict(data_dict)
    ret = ckan.logic.action.delete.package_delete(context, data_dict)
    return ret


def _log_action(target_type, action, who, target_id):
    try:
        log_str = '[ ' + target_type + ' ] [ ' + str(datetime.datetime.now())
        log_str += ' ] ' + target_type + ' ' + action + 'd by: ' + who
        log_str += ' target: ' + target_id
        log.info(log_str)
    except:
        log.info('Debug failed! Action not logged')


# Log should show who did what and when
def _decorate(f, target_type, action):
    def call(*args, **kwargs):
        if action is 'delete':
            # log id before we delete the data
            _log_action(target_type, action, args[0]['user'], args[1]['id'])

        ret = f(*args, **kwargs)
        if action is 'create' or action is 'update':
            _log_action(target_type, action, args[0]['user'], ret['id'])

        return ret

    return call

# Overwriting to add logging
resource_create = _decorate(ckan.logic.action.create.resource_create, 'resource', 'create')
resource_update = _decorate(ckan.logic.action.update.resource_update, 'resource', 'update')
resource_delete = _decorate(ckan.logic.action.delete.resource_delete, 'resource', 'delete')
related_delete = _decorate(ckan.logic.action.delete.related_delete, 'related', 'delete')
# member_create = _decorate(ckan.logic.action.create.member_create, 'member', 'create')
# member_delete = _decorate(ckan.logic.action.delete.member_delete, 'member', 'delete')
group_create = _decorate(ckan.logic.action.create.group_create, 'group', 'create')
group_update = _decorate(ckan.logic.action.update.group_update, 'group', 'update')
group_list = _decorate(ckan.logic.action.get.group_list, 'group', 'list')
group_delete = _decorate(ckan.logic.action.delete.group_delete, 'group', 'delete')
organization_create = _decorate(ckan.logic.action.create.organization_create, 'organization', 'create')
organization_update = _decorate(ckan.logic.action.update.organization_update, 'organization', 'update')
organization_delete = _decorate(ckan.logic.action.delete.organization_delete, 'organization', 'delete')


@side_effect_free
def package_search(context, data_dict):
    '''Return the metadata of a dataset (package) and its resources.

    :param id: the id or name of the dataset
    :type id: string
    :param context: context
    :type context: dictionary

    :rtype: dictionary
    '''
    #Wraps around the CKAN package_search action to add customizations
    #in some special cases.

    if c.controller == "home" and c.action == "index":
        data_dict['sort'] = "metadata_modified desc"
        data_dict['rows'] = 5
        # don't want harvest source packages
        data_dict['fq'] += " +dataset_type:dataset"

    return ckan.logic.action.get.package_search(context, data_dict)


# def group_list(context, data_dict):
#     '''
#     Return a list of the names of the site's groups.
#     '''
#     if not "for_view" in context:
#         return []
#     else:
#         return ckan.logic.action.get.group_list(context, data_dict)


def related_create(context, data_dict):
    '''
    Uses different schema and adds logging.
    Otherwise does what ckan's similar function does.

    :param context: context
    :type context: dictionary
    :param data_dict: related item's data
    :type data_dict: dictionary

    :returns: the newly created related item
    :rtype: dictionary
    '''
    schema = {
        'id': [ignore_missing, unicode],
        'title': [not_empty, unicode],
        'description': [ignore_missing, unicode],
        'type': [not_empty, unicode],
        'image_url': [ignore_missing, unicode, url_validator],
        'url': [ignore_missing, unicode],
        'owner_id': [not_empty, unicode],
        'created': [ignore],
        'featured': [ignore_missing, int],
    }
    context['schema'] = schema

    ret = ckan.logic.action.create.related_create(context, data_dict)
    # Logging for production use
    try:
        log_str = '[' + str(datetime.datetime.now())
        log_str += ']' + ' related created ' + 'by: ' + context['user']
        log_str += ' target: ' + ret['id']
        log.info(log_str)
    except:
        pass

    return ret


def related_update(context, data_dict):
    '''
    Uses different schema and adds logging.
    Otherwise does what ckan's similar function does.

    :param context: context
    :type context: dictionary
    :param data_dict: related item's data
    :type data_dict: dictionary

    :returns: the newly updated related item
    :rtype: dictionary
    '''
    schema = {
        'id': [ignore_missing, unicode],
        'title': [not_empty, unicode],
        'description': [ignore_missing, unicode],
        'type': [not_empty, unicode],
        'image_url': [ignore_missing, unicode, url_validator],
        'url': [ignore_missing, unicode],
        'owner_id': [not_empty, unicode],
        'created': [ignore],
        'featured': [ignore_missing, int],
    }
    context['schema'] = schema

    # Logging for production use
    try:
        log_str = '[' + str(datetime.datetime.now())
        log_str += ']' + ' related updated ' + 'by: ' + context['user']
        log_str += ' target: ' + data_dict['id']
        log.info(log_str)
    except:
        pass

    return ckan.logic.action.update.related_update(context, data_dict)


def dataset_editor_delete(context, data_dict):
    '''
    Deletes user and role in a dataset

    :param username: user name to delete
    :type username: string
    :param id: dataset id
    :type id: string
    :param role: editor, admin or reader
    :type role: string

    :rtype: message dict with `success` and `msg`
    '''
    pkg = model.Package.get(data_dict.get('name', None))
    user = model.User.get(context.get('user', None))
    role = data_dict.get('role', None)
    username = model.User.get(data_dict.get('username', None))

    if not (pkg and user and role):
        msg = _('Required information missing')
        return {'success': False, 'msg': msg}

    pkg_dict = get_action('package_show')(context, {'id': pkg.id})
    pkg_dict['domain_object'] = pkg_dict.get('id')
    domain_object_ref = _get_or_bust(pkg_dict, 'domain_object')
    # This could be simpler, as domain_object_ref is pkg.id
    domain_object = ckan.logic.action.get_domain_object(model, domain_object_ref)

    # Todo: use check_access instead? It is not this detailed, though
    if not username:
        msg = _('User not found')
        return {'success': False, 'msg': msg}

    if not (_authz.user_has_role(user, role, domain_object) or
            _authz.user_has_role(user, 'admin', domain_object) or
            role == 'reader' or user.sysadmin == True):
        msg = _('No sufficient privileges to remove user from role %s.') % role
        return {'success': False, 'msg': msg}

    if not _authz.user_has_role(username, role, pkg):
        msg = _('No such user and role combination')
        return {'success': False, 'msg': msg}

    if username.name == 'visitor' or username.name == 'logged_in':
        msg = _('Built-in users can not be removed')
        return {'success': False, 'msg': msg}

    if user.id == username.id:
        msg = _('You can not remove yourself')
        return {'success': False, 'msg': msg}

    _authz.remove_user_from_role(username, role, pkg)
    msg = _('User removed from role %s') % role

    return {'success': True, 'msg': msg}


def dataset_editor_add(context, data_dict):
    '''
    Adds a user and role to dataset

    :param name: dataset name
    :type name: string
    :param role: admin, editor or reader
    :type role: string
    :param username: user to be added
    :type username: string

    :rtype: message dict with 'success' and 'msg'
    '''
    pkg = model.Package.get(data_dict.get('name', None))
    user = model.User.get(context.get('user', None))
    role = data_dict.get('role', None)
    username = model.User.get(data_dict.get('username', None))

    if not (pkg and user and role):
        msg = _('Required information missing')
        return {'success': False, 'msg': msg}

    pkg_dict = get_action('package_show')(context, {'id': pkg.id})
    pkg_dict['domain_object'] = pkg_dict.get('id')

    domain_object_ref = _get_or_bust(pkg_dict, 'domain_object')
    domain_object = ckan.logic.action.get_domain_object(model, domain_object_ref)

    # Todo: use check_access instead? It is not this detailed, though
    if not username:
        msg = _('User not found')
        return {'success': False, 'msg': msg}

    if not (_authz.user_has_role(user, role, domain_object) or
            _authz.user_has_role(user, 'admin', domain_object) or
            role == 'reader' or user.sysadmin == True):
        msg = _('No sufficient privileges to add a user to role %s.') % role
        return {'success': False, 'msg': msg}

    if _authz.user_has_role(username, role, domain_object):
        msg = _('User already has %s rights') % role
        return {'success': False, 'msg': msg}

    if user.id == username.id:
        msg = _('You can not add yourself')
        return {'success': False, 'msg': msg}

    model.add_user_to_role(username, role, pkg)
    model.meta.Session.commit()
    msg = _('User added')

    return {'success': True, 'msg': msg}


@side_effect_free
def organization_list_for_user(context, data_dict):
    '''
    Get a list organizations available for current user. Modify CKAN organization permissions before calling original
    action.

    :returns: list of dictized organizations that the user is authorized to edit
    :rtype: list of dicts
    '''
    # NOTE! CHANGING CKAN ORGANIZATION PERMISSIONS
    ckan.new_authz.ROLE_PERMISSIONS = settings.ROLE_PERMISSIONS

    return ckan.logic.action.get.organization_list_for_user(context, data_dict)


def member_create(context, data_dict=None):
    '''
    Make an object (e.g. a user, dataset or group) a member of a group.

    Custom organization permission handling added on top of CKAN's own member_create action.
    '''
    _log_action('Member', 'create', context['user'], data_dict.get('id'))

    # NOTE! CHANGING CKAN ORGANIZATION PERMISSIONS
    ckan.new_authz.ROLE_PERMISSIONS = settings.ROLE_PERMISSIONS

    user = context['user']
    user_id = ckan.new_authz.get_user_id_for_username(user, allow_none=True)

    group_id, obj_id, obj_type, capacity = _get_or_bust(data_dict, ['id', 'object', 'object_type', 'capacity'])

    # get role the user has for the group
    user_role = utils.get_member_role(group_id, user_id)

    if obj_type == 'user':
        # get role for the target of this role change
        target_role = utils.get_member_role(group_id, obj_id)
        if target_role is None:
            target_role = capacity

        if ckan.new_authz.is_sysadmin(user):
            # Sysadmin can do anything
            pass
        elif not settings.ORGANIZATION_MEMBER_PERMISSIONS.get((user_role, target_role, capacity, user_id == obj_id), False):
            raise ckan.logic.NotAuthorized(_("You don't have permission to modify roles for this organization."))

    return ckan.logic.action.create.member_create(context, data_dict)


def member_delete(context, data_dict=None):
    '''
    Remove an object (e.g. a user, dataset or group) from a group.

    Custom organization permission handling added on top of CKAN's own member_create action.
    '''
    _log_action('Member', 'delete', context['user'], data_dict.get('id'))

    # NOTE! CHANGING CKAN ORGANIZATION PERMISSIONS
    ckan.new_authz.ROLE_PERMISSIONS = settings.ROLE_PERMISSIONS

    user = context['user']
    user_id = ckan.new_authz.get_user_id_for_username(user, allow_none=True)

    group_id, target_name, obj_type = _get_or_bust(data_dict, ['id', 'object', 'object_type'])

    if obj_type == 'user':
        # get user's role for this group
        user_role = utils.get_member_role(group_id, user_id)

        target_id = ckan.new_authz.get_user_id_for_username(target_name, allow_none=True)

        # get target's role for this group
        target_role = utils.get_member_role(group_id, target_id)

        if ckan.new_authz.is_sysadmin(user):
            # Sysadmin can do anything.
            pass
        elif not settings.ORGANIZATION_MEMBER_PERMISSIONS.get((user_role, target_role, 'member', user_id == target_id), False):
            raise ckan.logic.NotAuthorized(_("You don't have permission to remove this user."))

    return ckan.logic.action.delete.member_delete(context, data_dict)


def organization_member_create(context, data_dict):
    '''
    Wrapper for CKAN's group_member_create to modify organization permissions.
    '''
    # NOTE! CHANGING CKAN ORGANIZATION PERMISSIONS
    ckan.new_authz.ROLE_PERMISSIONS = settings.ROLE_PERMISSIONS

    return ckan.logic.action.create.group_member_create(context, data_dict)


def package_owner_org_update(context, data_dict):
    '''
    Update the owning organization of a dataset

    Used by both package_create and package_update
    '''

    user_id = model.User.by_name(context.get('user')).id
    org_id = data_dict.get('organization_id')

    # get role the user has for the group
    user_role = utils.get_member_role(org_id, user_id)

    pkg = model.Package.get(data_dict['id'])

    if not pkg.private and user_role == 'member':
        raise ckan.logic.NotAuthorized(_("You are not allowed to create public datasets for this organization."))

    return ckan.logic.action.update.package_owner_org_update(context, data_dict)
