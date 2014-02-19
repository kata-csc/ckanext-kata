from ckan.lib.navl.validators import (default,
                                      ignore,
                                      ignore_missing,
                                      not_empty,
                                      not_missing)
from ckan.logic.schema import (default_create_package_schema,
                               default_show_package_schema)
from ckan.logic.validators import (owner_org_validator,
                                   package_id_not_changed,
                                   package_name_validator,
                                   tag_length_validator,
                                   url_validator,
                                   vocabulary_id_exists)
from ckanext.kata.validators import (check_access_application_url,
                                     check_access_request_url,
                                     check_author_org,
                                     check_direct_download_url,
                                     check_junk,
                                     check_last_and_update_pid,
                                     check_project,
                                     check_project_dis,
                                     kata_tag_name_validator,
                                     kata_tag_string_convert,
                                     validate_algorithm,
                                     validate_discipline,
                                     validate_email,
                                     validate_general,
                                     validate_kata_date,
                                     validate_kata_date_relaxed,
                                     validate_mimetype,
                                     validate_phonenum,
                                     validate_spatial,
                                     validate_title)
from ckanext.kata.converters import (checkbox_to_boolean,
                                     convert_from_extras_kata,
                                     convert_languages,
                                     convert_to_extras_kata,
                                     event_from_extras,
                                     event_to_extras,
                                     ltitle_from_extras,
                                     ltitle_to_extras,
                                     org_auth_from_extras,
                                     org_auth_to_extras,
                                     org_auth_to_extras_oai,
                                     version_pid_from_extras,
                                     remove_disabled_languages,
                                     update_pid,
                                     xpath_to_extras)
from ckanext.kata import utils
import ckanext.kata.settings as settings


def tags_schema():
    schema = {
        'name': [not_missing,
                 not_empty,
                 unicode,
                 tag_length_validator,
                 kata_tag_name_validator,
                 ],
        'vocabulary_id': [ignore_missing, unicode, vocabulary_id_exists],
        'revision_timestamp': [ignore],
        'state': [ignore],
        'display_name': [ignore],
    }
    return schema

def create_package_schema():
    """
    Return the schema for validating new dataset dicts.
    """

    schema = default_create_package_schema()

    for key in settings.KATA_FIELDS_REQUIRED:
        schema[key] = [not_empty, convert_to_extras_kata, unicode, validate_general]
    for key in settings.KATA_FIELDS_RECOMMENDED:
        schema[key] = [ignore_missing, convert_to_extras_kata, unicode, validate_general]

    schema['id'] = [default(utils.generate_pid())]
    schema['langtitle'] = {'value': [not_missing, unicode, validate_title, ltitle_to_extras],
                           'lang': [not_missing, unicode, convert_languages]}

    schema['orgauth'] = {'value': [not_missing, unicode, org_auth_to_extras, validate_general],
                         'org': [not_missing, unicode, validate_general]}

    schema['temporal_coverage_begin'] = [ignore_missing, validate_kata_date, convert_to_extras_kata, unicode]
    schema['temporal_coverage_end'] = [ignore_missing, validate_kata_date, convert_to_extras_kata, unicode]
    schema['language'] = [ignore_missing, convert_languages, remove_disabled_languages, convert_to_extras_kata, unicode]
    schema['contact_phone'] = [not_missing, not_empty, validate_phonenum, convert_to_extras_kata, unicode]
    schema['maintainer_email'].append(validate_email)

    schema['tag_string'] = [not_missing, not_empty, kata_tag_string_convert]
    # otherwise the tags would be validated with default tag validator during update
    schema['tags'] = tags_schema()

    schema.update({
        'version': [not_empty, unicode, validate_kata_date_relaxed, check_last_and_update_pid],
        'version_PID': [default(u''), update_pid, unicode, convert_to_extras_kata],
        #'author': [],
        #'organization': [],
        'availability': [not_missing, convert_to_extras_kata],
        'langdis': [checkbox_to_boolean, convert_to_extras_kata],
        '__extras': [check_author_org],
        'projdis': [checkbox_to_boolean, check_project, convert_to_extras_kata],
        '__junk': [check_junk],
        'name': [ignore_missing, unicode, update_pid, package_name_validator, validate_general],
        'access_application_URL': [ignore_missing, check_access_application_url, convert_to_extras_kata,
                                   unicode, validate_general],
        'access_request_URL': [ignore_missing, check_access_request_url, url_validator, convert_to_extras_kata,
                               unicode, validate_general],

        'project_name': [ignore_missing, check_project_dis, unicode, convert_to_extras_kata, validate_general],
        'project_funder': [ignore_missing, check_project_dis, convert_to_extras_kata, unicode, validate_general],
        'project_funding': [ignore_missing, check_project_dis, convert_to_extras_kata, unicode, validate_general],
        'project_homepage': [ignore_missing, check_project_dis, convert_to_extras_kata, unicode, validate_general],
        'discipline': [validate_discipline, convert_to_extras_kata, unicode],
        'geographic_coverage': [validate_spatial, convert_to_extras_kata, unicode],
        'license_URL': [default(u''), convert_to_extras_kata, unicode, validate_general],
    })

    schema.pop('author')
    schema.pop('organization')

    schema['evtype'] = {'value': [ignore_missing, unicode, event_to_extras, validate_general]}
    schema['evwho'] = {'value': [ignore_missing, unicode, event_to_extras, validate_general]}
    schema['evwhen'] = {'value': [ignore_missing, unicode, event_to_extras, validate_kata_date_relaxed]}
    schema['evdescr'] = {'value': [ignore_missing, unicode, event_to_extras, validate_general]}
    #schema['groups'].update({
    #    'name': [ignore_missing, unicode, add_to_group]
    #})

    #schema['direct_download_URL'] = [ignore_missing, default(settings.DATASET_URL_UNKNOWN),
    #                                 check_direct_download_url, unicode, validate_general, to_resource]
    #schema['algorithm'] = [ignore_missing, unicode, validate_algorithm]
    #schema['checksum'] = [ignore_missing, validate_general]
    #schema['mimetype'] = [ignore_missing, validate_mimetype]

    # Dataset resources might currently be present in two different format.
    #schema['resources']['url'] = [ignore_missing, default(settings.DATASET_URL_UNKNOWN),
    #                              check_direct_download_url, unicode, validate_general]
    #schema['resources']['algorithm'] = schema['algorithm']
    #schema['resources']['checksum'] = schema['checksum']
    #schema['resources']['mimetype'] = schema['mimetype']

    schema['resources']['url'] = [default(settings.DATASET_URL_UNKNOWN), check_direct_download_url, unicode,
                                  validate_general]
    schema['resources']['algorithm'] = [ignore_missing, unicode, validate_algorithm]
    schema['resources']['hash'].append(validate_general)
    schema['resources']['format'].append(validate_mimetype)

    return schema

def create_package_schema_ddi():
    '''
    Modified schema for datasets imported with ddi reader.
    Some fields in ddi import are allowed to be  missing.

    :return schema
    '''
    # Todo: requires additional testing and planning
    schema = create_package_schema()

    schema['contact_phone'] = [ignore_missing, validate_phonenum, convert_to_extras_kata, unicode]
    schema['contact_URL'] = [ignore_missing, url_validator, convert_to_extras_kata, unicode, validate_general]
    schema['discipline'].insert(0, ignore_missing)
    schema['geographic_coverage'].insert(0, ignore_missing)
    schema['temporal_coverage_begin'] = [ignore_missing, validate_kata_date_relaxed, convert_to_extras_kata, unicode]
    schema['temporal_coverage_end'] = [ignore_missing, validate_kata_date_relaxed, convert_to_extras_kata, unicode]
    # schema['xpaths'] = [xpath_to_extras]
    # schema['orgauth'] = {'value': [ignore_missing, unicode, org_auth_to_extras_oai, validate_general],
    #                      'org': [ignore_missing, unicode, org_auth_to_extras_oai, validate_general]}

    return schema

def update_package_schema_ddi():
    '''
    Modified schema for datasets imported with ddi reader.
    Some fields in ddi import are allowed to be  missing.

    :return schema
    '''
    schema = create_package_schema_ddi()

    schema['id'] = [ignore_missing, package_id_not_changed]
    schema['owner_org'] = [ignore_missing, owner_org_validator, unicode]
    schema.pop('xpaths')

    return schema

