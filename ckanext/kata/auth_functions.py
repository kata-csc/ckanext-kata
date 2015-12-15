'''
Custom authorization functions for actions.
'''

import logging

from pylons.i18n import _

import ckan.logic
import ckan.logic.auth as logic_auth
import ckanext.kata.settings as settings
from ckan import authz
from ckan.logic import NotFound
from ckan.logic.auth import get_package_object, update
from ckan.logic.auth.create import _check_group_auth
from ckan.model import User, Package

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

    pkg = context.get('package', None) or Package.get(data_dict['id'])
    roles = pkg.roles if pkg else []
    user = context.get('user', False)
    if user:
        for role in roles:
            ruser = User.get(role.user.id)
            if user == ruser.name and role.role in ('admin', 'editor'):
                return {'success': True}

    # Check if the user has editor rights to this dataset through an organization
    package = get_package_object(context, data_dict)
    if authz.has_user_permission_for_group_or_org(package.owner_org, user, 'delete_dataset'):
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

    resource = logic_auth.get_resource_object(context, data_dict)

    if resource.resource_type == settings.RESOURCE_TYPE_DATASET:
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
        authorized = authz.has_user_permission_for_group_or_org(package.owner_org, user, 'delete_dataset')
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

    # Below is copy-pasted from CKAN auth.create.package_create
    # to allow dataset creation without explicit organization permissions.

    if authz.auth_is_anon_user(context):
        check1 = all(authz.check_config_permission(p) for p in (
            'anon_create_dataset',
            'create_dataset_if_not_in_organization',
            'create_unowned_dataset',
        ))
    else:
        check1 = True  # Registered users may create datasets

    if not check1:
        return {'success': False, 'msg': _('User %s not authorized to create packages') % user}

    check2 = _check_group_auth(context, data_dict)
    if not check2:
        return {'success': False, 'msg': _('User %s not authorized to edit these groups') % user}

    # If an organization is given are we able to add a dataset to it?
    data_dict = data_dict or {}
    org_id = data_dict.get('owner_org')
    if org_id and not authz.has_user_permission_for_group_or_org(
            org_id, user, 'create_dataset'):
        return {'success': False, 'msg': _('User %s not authorized to add dataset to this organization') % user}
    return {'success': True}


@ckan.logic.auth_allow_anonymous_access
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


def package_revision_list(context, data_dict):
    return package_show(context, data_dict)


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
    if logged_in_user and target_user_obj and hasattr(target_user_obj,
                                                      'name') and logged_in_user == target_user_obj.name:
        return {'success': True}
    else:
        return logic_auth.get.sysadmin(context, data_dict)


def member_list(context, data_dict):
    '''
    Limits group/organization member listing to editors and administrators
    of the organization.

    :param context:
    :param data_dict:
    :return:
    '''

    user_name = context.get('user')
    organization_id = data_dict.get('id')

    if authz.has_user_permission_for_group_or_org(organization_id, user_name, 'editor'):
        return {'success': True}
    else:
        return {'success': False}


def resource_delete(context, data_dict):
    '''
    Nearly plain copying of resource_delete: CKAN calls local package_delete, thus passing our local version of it.

    :param context: context
    :param data_dict: data_dict
    :return: dict with success and optional msg
    '''

    model = context['model']
    user = context.get('user')
    resource = logic_auth.get_resource_object(context, data_dict)

    # check authentication against package
    pkg = model.Package.get(resource.package_id)
    if not pkg:
        raise NotFound(_('No package found for this resource, cannot check auth.'))

    pkg_dict = {'id': pkg.id}
    authorized = package_delete(context, pkg_dict).get('success')

    if not authorized:
        return {'success': False, 'msg': _('User %s not authorized to delete resource %s') % (user, resource.id)}
    else:
        return {'success': True}
