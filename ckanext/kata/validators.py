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
from sqlalchemy import or_

import ckan.lib.helpers as h
from ckan.lib.navl.validators import not_empty
from ckan.lib.navl.dictization_functions import StopOnError, Invalid, missing
from ckan.logic.validators import tag_length_validator, url_validator
from ckanext.kata import utils, settings
import ckan.model as model

from utils import is_ida_pid

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

# Look for test_validators.py test_validate_phonenum_ functions to understand what TEL_REGEX really matches
TEL_REGEX = re.compile(r'^(tel:)?\s?(\+?\d|\(\d+\)(\s|\d))(\d+|\s|\-\d|\(\d+\)(\s|\d)){1,30}$')
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

    tagname_match = re.compile('[\w \-.()/#+:\?\=\&]*$', re.UNICODE)
    if not tagname_match.match(value):
        raise Invalid(_('Keyword "%s" must be alphanumeric '
                        'characters or symbols: -_.()/#+:?=&') % (value))
    return value


def kata_tag_string_convert(key, data, errors, context):
    '''
    Takes a list of tags that is a comma-separated string (in data[key])
    and parses tag names. These are added to the data dict, enumerated. They
    are also validated.
    '''

    if isinstance(data[key], basestring):
        tags = [tag.strip() for tag in data[key].split(',') if tag.strip()]
    else:
        tags = data[key]

    current_index = max([int(k[1]) for k in data.keys() if len(k) == 3 and k[0] == 'tags'] + [-1])

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
        _parse_iso8601_date(key, data[key], errors)


def validate_kata_interval_date(key, data, errors, context):
    '''
    Validate a date interval string. Empty strings also pass. Separator character '/'
    '''
    if isinstance(data[key], basestring) and data[key]:
        if '/' in data[key]:
            if data[key].endswith('/'):
                errors[key].append(_('Invalid date format, must be ISO 8601.'
                             ' Example: 2001-01-01/2002-01-01'))
            else:
                dates = data[key].split('/')
                from_date = _parse_iso8601_date(key, dates[0], errors)
                to_date = _parse_iso8601_date(key, dates[1], errors)
                if(from_date is not None and to_date is not None):
                    if(to_date < from_date):
                        errors[key].append(_('To date must be greater than from date.'
                             ' Example: 2001-01-01/2002-01-01'))
        else:
            _parse_iso8601_date(key, data[key], errors)


def _parse_iso8601_date(key, datestr, errors):
    try:
        return iso8601.parse_date(datestr)
    except (iso8601.ParseError, TypeError):
        errors[key].append(_('Invalid date format, must be ISO 8601.'
                             ' Example: 2001-01-01'))
    except ValueError:
        errors[key].append(_('Invalid date'))
    return None


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
            errors[key].append(_('Invalid telephone number, must be e.g. +358 (45) 123 45 67 or 010-234567'))


def validate_access_application_url(key, data, errors, context):
    '''
    Validate dataset's `access_application_URL`.

    Dummy value _must_ be added for other than access application url
    so that it can be overwritten in ckanext-rems when it knows what
    the access_application_URL will be.
    '''
    if data.get(('availability',)) == 'access_application':
        if data.get(('access_application',)) == 'access_application_reetta_ida' or \
        data.get(('access_application',))  == 'access_application_reetta':
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
    if data.get(('availability',)) == 'access_request' and data.get(('access_application')) == 'access_application_other':
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
    discipline_match = re.compile('[\w \-,:#+.?=&/]*$', re.UNICODE)
    if val:
        for item in val.split(","):
            if not discipline_match.match(item):
                raise Invalid(_('Discipline "%s" must be alphanumeric '
                                'characters or symbols: -,:#+?=&/.') % (item))
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
                data.get((fieldkey, k[1], 'value',)) is not missing and \
                len(data.get((fieldkey, k[1], 'value',), '')) > 0:
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
            data.get((key[0], key[1], 'URL')) or
            data.get((key[0], key[1], 'id')) or
            data.get((key[0], key[1], 'fundingid'))):
        data.pop(key, None)
        raise StopOnError


def check_langtitle(key, data, errors, context):
    '''
    Check that langtitle field exists
    '''
    if not (data.get(('langtitle', 0, 'value')) or data.get(('title',))):
        raise Invalid({'key': 'langtitle', 'value': _('Missing dataset title')})


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
        err = _(
        u"An organization must be supplied. If you do not find a suitable organization, please choose the default organization "
        u"'Ei linkitetä organisaatioon - do not link to an organization'."
        )
        raise Invalid(err)

    model = context['model']
    group = model.Group.get(value)
    if not group:
        org_name = re.sub(r'[^a-zA-Z0-9]+', '-', utils.slugify(value)).lower()
        org_name = re.sub(r'-$', '', org_name)
        group = model.Group.get(org_name)
        if not group:
            err = _(
            u'The provided organization does not exist. Please contact Etsin administration using our contact form at http://openscience.fi/contact-form')
            raise Invalid(err)

    if group:
        data[key] = group.id


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


def continue_if_missing(key, data, errors, context):
    '''
    Like ignore_missing but don't stop, instead run the other validators.

    :param key: key
    :param data: data
    :param errors: errors
    :param context: context
    '''

    value = data.get(key)

    if value is missing or value is None:
        data.pop(key, None)


def validate_pid_uniqueness(key, data, errors, context):
    '''
    Validate dataset pids are unique, i.e. they do not exist already.

    :param key: key
    :param data: data
    :param errors: errors
    :param context: context
    '''
    exam_pid = data.get(key)
    exam_package_id = data.get(('id',))

    # Query package extra table with key like pids_%_id and match exact pid name with the corresponding value
    # Return only rows with package state active, since deleted datasets might be re-added.
    query = model.Session.query(model.PackageExtra).filter(model.PackageExtra.key.like('pids_%_id')). \
            filter(or_(model.PackageExtra.value == exam_pid, model.PackageExtra.package_id == exam_pid)). \
            join(model.Package).filter(model.Package.state == 'active')

    q_amt = query.count()
    q_package_ids = [i[0] for i in query.values('package_id')]

    # If existing pids or package_ids with value matching the pid were found
    # and if none of those found values is the pid, raise an error.
    # The latter if is when updating a dataset.

    if q_amt > 0:
        for item in q_package_ids:
            if item != exam_package_id:
                raise Invalid(_('Identifier {pid} exists in another dataset {id}').format(pid=exam_pid, id=item))


def check_access_application_ida_identifier(key, data, errors, context):
    '''
    Check access_application_ida_identifier value is an IDA identifier
    (Identifier.series)

    :param key:
    :param data:
    :param errors:
    :param context:
    :return:
    '''
    if data.get(('availability',)) == 'access_application':
        if data.get(('access_application',)) == 'access_application_reetta_ida' and not is_ida_pid(data[key]):
            raise Invalid(_('Value must be a valid IDA identifier (urn:nbn:fi:csc-ida...s)'))
    else:
        data.pop(key, None)
        raise StopOnError