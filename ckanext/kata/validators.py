import iso8601
import logging

log = logging.getLogger('ckanext.kata.validators')


def validate_access(key, data, errors, context):
    if data[key] == 'form':
        if not data[('accessRights',)]:
            errors[key].append('You must fill up the form URL')


def check_language(key, data, errors, context):
    if data[('language',)]:
        errors[key].append('Language received even if disabled.')


def check_project(key, data, errors, context):
    if data[('project_name',)] or data[('project_funder',)] or\
        data[('project_funding',)] or data[('project_homepage',)]:
        errors[key].append('Project data received even if no project is associated.')


def validate_lastmod(key, data, errors, context):
    log.debug(data[key] == '')
    if data[key] == u'':
        return
    log.debug('if %r then pass' % (data[key] == ''))
    try:
        iso8601.parse_date(data[key])
    except iso8601.ParseError, ve:
        errors[key].append('Invalid date format, must be like 2012-12-31T13:12:11')


def check_junk(key, data, errors, context):
    log.debug(data[key])
