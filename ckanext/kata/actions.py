'''
Kata's action overrides.
'''

import datetime
import logging

import re
from pylons import c
from pylons.i18n import _

from paste.deploy.converters import asbool
import ckan.logic.action.get
import ckan.logic.action.create
import ckan.logic.action.update
import ckan.logic.action.delete
from ckan.model import Related, Session, Package
import ckan.model as model
from ckan.lib.search import index_for
from ckan.lib.navl.validators import ignore_missing, ignore, not_empty
from ckan.logic.validators import url_validator
from ckan.logic import check_access, NotAuthorized, side_effect_free, NotFound, ValidationError
from ckanext.kata import utils, settings
from ckan.logic import get_action
import ckan.new_authz
from ckanext.kata.schemas import Schemas
import sqlalchemy
import ckan.lib.dictization.model_dictize as model_dictize
from ckan.common import request
import ckan.new_authz as new_authz

_or_ = sqlalchemy.or_

_get_or_bust = ckan.logic.get_or_bust
_authz = model.authz

log = logging.getLogger(__name__)

TITLE_MATCH = re.compile(r'^(title_)?\d?$')


@side_effect_free
def package_show(context, data_dict):
    '''
    Return the metadata of a dataset (package) and its resources.

    Called before showing the dataset in some interface (browser, API),
    or when adding package to Solr index (no validation / conversions then).

    :param id: the id or name of the dataset
    :type id: string

    :rtype: dictionary
    '''

    if data_dict.get('type') == 'harvest':
        context['schema'] = Schemas.harvest_source_show_package_schema()

    if not data_dict.get('id') and not data_dict.get('name'):
        # Get package by data PIDs
        data_dict['id'] = utils.get_package_id_by_data_pids(data_dict)

    pkg_dict1 = ckan.logic.action.get.package_show(context, data_dict)
    pkg_dict1 = utils.resource_to_dataset(pkg_dict1)

    # Remove empty agents that come from padding the agent list in converters
    if 'agent' in pkg_dict1:
        agents = filter(None, pkg_dict1.get('agent', []))
        pkg_dict1['agent'] = agents or []

    #print "testing with dummy data"
    #pkg_dict1['titletest'] = {}

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

    return pkg_dict1


def _handle_pids(context, data_dict):
    '''
    Do some PID modifications to data_dict
    '''
    if not 'pids' in data_dict:
        data_dict['pids'] = []
    else:
        # Clean up empty PIDs
        non_empty = []

        for pid in data_dict['pids']:
            if pid.get('id'):
                non_empty.append(pid)

        data_dict['pids'] = non_empty

    if data_dict.get('generate_version_pid') == 'on':
        data_dict['pids'] += [{'id': utils.generate_pid(),
                               'type': 'version',
                               'provider': 'Etsin',
                               }]

    # If no primary data PID, generate one if this is a new dataset
    if not utils.get_pids_by_type('data', data_dict, primary=True):
        model = context["model"]
        session = context["session"]

        if data_dict.get('id'):
            query = session.query(model.Package.id).filter_by(name=data_dict['id'])  # id contains name !
            result = query.first()

            if result:
                return  # Existing dataset, don't generate new data PID

        data_dict['pids'].insert(0, {'id': utils.generate_pid(),
                                     'type': 'data',
                                     'primary': 'True',
                                     'provider': 'Etsin',
                                     })


def _add_ida_download_url(context, data_dict):
    '''
    Generate a download URL for actual data if no download URL has been specified,
    an access application is to be used for availability,
    and the dataset appears to be from IDA.

    TODO: this should probably be done at the source end, i.e. in IDA itself or harvesters
    '''

    availability = data_dict.get('availability')
    create_new_form = data_dict.get('access_application_new_form')

    if availability == 'access_application' and create_new_form in [u'True', u'on']:
        log.debug("Dataset wants a new access application")

        url = data_dict.get('access_application_download_URL')

        data_pid = utils.get_primary_pid('data', data_dict)

        if data_pid:
            if not url:
                log.debug("Checking for dataset IDAiness through data PID: {p}".format(p=data_pid))
                if utils.is_ida_pid(data_pid):
                    new_url = utils.generate_ida_download_url(data_pid)
                    log.debug("Adding download URL for IDA dataset: {u}".format(u=new_url))
                    data_dict['access_application_download_URL'] = new_url
        else:
            log.warn("Failed to get primary data PID for dataset")


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

    data_dict = utils.dataset_to_resource(data_dict)

    _handle_pids(context, data_dict)

    _add_ida_download_url(context, data_dict)
    if asbool(data_dict.get('private')) and not data_dict.get('persist_schema'):
        context['schema'] = Schemas.private_package_schema()

    data_dict.pop('persist_schema', False)

    if data_dict.get('type') == 'harvest':
        context['schema'] = Schemas.harvest_source_create_package_schema()

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
    # Get all resources here since we get only 'dataset' resources from WUI.
    package_context = {'model': model, 'ignore_auth': True, 'validate': True,
                       'extras_as_string': True}
    package_data = package_show(package_context, data_dict)
    # package_data = ckan.logic.action.get.package_show(package_context, data_dict)

    old_resources = package_data.get('resources', [])

    if not 'resources' in data_dict:
        # When this is reached, we are updating a dataset, not creating a new resource
        data_dict['resources'] = old_resources
        data_dict = utils.dataset_to_resource(data_dict)
    else:
        data_dict['accept-terms'] = 'yes'  # This is not needed when adding a resource

    _handle_pids(context, data_dict)

    _add_ida_download_url(context, data_dict)

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

    if asbool(data_dict.get('private')) and not data_dict.get('persist_schema'):
        context['schema'] = Schemas.private_package_schema()

    data_dict.pop('persist_schema', False)

    if package_data.get('type') == 'harvest':
        context['schema'] = Schemas.harvest_source_update_package_schema()

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
        try:
            log_str += ' Remote IP: ' + request.environ.get('REMOTE_ADDR', 'Could not read remote IP')
        except TypeError:
            log_str += ' Remote IP: Not available, probably a harvested dataset'
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

    sort = data_dict.get('sort', "")

    if c.controller == "organization" and c.action == "read":
        if not sort or sort == 'name asc':
            data_dict['sort'] = 'title_string asc'
        elif sort == 'name desc':
            data_dict['sort'] = 'title_string desc'

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
        log_str += ' Remote IP: ' + request.environ.get('REMOTE_ADDR', 'Could not read remote IP')
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
        log_str += ' Remote IP: ' + request.environ.get('REMOTE_ADDR', 'Could not read remote IP')
        log.info(log_str)
    except:
        pass

    return ckan.logic.action.update.related_update(context, data_dict)


def dataset_editor_delete(context, data_dict):
    '''
    Deletes user and role in a dataset

    :param username: user name to delete
    :type username: string
    :param name: dataset name or id
    :type name: string
    :param role: editor, admin or reader
    :type role: string

    :rtype: message string
    '''
    pkg = model.Package.get(data_dict.get('name', None))
    user = model.User.get(context.get('user', None))
    role = data_dict.get('role', None)
    username = model.User.get(data_dict.get('username', None))

    if not (pkg and user and role):
        msg = _('Required information missing')
        raise ValidationError(msg)

    pkg_dict = get_action('package_show')(context, {'id': pkg.id})
    pkg_dict['domain_object'] = pkg_dict.get('id')
    domain_object_ref = _get_or_bust(pkg_dict, 'domain_object')
    # This could be simpler, as domain_object_ref is pkg.id
    domain_object = ckan.logic.action.get_domain_object(model, domain_object_ref)

    # These are detailed checks to inform the user of the flaw
    if not username:
        msg = _('User not found')
        raise NotFound(msg)

    if not ((_authz.user_has_role(user, 'admin', domain_object) or
             user.sysadmin)) and role == 'admin':
        msg = _('No sufficient privileges to remove user from role %s.') % role
        raise NotAuthorized(msg)

    if not (check_access('package_update', context)):
        msg = _('No sufficient privileges to remove user from role %s.') % role
        raise NotAuthorized(msg)

    if not _authz.user_has_role(username, role, pkg):
        msg = _('No such user and role combination')
        # Validation error is not the correct answer here, but it does the job
        raise ValidationError(msg)

    if username.name == model.PSEUDO_USER__VISITOR or \
            username.name == model.PSEUDO_USER__LOGGED_IN or \
            username.name == 'harvest':
        msg = _('Built-in users can not be removed')
        raise ValidationError(msg)

    if user.id == username.id:
        msg = _('You can not remove yourself')
        raise ValidationError(msg)

    _authz.remove_user_from_role(username, role, pkg)

    msg = _('User removed from role %s') % role

    return msg


def dataset_editor_add(context, data_dict):
    '''
    Adds a user and role to dataset

    :param name: dataset name or id
    :type name: string
    :param role: admin, editor or reader
    :type role: string
    :param username: user to be added
    :type username: string

    :rtype: message string
    '''
    pkg = model.Package.get(data_dict.get('name', None))
    user = model.User.get(context.get('user', None))
    role = data_dict.get('role', None)
    username = model.User.get(data_dict.get('username', None))

    if not (pkg and user and role):
        msg = _('Required information missing')
        raise ValidationError(msg)

    pkg_dict = get_action('package_show')(context, {'id': pkg.id})
    pkg_dict['domain_object'] = pkg_dict.get('id')

    domain_object_ref = _get_or_bust(pkg_dict, 'domain_object')
    domain_object = ckan.logic.action.get_domain_object(model, domain_object_ref)

    # These are detailed checks to inform the user of the flaw
    if not username:
        msg = _('User not found')
        raise NotFound(msg)

    if not ((_authz.user_has_role(user, 'admin', domain_object) or
             user.sysadmin)) and role == 'admin':
        raise NotAuthorized

    if not (check_access('package_update', context)):
        raise NotAuthorized

    if _authz.user_has_role(username, role, domain_object):
        msg = _('User already has %s rights') % role
        raise ValidationError(msg)

    model.add_user_to_role(username, role, pkg)
    model.meta.Session.commit()

    msg = _('User added')

    return msg


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


@side_effect_free
def organization_list(context, data_dict):
    """ Modified from ckan.logic.action.get._group_or_org_list.
        Sort by title instead of name and lower case ordering.
    """

    model = context['model']
    api = context.get('api_version')
    groups = data_dict.get('groups')
    ref_group_by = 'id' if api == 2 else 'name'

    sort = data_dict.get('sort', 'title')
    q = data_dict.get('q')

    # order_by deprecated in ckan 1.8
    # if it is supplied and sort isn't use order_by and raise a warning
    order_by = data_dict.get('order_by', '')
    if order_by:
        log.warn('`order_by` deprecated please use `sort`')
        if not data_dict.get('sort'):
            sort = order_by
    # if the sort is packages and no sort direction is supplied we want to do a
    # reverse sort to maintain compatibility.
    if sort.strip() == 'packages':
        sort = 'packages desc'

    sort_info = ckan.logic.action.get._unpick_search(sort,
                                                     allowed_fields=['name', 'packages', 'title'],
                                                     total=1)

    all_fields = data_dict.get('all_fields', None)


    query = model.Session.query(model.Group).join(model.GroupRevision)
    query = query.filter(model.GroupRevision.state=='active')
    query = query.filter(model.GroupRevision.current==True)
    if groups:
        query = query.filter(model.GroupRevision.name.in_(groups))
    if q:
        q = u'%{0}%'.format(q)
        query = query.filter(_or_(
            model.GroupRevision.name.ilike(q),
            model.GroupRevision.title.ilike(q),
            model.GroupRevision.description.ilike(q),
        ))


    query = query.filter(model.GroupRevision.is_organization==True)

    groups = query.all()
    group_list = model_dictize.group_list_dictize(groups, context,
                                                  lambda x:x[sort_info[0][0]].lower(),
                                                  sort_info[0][1] == 'desc')

    if not all_fields:
        group_list = [group[ref_group_by] for group in group_list]

    return group_list


# TODO Juho: Temporary organisation autocomplete implementation in
# kata..plugin.py, kata..controllers.py, kata/actions.py, kata/auth_functions.py
def organization_autocomplete(context, data_dict):
    '''
    Return a list of organization names that contain a string.

    :param q: the string to search for
    :type q: string
    :param limit: the maximum number of organizations to return (optional,
        default: 20)
    :type limit: int

    :rtype: a list of organization dictionaries each with keys ``'name'``,
        ``'title'``, and ``'id'``
    '''

    check_access('organization_autocomplete', context, data_dict)

    q = data_dict['q']
    limit = data_dict.get('limit', 20)
    model = context['model']

    query = model.Group.search_by_name_or_title(q, group_type=None, is_org=True)

    organization_list = []
    for organization in query.all():
        result_dict = {}
        for k in ['id', 'name', 'title']:
            result_dict[k] = getattr(organization, k)
        organization_list.append(result_dict)

    log.debug("organization_list: {ol}".format(ol=organization_list))  # Remove this
    return organization_list


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

@side_effect_free
def user_activity_list(context, data_dict):
    '''
    Override to add stricter access limits for retrieving activity lists.
    :param context:
    :param data_dict:
    :return:
    '''

    check_access('user_activity_list', context)
    return ckan.logic.action.get.user_activity_list(context, data_dict)

@side_effect_free
def package_activity_list(context, data_dict):
    check_access('package_activity_list', context)
    return ckan.logic.action.get.package_activity_list(context, data_dict)

@side_effect_free
def group_activity_list(context, data_dict):
    check_access('group_activity_list', context)
    return ckan.logic.action.get.group_activity_list(context, data_dict)

@side_effect_free
def organization_activity_list(context, data_dict):
    check_access('organization_activity_list', context)
    return ckan.logic.action.get.organization_activity_list(context, data_dict)

@side_effect_free
def user_activity_list_html(context, data_dict):
    '''
    Override to add stricter access limits for retrieving activity lists.
    :param context:
    :param data_dict:
    :return:
    '''

    check_access('user_activity_list', context)
    return ckan.logic.action.get.user_activity_list_html(context, data_dict)

@side_effect_free
def package_activity_list_html(context, data_dict):
    check_access('package_activity_list', context)
    return ckan.logic.action.get.package_activity_list_html(context, data_dict)

@side_effect_free
def group_activity_list_html(context, data_dict):
    check_access('group_activity_list', context)
    return ckan.logic.action.get.group_activity_list_html(context, data_dict)

@side_effect_free
def organization_activity_list_html(context, data_dict):
    check_access('organization_activity_list', context)
    return ckan.logic.action.get.organization_activity_list_html(context, data_dict)

@side_effect_free
def member_list(context, data_dict):
    check_access('member_list', context, data_dict)

    # Copy from CKAN member_list:
    model = context['model']

    group = model.Group.get(_get_or_bust(data_dict, 'id'))
    if not group:
        raise NotFound

    obj_type = data_dict.get('object_type', None)
    capacity = data_dict.get('capacity', None)

    # User must be able to update the group to remove a member from it
    check_access('group_show', context, data_dict)

    q = model.Session.query(model.Member).\
        filter(model.Member.group_id == group.id).\
        filter(model.Member.state == "active")

    if obj_type:
        q = q.filter(model.Member.table_name == obj_type)
    if capacity:
        q = q.filter(model.Member.capacity == capacity)

    trans = new_authz.roles_trans()

    def translated_capacity(capacity):
        try:
            return _Capacity(trans[capacity], capacity) # Etsin modification
        except KeyError:
            return capacity

    return [(m.table_id, m.table_name, translated_capacity(m.capacity))
            for m in q.all()]


class _Capacity(object):
    """ Wrapper for capacity. In template view as translation,
        but the original capacity is accesible via original attribute.
    """
    def __init__(self, translation, original):
        self.translation = translation
        self.original = original

    def __repr__(self):
        return unicode(self.translation).encode('utf-8')

    def __str__(self):
        return unicode(self.translation)

    def __unicode__(self):
        return unicode(self.translation)
