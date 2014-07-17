'''
Custom authorization functions for actions.
'''

import logging

from pylons.i18n import _

import ckan.new_authz as new_authz
from ckan.logic.auth import get_package_object, update
from ckan.model import User, Package
import ckanext.kata.settings as settings


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
    # TODO: Don't use is_owner, but rather the one below and fix possible issues with missing rights for package editors
    # if h.check_access('package_delete', data_dict):
        return {'success': True}
    else:
        authorized = new_authz.has_user_permission_for_group_or_org(package.owner_org, user, 'delete_dataset')
        if not authorized:
            return {'success': False, 'msg': _('User %s not authorized to delete package %s') % (str(user), package.id)}
        else:
            return {'success': True}
