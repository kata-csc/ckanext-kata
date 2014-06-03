from ckan.lib.base import g
from ckanext.kata import settings

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
