'''
Kata's action overrides.
'''

import datetime
import logging

import re
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
from ckan.logic import check_access, NotAuthorized, side_effect_free, NotFound
from ckanext.kata import utils, settings
from ckan import authz
from ckanext.kata.schemas import Schemas
import sqlalchemy
from ckan.common import request
import ckanext.kata.clamd_wrapper as clamd_wrapper

_or_ = sqlalchemy.or_

_get_or_bust = ckan.logic.get_or_bust

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

    context['use_cache'] = False  # Disable package retrieval directly from Solr as contact.email is not there.

    if not data_dict.get('id') and not data_dict.get('name'):
        # Get package by data PIDs
        data_dict['id'] = utils.get_package_id_by_primary_pid(data_dict)

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

    return pkg_dict1


def _handle_package_id_on_create(data_dict):
    '''
    Create package id always on create. This method should set 'id' value for the
    given data_dict. The value should be unique in the system.
    If this method does not result in placing id to data_dict, then something
    is very wrong and the user does not have anything to do with it. This should
    always result in valid id getting placed into data_dict.
    '''

    data_dict['id'] = utils.get_unique_package_id()


def _handle_pids(data_dict):
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

    # If no primary identifier exists, use dataset id as primary identifier
    # by copying dataset id value to primary identifier PID
    if not utils.get_primary_pid(data_dict):
        if 'id' in data_dict and len(data_dict['id']) > 0:
            data_dict['pids'].insert(0, {'id': data_dict['id'],
                                    'type': 'primary',
                                    'provider': 'Etsin'
                                   })


def _add_ida_download_url(data_dict):
    '''
    Generate a download URL for actual data if no download URL has been specified
    and access application_rems is used for availability,
    and the dataset data appears to be from IDA.
    '''

    availability = data_dict.get('availability')
    external_id = data_dict.get('external_id')
    log.debug("Checking for dataset IDAiness through data PID: {p}".format(p=unicode(external_id)))
    if availability == 'access_application_rems' and \
        external_id and utils.is_ida_pid(external_id) and not \
        data_dict.get('access_application_download_URL'):

        new_url = utils.generate_ida_download_url(external_id)
        log.debug("Adding download URL for IDA dataset: {u}".format(u=new_url))
        data_dict['access_application_download_URL'] = new_url


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
    if data_dict.get('type') == 'harvest' and not user.sysadmin:
        ckan.lib.base.abort(401, _('Unauthorized to add a harvest source'))

    _remove_extras_from_data_dict(data_dict)

    data_dict = utils.dataset_to_resource(data_dict)

    if not user.name == 'harvest':
        _handle_package_id_on_create(data_dict)
    _handle_pids(data_dict)

    _add_ida_download_url(data_dict)
    
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

    _remove_extras_from_data_dict(data_dict)

    package_data = package_show(package_context, data_dict)

    if not 'resources' in data_dict:
        # When this is reached, we are updating a dataset, not creating a new resource
        old_resources = package_data.get('resources', [])
        data_dict['resources'] = old_resources
        data_dict = utils.dataset_to_resource(data_dict)
    else:
        data_dict['accept-terms'] = 'yes'  # This is not needed when adding a resource

    _handle_pids(data_dict)

    _add_ida_download_url(data_dict)

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


def _remove_extras_from_data_dict(data_dict):
    '''
    If the data_dict contains extras key with an array as value, one other extras
    value gets deleted for unknown reaasons at least in ckan's
    ckan.logic.action.update.package_update.

    Since extras is not supposed to be given in package_update (or package_create)
    call in any case, remove it just to make sure datasets do not get broken.

    :param data_dict:
    :return:
    '''

    if data_dict.get('extras'):
        del data_dict['extras']


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

    ret = ckan.logic.action.delete.package_delete(context, data_dict)
    index = index_for('package')
    index.remove_dict(data_dict)
    return ret


def dataset_purge(context, data_dict):
    '''
    Empty method because purging dataset needs to be disabled, 
    since datasets should exist even if they are deleted by users, so they
    can be referred to in the tombstone page.
    
    :param context: 
    :param data_dict: 
    :return: 
    '''
    return "Purging of datasets not allowed"


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
resource_delete = _decorate(ckan.logic.action.delete.resource_delete, 'resource', 'delete')
related_delete = _decorate(ckan.logic.action.delete.related_delete, 'related', 'delete')
group_create = _decorate(ckan.logic.action.create.group_create, 'group', 'create')
group_update = _decorate(ckan.logic.action.update.group_update, 'group', 'update')
group_delete = _decorate(ckan.logic.action.delete.group_delete, 'group', 'delete')
organization_create = _decorate(ckan.logic.action.create.organization_create, 'organization', 'create')
organization_update = _decorate(ckan.logic.action.update.organization_update, 'organization', 'update')
organization_delete = _decorate(ckan.logic.action.delete.organization_delete, 'organization', 'delete')


@clamd_wrapper.scan_for_malware
def resource_create(context, data_dict):
    return ckan.logic.action.create.resource_create(context, data_dict)


@clamd_wrapper.scan_for_malware
def resource_update(context, data_dict):
    return ckan.logic.action.update.resource_update(context, data_dict)


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

    def convert_to_dict(item):
        out = {}
        for k in ['id', 'name', 'title']:
            out[k] = getattr(item, k)
        out['hierarchy'] = get_hierarchy_string(item)
        return out

    def get_hierarchy_string(org_obj):
        parent_hierarchy = org_obj.get_parent_group_hierarchy(type='organization')
        parent_hierarchy.append(org_obj)
        return ' > '.join([o.display_name for o in parent_hierarchy])

    check_access('organization_autocomplete', context, data_dict)

    q = data_dict.get('q')
    query = model.Group.search_by_name_or_title(q, group_type=None, is_org=True).limit(20)
    out = map(convert_to_dict, query.all())

    return out


@side_effect_free
def organization_list_for_user(context, data_dict):
    '''
    Get a list organizations available for current user. Modify CKAN organization permissions before calling original
    action.

    :returns: list of dictized organizations that the user is authorized to edit
    :rtype: list of dicts
    '''
    # NOTE! CHANGING CKAN ORGANIZATION PERMISSIONS
    authz.ROLE_PERMISSIONS = settings.ROLE_PERMISSIONS

    return ckan.logic.action.get.organization_list_for_user(context, data_dict)


@side_effect_free
def organization_list(context, data_dict):
    """ Modified from ckan.logic.action.get._group_or_org_list.
        Sort by title instead of name and lower case ordering.

        For some reason, sorting by packages filters out all
        organizations without datasets, which results to
        a wrong number of organizations in the organization
        index view. The sort after a search query should,
        however default to 'packages'. 
    """

    if not data_dict.get('sort'):
        if data_dict.get('q'):
            data_dict['sort'] = 'packages'
        else:
            data_dict['sort'] = 'title'

    return ckan.logic.action.get.organization_list(context, data_dict)


def member_create(context, data_dict=None):
    '''
    Make an object (e.g. a user, dataset or group) a member of a group.

    Custom organization permission handling added on top of CKAN's own member_create action.
    '''
    _log_action('Member', 'create', context['user'], data_dict.get('id'))

    # NOTE! CHANGING CKAN ORGANIZATION PERMISSIONS
    authz.ROLE_PERMISSIONS = settings.ROLE_PERMISSIONS

    user = context['user']
    user_id = authz.get_user_id_for_username(user, allow_none=True)

    group_id, obj_id, obj_type, capacity = _get_or_bust(data_dict, ['id', 'object', 'object_type', 'capacity'])

    # get role the user has for the group
    user_role = utils.get_member_role(group_id, user_id)

    if obj_type == 'user':
        # get role for the target of this role change
        target_role = utils.get_member_role(group_id, obj_id)
        if target_role is None:
            target_role = capacity

        if authz.is_sysadmin(user):
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
    authz.ROLE_PERMISSIONS = settings.ROLE_PERMISSIONS

    user = context['user']
    user_id = authz.get_user_id_for_username(user, allow_none=True)

    group_id, target_name, obj_type = _get_or_bust(data_dict, ['id', 'object', 'object_type'])

    if obj_type == 'user':
        # get user's role for this group
        user_role = utils.get_member_role(group_id, user_id)

        target_id = authz.get_user_id_for_username(target_name, allow_none=True)

        # get target's role for this group
        target_role = utils.get_member_role(group_id, target_id)

        if authz.is_sysadmin(user):
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
    authz.ROLE_PERMISSIONS = settings.ROLE_PERMISSIONS

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

    trans = authz.roles_trans()

    def translated_capacity(capacity):
        try:
            return _Capacity(trans[capacity], capacity) # Etsin modification
        except KeyError:
            return capacity

    return [(m.table_id, m.table_name, translated_capacity(m.capacity))
            for m in q.all()]


@side_effect_free
def organization_show(context, data_dict):
    if not authz.is_authorized('member_list', context, {'id': data_dict.get('id')}).get('success'):
        data_dict['include_users'] = False
    return ckan.logic.action.get.organization_show(context, data_dict)


@side_effect_free
def group_show(context, data_dict):
    if not authz.is_authorized('member_list', context, {'id': data_dict.get('id')}).get('success'):
        data_dict['include_users'] = False
    return ckan.logic.action.get.group_show(context, data_dict)


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
