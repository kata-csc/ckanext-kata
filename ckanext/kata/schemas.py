from ckan.lib.navl.validators import (default,
                                      ignore,
                                      ignore_empty,
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
import ckanext.kata.validators as va
import ckanext.kata.converters as co
import ckanext.kata.settings as settings

import logging
log = logging.getLogger(__name__)


class Schemas:
    '''
    Class for static schemas
    '''

    def __init__(self):
        pass

    @classmethod
    def tags_schema(cls):
        '''
        Schema for dataset keywords (tags)
        '''
        schema = {
            'name': [not_missing,
                     not_empty,
                     unicode,
                     tag_length_validator,
                     va.kata_tag_name_validator,
                     ],
            'vocabulary_id': [ignore_missing, unicode, vocabulary_id_exists],
            'revision_timestamp': [ignore],
            'state': [ignore],
            'display_name': [ignore],
        }
        return schema

    @classmethod
    def create_package_schema(cls):
        """
        Return the schema for validating new dataset dicts that a user creates through web interface or API.

        :rtype: schema
        """
        schema = cls._create_package_schema()
        schema['tag_string'] = [not_missing, not_empty, va.kata_tag_string_convert]
        return schema

    @classmethod
    def _create_package_schema(cls):
        """ Create common schema for dataset create and update. Used by user interfaces and harvesters.
        """
        # Note: harvester schemas

        schema = default_create_package_schema()
        schema.pop('author')

        for key in settings.KATA_FIELDS_REQUIRED:
            schema[key] = [not_empty, co.convert_to_extras_kata, unicode, va.validate_general]
        for key in settings.KATA_FIELDS_RECOMMENDED:
            schema[key] = [ignore_missing, co.convert_to_extras_kata, unicode, va.validate_general]

        schema['accept-terms'] = [va.usage_terms_accepted, ignore]
        schema['__after'] = [co.organization_create_converter,
                             co.gen_translation_str_from_langtitle,
                             co.gen_translation_str_from_langnotes]
        schema['agent'] = {'role': [not_empty, va.check_agent_fields, va.validate_general, unicode, co.flattened_to_extras],
                           'name': [ignore_empty, va.validate_general, unicode, va.contains_alphanumeric, co.flattened_to_extras],
                           'id': [ignore_empty, va.validate_general, unicode, co.flattened_to_extras],
                           'organisation': [ignore_empty, va.validate_general, unicode, va.contains_alphanumeric, co.flattened_to_extras],
                           'URL': [ignore_empty, url_validator, va.validate_general, unicode, co.flattened_to_extras],
                           'fundingid': [ignore_empty, va.validate_general, unicode, co.flattened_to_extras]}
        schema['contact'] = {'name': [not_empty, va.validate_general, unicode, va.contains_alphanumeric, co.flattened_to_extras],
                             'email': [not_empty, unicode, va.validate_email, co.flattened_to_extras],
                             'URL': [ignore_empty, url_validator, va.validate_general, unicode, co.flattened_to_extras],
                             # phone number can be missing from the first users
                             'phone': [ignore_missing, unicode, va.validate_phonenum, co.flattened_to_extras]}
        # phone number can be missing from the first users
        # schema['contact_phone'] = [ignore_missing, validate_phonenum, convert_to_extras_kata, unicode]
        # schema['contact_URL'] = [ignore_missing, url_validator, convert_to_extras_kata, unicode, validate_general]
        schema['event'] = {'type': [ignore_missing, va.check_events, unicode, co.flattened_to_extras, va.validate_general],
                           'who': [ignore_missing, unicode, co.flattened_to_extras, va.validate_general, va.contains_alphanumeric],
                           'when': [ignore_missing, unicode, co.flattened_to_extras, va.validate_kata_date],
                           'descr': [ignore_missing, unicode, co.flattened_to_extras, va.validate_general, va.contains_alphanumeric]}
        schema['id'] = [default(u''), co.update_pid, unicode]

        # Langtitle fields are used by the UI, to construct a 'title' field with translations in JSON format
        # This is not necessarily needed for the API calls
        schema['langtitle'] = {'value': [unicode, va.validate_title, va.validate_title_duplicates, co.escape_quotes],
                               'lang': [unicode, co.convert_languages]}

        # The title field contains all the title translations in JSON format.
        # The converter gen_translation_str_from_langtitle
        # needs to be called to construct the JSON string from the UI's langtitle fields.
        schema['title'] = [ignore_empty]

        # Description (notes) is a multilanguage field similar to title
        schema['langnotes'] = {'value': [unicode, va.validate_notes_duplicates, co.escape_quotes],
                               'lang': [unicode, co.convert_languages]}
        schema['notes'] = [ignore_empty]

        schema['language'] = \
            [ignore_missing, co.convert_languages, co.remove_disabled_languages, co.convert_to_extras_kata, unicode]
        schema['license_id'] = [co.to_licence_id, unicode]
        schema['temporal_coverage_begin'] = \
            [ignore_missing, va.validate_kata_date, co.convert_to_extras_kata, unicode]
        schema['temporal_coverage_end'] = \
            [ignore_missing, va.validate_kata_date, co.convert_to_extras_kata, unicode]
        schema['pids'] = {'provider': [ignore_missing, unicode, co.flattened_to_extras],
                          'id': [not_empty, va.validate_general, unicode, co.flattened_to_extras],
                          'type': [not_missing, unicode, co.flattened_to_extras],
                          'primary': [ignore_missing, unicode, co.flattened_to_extras]}
        schema['tag_string'] = [ignore_missing, not_empty, va.kata_tag_string_convert]
        # otherwise the tags would be validated with default tag validator during update
        schema['tags'] = cls.tags_schema()
        schema['xpaths'] = [ignore_missing, co.to_extras_json]
        schema['version'] = [not_empty, unicode, va.validate_kata_date]
        schema['availability'] = [not_missing, co.convert_to_extras_kata]
        schema['langdis'] = [co.checkbox_to_boolean, co.convert_to_extras_kata]
        schema['__extras'] = [va.check_agent, va.check_contact, va.check_pids, va.check_langtitle]
        schema['__junk'] = [va.check_junk]
        schema['name'] = [va.continue_if_missing, co.default_name_from_id, unicode, package_name_validator,
                          va.validate_general]
        schema['access_application_download_URL'] = [ignore_missing, va.validate_access_application_download_url,
                                                     unicode, va.validate_general, co.convert_to_extras_kata]
        schema['access_application_new_form'] = [co.checkbox_to_boolean, co.convert_to_extras_kata,
                                                 co.remove_access_application_new_form]
        schema['access_application_URL'] = [ignore_missing, va.validate_access_application_url,
                                            unicode, va.validate_general, co.convert_to_extras_kata]
        schema['access_request_URL'] = [ignore_missing, va.check_access_request_url, url_validator,
                                        unicode, va.validate_general, co.convert_to_extras_kata]
        schema['through_provider_URL'] = [ignore_missing, va.check_through_provider_url, url_validator,
                                          unicode, va.validate_general, co.convert_to_extras_kata]
        schema['discipline'] = [ignore_missing, va.validate_discipline, co.convert_to_extras_kata, unicode]
        schema['geographic_coverage'] = [ignore_missing, va.validate_spatial, co.convert_to_extras_kata, unicode]
        schema['license_URL'] = [va.continue_if_missing, va.validate_license_url, co.convert_to_extras_kata, unicode,
                                 va.validate_general]
        schema['owner_org'] = [va.kata_owner_org_validator, unicode]
        schema['resources']['url'] = [default(settings.DATASET_URL_UNKNOWN), va.check_direct_download_url,
                                      unicode, va.validate_general]
        # Conversion (and validation) of direct_download_URL to resource['url'] is in utils.py:dataset_to_resource()
        schema['resources']['algorithm'] = [ignore_missing, unicode, va.validate_algorithm]
        schema['resources']['format'].append(va.validate_general)
        schema['resources']['hash'].append(va.validate_general)
        schema['resources']['mimetype'].append(va.validate_mimetype)
        return schema

    @classmethod
    def private_package_schema(cls):
        '''
        For a private dataset only a title and owner_org are required. The design is based on a principle,
        that as little changes as possible are made - ignore_empty are only added and the
        rest'll stay the same, if possible.

        The key lists should be updated according to schema changes.

        :return: schema, where only title and owner_org are required
        '''

        schema = cls.create_package_schema()
        dict_keys = ['tags', 'contact']
        pass_keys = ['langtitle', 'langnotes', 'agent']
        check_keys = settings.KATA_FIELDS_REQUIRED + ['language', '__extras', 'tag_string',
                                                      'accept-terms', 'version', 'license_URL']

        def _clean_schema_item(val):
            if ignore_empty not in val:
                val.insert(0, ignore_empty)
            if not_empty in val:
                val.remove(not_empty)
            if not_missing in val:
                val.remove(not_missing)

        for key, value in schema.iteritems():
            if key not in check_keys or key in pass_keys:
                continue
            elif key == '__extras':
                # Remove checks: no agent nor contact is required
                if va.check_agent in value:
                    value.remove(va.check_agent)
                if va.check_contact in value:
                    value.remove(va.check_contact)
            elif key == 'accept-terms':
                if va.usage_terms_accepted in value:
                    value.remove(va.usage_terms_accepted)
            elif key in dict_keys:
                # Add validators to pass empty stuff and remove validators that check that stuff exists
                for k, v in schema[key].iteritems():
                    _clean_schema_item(v)
            else:
                # Same as the one above, for non-dictionaries
                _clean_schema_item(value)

        return schema

    @classmethod
    def create_package_schema_oai_dc_ida(cls):
        """
        Mofidified schema for oai_dc using IDA. See `create_package_schema_oai_dc`.

        :rtype: dictionary
        """
        schema = cls.create_package_schema_oai_dc()
        for _key, value in schema['contact'].iteritems():
            value.insert(0, va.ignore_empty_data)

        schema['contact'] = {'name': [ignore_missing,  unicode, co.flattened_to_extras],
                             'email': [ignore_missing, unicode, co.flattened_to_extras],
                             'URL': [ignore_missing, ignore_empty, unicode, co.flattened_to_extras],
                             'phone': [ignore_missing, unicode, co.flattened_to_extras]}

        schema['agent'] = {'role': [not_empty, va.check_agent_fields, unicode, co.flattened_to_extras],
                           'name': [ignore_missing, ignore_empty, unicode, co.flattened_to_extras],
                           'id': [ignore_missing, ignore_empty, unicode, co.flattened_to_extras],
                           'organisation': [ignore_missing, ignore_empty, unicode, co.flattened_to_extras],
                           'URL': [ignore_missing, ignore_empty, unicode, co.flattened_to_extras],
                           'fundingid': [ignore_missing, ignore_empty, unicode, co.flattened_to_extras]}

        schema['language'] = \
            [ignore_missing, co.convert_to_extras_kata, unicode]

        schema['tag_string'] = [ignore_missing, ignore_empty, va.kata_tag_string_convert]
        schema['version'] = [ignore_missing, unicode]
        return schema

    @classmethod
    def create_package_schema_oai_dc(cls):
        '''
        Modified schema for datasets imported with oai_dc reader.
        Some fields are missing, as the dublin core format
        doesn't provide so many options

        :rtype: schema
        '''
        # Todo: requires additional testing and planning
        schema = cls._create_package_schema()

        schema.pop('accept-terms', None)

        schema['__extras'] = [ignore]   # This removes orgauth checking
        schema['availability'].insert(0, ignore_missing)
        # Todo: this shouldn't be anymore
        schema['contact_URL'] = [ignore_missing, url_validator, co.convert_to_extras_kata, unicode, va.validate_general]
        schema['discipline'].insert(0, ignore_missing)
        schema['geographic_coverage'].insert(0, ignore_missing)
        schema['license_URL'] = [ignore_missing, co.convert_to_extras_kata, unicode, va.validate_general]
        schema['maintainer'] = [ignore_missing, unicode, va.validate_general]
        schema['contact'] = {'name': [ignore_missing, va.validate_general, unicode, va.contains_alphanumeric, co.flattened_to_extras],
                             'email': [ignore_missing, unicode, va.validate_email, co.flattened_to_extras],
                             'URL': [ignore_empty, url_validator, va.validate_general, unicode, co.flattened_to_extras],
                             'phone': [ignore_missing, unicode, va.validate_phonenum, co.flattened_to_extras]}
        schema['version'] = [not_empty, unicode, va.validate_kata_date_relaxed]
        return schema


    @classmethod
    def create_package_schema_oai_cmdi(cls):
        """
        Mofidified schema for oai_dc using CMDI. See `create_package_schema_oai_dc`.

        :rtype: dictionary
        """
        schema = cls.create_package_schema_oai_dc()
        schema['tag_string'] = [ignore_missing, not_empty, va.kata_tag_string_convert]
        return schema


    @classmethod
    def create_package_schema_ddi(cls):
        '''
        Modified schema for datasets imported with ddi reader.
        Some fields in ddi import are allowed to be  missing.

        :rtype: schema
        '''
        schema = cls._create_package_schema()

        schema.pop('accept-terms', None)

        schema['discipline'].insert(0, ignore_missing)
        schema['event'] = {'type': [ignore_missing, unicode, co.flattened_to_extras, va.validate_general],
                           'who': [ignore_missing, unicode, co.flattened_to_extras, va.validate_general, va.contains_alphanumeric],
                           'when': [ignore_missing, unicode, co.flattened_to_extras, va.validate_kata_date_relaxed],
                           'descr': [ignore_missing, unicode, co.flattened_to_extras, va.validate_general, va.contains_alphanumeric]}
        schema['geographic_coverage'].insert(0, ignore_missing)
        schema['license_URL'] = [ignore_missing, co.convert_to_extras_kata, unicode, va.validate_general]
        schema['temporal_coverage_begin'] = [ignore_missing, va.validate_kata_date_relaxed, co.convert_to_extras_kata, unicode]
        schema['temporal_coverage_end'] = [ignore_missing, va.validate_kata_date_relaxed, co.convert_to_extras_kata, unicode]
        schema['version'] = [not_empty, unicode, va.validate_kata_date_relaxed]
        # schema['xpaths'] = [xpath_to_extras]

        return schema

    @classmethod
    def update_package_schema(cls):
        """
        Return the schema for validating updated dataset dicts.

        :rtype: schema
        """
        schema = cls._create_package_schema()
        # Taken from ckan.logic.schema.default_update_package_schema():
        schema['id'] = [ignore_missing, package_id_not_changed]
        schema['name'] = [ignore_missing, va.package_name_not_changed]
        schema['owner_org'] = [ignore_missing, va.kata_owner_org_validator, unicode]
        return schema

    @classmethod
    def update_package_schema_oai_dc_ida(cls):
        '''
        Oai_dc reader schema for IDA. See `update_package_schema_oai_dc`.

        :rtype: dict
        '''
        schema = cls.create_package_schema_oai_dc_ida()

        schema['id'] = [ignore_missing, package_id_not_changed]
        schema['owner_org'] = [ignore_missing, owner_org_validator, unicode]

        return schema

    @classmethod
    def update_package_schema_oai_dc(cls):
        '''
        Modified schema for datasets imported with oai_dc reader.
        Some fields are missing, as the dublin core format
        doesn't provide so many options

        :rtype: schema
        '''
        schema = cls.create_package_schema_oai_dc()

        schema['id'] = [ignore_missing, package_id_not_changed]
        schema['owner_org'] = [ignore_missing, owner_org_validator, unicode]

        return schema

    @classmethod
    def show_package_schema(cls):
        """
        The data fields that are returned from CKAN for each dataset can be changed with this method.
        This method is called when viewing or editing a dataset.

        :rtype: schema
        """

        schema = default_show_package_schema()
        # Put back validators for several keys into the schema so validation
        # doesn't bring back the keys from the package dicts if the values are
        # 'missing' (i.e. None).
        # See few lines into 'default_show_package_schema()'
        schema['author'] = [ignore_missing]
        schema['author_email'] = [ignore_missing]
        schema['organization'] = [ignore_missing]

        for key in settings.KATA_FIELDS:
            schema[key] = [co.convert_from_extras_kata, ignore_missing, unicode]

        schema['__after'] = [co.check_primary_pids]
        schema['agent'] = [co.flattened_from_extras, ignore_missing]
        schema['contact'] = [co.flattened_from_extras, ignore_missing]
        schema['access_application_new_form'] = [unicode],
        # schema['author'] = [org_auth_from_extras, ignore_missing, unicode]
        schema['event'] = [co.flattened_from_extras, ignore_missing]
        schema['langdis'] = [unicode]
        # schema['organization'] = [ignore_missing, unicode]
        schema['pids'] = [co.flattened_from_extras, ignore_missing]
        # schema['projdis'] = [unicode]

        # co.gen_translation_str_from_extras updates the title field to show the JSON
        # translation string if old format titles are found from extras
        schema['title'] = [ignore_missing, co.gen_translation_str_from_extras, co.set_language_for_title]

        schema['notes'] = [co.ensure_valid_notes]

        # schema['langtitle'] = {'value': [unicode, co.gen_translation_str_from_langtitle],
        #                        'lang': [unicode, co.convert_languages]}

        #schema['version_PID'] = [version_pid_from_extras, ignore_missing, unicode]
        schema['xpaths'] = [co.from_extras_json, ignore_missing, unicode]
        #schema['resources']['resource_type'] = [from_resource]

        return schema

    @staticmethod
    def _harvest_non_unique_url(schema):
        schema['url'] = [not_empty, unicode, url_validator]
        return schema

    @classmethod
    def harvest_source_create_package_schema(cls):
        from ckanext.harvest.logic.schema import harvest_source_create_package_schema
        return cls._harvest_non_unique_url(harvest_source_create_package_schema())

    @classmethod
    def harvest_source_update_package_schema(cls):
        from ckanext.harvest.logic.schema import harvest_source_update_package_schema
        return cls._harvest_non_unique_url(harvest_source_update_package_schema())

    @classmethod
    def harvest_source_show_package_schema(cls):
        from ckanext.harvest.logic.schema import harvest_source_show_package_schema
        return cls._harvest_non_unique_url(harvest_source_show_package_schema())
