'''
Custom authorization functions for actions.
'''

import logging

from pylons.i18n import _

import ckan.new_authz as new_authz
from ckan.logic.auth import get_package_object, update
from ckan.model import User, Package
import ckanext.kata.settings as settings
import ckan.logic.auth as logic_auth


log = logging.getLogger(__name__)


def is_owner(context, data_dict):
    '''
    This is used in "request edit rights" feature.
    Checks if the user is admin or editor of the
    package in question

    :param context: context
    :param data_dict: package data
    :type data_dict: dictionary

    :rtype: dictionary
    '''

    pkg = context.get('package', None)
    roles = pkg.roles if pkg else Package.get(data_dict['id']).roles
    user = context.get('user', False)
    if user:
        for role in roles:
            ruser = User.get(role.user.id)
            if user == ruser.name and role.role in ('admin', 'editor'):
                return {'success': True}

    # Check if the user has editor rights to this dataset through an organization
    package = get_package_object(context, data_dict)
    if new_authz.has_user_permission_for_group_or_org(package.owner_org, user, 'delete_dataset'):
        return {'success': True}

    return {'success': False}


def edit_resource(context, data_dict):
    '''
    Check if a user is allowed edit a resource.

    :param context: context
    :param data_dict: data dictionary

    :rype: dictionary
    '''
    auth_dict = update.resource_update(context, data_dict)

    if data_dict['resource_type'] == settings.RESOURCE_TYPE_DATASET:
        return {'success': False, 'msg': _('Resource %s not editable') % (data_dict['id'])}
    else:
        return auth_dict


def package_delete(context, data_dict):
    '''
    Modified check from CKAN, whether the user has a permission to
    delete the package. In addition to privileges given by CKAN's
    authorisation, also the package owner has full privileges in Kata.
    
    :param context: context
    :type context: dictionary
    :param data_dict: package data
    :type data_dict: dictionary
    :rtype: dictionary with 'success': True|False
    '''
    user = context['user']
    package = get_package_object(context, data_dict)
    if is_owner(context, data_dict)['success'] == True:
    # if h.check_access('package_delete', data_dict):
        return {'success': True}
    else:
        authorized = new_authz.has_user_permission_for_group_or_org(package.owner_org, user, 'delete_dataset')
        if not authorized:
            return {'success': False, 'msg': _('User %s not authorized to delete package %s') % (str(user), package.id)}
        else:
            return {'success': True}


def package_create(context, data_dict=None):
    '''
    Modified from CKAN's original check. Any logged in user can add
    a dataset to any organisation.
    Packages owner check is done when adding a resource.

    :param context: context
    :param data_dict: data_dict
    :return: dictionary with 'success': True|False
    '''

    user = context['user']

    # Needed in metadata supplements
    if context.get('package', False):
        return is_owner(context, context.get('package').get('id'))

    # If an organization is given are we able to add a dataset to it?
    data_dict = data_dict or {}
    org_id = data_dict.get('owner_org', False)
    if org_id and not kata_has_user_permission_for_org(
            org_id, user, 'create_dataset'):
        return {'success': False, 'msg': _('User %s not authorized to add a dataset') % user}
    elif org_id and kata_has_user_permission_for_org(org_id, user, 'create_dataset'):
        return {'success': True}

    return logic_auth.create.package_create(context, data_dict)


def package_show(context, data_dict):
    '''
    Modified from CKAN's original check. Package's owner
    can see the dataset no matter in what organization it lies in.

    :param context: context
    :type context: dictionary
    :param data_dict: package data
    :type data_dict: dictionary
    :rtype: dictionary with 'success': True|False
    '''

    is_ownr = is_owner(context, data_dict)

    if is_ownr.get('success') == False:
        return logic_auth.get.package_show(context, data_dict)
    else:
        return is_ownr

def kata_has_user_permission_for_org(org_id, user_name, permission):
    '''
    Used by auth function package create: everyone has a right to add a dataset to any organisation

    :param user_name:
    :param permission:
    :return: True, as everyone has a right to add a dataset to an organisation
    '''
    if org_id and user_name and permission:
        return True
    return False

def user_list(context, data_dict):
    '''
    Override to prevent access to user listing for non-admin users.
    :param context:
    :param data_dict:
    :return:
    '''

    return logic_auth.get.sysadmin(context, data_dict)

def user_autocomplete(context, data_dict):
    '''
    Override to explicitly allow logged in users to have
    user autocompletion even if user_list is disallowed.
    :param context:
    :param data_dict:
    :return:
    '''

    user_name = context.get('user')
    user_obj = User.get(user_name) if user_name else None

    if user_obj:
        return {'success': True}
    else:
        return {'success': False}

def user_activity_list(context, data_dict):
    '''
    Disables user activity listing except for sysadmins and the users themselves.
    :param context:
    :param data_dict:
    :return:
    '''

    # Allow any logged in user to view their own activity stream
    logged_in_user = context.get('user')
    target_user_obj = context.get('user_obj')
    if logged_in_user and target_user_obj and hasattr(target_user_obj, 'name') and logged_in_user == target_user_obj.name:
        return {'success': True}
    else:
        return logic_auth.get.sysadmin(context, data_dict)

def package_activity_list(context, data_dict):
    '''
    Disables package activity listing from non-sysadmin users.
    :param context:
    :param data_dict:
    :return:
    '''

    return logic_auth.get.sysadmin(context, data_dict)

def group_activity_list(context, data_dict):
    '''
    Disables group activity listing from non-sysadmin users.
    :param context:
    :param data_dict:
    :return:
    '''

    return logic_auth.get.sysadmin(context, data_dict)

def organization_activity_list(context, data_dict):
    '''
    Disables organization activity listing from non-sysadmin users.
    :param context:
    :param data_dict:
    :return:
    '''

    return logic_auth.get.sysadmin(context, data_dict)
