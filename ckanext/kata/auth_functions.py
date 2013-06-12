from ckan.model import User, Package

def is_owner(context, data_dict):
    """
    This is used in "request edit rights" feature.
    """
    
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
