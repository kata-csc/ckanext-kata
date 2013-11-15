# pylint: disable=unused-argument

"""
Validators for user inputs.
"""

import iso8601
import logging
import pycountry
import re

from ckan.model import Package

from pylons.i18n import _
import ckanext.kata.utils as utils
from ckan.lib.navl.validators import not_empty
from ckan.lib.navl.dictization_functions import StopOnError, Invalid
from ckan.logic.validators import tag_length_validator
from itertools import count

log = logging.getLogger('ckanext.kata.validators')

# Regular expressions for validating e-mail and telephone number
# Characters accepted for e-mail. Note that the first character can't be .
EMAIL_REGEX = re.compile(r'^[\w\d!#$%&\'\*\+\-/=\?\^`{\|\}~][\w\d!#$%&\'\*\+\-/=\?\^`{\|\}~.]+@[a-z.]+\.[a-z]{2,6}$')
TEL_REGEX = re.compile(r'^(tel:)?\+?\d+$')
# General regex to use in fields with no specific input
GEN_REGEX = re.compile(r'^[^><]*$')
HASH_REGEX = re.compile(r'^[\w\d\ \-(),]*$', re.U)
MIME_REGEX = re.compile(r'^[\w\d\ \-.\/+]*$', re.U)

def kata_tag_name_validator(value, context):
    '''
    Checks an individual tag for unaccepted characters
    '''

    tagname_match = re.compile('[\w \-.()/#+]*$', re.UNICODE)
    if not tagname_match.match(value):
        raise Invalid(_('Tag "%s" must be alphanumeric '
                        'characters or symbols: -_.()/#+') % (value))
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

def validate_access(key, data, errors, context):
    '''
    Validates that accessRights field is filled
    '''
    if data[key] == 'form':
        if not data[('accessRights',)]:
            errors[key].append(_('You must fill up the form URL'))


def check_project(key, data, errors, context):
    '''
    Check if user is trying to send project data when project is disabled.
    '''
    if data[('project_name',)] or data[('funder',)] or\
        data[('project_funding',)] or data[('project_homepage',)]:
        if data[('projdis',)] != 'False':
            errors[key].append(_('Project data received even if no project is associated.'))


def validate_kata_date(key, data, errors, context):
    '''
    Validate a date string. Empty strings also pass.
    '''
    if data[key] == u'':
        return
    try:
        iso8601.parse_date(data[key])
    except iso8601.ParseError:
        errors[key].append(_('Invalid date format, must be like 2012-12-31T13:12:11.'))
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
                data[('versionPID',)] = utils.generate_pid()


def validate_language(key, data, errors, context):
    '''
    Validate ISO 639 language abbreviations.

    data['key'] may be a string with comma separated values or a single language code.
    '''

    value = data.get(key)

    if type(value) not in [str, unicode]:
        return
    langs = value.split(',')

    for lang in langs:
        lang = lang.strip()
        if lang:
            try:
                pycountry.languages.get(terminology=lang)
            except KeyError:
                errors[key].append(_('Language %s not in ISO 639-2 T format' % lang))


def validate_email(key, data, errors, context):
    '''
    Validate an e-mail address against a regular expression.
    '''
    if not EMAIL_REGEX.match(data[key]):
        errors[key].append(_('Invalid email address'))

def validate_general(key, data, errors, context):
    '''
    General input validator.
    Validate random data for characters specified by GEN_REGEX
    '''
    if len(data[key]) == 0:
        pass
    if not GEN_REGEX.match(data[key]):
        errors[key].append(_('Invalid characters: <> not allowed'))

def validate_phonenum(key, data, errors, context):
    '''
    Validate a phone number against a regular expression.
    '''
    if not TEL_REGEX.match(data[key]):
        errors[key].append(_('Invalid telephone number, must be like +13221221'))


def check_project_dis(key, data, errors, context):
    '''
    If projdis checkbox is checked, check out that the project fields have data.
    '''
    if not ('projdis',) in data:
        not_empty(key, data, errors, context)
    else:
        projdis = data.get(('projdis',), False)
        value = data.get(key)
        if not projdis or projdis == 'False':
            if value == "":
                errors[(key[0],)].append(_('Missing value'))


def check_accessrights(key, data, errors, context):
    if data[('access',)] == 'form':
        not_empty(key, data, errors, context)


def check_accessrequesturl(key, data, errors, context):
    '''
    Validate dataset's access request URL (resource.url).
    '''
    if ('access',) in data and data[('access',)] in ('free', 'ident'):
        not_empty(key, data, errors, context)


def not_empty_kata(key, data, errors, context):
    if data[key] == []:
        errors[key].append(_('Missing value'))
        raise StopOnError


def check_author_org(key, data, errors, context):
    '''
    Validates author's organisation
    '''
    if all(k in data[key] for k in ('author', 'organization')):
        if not ('author',) in errors:
            errors[('author',)] = []
        errors[('author',)].append('Missing author and organization pairs!')
        
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
    spatial_match = re.compile('[\w \-,():.]*$', re.UNICODE)
    if val:
        if not spatial_match.match(val):
            raise Invalid(_('Spatial coverage "%s" must be alphanumeric '
                            'characters or symbols: -,:().') % (val))
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
    if not MIME_REGEX.match(val):
        raise Invalid(_('File type (mimetype) "%s" must be alphanumeric '
                        'characters or symbols: _-+./') % (val))
    

def validate_algorithm(key, data, errors, context):
    '''
    Matching to hash functions according to list in
    http://en.wikipedia.org/wiki/List_of_hash_functions
    '''
    val = data.get(key)
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
