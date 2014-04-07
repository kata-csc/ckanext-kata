# pylint: disable=unused-argument

"""
Validators for user inputs.
"""
import logging
from itertools import count

import iso8601
import re
from pylons.i18n import _

from ckan.lib.navl.validators import not_empty
from ckan.lib.navl.dictization_functions import StopOnError, Invalid
from ckan.logic.validators import tag_length_validator
from ckan.model import Package
from ckanext.kata import utils, converters, settings

log = logging.getLogger('ckanext.kata.validators')

# Regular expressions for validating e-mail and telephone number
# Characters accepted for e-mail. Note that the first character can't be .
EMAIL_REGEX = re.compile(
    r"""
    ^[\w\d!#$%&\'\*\+\-/=\?\^`{\|\}~]
    [\w\d!#$%&\'\*\+\-/=\?\^`{\|\}~.]+
    @
    [a-z.]+
    \.
    [a-z]{2,6}$
    """,
    re.VERBOSE)
TEL_REGEX = re.compile(r'^(tel:)?\+?\d+$')
# General regex to use in fields with no specific input
GEN_REGEX = re.compile(r'^[^><]*$')
HASH_REGEX = re.compile(r'^[\w\d\ \-(),]*$', re.U)
MIME_REGEX = re.compile(r'^[\w\d\ \-.\/+]*$', re.U)
EVWHEN_REGEX = re.compile(
    r"""
    ^([0-9]{4})
    (-?(0[0-9]?|1[012]?))?
    (-?(0[0-9]?|1[0-9]?|2[0-9]?|3[01]?))?$
    """,
    re.VERBOSE)


def kata_tag_name_validator(value, context):
    '''
    Checks an individual tag for unaccepted characters
    '''

    tagname_match = re.compile('[\w \-.()/#+:]*$', re.UNICODE)
    if not tagname_match.match(value):
        raise Invalid(_('Tag "%s" must be alphanumeric '
                        'characters or symbols: -_.()/#+:') % (value))
    return value


def kata_tag_string_convert(key, data, errors, context):
    '''Takes a list of tags that is a comma-separated string (in data[key])
    and parses tag names. These are added to the data dict, enumerated. They
    are also validated.'''

    if isinstance(data[key], basestring):
        tags = [tag.strip() \
                for tag in data[key].split(',') \
                if tag.strip()]
    else:
        tags = data[key]

    current_index = max( [int(k[1]) for k in data.keys() if len(k) == 3 and k[0] == 'tags'] + [-1] )

    for num, tag in zip(count(current_index+1), tags):
        data[('tags', num, 'name')] = tag

    for tag in tags:
        tag_length_validator(tag, context)
        kata_tag_name_validator(tag, context)


def check_project(key, data, errors, context):
    '''
    Check if user is trying to send project data when project is disabled.
    '''
    if data[('project_name',)] or data[('project_funder',)] or\
        data[('project_funding',)] or data[('project_homepage',)]:
        if data[('projdis',)] != 'False':
            errors[key].append(_('Project data received even if no project is associated.'))


def validate_kata_date(key, data, errors, context):
    '''
    Validate a date string. Empty strings also pass.
    '''
    if isinstance(data[key], basestring) and data[key]:
        try:
            iso8601.parse_date(data[key])
        except (iso8601.ParseError, TypeError):
            errors[key].append(_('Invalid date format: {val}, must be ISO 8601.'
                                 ' Example: 2001-01-01'.format(val=data[key])))
        except ValueError:
            errors[key].append(_('Invalid date'))


def validate_kata_date_relaxed(key, data, errors, context):
    '''
    Validate a event date string. Empty strings also pass.
    '2001-03-01',
    '2001-03' and
    '2001' pass.
    '''
    if isinstance(data[key], basestring) and data[key]:
        try:
            iso8601.parse_date(data[key])
        except (iso8601.ParseError, TypeError):
            if not EVWHEN_REGEX.match(data[key]):
                errors[key].append(_('Invalid {key} date format: {val}, must be'
                                     ' ISO 8601 or truncated: 2001-03-01 or '
                                     '2001-03'.format(key=key[0],
                                                      val=data[key])))
        except ValueError:
            errors[key].append(_('Invalid date'))


def check_junk(key, data, errors, context):
    '''
    Checks the existence of ambiguous parameters
    '''
    if key in data:
        log.debug('Junk: %r' % (data[key]))


def check_last_and_update_pid(key, data, errors, context):
    '''
    Generates a pid (URN) for package if package.extras.version has changed.
    '''
    if key == ('version',):
        pkg = Package.get(data[('name',)])
        if pkg:
            if not data[key] == pkg.as_dict()['version']:
                data[('version_PID',)] = utils.generate_pid()


def validate_email(key, data, errors, context):
    '''
    Validate an e-mail address against a regular expression.
    '''
    if isinstance(data[key], basestring) and data[key]:
        if not EMAIL_REGEX.match(data[key]):
            errors[key].append(_('Invalid email address'))


def validate_general(key, data, errors, context):
    '''
    General input validator.
    Validate arbitrary data for characters specified by GEN_REGEX
    '''
    if isinstance(data[key], basestring) and data[key]:
        if not GEN_REGEX.match(data[key]):
            errors[key].append(_('Invalid characters: <> not allowed'))


def validate_phonenum(key, data, errors, context):
    '''
    Validate a phone number against a regular expression.
    '''
    if isinstance(data[key], basestring) and data[key]:
        if not TEL_REGEX.match(data[key]):
            errors[key].append(_('Invalid telephone number, must be like +13221221'))


def check_project_dis(key, data, errors, context):
    '''
    If projdis checkbox is checked, check that the project fields have data.
    '''
    if not ('projdis',) in data:
        not_empty(key, data, errors, context)
    else:
        projdis = data.get(('projdis',), False)
        value = data.get(key)
        if not projdis or projdis == 'False':
            if value == "":
                errors[(key[0],)].append(_('Missing value'))


def validate_access_application_url(key, data, errors, context):
    '''
    Validate dataset's access_application_URL.

    Dummy value _must_ be added for a new form so that it can be overwritten
    in the same session in iPackageController 'edit' hook. For REMS.
    '''
    if data[('availability',)] == 'access_application':
        if data[('access_application_new_form',)] not in [u'True', u'on']:
            not_empty(key, data, errors, context)
        else:
            data[key] = 'Dummy, overwritten in ckanext-rems'
        converters.convert_to_extras_kata(key, data, errors, context)
    else:
        data.pop(key, None)
        raise StopOnError


def check_direct_download_url(key, data, errors, context):
    '''
    Validate dataset's direct download URL (resource.url).
    '''
    if ('availability',) in data and data[('availability',)] == 'direct_download':
        not_empty(key, data, errors, context)
    else:
        data.pop(key, None)
        raise StopOnError


def check_access_request_url(key, data, errors, context):
    '''
    Validate dataset's access request URL.
    '''
    if ('availability',) in data and data[('availability',)] == 'access_request':
        not_empty(key, data, errors, context)
    else:
        data.pop(key, None)
        raise StopOnError


def check_through_provider_url(key, data, errors, context):
    '''
    Validate dataset's through_provider_URL.
    '''
    if ('availability',) in data and data[('availability',)] == 'through_provider':
        not_empty(key, data, errors, context)
    else:
        data.pop(key, None)
        raise StopOnError


def validate_discipline(key, data, errors, context):
    '''
    Validate discipline
    
    :param key: 'discipline'
    :param data:
    :param errors:
    :param context:
    '''
    val = data.get(key)
    # Regexp is specifically for okm-tieteenala, at:
    # http://onki.fi/fi/browser/overview/okm-tieteenala
    discipline_match = re.compile('[\w \-,]*$', re.UNICODE)
    if val:
        if not discipline_match.match(val):
            raise Invalid(_('Discipline "%s" must be alphanumeric '
                            'characters or symbols: -,') % (val))
    else:
        # With ONKI component, the entire parameter might not exist
        # so we generate it any way
        data[key] = u''


def validate_spatial(key, data, errors, context):
    '''
    Validate spatial (aka geographical) coverage
    
    :param key: eg. 'geographical_coverage'
    :param data:
    :param errors:
    :param context:
    '''
    val = data.get(key)
    # Regexp is specifically for the SUO ontology
    spatial_match = re.compile('[\w \- \'/,():.]*$', re.UNICODE)
    if val:
        if not spatial_match.match(val):
            mismatch = '|'.join([s for s in val.split(',')
                                 if not spatial_match.match(s)])
            raise Invalid(_("Spatial coverage '%s' must be alphanumeric "
                            "characters or symbols: -'/,:()."
                            "Mismatching strings: '%s'") % (val, mismatch))
    else:
        # With ONKI component, the entire parameter might not exist
        # so we generate it any way
        data[key] = u''


def validate_mimetype(key, data, errors, context):
    '''
    Validate mimetype, match to characters in
    http://www.freeformatter.com/mime-types-list.html#mime-types-list
    Also: http://www.iana.org/assignments/media-types
    '''

    val = data.get(key)
    if isinstance(val, basestring):
        if not MIME_REGEX.match(val):
            raise Invalid(_('File type (mimetype) "%s" must be alphanumeric '
                            'characters or symbols: _-+./') % (val))
    

def validate_algorithm(key, data, errors, context):
    '''
    Matching to hash functions according to list in
    http://en.wikipedia.org/wiki/List_of_hash_functions
    '''
    val = data.get(key)
    if isinstance(val, basestring):
        if not HASH_REGEX.match(val):
            raise Invalid(_('Algorithm "%s" must be alphanumeric characters '
                            'or symbols _-()') % (val))


def validate_title(key, data, errors, context):
    '''
    Check the existence of first title
    '''
    if key[1] == 0:
        val = data.get(key)
        if len(val) == 0:
            raise Invalid(_('First title can not be empty'))


def validate_title_duplicates(key, data, errors, context):
    '''
    Checks that there is only one title per language
    '''
    langs = []
    for k in data.keys():
        if k[0] == 'langtitle' and k[2] == 'lang':
            langs.append(data[k])
    if len(set(langs)) != len(langs):
        raise Invalid(_('Duplicate titles for a language not permitted'))


def package_name_not_changed(key, data, errors, context):
    '''
    Checks that package name doesn't change
    '''
    package = context.get('package')
    if data[key] == u'':
        data[key] = package.name
    value = data[key]
    if package and value != package.name:
        raise Invalid('Cannot change value of key from %s to %s. '
                      'This key is read-only' % (package.name, value))


def validate_direct_download_url(key, data, errors, context):
    '''
    Validates that direct_download_URL (at this stage a resource.url) is present
    '''
    if data[('availability',)] == 'direct_download' and\
      (data[key] == u'' or data[key] == u'http://'):
        raise Invalid(_('Missing URL'))


def check_agent(key, data, errors, context):
    '''
    Check that compulsory agents exists.
    '''
    author_found = False
    distributor_found = False
    role = ''
    index = 0

    while role is not None:
        role = data.get(('agent', index, 'role'), None)
        if role == 'author':
            author_found = True
        if role == 'distributor':
            distributor_found = True
        index += 1

    if not (author_found and distributor_found):
        error = 'Missing compulsory agents ({0}, {1}'.format(
            settings.AGENT_ROLES['author'], settings.AGENT_ROLES['distributor'])
        raise Invalid(_(error))
        # if ('agent',) in errors:
        #     errors[('agent',)].append(_(error))
        # else:
        #     errors[('agent',)] = [_(error)]


def check_langtitle(key, data, errors, context):
    '''
    Check that langtitle field exists
    '''
    # import pprint
    # pprint.pprint(data)
    if data.get(('langtitle', 0, 'value'), None) is None:
        error = 'Missing dataset title'
        raise Invalid(_(error))
        # if ('langtitle',) in errors:
        #     errors[('langtitle',)].append(_(error))
        # else:
        #     errors[('langtitle',)] = [_(error)]


def check_pids(key, data, errors, context):
    '''
    Check that pids field exists
    '''
    if data.get((u'pids', 0, u'id'), None) is None:
        error = 'Missing dataset PIDs'
        raise Invalid(_(error))


