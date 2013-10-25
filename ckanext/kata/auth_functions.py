from ckan.logic.auth import update
from ckan.model import User, Package
import ckanext.kata.settings as settings
from pylons.i18n import _
import ckan.new_authz as new_authz
from ckan.logic.auth import get_package_object
import logging

log = logging.getLogger(__name__)


def is_owner(context, data_dict):
    '''
    This is used in "request edit rights" feature.
    '''
    
    pkg = context.get('package', None)
    roles = pkg.roles if pkg else Package.get(data_dict['id']).roles
    user = context.get('user', False)
    if user:
        for role in roles:
            ruser = User.get(role.user_id)
            if user == ruser.name and role.role in ('admin', 'editor'):
                return {'success': True}
    else:
        return {'success': False}
    return {'success': False}


def allow_edit_resource(context, data_dict):
    '''
    Check if a user is allowed edit a resource.
    '''

    auth_dict = update.resource_update(context, data_dict)

    if (data_dict['resource_type'] == settings.RESOURCE_TYPE_DATASET):
        return {'success': False, 'msg': _('Resource %s not editable') % (data_dict['id'])}
    else:
        return auth_dict
    
def package_delete(context, data_dict):
    '''
    Modified check from CKAN, whether the user has a permission to
    delete the package. In addition to privileges given by CKAN's
    authorisation, also the package owner has full privileges in Kata.
    
    :param context:
    :param data_dict:
    :return dict: 'success': True|False
    '''
    user = context['user']
    package = get_package_object(context, data_dict)
    if is_owner(context, data_dict)['success'] == True:
        return {'success': True}
    else:
        authorized = new_authz.has_user_permission_for_group_or_org(package.owner_org, user, 'delete_dataset')
        if not authorized:
            return {'success': False, 'msg': _('User %s not authorized to delete package %s') % (str(user),package.id)}
        else:
            return {'success': True}
    return {'success': False}
