# pylint: disable=unused-argument

"""
Main plugin file for Kata CKAN extension
"""

import datetime
import logging
import os
import json
import functionally as fn

from ckan.lib.base import g, c
from ckan.lib.navl.validators import (default,
                                      ignore,
                                      ignore_empty,
                                      ignore_missing,
                                      not_empty,
                                      not_missing)
from ckan.lib.plugins import DefaultDatasetForm
from ckan.logic.schema import (default_create_package_schema,
                               default_show_package_schema)
from ckan.logic.validators import (owner_org_validator,
                                   package_id_not_changed,
                                   package_name_validator,
                                   tag_length_validator,
                                   url_validator,
                                   vocabulary_id_exists)
from ckan.plugins import (implements,
                          toolkit,
                          IActions,
                          IAuthFunctions,
                          IConfigurable,
                          IConfigurer,
                          IDatasetForm,
                          IMapper,
                          IPackageController,
                          IRoutes,
                          IFacets,
                          ITemplateHelpers,
                          SingletonPlugin)
from ckan.plugins.core import unload
from ckanext.kata.validators import (check_access_request_url,
                                     check_agent,
                                     check_junk,
                                     kata_tag_name_validator,
                                     kata_tag_string_convert,
                                     validate_access_application_url,
                                     validate_algorithm,
                                     validate_discipline,
                                     validate_email,
                                     validate_general,
                                     validate_kata_date,
                                     validate_kata_date_relaxed,
                                     validate_mimetype,
                                     validate_phonenum,
                                     validate_spatial,
                                     validate_title,
                                     validate_title_duplicates,
                                     check_through_provider_url,
                                     contains_alphanumeric,
                                     check_events,
                                     validate_direct_download_url,
                                     package_name_not_changed, check_langtitle, check_pids, check_agent_fields)
from ckanext.kata import actions, auth_functions
from ckanext.kata.converters import (checkbox_to_boolean,
                                     convert_from_extras_kata,
                                     convert_languages,
                                     convert_to_extras_kata,
                                     ltitle_from_extras,
                                     ltitle_to_extras,
                                     remove_access_application_new_form,
                                     remove_disabled_languages,
                                     update_pid,
                                     to_extras_json,
                                     from_extras_json,
                                     flattened_to_extras,
                                     flattened_from_extras)
import ckanext.kata.settings as settings


log = logging.getLogger('ckanext.kata')     # pylint: disable=invalid-name
t = toolkit                                 # pylint: disable=invalid-name


class KataMetadata(SingletonPlugin):
    """
    Kata metadata plugin.
    """
    # pylint: disable=no-init, no-self-use

    implements(IRoutes, inherit=True)
    implements(IMapper, inherit=True)

    def before_map(self, map):
        """
        Override IRoutes.before_map()
        """
        get = dict(method=['GET'])
        controller = "ckanext.kata.controllers:MetadataController"
        api_controller = "ckanext.kata.controllers:KATAApiController"
        map.connect('/dataset/{id}.{format:rdf}',
                    controller=controller,
                    action='tordf')
        map.connect('/urnexport',
                    controller=controller,
                    action='urnexport')
        map.connect('/api/2/util/organization_autocomplete',
                    controller=api_controller,
                    conditions=get,
                    action="organization_autocomplete")
        map.connect('/api/2/util/discipline_autocomplete',
                    controller=api_controller,
                    conditions=get,
                    action="discipline_autocomplete")
        map.connect('/api/2/util/location_autocomplete',
                    controller=api_controller,
                    conditions=get,
                    action="location_autocomplete")
        map.connect('/api/2/util/tag/autocomplete',
                    controller=api_controller,
                    conditions=get,
                    action="tag_autocomplete")
        map.connect('/unlock_access/{id}',
                    controller="ckanext.kata.controllers:AccessRequestController",
                    action="unlock_access")
        map.connect('/create_request/{pkg_id}',
                    controller="ckanext.kata.controllers:AccessRequestController",
                    action="create_request")
        map.connect('/render_edit_request/{pkg_id}',
                    controller="ckanext.kata.controllers:AccessRequestController",
                    action="render_edit_request")
        map.connect('/request_dataset/send/{pkg_id}',
                    controller="ckanext.kata.controllers:ContactController",
                    action="send_request")
        map.connect('/request_dataset/{pkg_id}',
                    controller="ckanext.kata.controllers:ContactController",
                    action="render_request")
        map.connect('/contact/send/{pkg_id}',
                    controller="ckanext.kata.controllers:ContactController",
                    action="send_contact")
        map.connect('/contact/{pkg_id}',
                    controller="ckanext.kata.controllers:ContactController",
                    action="render_contact")
        map.connect('/dataset/import_xml/',
                    controller="ckanext.harvest.controllers.view:ViewController",
                    action="import_xml")
        map.connect('/user/logged_in',
                    controller="ckanext.kata.controllers:KataUserController",
                    action="logged_in")
        map.connect('/dataset/',
                    controller="ckanext.kata.controllers:KataPackageController",
                    action="advanced_search")
        map.connect('help',
                    '/help',
                    controller="ckanext.kata.controllers:KataInfoController",
                    action="render_help")
        map.connect('faq',
                    '/faq',
                    controller="ckanext.kata.controllers:KataInfoController",
                    action="render_faq")
        return map


class KataPlugin(SingletonPlugin, DefaultDatasetForm):
    """
    Kata functionality and UI plugin.
    """
    # pylint: disable=no-init, no-self-use

    implements(IDatasetForm, inherit=True)
    implements(IConfigurer, inherit=True)
    implements(IConfigurable, inherit=True)
    implements(IPackageController, inherit=True)
    implements(ITemplateHelpers, inherit=True)
    implements(IActions, inherit=True)
    implements(IAuthFunctions, inherit=True)
    implements(IFacets, inherit=True)

    def get_auth_functions(self):
        """
        Returns a dict of all the authorization functions which the
        implementation overrides
        """
        return {'package_update': auth_functions.is_owner,
                'resource_update': auth_functions.edit_resource,
                'package_delete': auth_functions.package_delete,
                }

    def get_actions(self):
        """ Register actions. """
        return {'package_show': actions.package_show,
                'package_create': actions.package_create,
                'package_update': actions.package_update,
                'package_delete': actions.package_delete,
                'package_search': actions.package_search,
                'resource_create': actions.resource_create,
                'resource_update': actions.resource_update,
                'resource_delete': actions.resource_delete,
                'group_list': actions.group_list,
                'group_create': actions.group_create,
                'group_update': actions.group_update,
                'group_delete': actions.group_delete,
                'related_create': actions.related_create,
                'related_update': actions.related_update,
                'related_delete': actions.related_delete,
                'member_create': actions.member_create,
                'member_delete': actions.member_delete,
                'organization_create': actions.organization_create,
                'organization_update': actions.organization_update,
                'organization_delete': actions.organization_delete,
                }

    def get_helpers(self):
        """ Register helpers """
        return {'get_authors': self.get_authors,
                'get_distributor': self.get_distributor,
                'get_funder': self.get_funder,
                'get_kata_errors': self.get_kata_errors,
                'get_owner': self.get_owner,
                'has_agents_funding_id': self.has_agents_funding_id,
                'has_agents_name': self.has_agents_name,
                'has_agents_organisation': self.has_agents_organisation,
                'has_agents_url': self.has_agents_url,
                'is_custom_form': self.is_custom_form,
                'kata_sorted_extras': self.kata_sorted_extras,
                'reference_update': self.reference_update,
                'resolve_agent_role': settings.resolve_agent_role,
                }

    def get_distributor(self, data_dict):
        '''Get a single distributor from agent field in data_dict'''
        return fn.first(filter(lambda x: x.get('role') == u'distributor', data_dict.get('agent', [])))

    def get_funder(self, data_dict):
        '''Get a single funder from agent field in data_dict'''
        return fn.first(filter(lambda x: x.get('role') == u'funder', data_dict.get('agent', [])))

    def get_owner(self, data_dict):
        '''Get a single owner from agent field in data_dict'''
        return fn.first(filter(lambda x: x.get('role') == u'owner', data_dict.get('agent', [])))

    def get_authors(self, data_dict):
        '''Get all authors from agent field in data_dict'''
        return filter(lambda x: x.get('role') == u'author', data_dict.get('agent', []))

    def has_agents_name(self, data_dict):
        '''Return true if some of the data dict's agents has attribute 'name'.'''
        return [] != filter(lambda x : x.get('name'), data_dict.get('agent', []))

    def has_agents_organisation(self, data_dict):
        '''Return true if some of the data dict's agents has attribute 'name'.'''
        return [] != filter(lambda x : x.get('organisation'), data_dict.get('agent', []))

    def has_agents_url(self, data_dict):
        '''Return true if some of the data dict's agents has attribute 'name'.'''
        return [] != filter(lambda x : x.get('URL'), data_dict.get('agent', []))

    def has_agents_funding_id(self, data_dict):
        '''Return true if some of the data dict's agents has attribute 'name'.'''
        return [] != filter(lambda x : x.get('funding-id'), data_dict.get('agent', []))

    def reference_update(self, ref):
        #@beaker_cache(type="dbm", expire=2678400)
        def cached_url(url):
            return url
        return cached_url(ref)

    def is_custom_form(self, _dict):
        """
        Template helper, used to identify ckan custom form
        """
        for key in self.hide_extras_form:
            if _dict.get('key', None) and _dict['key'].find(key) > -1:
                return False
        return True

    def get_kata_errors(self, errors):
        '''
        Helper for Kata errors, specifically the repeatable fields
        Constructs an array out of dict items. Tailored for
        events and orgauth (for now).
        
        :return {'orgauth': [u'error1. error2', u'error3']}
        '''
        output = {}
        for key in errors.keys():
            val = []
            for item in errors[key]:
                if not item:
                    val.append('')
                else:
                    if type(item) is dict:
                        # For orgauth, the key name is value OR org
                        for valuekey in item.keys():
                            val.append('. '.join(map(unicode, item[valuekey])))
            output[key] = val
        return output

    def kata_sorted_extras(self, list_):
        '''
        Used for outputting package extras, skips package_hide_extras
        '''
        output = []
        for extra in sorted(list_, key=lambda x:x['key']):
            if extra.get('state') == 'deleted':
                continue
            
            key, val = extra['key'], extra['value']
            if key in g.package_hide_extras and\
                key in settings.KATA_FIELDS and\
                key.startswith('author_') and\
                key.startswith('organization_'):
                continue
            
            if  key.startswith('title_') or\
                key.startswith('lang_title_') or\
                key == 'harvest_object_id' or\
                key == 'harvest_source_id' or\
                key == 'harvest_source_title':
                continue
            
            found = False
            for _key in g.package_hide_extras:
                if extra['key'].startswith(_key):
                    found = True
            if found:
                continue
            
            if isinstance(val, (list, tuple)):
                val = ", ".join(map(unicode, val))
            output.append((key, val))
        return output

    def update_config(self, config):
        """
        This IConfigurer implementation causes CKAN to look in the
        ```templates``` directory when looking for the package_form()
        """
        here = os.path.dirname(__file__)
        rootdir = os.path.dirname(os.path.dirname(here))
        template_dir = os.path.join(rootdir, 'ckanext', 'kata', 'theme', 'templates')
        config['extra_template_paths'] = ','.join([template_dir, config.get('extra_template_paths', '')])
        
        public_dir = os.path.join(rootdir, 'ckanext', 'kata', 'public')
        config['extra_public_paths'] = ','.join([public_dir, config.get('extra_public_paths', '')])
        toolkit.add_resource(public_dir, 'kata-resources')
        roles = config.get('kata.contact_roles', 'Please, Configure')
        config['package_hide_extras'] = ' '.join(settings.KATA_FIELDS)
        config['ckan.i18n_directory'] = os.path.join(rootdir, 'ckanext', 'kata')
        roles = [r for r in roles.split(', ')]
        self.roles = roles
        self.hide_extras_form = config.get('kata.hide_extras_form', '').split()

        log.debug("disable synchronous search")
        try:
            # This controls the operation of the CKAN search indexing. If you don't define this option
            # then indexing is on. You will want to turn this off if you have a non-synchronous search
            # index extension installed.
            unload('synchronous_search')
        except:
            pass

    def package_types(self):
        '''
        Return an iterable of package types that this plugin handles.
        '''
        return ['dataset']

    def is_fallback(self):
        '''
        Overrides IDatasetForm.is_fallback()
        From CKAN documentation:  "Returns true iff this provides the fallback behaviour,
        when no other plugin instance matches a package's type."
        '''
        return True

    def configure(self, config):
        '''
        Pass configuration to plugins and extensions.
        Called by load_environment.
        '''
        self.date_format = config.get('kata.date_format', '%Y-%m-%d')

    def setup_template_variables(self, context, data_dict):
        """
        Override DefaultDatasetForm.setup_template_variables() form  method from ckan.lib.plugins.py.
        """
        super(KataPlugin, self).setup_template_variables(context, data_dict)

        c.roles = self.roles
        c.lastmod = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

    def new_template(self):
        """Return location of the add dataset page"""
        return 'package/new.html'

    def comments_template(self):
        """Return location of the package comments page"""
        return 'package/comments.html'

    def search_template(self):
        """Return location of the package search page"""
        return 'package/search.html'

    def read_template(self):
        """Return location of the package read page"""
        return 'package/read.html'

    def history_template(self):
        """Return location of the package history page"""
        return 'package/history.html'

    def package_form(self):
        """Return location of the main package page"""
        return 'package/new_package_form.html'

    @classmethod
    def tags_schema(cls):
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

    @classmethod
    def create_package_schema(cls):
        """
        Return the schema for validating new dataset dicts.
        """

        # TODO: Use the general converter for lang_title and check that lang_title exists!

        schema = default_create_package_schema()
        schema.pop('author')
        # schema.pop('organization')

        for key in settings.KATA_FIELDS_REQUIRED:
            schema[key] = [not_empty, convert_to_extras_kata, unicode, validate_general]
        for key in settings.KATA_FIELDS_RECOMMENDED:
            schema[key] = [ignore_missing, convert_to_extras_kata, unicode, validate_general]

        schema['agent'] = {'role': [not_empty, check_agent_fields, validate_general, unicode, flattened_to_extras],
                           'name': [ignore_empty, validate_general, unicode, contains_alphanumeric, flattened_to_extras],
                           'id': [ignore_empty, validate_general, unicode, flattened_to_extras],
                           'organisation': [ignore_empty, validate_general, unicode, contains_alphanumeric, flattened_to_extras],
                           'URL': [ignore_empty, validate_general, unicode, flattened_to_extras],
                           # Note: Changed to 'funding-id' for now because 'funding_id'
                           # was returned as 'funding' from db. Somewhere '_id' was
                           # splitted off.
                           'funding-id': [ignore_empty, validate_general, unicode, flattened_to_extras]}
        # phone number can be missing from the first users
        schema['contact_phone'] = [ignore_missing, validate_phonenum, convert_to_extras_kata, unicode]
        schema['event'] = {'type': [ignore_missing, check_events, unicode, flattened_to_extras, validate_general],
                           'who': [ignore_missing, unicode, flattened_to_extras, validate_general, contains_alphanumeric],
                           'when': [ignore_missing, unicode, flattened_to_extras, validate_kata_date],
                           'descr': [ignore_missing, unicode, flattened_to_extras, validate_general, contains_alphanumeric]}
        schema['id'] = [default(u''), update_pid, unicode]
        schema['langtitle'] = {'value': [not_missing, unicode, validate_title, validate_title_duplicates, ltitle_to_extras],
                               'lang': [not_missing, unicode, convert_languages]}
        schema['language'] = \
            [ignore_missing, convert_languages, remove_disabled_languages, convert_to_extras_kata, unicode]
        schema['maintainer'] = [not_empty, unicode, validate_general, contains_alphanumeric]
        schema['maintainer_email'] = [not_empty, unicode, validate_email]
        # schema['orgauth'] = {'value': [not_missing, unicode, org_auth_to_extras, validate_general, contains_alphanumeric],
        #                      'org': [not_missing, unicode, org_auth_to_extras, validate_general, contains_alphanumeric]}
        schema['temporal_coverage_begin'] = \
            [ignore_missing, validate_kata_date, convert_to_extras_kata, unicode]
        schema['temporal_coverage_end'] = \
            [ignore_missing, validate_kata_date, convert_to_extras_kata, unicode]
        # schema['pids'] = [update_pids, ignore_missing, to_extras_json]
        schema['pids'] = {'provider': [not_missing, unicode, flattened_to_extras],
                          'id': [not_missing, unicode, flattened_to_extras],
                          'type': [not_missing, unicode, flattened_to_extras]}
        schema['tag_string'] = [ignore_missing, not_empty, kata_tag_string_convert]
        # otherwise the tags would be validated with default tag validator during update
        schema['tags'] = cls.tags_schema()
        schema['xpaths'] = [ignore_missing, to_extras_json]
        # these two can be missing from the first Kata end users
        # schema['owner'] = [ignore_missing, convert_to_extras_kata, unicode, validate_general, contains_alphanumeric]
        schema['contact_URL'] = [ignore_missing, url_validator, convert_to_extras_kata, unicode, validate_general]
        # TODO: version date validation should be tighter, see metadata schema
        schema['version'] = [not_empty, unicode, validate_kata_date]
        schema['availability'] = [not_missing, convert_to_extras_kata]
        schema['langdis'] = [checkbox_to_boolean, convert_to_extras_kata]
        schema['__extras'] = [check_agent, check_langtitle]
        schema['__junk'] = [check_junk]
        schema['name'] = [ignore_missing, unicode, update_pid, package_name_validator, validate_general]
        schema['access_application_new_form'] = [checkbox_to_boolean, convert_to_extras_kata, remove_access_application_new_form]
        schema['access_application_URL'] = [ignore_missing, validate_access_application_url,
                                            unicode, validate_general]
        schema['access_request_URL'] = [ignore_missing, check_access_request_url, url_validator, convert_to_extras_kata,
                                   unicode, validate_general]
        schema['through_provider_URL'] = [ignore_missing, check_through_provider_url, url_validator, convert_to_extras_kata,
                                     unicode]
        schema['discipline'] = [ignore_missing, validate_discipline, convert_to_extras_kata, unicode]
        schema['geographic_coverage'] = [ignore_missing, validate_spatial, convert_to_extras_kata, unicode]
        schema['license_URL'] = [ignore_missing, convert_to_extras_kata, unicode, validate_general]

        #schema['groups'].update({
        #    'name': [ignore_missing, unicode, add_to_group]
        #})

        schema['resources']['url'] = [default(settings.DATASET_URL_UNKNOWN), unicode, validate_general, validate_direct_download_url]
        # Conversion (and validation) of direct_download_URL to resource['url'] is in utils.py:dataset_to_resource()
        schema['resources']['algorithm'] = [ignore_missing, unicode, validate_algorithm]
        schema['resources']['hash'].append(validate_general)
        schema['resources']['mimetype'].append(validate_mimetype)

        return schema
    
    @classmethod
    def create_package_schema_oai_dc(cls):
        '''
        Modified schema for datasets imported with oai_dc reader.
        Some fields are missing, as the dublin core format
        doesn't provide so many options
        
        :return schema
        '''
        # Todo: requires additional testing and planning
        schema = cls.create_package_schema()
        
        schema['__extras'] = [ignore]   # This removes orgauth checking
        schema['availability'].insert(0, ignore_missing)
        schema['contact_phone'] = [ignore_missing, validate_phonenum, convert_to_extras_kata, unicode]
        schema['contact_URL'] = [ignore_missing, url_validator, convert_to_extras_kata, unicode, validate_general]
        schema['discipline'].insert(0, ignore_missing)
        schema['geographic_coverage'].insert(0, ignore_missing)
        #schema['maintainer_email'].insert(0, ignore_missing)
        schema['maintainer_email'] = [ignore_missing, validate_email, unicode]
        # schema['maintainer'].insert(0, ignore_missing)
        schema['maintainer'] = [ignore_missing, unicode, validate_general]
        # schema['orgauth'] = {'value': [ignore_missing, unicode, org_auth_to_extras_oai, validate_general],
        #                      'org': [ignore_missing, unicode, org_auth_to_extras_oai, validate_general]}
        # schema['owner'] = [ignore_missing, convert_to_extras_kata, unicode, validate_general]
        schema['version'] = [not_empty, unicode, validate_kata_date_relaxed]

        return schema

    @classmethod
    def create_package_schema_ddi(cls):
        '''
        Modified schema for datasets imported with ddi reader.
        Some fields in ddi import are allowed to be  missing.

        :return schema
        '''
        # Todo: requires additional testing and planning
        schema = cls.create_package_schema()

        schema['contact_phone'] = [ignore_missing, validate_phonenum, convert_to_extras_kata, unicode]
        schema['contact_URL'] = [ignore_missing, url_validator, convert_to_extras_kata, unicode, validate_general]
        schema['discipline'].insert(0, ignore_missing)
        schema['event'] = {'type': [ignore_missing, check_events, unicode, flattened_to_extras, validate_general],
                           'who': [ignore_missing, unicode, flattened_to_extras, validate_general, contains_alphanumeric],
                           'when': [ignore_missing, unicode, flattened_to_extras, validate_kata_date_relaxed],
                           'descr': [ignore_missing, unicode, flattened_to_extras, validate_general, contains_alphanumeric]}
        schema['geographic_coverage'].insert(0, ignore_missing)
        # schema['orgauth'] = {'value': [ignore_missing, unicode, org_auth_to_extras_ddi, validate_general],
        #                      'org': [ignore_missing, unicode, validate_general]}
        schema['temporal_coverage_begin'] = [ignore_missing, validate_kata_date_relaxed, convert_to_extras_kata, unicode]
        schema['temporal_coverage_end'] = [ignore_missing, validate_kata_date_relaxed, convert_to_extras_kata, unicode]
        schema['version'] = [not_empty, unicode, validate_kata_date_relaxed]
        # schema['xpaths'] = [xpath_to_extras]

        return schema

    def update_package_schema(self):
        """
        Return the schema for validating updated dataset dicts.
        """

        schema = self.create_package_schema()

        # Taken from ckan.logic.schema.default_update_package_schema():
        schema['id'] = [ignore_missing, package_id_not_changed]
        schema['name'] = [ignore_missing, package_name_not_changed]
        schema['owner_org'] = [ignore_missing, owner_org_validator, unicode]
        return schema
    
    @classmethod
    def update_package_schema_oai_dc(cls):
        '''
        Modified schema for datasets imported with oai_dc reader.
        Some fields are missing, as the dublin core format
        doesn't provide so many options
        
        :return schema
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
            schema[key] = [convert_from_extras_kata, ignore_missing, unicode]

        schema['agent'] = [flattened_from_extras, ignore_missing]
        schema['access_application_new_form'] = [unicode],
        # schema['author'] = [org_auth_from_extras, ignore_missing, unicode]
        schema['event'] = [flattened_from_extras, ignore_missing]
        schema['langdis'] = [unicode]
        # schema['organization'] = [ignore_missing, unicode]
        schema['pids'] = [flattened_from_extras, ignore_missing]
        # schema['projdis'] = [unicode]
        schema['title'] = [ltitle_from_extras, ignore_missing]
        #schema['version_PID'] = [version_pid_from_extras, ignore_missing, unicode]
        schema['xpaths'] = [from_extras_json, ignore_missing, unicode]

        #schema['resources']['resource_type'] = [from_resource]

        return schema

    def update_facet_titles(self, facet_titles):
        """
        Update the dictionary mapping facet names to facet titles.

        Example: {'facet_name': 'The title of the facet'}

        Called after the search operation was performed and
        before the search page will be displayed.
        The titles show up on the search page.
        """

        facet_titles.update(settings.get_field_titles(t._))
        return facet_titles
    
    def dataset_facets(self, facets_dict, package_type):
        '''
        Updating facets, before rendering search page.
        This is CKAN 2.0.3 hook, 2.1 will use the function above
        '''
        facets_dict.update(settings.get_field_titles(t._))

        return facets_dict

    def extract_search_params(self, data_dict):
        """
        Extracts parameters beginning with 'ext_' from data_dict['extras']
        for advanced search.
        @param data_dict: contains all parameters from search.html
        @return: unordered lists extra_terms and extra_ops, dict extra_dates
        """
        extra_terms = []
        extra_ops = []
        extra_dates = {}
        # Extract parameters
        for (param, value) in data_dict['extras'].items():
            if len(value):
                # Extract search operators
                if param.startswith('ext_operator'):
                    extra_ops.append((param, value))
                # Extract search date limits from eg.
                # name = "ext_date-metadata_modified-start"
                elif param.startswith('ext_date'):
                    param_tokens = param.split('-')
                    extra_dates[param_tokens[2]] = value  # 'start' or 'end' date
                    extra_dates['field'] = param_tokens[1]
                else: # Extract search terms
                    extra_terms.append((param, value))
        return extra_terms, extra_ops, extra_dates

    def parse_search_terms(self, data_dict, extra_terms, extra_ops):
        """
        Parse extra terms and operators into query q into data_dict:
        data_dict['q']: ((author:*onstabl*) OR (title:*edliest jok* AND \
          tags:*somekeyword*) OR (title:sometitle NOT tags:*otherkeyword*))
        Note that all ANDs and NOTs are enclosed in parenthesis by ORs.
        Outer parenthesis are for date limits to work correctly.

        @param data_dict: full data_dict from package:search
        @param extra_terms: [(ext_organization-2, u'someOrg'), ...]
        @param extra_ops: [(ext_operator-2, u'AND'), ...]
        """
        def extras_cmp(a, b):
            a  = a.split("-")[-1]
            b  = b.split("-")[-1]
            if a <= b:
                if a < b:
                    return -1
                else:
                    return 0
            else:
                return 1

        extra_terms.sort(cmp=extras_cmp, key=lambda tpl: tpl[0])
        extra_ops.sort(cmp=extras_cmp, key=lambda tpl: tpl[0])
        c.current_search_rows = []
        # Handle first search term row
        (param, value) = extra_terms[0]
        p_no_index = param.split("-")[0]
        data_dict['q'] += ' ((%s:%s' % (p_no_index[4:], value)  # Add field search to query q
        c.current_search_rows.append({'field': p_no_index, 'text': value})

        n = min(len(extra_terms)-1, len(extra_ops))
        for i1 in range(0, n):
            (oparam, ovalue) = extra_ops[i1]
            (param, value) = extra_terms[i1+1]
            p_no_index = param.split("-")[0]
            if ovalue in ['AND', 'NOT']:
                data_dict['q'] += ' %s' % ovalue  # Add operator (AND / NOT)
                data_dict['q'] += ' %s:%s' % (p_no_index[4:], value)  # Add field search to query q
            elif ovalue == 'OR':
                data_dict['q'] += ') %s (' % ovalue  # Add operator OR
                data_dict['q'] += ' %s:%s' % (p_no_index[4:], value)  # Add field search to query q
            c.current_search_rows.append(
                {'field':p_no_index, 'text':value, 'operator':ovalue})
        data_dict['q'] += '))'

    def parse_search_dates(self, data_dict, extra_dates):
        """
        Parse extra date into query q into data_dict:
        data_dict['q']: ((author:*onstabl*) OR (title:*edliest jok* AND \
          tags:*somekeyword*) OR (title:sometitle NOT tags:*otherkeyword*)) AND \
          metadata_modified:[1900-01-01T00:00:00.000Z TO 2000-12-31T23:59:59.999Z]

        @param data_dict: full data_dict from package:search
        @param extra_dates: {'start': 1991,
                             'end': 1994,
                             'field': 'metadata_modified'}
        """
        c.current_search_limiters = {}
        if len(data_dict['q']) > 0:
            data_dict['q'] += ' AND '
        qdate = ''
        if extra_dates.has_key('start'):
            # TODO: Validate that input is valid year
            qdate += '[' + extra_dates['start'] + '-01-01T00:00:00.000Z TO '
            key = 'ext_date-' + extra_dates['field'] + '-start'
            c.current_search_limiters[key] = extra_dates['start']
        else:
            qdate += '[* TO '
        if extra_dates.has_key('end'):
            # TODO: Validate that input is valid year
            qdate += extra_dates['end'] + '-12-31T23:59:59.999Z]'
            key = 'ext_date-' + extra_dates['field'] + '-end'
            c.current_search_limiters[key] = extra_dates['end']
        else:
            qdate += '*]'
        data_dict['q'] += ' %s:%s' % (extra_dates['field'], qdate)

    def before_search(self, data_dict):
        '''
        Things to do before querying Solr.

        :param data_dict: data_dict to modify
        '''

        if data_dict.has_key('sort') and data_dict['sort'] is None:
            data_dict['sort'] = settings.DEFAULT_SORT_BY
            c.sort_by_selected = settings.DEFAULT_SORT_BY  # This is to get the correct one pre-selected on the HTML form.

        c.search_fields = settings.SEARCH_FIELDS
        c.translated_field_titles = settings.get_field_titles(t._)

        # Start advanced search parameter parsing
        if data_dict.has_key('extras') and len(data_dict['extras']) > 0:
            #log.debug("before_search(): data_dict['extras']: %r" %
            #          data_dict['extras'].items())

            extra_terms, extra_ops, extra_dates = self.extract_search_params(data_dict)
            #log.debug("before_search(): extra_terms: %r; extra_ops: %r; "
            #          + "extra_dates: %r", extra_terms, extra_ops, extra_dates)

            if len(extra_terms) > 0:
                self.parse_search_terms(data_dict, extra_terms, extra_ops)
            if len(extra_dates) > 0:
                self.parse_search_dates(data_dict, extra_dates)

            #log.debug("before_search(): c.current_search_rows: %s; \
            #    c.current_search_limiters: %s" % (c.current_search_rows,
            #    c.current_search_limiters))
        # End advanced search parameter parsing

        data_dict['facet.field'] = settings.FACETS

        #log.debug("before_search(): data_dict: %r" % data_dict)
        # Uncomment below to show query with results and in the search field
        #c.q = data_dict['q']

        # Log non-empty search queries and constraints (facets)
        if data_dict['q'] or (data_dict['fq'] and data_dict['fq'] != '+dataset_type:dataset'):
            log.info(u"[{t}] Search query: {q};  constraints: {c}".format(t=datetime.datetime.now(), q=data_dict['q'], c=data_dict['fq']))

        return data_dict

    def before_index(self, pkg_dict):
        '''
        Modification to package dictionary before
        indexing it to Solr index
        
        :param pkg_dict: pkg_dict to modify
        '''
        
        # Add res_mimetype to pkg_dict. Can be removed after res_mimetype is
        # added to CKAN's index function.
        data = json.loads(pkg_dict['data_dict'])
        res_mimetype = []
        for resource in data['resources']:
            if resource['mimetype'] == None:
                res_mimetype.append(u'')
            else:
                res_mimetype.append(resource['mimetype'])
        pkg_dict['res_mimetype'] = res_mimetype

        # Separate agent roles for Solr indexing

        # pkg_dict2 = {'access_application_new_form': u'False',
        #              'agent': [],
        #              'agent_0_URL': u'www.csc.fi',
        #              'agent_0_funding-id': u'43096ertjgad\xf6sjgn89q3q4',
        #              'agent_0_name': u'F. Under',
        #              'agent_0_organisation': u'Agentti-Project',
        #              'agent_0_role': u'funder',
        #              'agent_1_name': u'o. oWNER',
        #              'agent_1_role': u'owner',
        #              'agent_2_name': u'M. Merger',
        #              'agent_2_role': u'author',
        #              'agent_3_name': u'juho',
        #              'agent_3_role': u'distributor',}
        new_items = {}

        for key, value in pkg_dict.iteritems():
            tokens = key.split('_')
            if tokens[0] == 'agent' and tokens[2] == 'role':
                role = value
                role_idx = role + '_' + tokens[1]
                new_items[role_idx] = pkg_dict.get('_'.join((tokens[0], tokens[1], 'name')), '')
                org_idx = 'organization_' + tokens[1]
                new_items[org_idx] = pkg_dict.get('_'.join((tokens[0], tokens[1], 'organisation')), '')

        pkg_dict.update(new_items)

        return pkg_dict
