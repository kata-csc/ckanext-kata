# coding=utf-8
'''
Template helpers for Kata CKAN extension.
'''

from paste.deploy.converters import asbool
from pylons import config
import functionally as fn
import logging
from iso639 import languages
import re
from pylons.decorators.cache import beaker_cache
import json
import urllib2

import ckan.model as model
from ckan.model import Related, Package, User
from ckan.lib.base import g, h, c
from ckan.logic import get_action, ValidationError
from ckanext.kata import settings, utils
from ckan.lib.navl.dictization_functions import validate
from ckan.lib import plugins
from ckanext.kata.utils import get_pids_by_type
from pylons.i18n.translation import gettext_noop as N_

log = logging.getLogger(__name__)


class LoopIndex(object):
    """ Simple index object for Jinja2 templates. Avoids problem with Jinja2 variable scope. """

    def __init__(self):
        """ New index with value 0 """
        super(LoopIndex, self).__init__()
        self.index = 0

    def increase(self):
        """ Increase index value by one and return previous value """
        current = self.index
        self.index = self.index + 1
        return current

    def next(self):
        """ Returns next index number, but does not increase value. """
        return self.index + 1

    def __repr__(self):
        return str(self.index)

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
        # Todo: fix. The ANDs make no sense
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

    :param errors: the error dict
    :param field: field name
    :param index: index, eg. agents are repeatable -> a certain agent might lie in index 2
    :param name:
    :returns: `[u'error1', u'error2']`
    '''
    error = []
    error_dict = errors.get(field)
    try:
        if error_dict and error_dict[index]:
            error = error_dict[index].get(name)
    except IndexError:
        pass
    return error


def get_package_ratings_for_data_dict(data_dict):
    '''
    Create a metadata rating (1-5) for given data_dict.

    This is the same as :meth:`get_package_ratings` but can be used
    for getting metadata ratings e.g. for search results where
    only raw data_dicts are available rather than already-converted
    package dicts.

    :param data_dict: A CKAN data_dict
    '''
    from ckanext.kata.schemas import Schemas         # Importing here prevents circular import

    context = {
        'model': model,
        'schema': Schemas.show_package_schema()
    }
    try:
        pkg_dict = get_action('package_show')(context, data_dict)
    except ValidationError:
        return (0, u'○○○○○')

    return get_package_ratings(pkg_dict)


def get_package_ratings(data):
    '''
    Create a metadata rating (1-5) for given dataset

    :param data: A CKAN data_dict
    :returns: `(rating, stars)`
    '''
    score = 0   # Scale 0-49

    required_fields =['pids', 'version', 'contact', 'license_id', 'agent', 'language', 'availability']
    if all(data.get(field) for field in required_fields):
        score += 2

    # MAX 2

    pid_types = [pid.get('type') for pid in data.get('pids', [])]
    pid_types_expected = ['data', 'metadata', 'version']
    if len(pid_types) < 3:
        # The minimum metadata model is a bit vague in this part, this is one iterpretation
        pid_types_expected.pop(2)

    if all(pid_type in pid_types for pid_type in pid_types_expected):
        score += 2 * len(pid_types) if len(pid_types) < 3 else 6

    if len(unicode(data.get('version', ''))) > 15:   # ISO8601 datetime
        score += 1

    # MAX 9

    if data.get('license_id', '') not in ['notspecified', '']:
        score += 6

    if not (data.get('tags') or data.get('tag_string')):    # Either of these should be present
        score -= 5  # MINUS

    if len(data.get('agent', [])) >= 2:
        score += 2 * len(data['agent']) if len(data['agent']) < 6 else 6

    if len(data.get('event', [])) >= 1:
        score += 1

    if get_funder(data):
        score += 6

    # MAX 28

    if len(unicode(data.get('notes', ''))) >= 10:
        score += (len(data['notes']) / 10) if len(data['notes']) < 60 else 6

    required_fields = ['geographic_coverage', 'event', 'checksum', 'algorithm', 'mimetype', 'langtitle']
    score += len(filter(lambda field: data.get(field), required_fields))

    # MAX 40

    if filter(lambda con: con.get('name') and con.get('email') and con.get('URL') and con.get('phone'), data.get('contact', [])):
        score += 4

    # MAX 44

    if data.get('temporal_coverage_begin') and data.get('temporal_coverage_end'):
        score += 1

    if data.get('discipline'):
        score += 4

    # MAX 49

    rating = 1 + int(score / 10)
    stars = u'●●●●●'[:rating] + u'○○○○○'[rating:]   # Star rating as string
    return (rating, stars)


def get_related_urls(pkg):
    '''
    Get related urls for package
    '''
    ret = []
    for rel in Related.get_for_dataset(pkg):
        ret.append(rel.related.url)
    return ret

def get_download_url(pkg_dict, type=''):
    '''
    :param pkg_dict: package dictionary
    :return: download url or None
    '''
    return pkg_dict.get(settings.AVAILABILITY_OPTIONS.get(pkg_dict.get('availability', '')), None)


def get_if_url(data):
    '''
    Try to guess if data is sufficient type for rdf:about

    :param data: the data to check out
    :rtype: boolean
    '''
    if data and (data.startswith('http://') or data.startswith('https://') or \
    data.startswith('urn:')):
        return True
    return False


def string_to_list(data):
    '''
    Split languages and make it a list for Genshi (read.rdf)

    :param data: the string to split
    :rtype: list
    '''
    if data:
        return data.split(", ")
    return ''


def get_first_admin(id):
    '''
    Get the url of the first one with an admin role

    :param id: the package id
    :returns: profile url
    :rtype: string
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
    
    :returns: LICENSED, COPYRIGHTED, OTHER or PUBLIC DOMAIN
    '''
    if license == 'other-pd':
        return "PUBLIC DOMAIN"
    elif license and license not in ['notspecified', 'other-closed', 'other_closed', 'other-nc', 'other-at', 'other-open']:
        return "LICENSED"
    return "OTHER"


def get_authors(data_dict):
    '''Get all authors from agent field in data_dict'''
    return filter(lambda x: x.get('role') == u'author', data_dict.get('agent', []))


def get_contacts(data_dict):
    '''Get all contacts from data_dict'''
    return data_dict.get('contact', [])


def get_distributors(data_dict):
    '''Get a all distributors from agent field in data_dict'''
    return filter(lambda x: x.get('role') == u'distributor', data_dict.get('agent', []))


def get_distributor(data_dict):
    '''Get a single distributor from agent field in data_dict'''
    return fn.first(get_distributors(data_dict))


def get_contributors(data_dict):
    '''Get a all contributors from agent field in data_dict'''
    return filter(lambda x: x.get('role') == u'contributor', data_dict.get('agent', []))


def get_owners(data_dict):
    '''Get a all owners from agent field in data_dict'''
    return filter(lambda x: x.get('role') == u'owner', data_dict.get('agent', []))


def resolve_agent_role(role):
    '''
    Get a non-translated role name.
    '''
    return settings.AGENT_ROLES.get(role, None)


def get_funder(data_dict):
    '''Get a single funder from agent field in data_dict'''
    return fn.first(get_funders(data_dict))


def get_funders(data_dict):
    '''Get all funders from agent field in data_dict'''
    return utils.get_funders(data_dict)

def is_allowed_org_member_edit(group_dict, user_id, target_id, target_role):
    '''
    Check if the user is allowed to edit an organization member

    :param group_dict: dict of all groups (organizations)
    :param user_id: user id
    :param target_id: target user id
    :param target_role: target's current role
    '''
    target_role = getattr(target_role, 'original', target_role)

    user = fn.first(filter(lambda user: user.get('id') == user_id, group_dict['users']))

    if not user:
        return False

    user_role = user.get('capacity')
    target_role = target_role.lower()

    if user.get('sysadmin'):
        return True

    for possible_role in ['admin', 'editor', 'member']:
        if settings.ORGANIZATION_MEMBER_PERMISSIONS.get((user_role, target_role, possible_role, user_id == target_id), False):
            return True

    return False


def get_visibility_options():
    '''
    Get possible dataset visibility options for this group and user
    For now the specs say that everyone can add public/private datasets
    to any organisation, thus the simple list to return
    '''

    return [(True, N_('Unpublished')), (False, N_('Published'))]


def create_loop_index():
    """ Create and return LoopIndex object """
    return LoopIndex()


def get_dict_errors(errors, errors_key, field_key):
    """ Return dictionary error values from errors dictionary """
    result = []

    if errors:
        for error in errors.get(errors_key, []):
            if isinstance(error, dict) and error.get('key', None) == field_key:
                result.append(error.get('value', "Internal error"))

    return result


def dataset_is_valid(package):
    """ Check if given dataset is valid. Uses schema from plugin.
        Return true if dataset is valid.
    """
    package_plugin = plugins.lookup_package_plugin(package['type'])
    _, errors = validate(package, package_plugin.update_package_schema(), {'model': model, 'session': model.Session, 'user': c.user})
    return not bool(errors)


def filter_system_users(users):
    """
    Filters system users ('logged_in', 'visitor', 'harvest') out of the
    given iterable of users.
    :param users: an iterable of user data dicts
    :return: a new list with system users omitted
    :rtype: list
    """

    system_user_names = ['logged_in', 'visitor', 'harvest']
    return filter(lambda x: x.get('user') not in system_user_names, users)


def is_urn(name):
    return name and name.startswith('urn:nbn:fi:')


def get_urn_fi_address(package):
    if package.get('id', '').startswith('http://') or package.get('id', '').startswith('https://'):
        return package.get('id')
    pid = get_pids_by_type('data', package, primary=True)[0].get('id', None)
    if is_urn(pid):
        template = config.get('ckanext.kata.urn_address_template', "http://urn.fi/%(pid)s")
        return template % {'pid': pid}
    return ''


def modify_error_summary(errors):
    '''
    Modifies error_summary keys. Otherwise the keys in database are printed, which leads
    to strings like "Lantitle", "Tag string" etc.

    :param errors: error summary dictionary
    :return: errors: keys as specified in settings.ERRORS are changed

    '''
    # Saw an effect, where Tag string and Tags both were displayed and they were identical
    if (errors.get('Tag string', False) and errors.get('Tags', False)) and \
       (errors.get('Tag string') == errors.get('Tags')):
        errors.pop('Tag string')

    for (key, value) in settings.ERRORS.items():
        if errors and errors.get(key, False):
            errors[value] = errors.get(key)
            errors.pop(key)

    return errors


def get_pid_types():
    '''
    :return: PID types defined in settings.py
    '''
    return settings.PID_TYPES


def is_backup_instance():
    '''
    :return: Config value kata.is_backup in kata.ini as boolean
    '''
    return asbool(config.get('kata.is_backup', False))


def _sort_organizations(organization_dictionary):
    return sorted(organization_dictionary, key=lambda organization: organization.get('title', "").lower())


def list_organisations(user):
    '''
    Lists all organisations

    :param user: the logged in user
    :return: organization_list
    '''
    context = dict()
    context['model'] = model
    context['user'] = user.get('name')
    data_dict = dict()
    data_dict['all_fields'] = True

    return _sort_organizations(get_action('organization_list')(context, data_dict))


def organizations_available(permission='edit_group'):
    organizations = _sort_organizations(h.organizations_available(permission))
    if permission == 'create_dataset':
        for organization in organizations:
            organization['name'] = organization.get('title', None) or organization['name']
    return organizations


def convert_language_code(lang, to_format, throw_exceptions=True):
    '''
    Convert ISO 639 language code to <to_format>. Throws KeyError if none found.

    :param throw_exceptions: Set to False to never throw KeyError.
    :param lang: original language code
    :param to_format: 'alpha2' or 'alpha3'
    '''

    mappings = {'alpha2': 'part1', 'alpha3': 'part2b'}
    if to_format in mappings:
        to_format = mappings[to_format]

    if throw_exceptions:
        catch = [KeyError, None]
    else:
        catch = [Exception, Exception]

    try:
        return getattr(languages.get(part2b=lang), to_format)
    except catch[0]:
        try:
            return getattr(languages.get(part3=lang), to_format)
        except catch[0]:
            try:
                return getattr(languages.get(part1=lang), to_format)
            except catch[1]:
                return ''

def split_disciplines(disc):
    '''
    Split disciplines with the help of lookahead

    :param disc: discipline string
    :return: list of disciplines
    '''
    if isinstance(disc, basestring):
        return re.split(r',(?! )', disc)


def get_ga_id():
    '''

    :return: google analytics id
    '''
    return config.get('kata.ga_id', '')

@beaker_cache(type="dbm", expire=86400)
def get_labels_for_uri(uri, ontology=None):
    '''
    Return all labels for an uri

    :param uri: single uri to get the labels for
    :param ontology: ontology to use or none to guess it
    :return: dict of labels (fi, en, sv), [{u'lang': u'fi', u'value': u'Matematiikka},{u'lang': u'en'...}] or None
    '''

    if not uri.startswith("http://www.yso.fi") or not isinstance(uri, basestring):
        return None

    # try to find ontology, if it wasn't provided. Copes with some erratic inputs
    if not ontology:
        search = re.search(r'.*\/onto\/([^\/]*)\/.*$', uri)
        try:
            ontology = search.group(1)
        except AttributeError:
            return None
    if not ontology:
        return None

    url = "http://finto.fi/rest/v1/{ontology}/data?uri={uri}&format=application/json".format(ontology=ontology, uri=uri)
    # Reverse DNS resolving can be extremely slow
    data = urllib2.urlopen(url).read()
    jsondata = json.loads(data)
    if jsondata.get('graph'):
        for item in jsondata['graph']:
            if item.get('uri') == uri:
                return item['prefLabel']

    return None

@beaker_cache(type="dbm", expire=86400)
def get_label_for_uri(uri, ontology=None, lang=None):
    '''
    Return a label for an uri

    :param uri: single uri to get a label for
    :param ontology: ontology to use or none
    :param lang: language of the label. If not provided, uses the language of environment
    :return:
    '''
    if not uri.startswith("http://www.yso.fi") or not isinstance(uri, basestring):
        return uri

    if not lang:
        lang = h.lang()

    labels = get_labels_for_uri(uri, ontology)
    if labels:
        for label in labels:
            if label.get('lang') == lang:
                return label.get('value') or uri

    return uri

def disciplines_string_resolved(disciplines, ontology=None, lang=None):
    '''

    :param disciplines: comma separated string containing all disciplines
    :param ontology: ontology to use or none to guess it
    :param lang: language of the label. If not provided, uses the language set in environment.
    :return: comma separated string of resolved disciplines
    '''
    disc_list = split_disciplines(disciplines)
    if hasattr(disc_list, "__iter__"):
        return ", ".join([get_label_for_uri(x, ontology, lang) for x in disc_list])
    else:
        return disciplines