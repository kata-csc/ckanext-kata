# coding=utf-8
'''
Template helpers for Kata CKAN extension.
'''
import iso8601
import os
from paste.deploy.converters import asbool
from pylons import config
import functionally as fn
import logging
from iso639 import languages
import re
from pylons.decorators.cache import beaker_cache
import json
import urllib2
import httplib
import copy
from urlparse import urlparse

import ckan.model as model
from ckan.model import Related, Package, User
from ckan.lib.base import g, h, c
from ckan.logic import get_action, ValidationError
from ckanext.kata import settings, utils
from ckan.lib.navl.dictization_functions import validate
from ckan.lib import plugins
from pylons.i18n.translation import gettext_noop as N_
from ckan.common import request
from webhelpers.html import literal

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


def reference_update(ref):
    # @beaker_cache(type="dbm", expire=2678400)
    def cached_url(url):
        return url
    return cached_url(ref)


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

    required_fields = ['pids', 'version', 'contact', 'license_id', 'agent', 'language', 'availability']
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

    ag = list()
    for d in data.get('agent', []):
        if d.get('role'):
            ag.append(d)
    if len(ag) >= 2:
        score += 2 * len(ag) if len(ag) < 6 else 6

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

    if filter(lambda con: con.get('name') and con.get('email') and con.get('URL') and con.get('phone'),
              data.get('contact', [])):
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


def get_description(package):
    '''
    Get description (notes)

    :return: translated notes from multilanguage field or notes as is
    '''
    try:
        t = package.get('notes', '')
        json.loads(t)
        return get_translation(t)
    except (ValueError, TypeError):
        return package.get('notes', '')


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
    if data and (data.startswith('http://') or data.startswith('https://') or
                 data.startswith('urn:')):
        return True
    else:
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


def get_rightscategory(data_dict):
    '''
    Return METS rights category and rights declaration for dataset

    :returns: CONTRACTUAL, LICENSED, COPYRIGHTED or PUBLIC DOMAIN
    '''

    license = data_dict.get('license_id')
    availability = data_dict.get('availability')

    declarations = []

    if availability in ['access_application', 'access_request']:
        category = "CONTRACTUAL"
        declarations.append(data_dict.get('access_application_URL') or data_dict.get('access_request_URL'))
    elif license in ['other-pd', "ODC-PDDL-1.0", "CC0-1.0", "cc-zero"]:
        category = "PUBLIC DOMAIN"
    elif license and license[:2] in ['CC', 'OD']:
        category = "LICENSED"
    else:
        category = "COPYRIGHTED"

    declarations.append(data_dict.get('license_url') or data_dict.get('license_URL') or data_dict.get('license_id'))

    return category, declarations


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
    return settings.AGENT_ROLES.get(role, role.title())


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
        if settings.ORGANIZATION_MEMBER_PERMISSIONS.get((user_role, target_role, possible_role, user_id == target_id)):
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
    package['accept-terms'] = u'True'
    package_plugin = plugins.lookup_package_plugin(package['type'])
    _, errors = validate(package, package_plugin.update_package_schema(),
                         {'model': model, 'session': model.Session, 'user': c.user})
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


def is_url(data):
    return data.startswith('http://') or data.startswith('https://')


def get_dataset_permanent_address(package):
    package_id = package.get('id', '')
    template = config.get('ckanext.kata.urn_address_template', "http://urn.fi/%(id)s")
    return template % {'id': package_id if package_id else 'ERROR'}


def get_dummy_title():
    return json.dumps({
      'fin': 'Otsikko suomeksi wäää "qwerty"', 'eng': 'Title in English 算盤爾後'
    })

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


def list_organisations_for_create_dataset(user):
    '''
    Lists organization for create dataset page. Basically works like the old version, calling now
    empty query.

    :return: list of organizations (list of dicts)
    '''
    return get_action('organization_autocomplete')({'user': user}, {'q': ''})


def organizations_available(permission='edit_group'):
    organizations = _sort_organizations(h.organizations_available(permission))
    if permission == 'create_dataset':
        for organization in organizations:
            organization['name'] = organization.get('title', None) or organization['name']
    return organizations


def get_organization_sorters():
    return [(N_("By datasets"), "packages"), (N_("Show all"), "title")]


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


def json_to_list(pkg_dict):

    langlist = []

    if not pkg_dict:
        return langlist

    try:
        json_data = json.loads(pkg_dict)
    except ValueError:
        return pkg_dict
    except TypeError:
        for k, v in pkg_dict:
            langlist.append({"lang": k, "value": v})
            return langlist

    for k, v in json_data.iteritems():
        langlist.append({"lang": k, "value": v})

    return langlist


def has_json_content(data):
    '''
    Return True if data contains at least some non-empty values in json.
    E.g. '{"fin": ""}' returns False
    '''
    if not data:
        return False
    try:
        json_data = json.loads(data)
    except (ValueError, TypeError):
        return False
    if len(json_data) == 0 or (isinstance(json_data, dict) and not any(json_data.values())):
        return False
    return True


@beaker_cache(type="dbm", expire=86400)
def get_labels_for_uri(uri, ontology=None):
    '''
    Return all labels for an uri. Cached version.

    :param uri: single uri to get the labels for
    :param ontology: ontology to use or none to guess it
    :return: dict of labels (fi, en, sv), [{u'lang': u'fi', u'value': u'Matematiikka},{u'lang': u'en'...}] or None
    '''
    return get_labels_for_uri_nocache(uri, ontology)


# E.g. harvesters must bypass cache
def get_labels_for_uri_nocache(uri, ontology=None):
    '''
    Return all labels for an uri.

    :param uri: single uri to get the labels for
    :param ontology: ontology to use or none to guess it
    :return: dict of labels (fi, en, sv), [{u'lang': u'fi', u'value': u'Matematiikka},{u'lang': u'en'...}] or None
    '''

    if not isinstance(uri, basestring) or not uri.startswith("http://www.yso.fi"):
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

    try:
        data = urllib2.urlopen(url).read()

    except urllib2.HTTPError as e:
        log.error("Can not connect to Finto: %s" % str(e.code))
        return None
    except urllib2.URLError as e:
        log.error("Can not connect to Finto: %s" % str(e.reason))
        return None
    except httplib.HTTPException:
        log.error('Can not connect to Finto: HTTPException')
        return None

    try:
        jsondata = json.loads(data)
    except (ValueError, TypeError):
        return None

    if jsondata.get('graph'):
        for item in jsondata['graph']:
            if item.get('uri') == uri:
                translations = item.get('prefLabel')

                # When FINTO has only one translation for a word
                # it returns a singular dict item. In this case we need
                # to return it within a list to have a consistent return value
                if isinstance(translations, dict):
                    return [translations]

                return translations
    return None


def get_label_for_uri(uri, ontology=None, lang=None):
    '''
    Return a label for an uri

    :param uri: single uri to get a label for
    :param ontology: ontology to use or none
    :param lang: language of the label. If not provided, uses the language of environment
    :return: resolved label by given language or original string if uri can not be resolved
    '''
    if not isinstance(uri, basestring) or not uri.startswith("http://www.yso.fi"):
        return uri

    try:
        if not lang:
            lang = h.lang()
    except TypeError:
        lang = config.get('ckan.locale_default', 'en')

    try:
        labels = get_labels_for_uri(uri, ontology)
    except TypeError:
        labels = get_labels_for_uri_nocache(uri, ontology)
    if labels:
        for label in labels:
            if label.get('lang') == lang:
                return label.get('value')

    return uri


def get_translation(translation_json_string, lang=None):
    '''
    Returns the given JSON translation string in correct language.

    :param translation_json_string: a json string containing translations, i.e. title
    :param lang: language of the translation
    :return:
    '''

    try:
        json_data = json.loads(translation_json_string)
    except (ValueError, TypeError):
        return translation_json_string

    # if no language is given as a parameter, fetch the currently used
    if not lang:
        lang = h.lang()

    # convert ISO639-1 to ISO639-2 (fi -> fin, en -> eng)
    lang = convert_language_code(lang, 'alpha3')

    # return the given language if it is found,
    # otherwise return the next one from the defaults list
    defaults = [lang, 'eng', 'fin']
    for lang in defaults:
        translation = json_data.get(lang)
        if translation:
            return translation

    if not translation:
        try:
            return json_data.itervalues().next()
        except StopIteration:
            return


def get_language(lang):
    '''
    Resolves the complete language name from a given language code

    :param lang: language code in iso format
    :return:

    '''

    try:
        return languages.get(part2b=lang).name
    except:
        try:
            return languages.get(part3=lang).name
        except:
            try:
                return languages.get(part1=lang).name
            except:
                return lang


def get_translation_from_extras(package):
    '''
    Fetch the translation string from the extras, in case the title is of the old type.
    This function ensures that the legacy title is shown in right language even though the
    package hasn't gone through the converter in show_package_schema or create_package_schema
    yet (i.e. in package_item.html).

    :param package: package dict
    :param default: default value to return, if there is no matching value to the language
    :return: translated value
    '''

    # Try to translate the valid package title, if it doesn't work,
    # we need to fetch the title from extras
    try:
        t = package.get("title", "")
        json.loads(t)
        return get_translation(t)
    except (ValueError, TypeError):
        pass

    ret = ""
    lang = convert_language_code(h.lang(), 'alpha3')    # fi -> fin

    langlist = list()   # an ordered list of title languages
    valuelist = list()  # an ordered list of titles

    if package.get('extras') and lang:
        for extra in package.get('extras'):
            for key, value in extra.iteritems():
                if value.startswith("lang_title"):  # fetch the language of the given title
                    langlist.insert(int(value.split('_')[2]), extra['value'])
                if value.startswith("title"):       # fetch the title
                    valuelist.insert(int(value.split('_')[1]), extra['value'])
        try:
            ret = valuelist[langlist.index(lang)]
        except:
            log.debug('List index was probably out of range')
            if valuelist:   # use the first title given, if any are given at all
                ret = valuelist[0]

    return ret


def disciplines_string_resolved(disciplines, ontology=None, lang=None):
    '''
    Function to print disciplines nicely on dataset view page, resolving what can
    be resolved and leaving the rest as they were.

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


def format_facet_labels(facet_item):
    '''
    This function is used by facet_list.html to format the labels properly.
    In the case of Etsin, the facet label url's are resolved and returned
    according to the display language

    :param facet_item: a dict containing the Finto uri as display_name
    :return: a resolved label in an according language
    '''

    return get_label_for_uri(facet_item['display_name'])


def resolve_org_name(org_id):
    '''
    Get the name of the organization by id.
    '''
    group = model.Group.get(org_id)
    if not group:
        return org_id
    return group.title


def get_active_facets(facets):
    '''
    Constructs a summary of currently active facets for search view.
    Resolves also if any "show more"/"show only top" toggles are on (limits).
    '''

    if not facets or not type(facets.get('search')) is dict:
        return '{}'

    facet_info = dict()
    facet_info['fields'] = facets.get('fields')
    facet_info['fields'].pop('isopen', None)
    facet_info['search'] = dict()
    limits = [k for k, v in request.params.items() if v and k.endswith('_limit')]
    limits = [limit.rsplit('_', 1)[0].strip('_') for limit in limits]
    for key in facets.get('search').iterkeys():
        facet_info['search'][key] = bool(key in limits)
    return json.dumps(facet_info)

def get_fields_grouped():
    '''
    Generates data equivalent to c.fields_grouped for organisation's search page
    Needed by Limit search results feature

    :return: Selected facets as a dict
    '''
    fields_grouped = {}
    for (param, value) in request.params.items():
        if param not in ['q', 'page', 'sort'] \
                and len(value) and not param.startswith('_'):
            if not param.startswith('ext_'):
                if param not in fields_grouped:
                    fields_grouped[param] = [value]
    return fields_grouped


def is_active_facet(facet, active_facets):
    '''
    Returns True if given facet is expanded or has selected items
    :param facet: facet id string
    :param active_facets: result of get_active_facets
    '''
    try:
        data = json.loads(active_facets)
    except (ValueError, TypeError):
        return False
    if not data:
        return False
    return facet in data.get('fields') or data.get('search').get(facet)


def get_dataset_paged_order(index, per_page):
    '''
    Get index for a list with pagination (starting from 1)
    :param index: current visible list index starting from 0
    :param per_page: amount of items per page
    '''
    current_page = 1
    page_param = [v for k, v in request.params.items() if k == 'page']
    if page_param:
        try:
            current_page = int(page_param[0])
        except ValueError:
            pass
    return (current_page - 1) * per_page + index + 1


def get_iso_datetime(datetime_string):
    '''
    Format given datetime string as ISO 8601 (or XSD) datetime.

    :param datetime_string:
    :return:
    '''
    try:
        return iso8601.parse_date(datetime_string).isoformat()
    except iso8601.iso8601.ParseError:
        return datetime_string


def kata_build_nav_main(*args):
    '''
    Fix active links in main navigation. Basically merges build_main_nav and _make_menu_item. The latter especially is
    modified.

    :param args: (menu_item, title)
    :return: <li><a href="..."></i> title</a></li>
    '''

    output = ''
    routers = {
        'home': ['ckanext.kata.controllers:KataHomeController'],
        'search': ['ckanext.kata.controllers:KataPackageController', 'package'],
        'organizations_index': ['ckanext.kata.controllers:KataOrganizationController', 'organization'],
        'about': ['home']
    }

    for item in args:
        menu_item, title = item[:2]
        if len(item) == 3 and not h.check_access(item[2]):
            continue

        _menu_items = config['routes.named_routes']
        _menu_item = copy.copy(_menu_items[menu_item])
        link = h._link_to(title, menu_item, suppress_active_class=True)
        active = h._link_active(_menu_item)

        if not active:
            # Ensure the reply is iterable: needed if variable routers is not consistent
            active = c.controller in routers.get(item[0], list())
        if active:
            output += literal('<li class="active">') + link + literal('</li>')
        else:
            output += literal('<li>') + link + literal('</li>')

    return output


def get_tab_errors(errors, tab):
    '''
    Check if there are errors somewhere in the given tab

    :param errors: errors dict
    :param tab: tab number
    :return: "tab-error" or "" if now errors are found in tab
    '''
    if not errors:
        return ''

    tabs = {'1': ['langtitle', 'langnotes', 'language', 'tag_string'],
            '2': ['agent', 'contact', 'owner_org'],
            '3': ['license', 'license_URL', 'availability', 'direct_download_URL', 'external_id', 'access_application_URL', 'access_request_URL', 'url'],
            '4': ['geographic_coverage', 'temporal_coverage_begin', 'temporal_coverage_end', 'event', 'mimetype', 'format', 'hash', 'algorithm'],
            '5': ['pids', 'version', '__extras'],
            'resources': ['url', 'mimetype', 'format', 'hash', 'algorithm']}

    for key in errors.keys():
        if key in tabs.get(tab):
            return "tab-error"

    if 'resources' in errors:
        # Hard coded resource index 0 may be wrong for datasets created through API.
        for key in errors.get('resources')[0].keys():
            if key in tabs.get('resources') and key in tabs.get(tab):
                return "tab-error"
    return ''


def multilang_to_json(datadict, from_field, to_field):
    '''
    Convert langtitle list (HTML form format) to title JSON string (DB format). Creates title field to datadict and
    returns title value.

    :param datadict: CKAN datadict
    :return:
    '''
    json_data = {}

    # loop through all the translations
    for langtitle in datadict.get(from_field, []):
        lval = langtitle.get('lang')
        rval = langtitle.get('value')
        json_data[lval] = rval

    if json_data:
        datadict[to_field] = json.dumps(json_data)

    return datadict.get(to_field, '')


def get_contact_captcha():
    '''
    Return whether captcha should be used

    :return: boolean
    '''

    return asbool(config.get('kata.contact_captcha', 'False'))

def get_autocomplete_format(data):
    '''
    Splits and resolves

    :param data: string of uris
    :return: json: [{"id": "value", "text": "label"}...]
    '''

    rets = list()
    if data:
        items = [x.strip() for x in data.split(',')]
        if items:
            for item in items:
                label = get_label_for_uri(item)
                rets.append({"id": item, "text": label})
    return json.dumps(rets)


def get_identifier_display_html(identifier):
    '''
    Get identifier html for displaying in the UI.

    :param identifier: identifier value
    :return: string - either plain string or html link string
    '''

    if not isinstance(identifier, basestring):
        return identifier
    if re.match('^urn:nbn:fi:csc-(kata|ida)', identifier):
        return '<a target="_blank" href="http://urn.fi/' + identifier + '">' + identifier + '</a>'
    elif identifier.startswith('http'):
        return '<a target="_blank" href="' + identifier + '">' + identifier + '</a>'
    else:
        return identifier


def get_current_url():
    '''
    Get current url without the host part and query parameters etc.,
    change it to secure ssl connection if not in debug mode

    :return: url path, e.g. https://host.name.fi/fi/dataset/abc-1234
    '''

    url = urlparse(h.full_current_url())
    # Dropping the rest of the parameters because url encoding will too easily break stuff
    if g.debug:
        return 'http://' + url.netloc + url.path
    return 'https://' + url.netloc + url.path


def get_relation_types():
    url = "file://%s" % os.path.abspath(
        os.path.join(os.path.dirname(__file__), "theme/public/relations.json"))
    source = urllib2.urlopen(url)
    try:
        return json.load(source)
    finally:
        source.close()

def get_relation_type_translation(relation_type, lang):
    res = filter(lambda rel: rel['id'] == relation_type, get_relation_types())
    if res:
        return res[0][lang]
    return "Unknown relation type"
