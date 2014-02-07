# pylint: disable=unused-argument

"""
Validators for user inputs.
"""

import logging
from itertools import count

import iso8601
import re
from pylons.i18n import _

from ckan.model import Package
import ckanext.kata.utils as utils
from ckan.lib.navl.validators import not_empty
from ckan.lib.navl.dictization_functions import StopOnError, Invalid
from ckan.logic.validators import tag_length_validator


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
    (?P<year>[0-9]{4})
    (-{0,1}(?P<month>[0-9]{1,2})){0,1}
    (-{0,1}(?P<day>[0-9]{1,2})){0,1}
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
    # TODO: validate_kata_date() should be replaced with this
    '''
    Validate a event date string. Empty strings also pass.
    '2001-01-01',
    '2001-01' and
    '2001' pass.
    '''
    if isinstance(data[key], basestring) and data[key]:
        try:
            iso8601.parse_date(data[key])
        except (iso8601.ParseError, TypeError):
            if not EVWHEN_REGEX.match(data[key]):
                errors[key].append(_('Invalid {key} date format: {val}, must be'
                                     ' ISO 8601 or truncated: 2001-01-01 or '
                                     '2001-01'.format(key=key[0],
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


def check_access_application_url(key, data, errors, context):
    if data[('availability',)] == 'access_application':
        not_empty(key, data, errors, context)


def check_direct_download_url(key, data, errors, context):
    '''
    Validate dataset's direct download URL (resource.url).
    '''
    if ('availability',) in data and data[('availability',)] == 'direct_download':
        not_empty(key, data, errors, context)


def check_access_request_url(key, data, errors, context):
    '''
    Validate dataset's access request URL.
    '''
    if ('availability',) in data and data[('availability',)] == 'access_request':
        not_empty(key, data, errors, context)


def check_through_provider_url(key, data, errors, context):
    '''
    Validate dataset's through_provider_URL.
    '''
    if ('availability',) in data and data[('availability',)] == 'through_provider':
        not_empty(key, data, errors, context)


def not_empty_kata(key, data, errors, context):
    if data[key] == []:
        errors[key].append(_('Missing value'))
        raise StopOnError


def check_author_org(key, data, errors, context):
    '''
    Validates author and organisation
    '''
    # index 0 must exist, for plain orgauth is false positive
    if not (('orgauth', 0, 'org') in data):
        if not ('orgauth', 0, 'value') in errors:
            errors[('orgauth', 0, 'value',)] = []
        # To 0, to orgauth would mess the unflatten function with multiple authors
        errors[('orgauth', 0, 'value')].append('Missing author and organisation pairs')


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
