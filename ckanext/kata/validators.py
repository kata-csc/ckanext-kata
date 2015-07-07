#### coding=utf-8
# -*- coding: utf-8 -*-
"""
Validators for user inputs.
"""
import logging
from itertools import count
import iso8601
import re
import urlparse

from pylons.i18n import _
from paste.deploy.converters import asbool

import ckan.lib.helpers as h
from ckan.lib.navl.validators import not_empty
from ckan.lib.navl.dictization_functions import StopOnError, Invalid, missing
from ckan.logic.validators import tag_length_validator, url_validator
from ckan.model import Package, User
from ckanext.kata import utils, converters, settings
import ckan.lib.navl.dictization_functions as df
import ckan.new_authz as new_authz
import ckan.logic as logic

log = logging.getLogger('ckanext.kata.validators')

PACKAGE_NAME_MAX_LENGTH = 100

# Regular expressions for validating e-mail and telephone number
# Characters accepted for e-mail. Note that the first character can't be .
EMAIL_REGEX = re.compile(
    r"""
    ^[\w\d!#$%&\'\*\+\-/=\?\^`{\|\}~]
    [\w\d!#$%&\'\*\+\-/=\?\^`{\|\}~.]+
    @
    [a-z.A-Z0-9-]+
    \.
    [a-zA-Z]{2,6}$
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
ALPHANUM_REGEX = re.compile(r'(?=(.*[\w]){2,})', re.U)


def kata_tag_name_validator(value, context):
    '''
    Checks an individual tag for unaccepted characters
    '''

    tagname_match = re.compile('[\w \-.()/#+:]*$', re.UNICODE)
    if not tagname_match.match(value):
        raise Invalid(_('Keyword "%s" must be alphanumeric '
                        'characters or symbols: -_.()/#+:') % (value))
    return value


def kata_tag_string_convert(key, data, errors, context):
    '''
    Takes a list of tags that is a comma-separated string (in data[key])
    and parses tag names. These are added to the data dict, enumerated. They
    are also validated.
    '''

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


def validate_kata_date(key, data, errors, context):
    '''
    Validate a date string. Empty strings also pass.
    '''
    if isinstance(data[key], basestring) and data[key]:
        try:
            iso8601.parse_date(data[key])
        except (iso8601.ParseError, TypeError):
            errors[key].append(_('Invalid date format, must be ISO 8601.'
                                 ' Example: 2001-01-01'))
        except ValueError:
            errors[key].append(_('Invalid date'))


def validate_kata_date_relaxed(key, data, errors, context):
    '''
    Validate a event date string. Empty strings also pass.
    `2001-03-01`,
    `2001-03` and
    `2001` pass.
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


def validate_email(key, data, errors, context):
    '''
    Validate an email address against a regular expression.
    '''
    if isinstance(data[key], basestring) and data[key]:
        if not EMAIL_REGEX.match(data[key]):
            errors[key].append(_('Invalid email address'))


def validate_general(key, data, errors, context):
    '''
    General input validator.
    Validate arbitrary data for characters specified by `GEN_REGEX`
    '''
    if isinstance(data[key], basestring) and data[key]:
        if not GEN_REGEX.match(data[key]):
            errors[key].append(_('Invalid characters: <> not allowed'))

def contains_alphanumeric(key, data, errors, context):
    '''
    Checks that the field contains some characters, so that eg.
    empty space isn't a valid input
    '''
    if isinstance(data[key], basestring) and data[key]:
        if not ALPHANUM_REGEX.match(data[key]):
            errors[key].append(_('Value must contain alphanumeric characters'))

def validate_phonenum(key, data, errors, context):
    '''
    Validate a phone number against a regular expression.
    '''
    if isinstance(data[key], basestring) and data[key]:
        if not TEL_REGEX.match(data[key]):
            errors[key].append(_('Invalid telephone number, must be like +13221221'))

def validate_access_application_url(key, data, errors, context):
    '''
    Validate dataset's `access_application_URL`.

    Dummy value _must_ be added for a new form so that it can be overwritten
    in the same session in iPackageController `edit` hook. For REMS.
    '''
    if data.get(('availability',)) == 'access_application':
        if data.get(('access_application_new_form',)) in [u'True', u'on']:
            data[key] = h.full_current_url().replace('/edit/', '/')
        else:
            not_empty(key, data, errors, context)
            url_validator(key, data, errors, context)
    else:
        data.pop(key, None)
        raise StopOnError


def validate_access_application_download_url(key, data, errors, context):
    '''
    Validate the access_application_download_URL field of a dataset.
    The field is used for expressing the URL at which the actual data
    can be downloaded after entitlement through the access application
    server has been given.
    '''

    if data.get(('availability',)) == 'access_application':
        value = data.get(key)
        if value:
            url_not_empty(key, data, errors, context)
    else:
        data.pop(key, None)
        raise StopOnError


def check_direct_download_url(key, data, errors, context):
    '''
    Validate dataset's direct download URL.
    '''
    if data.get(('availability',)) == 'direct_download':
        url_not_empty(key, data, errors, context)


def check_access_request_url(key, data, errors, context):
    '''
    Validate dataset's access request URL.
    '''
    if data.get(('availability',)) == 'access_request':
        not_empty(key, data, errors, context)
    else:
        data.pop(key, None)
        raise StopOnError


def check_through_provider_url(key, data, errors, context):
    '''
    Validate dataset's `through_provider_URL`.
    '''
    if data.get(('availability',)) == 'through_provider':
        not_empty(key, data, errors, context)
    else:
        data.pop(key, None)
        raise StopOnError


def validate_discipline(key, data, errors, context):
    '''
    Validate discipline

    :param key: 'discipline'
    '''
    val = data.get(key)
    # Regexp is specifically for okm-tieteenala, at:
    # http://onki.fi/fi/browser/overview/okm-tieteenala
    discipline_match = re.compile('(http://)?[\w \-,\.\/]*$', re.UNICODE)
    if val:
        for item in val.split(","):
            if not discipline_match.match(item):
                raise Invalid(_('Discipline "%s" must be alphanumeric '
                                'characters or symbols: -,/.') % (item))
    else:
        # With ONKI component, the entire parameter might not exist
        # so we generate it any way
        data[key] = u''


def validate_spatial(key, data, errors, context):
    '''
    Validate spatial (aka geographical) coverage

    :param key: eg. 'geographical_coverage'
    '''
    val = data.get(key)
    # Regexp is specifically for the SUO ontology
    spatial_match = re.compile('[\w \- \'/,():.;=]*$', re.UNICODE)
    if val:
        if not spatial_match.match(val):
            mismatch = '|'.join([s for s in val.split(',')
                                 if not spatial_match.match(s)])
            raise Invalid(_("Spatial coverage \"%s\" must be alphanumeric "
                            "characters or symbols: -'/,:().;= ") % mismatch)
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
        for item in val.split(","):
            if not MIME_REGEX.match(item):
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


def validate_multilang_field(fieldkey, key, data, errors, context):
    '''
    Checks that there is only one multilanguage field per language

    :param fieldkey: 'langtitle' or 'langnotes' currently
    '''
    langs = []
    for k in data.keys():
        if len(k) > 2 and k[0] == fieldkey and k[2] == 'lang' and \
                (fieldkey, k[1], 'value',) in data and \
                len(data.get((fieldkey, k[1], 'value',))) > 0:
            langs.append(data[k])
    if len(set(langs)) != len(langs):
        raise Invalid(_('Duplicate fields for a language not permitted'))


def validate_title_duplicates(key, data, errors, context):
    return validate_multilang_field('langtitle', key, data, errors, context)


def validate_notes_duplicates(key, data, errors, context):
    return validate_multilang_field('langnotes', key, data, errors, context)


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


def check_agent(key, data, errors, context):
    '''
    Check that compulsory agents exist.
    '''
    author_found = False
    roles = [data[k] for k in data.keys() if k[0] == 'agent' and k[2] == 'role']

    for role in roles:
        if role == 'author':
            author_found = True

    if not author_found:
        missing_role = 'author'
        error = {'key': missing_role, 'value': _("Missing compulsory agent: {0}").format(_(settings.AGENT_ROLES[missing_role]))}
        raise Invalid(error)


def check_contact(key, data, errors, context):
    '''
    Check that compulsory contacts exist.
    '''

    # Simplified check to see that we get at least one contact (4 compulsory fields).
    # Further validation done in contact validators.
    if not [k[0] for k in data.keys()].count('contact') >= 1:
        raise Invalid({'value': _('Missing compulsory distributor information'), 'key': 'contact'})


def check_agent_fields(key, data, errors, context):
    '''
    Check that compulsory fields for this agent exists.
    '''

    if not (data.get((key[0], key[1], 'name')) or
            data.get((key[0], key[1], 'organisation')) or
            data.get((key[0], key[1], 'URL'))):
        data.pop(key, None)
        raise StopOnError


def check_langtitle(key, data, errors, context):
    '''
    Check that langtitle field exists
    '''
    if not (data.get(('langtitle', 0, 'value')) or data.get(('title',))):
        raise Invalid({'key': 'langtitle', 'value': _('Missing dataset title')})


def check_pids(key, data, errors, context):
    '''
    Check that compulsory PIDs exist. Also check that primary data PID is not modified in any way.
    '''

    # Empty PIDs are removed in actions, so this check should do
    if data.get((u'pids', 0, u'id'), None) is None:
        raise Invalid({'key': 'pids', 'value': _('Missing dataset PIDs')})

    primary_data_pid_found = False
    primary_pid = None

    primary_keys = [k for k in data.keys() if k[0] == 'pids' and k[2] == 'primary']

    for k in primary_keys:
        if asbool(data[k] or False) and data[(k[0], k[1], 'type')] == 'data' and data[(k[0], k[1], 'id')]:
            primary_data_pid_found = True
            primary_pid = data[(k[0], k[1], 'id')]

    if not primary_data_pid_found:
        raise Invalid({'key': 'pids', 'value': _("Missing primary data PID")})

    # Check constancy of primary data PID

    try:
        data_dict = logic.get_action('package_show')({}, {'id': data[('id',)]})
        old_primary_pid = utils.get_pids_by_type('data', data_dict, primary=True)[0].get('id')
        if old_primary_pid and old_primary_pid != primary_pid:
            raise Invalid({'key': 'pids', 'value': _("Primary data PID can not be modified")})
    except (logic.NotFound, KeyError):
        # New dataset, all is well
        pass


def check_events(key, data, errors, context):
    '''
    Validates that none of the event's data is empty
    If there is only type, removes it
    '''
    (k0, k1, k2) = key
    if (data[(k0, k1, 'when')] or
        data[(k0, k1, 'who')] or
        data[(k0, k1, 'descr')]):
        if not (data[(k0, k1, 'when')] and
                data[(k0, k1, 'who')] and
                data[(k0, k1, 'descr')]):
            raise Invalid(_('Missing value'))
    else:
        data.pop(key, None)
        raise StopOnError


def ignore_empty_data(key, data, errors, context):
    ''' Ignore empty data, example '-' or whitespace.

    :raises ckan.lib.navl.dictization_functions.StopOnError: if ``data[key]``
        is :py:data:`ckan.lib.navl.dictization_functions.missing` or ``None``

    :returns: ``None``

    '''
    value = data.get(key)

    if value is missing or value is None or re.match('^\s*-{0,1}\s*$', value):
        data.pop(key, None)
        raise StopOnError


def url_not_empty(key, data, errors, context):
    '''
    Check that the data value is non-empty and contains both a URL scheme and a hostname.

    :raises ckan.lib.navl.dictization_functions.Invalid: if data[key] is empty, missing, or
                                                         omits either URL scheme or hostname
    :returns: None
    '''
    value = data.get(key)
    if value and value is not missing:
        url_components = urlparse.urlparse(value)
        if all([url_components.scheme, url_components.netloc]):
            return

    raise Invalid(_('Missing value'))


def kata_owner_org_validator(key, data, errors, context):
    '''
    Modified version of CKAN's owner_org_validator. Anyone can add a
    dataset to an organisation. If the organisation doesn't exist it is created later on.

    :param key: key
    :param data: data
    :param errors: errors
    :param context: context
    :return: nothing
    '''

    value = data.get(key)

    if value is missing or not value:
        if not new_authz.check_config_permission('create_unowned_dataset'):
            err = _(
            u"An organization must be supplied. If you do not find a suitable organization, please choose the default organization "
            u"'Ei linkitetä organisaatioon - do not link to an organization' or create a new one."
            )

            raise Invalid(err)
        data.pop(key, None)
        raise df.StopOnError

    if len(value) < 2:
        raise Invalid(_('Organization name must be at least %s characters long') % 2)
    if len(value) > PACKAGE_NAME_MAX_LENGTH:
        raise Invalid(_('Organization name must be a maximum of %i characters long') % \
                      PACKAGE_NAME_MAX_LENGTH)
    if value.lower() in ['new', 'edit', 'search']:
        raise Invalid(_('This organization name cannot be used'))

    model = context['model']
    group = model.Group.get(value)
    if group:
        data[key] = group.id


def check_private(key, data, errors, context):
    '''
    Changes to owner_org_validator requires checking of private value.

    :param key: key
    :param data: data
    :param errors: errors
    :param context: context
    :return: nothing. Raise invalid if not organisation editor and private == False
    '''

    value = data.get(key)
    is_editor = False
    if not value or value == u'False':
        user = context.get('user', False)
        if user:
            if utils.get_member_role(data.get((u'owner_org',)), User.get(user).id) in ('admin', 'editor'):
                is_editor = True
        if not is_editor:
            raise Invalid(_('Only organization\'s editors and admins can create a public dataset'))


def usage_terms_accepted(value, context):
    '''
    Check if a boolean value is true

    :param value: value to check
    :param context: CKAN context
    '''
    if not asbool(value):
        raise Invalid(_('Terms of use must be accepted'))


def validate_license_url(key, data, errors, context):
    '''
    Check that more information about the license is provided, if license is not specific.

    :param key: key
    :param data: data
    :param errors: errors
    :param context:
    :return: nothing. Raise invalid if length is less than 2 and lisense is not specific.
    '''

    value = data.get(key)
    if data.get(('license_id',)) in ['notspecified', 'other-closed', 'other-nc', 'other-at', 'other-pd', 'other-open']:
        if not value or len(value) < 2:
            raise Invalid(_('Copyright notice is needed if license is not specified or '
                            'is a variant of license type other.'))


