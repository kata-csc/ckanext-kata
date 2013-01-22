import iso8601
import logging
import pycountry
import re

from ckan.model import Package
from pylons.i18n import gettext as _
import utils
from ckan.lib.navl.validators import not_empty, not_missing
from ckan.lib.navl.dictization_functions import StopOnError

log = logging.getLogger('ckanext.kata.validators')


def validate_access(key, data, errors, context):
    if data[key] == 'form':
        if not data[('accessRights',)]:
            errors[key].append(_('You must fill up the form URL'))


def check_language(key, data, errors, context):
    if data[('language',)] and data[('langdis',)] != 'False':
        errors[key].append(_('Language received even if disabled.'))


def check_project(key, data, errors, context):
    if data[('project_name',)] or data[('funder',)] or\
        data[('project_funding',)] or data[('project_homepage',)]:
        if data[('projdis',)] != 'False':
            errors[key].append(_('Project data received even if no project is associated.'))


def validate_lastmod(key, data, errors, context):
    if data[key] == u'':
        return
    try:
        iso8601.parse_date(data[key])
    except iso8601.ParseError, ve:
        errors[key].append(_('Invalid date format, must be like 2012-12-31T13:12:11'))


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
    value = data[key]
    for lang in value.split(','):
        lang = lang.strip()
        try:
            if lang:
                pycountry.languages.get(alpha2=lang)
            elif not ('langdis',) in data:
                errors[key].append(_('No language given.'))
        except KeyError:
            if not ('langdis',) in data and 'save' in context:
                errors[key].append(_('Invalid language %s, not in ISO 639.' % lang))

EMAIL_REGEX = re.compile(r'[^@]+@[^@]+\.[^@]+')
TEL_REGEX = re.compile(r'^(tel:)?\+?\d+$')


def validate_email(key, data, errors, context):
    if not EMAIL_REGEX.match(data[key]):
        errors[key].append(_('Invalid email address'))


def validate_phonenum(key, data, errors, context):
    if not TEL_REGEX.match(data[key]):
        errors[key].append(_('Invalid telephone number, must be like +13221221'))


def check_project_dis(key, data, errors, context):
    if not ('projdis',) in data:
        not_empty(key, data, errors, context)


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
