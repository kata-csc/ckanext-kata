# -*- coding: utf-8 -*-
"""
Validators for user inputs.
"""
import logging, os, json
from itertools import count
import iso8601
import re
import urllib2
import urlparse

from paste.deploy.converters import asbool
from pylons.i18n import _
from sqlalchemy import and_

import ckan.lib.helpers as h
import ckan.model as model
from ckan.lib.navl.dictization_functions import StopOnError, Invalid, missing
from ckan.lib.navl.validators import not_empty
from ckan.logic.validators import tag_length_validator, url_validator
from ckanext.kata import utils, settings
import kata_ldap

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

    Dummy value _must_ be added if user chooses either reetta option
    so that its value can be overwritten in ckanext-rems when it knows what
    the access_application_URL will be. If user has chosen the option to
    which access application URL is input directly, then validation checks
    its not empty and that it is an url.
    '''
    if data.get(('availability',)) == 'access_application_rems' or \
        data.get(('availability',)) == 'access_application_other':

        if  data.get(('availability',)) == 'access_application_rems':
            data[key] = h.full_current_url().replace('/edit/', '/')
        elif data.get(('availability',)) == 'access_application_other':
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

    if data.get(('availability',)) == 'access_application_rems' or \
        data.get(('availability',)) == 'access_application_other':
        value = data.get(key)
        if value:
            url_not_empty(key, data, errors, context)
    else:
        data.pop(key, None)
        raise StopOnError


def check_resource_url_for_direct_download_url(key, data, errors, context):
    '''
    Validate dataset's direct download URL.
    '''

    lst = list(key)
    lst[2] = 'resource_type'
    resource_type_key = tuple(lst)
    if data.get(('availability',)) == 'direct_download' and data.get(resource_type_key) == settings.RESOURCE_TYPE_DATASET:
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

            # Validate discipline so that it must be a valid URL from okm-tieteenala vocabulary
            if not 'finto.fi/okm-tieteenala' in item and not 'yso.fi/onto/okm-tieteenala' in item:
                raise Invalid(
                    _('Discipline "%s" must be a valid concept defined in Finto okm-tieteenala vocabulary') % item)
            else:
                try:
                    response = urllib2.urlopen(item)
                    if response.getcode() != 200:
                        raise Invalid(_('Discipline "%s" must be a valid concept URL defined in Finto okm-tieteenala vocabulary') % item)
                except urllib2.HTTPError:
                    raise Invalid(
                        _('Discipline "%s" must be a valid concept URL defined in Finto okm-tieteenala vocabulary') % item)


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
    :return: nothing. Raise invalid if length is less than 2 and license is not specific.
    '''

    value = data.get(key)
    if data.get(('license_id',)) in [u'notspecified', u'other', u'other-closed', u'other-nc', u'other-at', u'other-pd', u'other-open']:
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


def validate_external_id_uniqueness(key, data, errors, context):
    '''
        Validate external id is unique, i.e. it does not exist already in any other dataset.

        :param key: key
        :param data: data
        :param errors: errors
        :param context: context
        '''

    exam_external_id = data.get(key)
    exam_package_id = data.get(('id',))

    if exam_external_id:
        all_similar_external_ids_query = model.Session.query(model.PackageExtra) \
            .filter(model.PackageExtra.key.like('external_id')) \
            .filter(model.PackageExtra.value == exam_external_id) \
            .join(model.Package).filter(model.Package.state == 'active').values('package_id', 'value')

        for package_id, exteral_id_value in all_similar_external_ids_query:
            if package_id != exam_package_id:
                raise Invalid(_('Value {ext_id} exists in another dataset {id}').format(ext_id=exam_external_id,
                                                                                            id=package_id))

def validate_primary_pid_uniqueness(key, data, errors, context):
    '''
        Validate dataset primary pid is unique, i.e. it does not exist already in any other dataset.

        :param key: key
        :param data: data
        :param errors: errors
        :param context: context
        '''

    lst = list(key)
    lst[2] = 'type'
    pid_type_key = tuple(lst)
    if data.get(pid_type_key) == u'primary':
        exam_primary_pid = data.get(key)
        exam_package_id = data.get(('id',))
        all_similar_pids_query = model.Session.query(model.PackageExtra)\
                    .filter(model.PackageExtra.key.like('pids_%_id'))\
                    .filter(model.PackageExtra.value == exam_primary_pid)\
                    .join(model.Package).filter(model.Package.state == 'active').values('package_id', 'key', 'value')

        for package_id, pid_id_key, pid_id_value in all_similar_pids_query:
            if package_id != exam_package_id:
                pid_type_key = 'pids_' + pid_id_key[pid_id_key.find('_')+1:pid_id_key.rfind('_')] + '_type'
                primary_type_in_other_dataset_query = model.Session.query(model.PackageExtra)\
                            .filter(and_(model.PackageExtra.package_id == package_id,
                                         model.PackageExtra.key == pid_type_key,
                                         model.PackageExtra.value == u'primary'))
                if primary_type_in_other_dataset_query.first():
                    raise Invalid(_('Primary identifier {pid} exists in another dataset {id}').format(pid=exam_primary_pid, id=package_id))


# def validate_external_id_format(key, data, errors, context):
#     '''
#     Check external_id value is an IDA identifier (or, if in the future other types of accesses than IDA
#     are needed, then this validator should be extended to also accept those types of IDs).
#     (Identifier.series)
#
#     :param key:
#     :param data:
#     :param errors:
#     :param context:
#     :return:
#     '''
#     if data.get(('availability',)) == 'access_application_rems' and \
#     not is_ida_pid(data[key]):
#         raise Invalid(_('Value must be a valid IDA identifier (urn:nbn:fi:csc-ida...s)'))


def validate_pid_relation_type(key, data, errors, context):
    '''
    Check relation key is valid

    :param key:
    :param data:
    :param errors:
    :param context:
    :return:
    '''

    if data.get(key):
        map_file_name = os.path.dirname(os.path.realpath(__file__)) + '/theme/public/relations.json'
        with open(map_file_name) as map_file:
            relation_map = json.load(map_file)

        if not any(relation.get('id') == data.get(key) for relation in relation_map):
            raise Invalid(_('PID relation must be one of the following values: ') + ",".join(map(lambda rel: rel.get('id'), relation_map)))


def validate_pid_type(key, data, errors, context):
    '''
    If pid type is 'relation', make sure 'relation' key has a value

    :param key:
    :param data:
    :param errors:
    :param context:
    :return:
    '''

    lst = list(key)
    lst[2] = 'relation'
    relation_key = tuple(lst)
    if data.get(key) == 'relation' and not data.get(relation_key):
        raise Invalid(_('PID relation must be defined if PID type is relation'))


def validate_package_id_format(key, data, errors, context):
    '''
    Valida package id is starts with urn:nbn:fi:csc-kata

    :param key:
    :param data:
    :param errors:
    :param context:
    :return:
    '''

    if not data.get(key).startswith("urn:nbn:fi:csc-kata"):
        raise Invalid(_('Package id must start with "urn:nbn:fi:csc-kata"'))

def validate_ida_data_auth_policy(key, data, errors, context):
    '''
    This validator is IDA-specific and due to IDA requirements. The validator is
    related to giving authorization for creating access request form automatically
    to IDA data.

    Validate whether either the logged in user or the person owning the distributor
    email address has permission to create new access request form automatically for
    IDA identifier

    :param key:
    :param data:
    :param errors:
    :param context:
    :return:
    '''

    # Assert create new access request form automatically checkbox is checked
    if data[key] == u'False' or data[key] == u'':
        return

    # Extract external identifier from the data dict and assert its existence
    ext_id = utils.get_external_id(data)
    if not ext_id:
        raise Invalid(_('External identifier must be provided to create new access request form automatically'))

    # If external identifier is not IDA pid, validation is not needed
    if not ext_id.startswith('urn:nbn:fi:csc-ida'):
        return

    # Get user EPPN
    auo = context.get('auth_user_obj')
    eppn = auo.openid if auo else ''

    is_ok = False
    prj_ldap_dn = None
    try:
        # Get LDAP dn for the given IDA data pid
        # Fetch IDA project numbers related to the IDA data identifier
        res = urllib2.urlopen("http://researchida6.csc.fi/cgi-bin/pid-to-project?pid={pid}".format(pid=ext_id))
        res_json = json.loads(res.read().decode('utf-8')) if res else {}
        owner_prjs_from_ida = res_json['projects'] or []

        if len(owner_prjs_from_ida) > 0:
            # Loop through all (usually only one) project numbers and use LDAP
            # to validate user has rights
            for prj_num in owner_prjs_from_ida:
                # Find out project LDAP dn related to project number
                prj_ldap_dn = kata_ldap.get_csc_project_from_ldap(prj_num)

        # Validation using user eppn (openid field in db)
        if prj_ldap_dn:
            # Validate user belongs to project corresponding the project number
            is_ok = kata_ldap.user_belongs_to_project_in_ldap(eppn, prj_ldap_dn, True)
    except Exception:
        raise Invalid(_('There was an internal problem in validating permissions for creating new access request form automatically. Please contact Etsin administration for more information.'))

    if not is_ok:
        # Validate user has input distributor email
        if not data.get((u'contact', 0, u'email')):
            raise Invalid(_('Distributor email address must be provided to create new access request form automatically'))
        contact_email = data.get((u'contact', 0, u'email'))
        try:
            # Validation using distributor email address
            if prj_ldap_dn:
                # Validate user belongs to project corresponding the project number
                is_ok = kata_ldap.user_belongs_to_project_in_ldap(contact_email, prj_ldap_dn, False)
        except Exception:
            raise Invalid(_('There was an internal problem in validating permissions for creating new access request form automatically. Please contact Etsin administration for more information.'))
        if not is_ok:
            raise Invalid(_('Neither you nor the distributor ({dist}) is allowed to create new access request form automatically. Please check the validity of distributor email address.').format(dist=contact_email))


def not_empty_if_langtitle_empty(key, data, errors, context):
    from ckan.lib.navl.validators import not_empty
    if not data.get(('langtitle', 0, 'value')):
        not_empty(key, data, errors, context)

def validate_availability(key, data, errors, context):
    if not data.get(key) in settings.AVAILABILITIES:
        raise Invalid(_('Invalid availability. Must be one of: {availabilities}'.format(availabilities=', '.join(settings.AVAILABILITIES))))
