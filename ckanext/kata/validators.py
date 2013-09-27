"""
Validators for user inputs
"""

import iso8601
import logging
import pycountry
import re

from ckan.model import Package
from ckan.lib import helpers as h

from pylons.i18n import gettext as _
import ckanext.kata.utils as utils
from ckan.lib.navl.validators import not_empty, not_missing
from ckan.lib.navl.dictization_functions import StopOnError, Invalid
from ckan.logic.validators import tag_length_validator
from itertools import count

log = logging.getLogger('ckanext.kata.validators')

# Regular expressions for validating e-mail and telephone number
EMAIL_REGEX = re.compile(r'[^@]+@[^@]+\.[^@]+')
TEL_REGEX = re.compile(r'^(tel:)?\+?\d+$')

def kata_tag_name_validator(value, context):
    '''
    Checks an individual tag for unaccepted characters
    '''

    tagname_match = re.compile('[\w \-.\(\)\/]*$', re.UNICODE)
    if not tagname_match.match(value):
        raise Invalid(_('Tag "%s" must be alphanumeric '
                        'characters or symbols: -_.()/') % (value))
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
    if data[key] == 'form':
        if not data[('accessRights',)]:
            errors[key].append(_('You must fill up the form URL'))


def check_project(key, data, errors, context):
    """
    Check if user is trying to send project data when project is disabled.
    """
    if data[('project_name',)] or data[('funder',)] or\
        data[('project_funding',)] or data[('project_homepage',)]:
        if data[('projdis',)] != 'False':
            errors[key].append(_('Project data received even if no project is associated.'))


def validate_kata_date(key, data, errors, context):
    """
    Validate a date string. Empty strings also pass.
    """
    if data[key] == u'':
        return
    try:
        iso8601.parse_date(data[key])
    except iso8601.ParseError:
        errors[key].append(_('Invalid date format, must be like 2012-12-31T13:12:11.'))
    except ValueError:
        errors[key].append(_('Invalid date'))


def check_junk(key, data, errors, context):
    log.debug(data)
    if key in data:
        log.debug(data[key])


def check_last_and_update_pid(key, data, errors, context):
    if key == ('version',):
        pkg = Package.get(data[('name',)])
        if pkg:
            if not data[key] == pkg.as_dict()['version']:
                data[('versionPID',)] = utils.generate_pid()


def validate_language(key, data, errors, context):
    """
    Validate ISO 639 language abbreviations. If langdis == 'True', remove all languages.
    """

    value = data.get(key)
    langs = value.split(',')

    langdis = data.get(('langdis',), None)

    if langdis == 'False':
        # Language enabled

        if langs == [u'']:
            errors[key].append(_('No language given.'))
            return
    else:
        # Language disabled

        # Display flash message if user is loading a page.
        if 'session' in globals():
            h.flash_notice(_("Language is disabled, removing languages: '%s'" % value))

        # Remove languages.
        del data[key]
        data[key] = u''

        return

    for lang in langs:
        lang = lang.strip()
        if lang:
            try:
                pycountry.languages.get(terminology=lang)
            except KeyError:
                errors[key].append(_('Language %s not in ISO 639-2 T format' % lang))


def validate_email(key, data, errors, context):
    """
    Validate an e-mail address against a regular expression.
    """
    if not EMAIL_REGEX.match(data[key]):
        errors[key].append(_('Invalid email address'))


def validate_phonenum(key, data, errors, context):
    """
    Validate a phone number against a regular expression.
    """
    if not TEL_REGEX.match(data[key]):
        errors[key].append(_('Invalid telephone number, must be like +13221221'))


def check_project_dis(key, data, errors, context):
    """
    If projdis checkbox is checked, check out that the project fields have data.
    """
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
    if data[('access',)] in ('free', 'ident'):
        not_empty(key, data, errors, context)


def not_empty_kata(key, data, errors, context):
    if data[key] == []:
        errors[key].append(_('Missing value'))
        raise StopOnError


def check_author_org(key, data, errors, context):
    if all(k in data[key] for k in ('author', 'organization')):
        if not ('author',) in errors:
            errors[('author',)] = []
        errors[('author',)].append('Missing author and organization pairs!')

def set_default_type(key, data, errors, context):
    if data[key] == [] or data[key] == 'None':
        data[key] = u'dataset'