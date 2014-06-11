from ckan.lib.base import g, h
from ckanext.kata import settings
from ckan.model import Related, Package, User
from pylons import config

def has_agents_field(data_dict, field):
    '''Return true if some of the data dict's agents has attribute given in field.'''
    return [] != filter(lambda x : x.get(field), data_dict.get('agent', []))

def has_contacts_field(data_dict, field):
    '''Return true if some of the data dict's contacts has attribute given in field'.'''
    return [] != filter(lambda x : x.get(field), data_dict.get('contact', []))

def reference_update(ref):
    #@beaker_cache(type="dbm", expire=2678400)
    def cached_url(url):
        return url
    return cached_url(ref)

def kata_sorted_extras(list_):
    '''
    Used for outputting package extras, skips package_hide_extras
    '''
    output = []
    for extra in sorted(list_, key=lambda x:x['key']):
        if extra.get('state') == 'deleted':
            continue

        key, val = extra['key'], extra['value']
        if key in g.package_hide_extras and\
            key in settings.KATA_FIELDS and\
            key.startswith('author_') and\
            key.startswith('organization_'):
            continue

        if  key.startswith('title_') or\
            key.startswith('lang_title_') or\
            key == 'harvest_object_id' or\
            key == 'harvest_source_id' or\
            key == 'harvest_source_title':
            continue

        found = False
        for _key in g.package_hide_extras:
            if extra['key'].startswith(_key):
                found = True
        if found:
            continue

        if isinstance(val, (list, tuple)):
            val = ", ".join(map(unicode, val))
        output.append((key, val))
    return output

def get_dict_field_errors(errors, field, index, name):
    '''Get errors correctly for fields that are represented as nested dict fields in data_dict.

    :return: [u'error1', u'error2']
    '''
    error = []
    error_dict = errors.get(field)
    if error_dict and error_dict[index]:
        error = error_dict[index].get(name)
    return error

def get_related_urls(pkg):
    '''
    Get related urls for package
    '''
    ret = []
    for rel in Related.get_for_dataset(pkg):
        ret.append(rel.related.url)
    return ret

def get_rdf_extras(pkg_dict):
    '''
    Get extras that have no defined location in rdf
    
    Contains much "manual" stuff for keeping the logical
    order and for prettier display
    
    :pkg_dict: the package data dict
    :return: [{ 'key': 'the key', 'value': 'the value'}, {..}, ..]
    '''
    ret = []
    if pkg_dict.get('discipline', None):
        ret.append({'key': 'discipline', 
                    'value': pkg_dict.get('discipline', None)})
    if pkg_dict.get('event', None):
        for event in pkg_dict.get('event'):
            value = 'type=' + event.get('type', '') + '; who=' + \
                    event.get('who', '') + '; when=' + \
                    event.get('when', '') + '; description=' + \
                    event.get('descr', '')
            ret.append({'key': 'event', 'value': value})
    availability = pkg_dict.get('availability', '')
    if availability == 'direct_download':
        ret.append({'key': 'availability', 
                    'value': availability})
        ret.append({'key': 'direct_download_URL', 
                    'value': pkg_dict.get('direct_download_URL', None)})            
    if availability == 'access_application':
        ret.append({'key': 'availability', 
                    'value': availability})
        ret.append({'key': 'access_application_URL', 
                    'value': pkg_dict.get('access_application_URL', None)})
    if availability == 'access_request':
        ret.append({'key': 'availability', 'value': availability})
        ret.append({'key': 'access_request_URL', 
                    'value': pkg_dict.get('access_request_URL', None)})
    if availability == 'contact_owner':
         ret.append({'key': 'availability', 'value': availability})
    
    ret.append({'key': 'hash', 'value': pkg_dict.get('hash', None)})
    ret.append({'key': 'algorithm', 'value': pkg_dict.get('algorithm', None)})
    
    return ret

def get_if_url(data):
    '''
    Try to guess if data is sufficient type for rdf:about
    '''
    if data and (data.startswith('http://') or data.startswith('https://') or \
    data.startswith('urn:')):
        return True
    return False

def string_to_list(data):
    '''
    Split languages and make it a list for Genshi (read.rdf)
    '''
    if data:
        return data.split(", ")
    return ''

def get_first_admin(id):
    '''
    Get the url of the first one with an admin role
    '''
    pkg = Package.get(id)
    if pkg:
        data = pkg.as_dict()
        user = None
        if pkg.roles:
            owner = [role for role in pkg.roles if role.role == 'admin']
            if len(owner):
                user = User.get(owner[0].user_id)
                profileurl = ""
                if user:
                    profileurl = config.get('ckan.site_url', '') + \
                                 h.url_for(controller="user", action="read", 
                                           id=user.name)
                    return profileurl
    return False

def get_rightscategory(license):
    '''
    Return rightscategory based on license id
    
    :return LICENSED, COPYRIGHTED, PUBLIC DOMAIN
    '''
    if license == "other_closed":
        return "COPYRIGHTED"
    if license == "cc-zero" or license == "cc-by" or license == "cc-by-4.0":
        return "LICENSED"
    # Can not recognise the license:
    return "OTHER"
