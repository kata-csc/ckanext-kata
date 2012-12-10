import iso8601
import logging

from ckan.model import Package

import utils

log = logging.getLogger('ckanext.kata.validators')


def validate_access(key, data, errors, context):
    if data[key] == 'form':
        if not data[('accessRights',)]:
            errors[key].append(_('You must fill up the form URL'))


def check_language(key, data, errors, context):
    if data[('language',)]:
        errors[key].append(_('Language received even if disabled.'))


def check_project(key, data, errors, context):
    if data[('project_name',)] or data[('project_funder',)] or\
        data[('project_funding',)] or data[('project_homepage',)]:
        errors[key].append(_('Project data received even if no project is associated.'))


def validate_lastmod(key, data, errors, context):
    if data[key] == u'':
        return
    try:
        iso8601.parse_date(data[key])
    except iso8601.ParseError, ve:
        errors[key].append(_('Invalid date format, must be like 2012-12-31T13:12:11'))


def check_junk(key, data, errors, context):
    if key in data:
        log.debug(data[key])


def check_last_and_update_pid(key, data, errors, context):
    if key == ('version',):
        pkg = Package.get(data[('name',)])
        if pkg:
            log.debug(pkg.as_dict())
            log.debug(data[key])
            log.debug(data[key] == pkg.as_dict()['version'])
            if not data[key] == pkg.as_dict()['version']:
                data[('versionPID',)] = utils.generate_pid()
