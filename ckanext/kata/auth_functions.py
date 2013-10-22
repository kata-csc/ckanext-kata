from ckan.logic.auth import update
from ckan.model import User, Package
import ckanext.kata.settings as settings
from pylons.i18n import _


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