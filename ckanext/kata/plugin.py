# pylint: disable=unused-argument

"""
Main plugin file for Kata CKAN extension
"""

import logging
import datetime

import os

from ckan.plugins import implements, SingletonPlugin, toolkit
from ckan.plugins import IPackageController, IDatasetForm, IConfigurer, ITemplateHelpers
from ckan.plugins import IRoutes
from ckan.plugins import IConfigurable
from ckan.plugins import IMapper
from ckan.plugins import IActions
from ckan.plugins import IAuthFunctions
from ckan.plugins.core import unload
from ckan.lib.base import g, c
from ckan.model import Package
from ckan.lib.plugins import DefaultDatasetForm
from ckan.logic.schema import default_show_package_schema, \
    default_create_package_schema
from ckan.logic.validators import package_id_not_changed, owner_org_validator
from ckan.lib.navl.validators import ignore_missing, not_empty, not_missing, default, \
    ignore
from ckanext.kata.validators import check_project, validate_kata_date, \
    check_junk, check_last_and_update_pid, \
    validate_email, validate_phonenum, \
    check_project_dis, check_direct_download_url, check_access_request_url, check_access_application_url, \
    check_author_org, kata_tag_string_convert, \
    kata_tag_name_validator, validate_general, \
    validate_discipline, validate_spatial, validate_title, \
    validate_mimetype, validate_algorithm, validate_event_date
from ckanext.kata.converters import event_from_extras, \
    event_to_extras, ltitle_from_extras, ltitle_to_extras, \
    org_auth_from_extras, pid_from_extras, \
    remove_disabled_languages, checkbox_to_boolean, \
    org_auth_to_extras, update_pid, convert_from_extras_kata, convert_to_extras_kata, \
    convert_languages, org_auth_to_extras_oai
from ckanext.kata import actions, auth_functions, utils
import ckan.lib.helpers as h
from ckan.logic.validators import tag_length_validator, vocabulary_id_exists, \
    url_validator, package_name_validator
import ckanext.kata.settings as settings


log = logging.getLogger('ckanext.kata')     # pylint: disable=invalid-name
t = toolkit                                 # pylint: disable=invalid-name


def snippet(template_name, **kw):
    """This function is used to load html snippets into pages. keywords
    can be used to pass parameters into the snippet rendering."""
    import ckan.lib.base as base
    return base.render_snippet(template_name, **kw)


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
        map.connect('/api/2/util/owner_autocomplete',
                    controller=api_controller,
                    conditions=get,
                    action="owner_autocomplete")
        map.connect('/api/2/util/author_autocomplete',
                    controller=api_controller,
                    conditions=get,
                    action="author_autocomplete")
        map.connect('/api/2/util/organization_autocomplete',
                    controller=api_controller,
                    conditions=get,
                    action="organization_autocomplete")
        map.connect('/api/2/util/contact_autocomplete',
                    controller=api_controller,
                    conditions=get,
                    action="contact_autocomplete")
        map.connect('/api/2/util/discipline_autocomplete',
                    controller=api_controller,
                    conditions=get,
                    action="discipline_autocomplete")
        map.connect('/unlock_access/{id}',
                    controller="ckanext.kata.controllers:AccessRequestController",
                    action="unlock_access")
        map.connect('/create_request/{pkg_id}',
                    controller="ckanext.kata.controllers:AccessRequestController",
                    action="create_request")
        map.connect('/render_edit_request/{pkg_id}',
                    controller="ckanext.kata.controllers:AccessRequestController",
                    action="render_edit_request")
        map.connect('/read_data/{id}/{resource_id}',
                    controller="ckanext.kata.controllers:DataMiningController",
                    action="read_data")
        map.connect('/data_mining/save',
                    controller="ckanext.kata.controllers:DataMiningController",
                    action="save")
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

    def before_insert(self, mapper, connection, instance):
        """
        Override IMapper.before_insert(). Receive an object instance before that instance is INSERTed.
        """
        if isinstance(instance, Package) and not instance.id:
            instance.id = utils.generate_pid()


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
        return {'is_custom_form': self.is_custom_form,
                'kata_sorted_extras': self.kata_sorted_extras,
                'reference_update': self.reference_update
                }

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
        """
        Return location of the package add dataset page
        """
        return 'package/new.html'

    def comments_template(self):
        """
        Return location of the package comments page
        """
        return 'package/comments.html'

    def search_template(self):
        """
        Return location of the package search page
        """
        return 'package/search.html'

    def read_template(self):
        """
        Return location of the package read page
        """
        return 'package/read.html'

    def history_template(self):
        """
        Return location of the package history page
        """
        return 'package/history.html'

    def package_form(self):
        """
        Return location of the main package page
        """
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

        schema = default_create_package_schema()

        for key in settings.KATA_FIELDS_REQUIRED:
            schema[key] = [not_empty, convert_to_extras_kata, unicode, validate_general]
        for key in settings.KATA_FIELDS_RECOMMENDED:
            schema[key] = [ignore_missing, convert_to_extras_kata, unicode, validate_general]

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
        schema['tags'] = cls.tags_schema()

        schema.update({
            'version': [not_empty, unicode, validate_kata_date, check_last_and_update_pid],
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
        schema['evwhen'] = {'value': [ignore_missing, unicode, event_to_extras, validate_event_date]}
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
        
        schema['owner'] = [ignore_missing]
        schema['contact_phone'].insert(0, ignore_missing)
        #schema['contact_URL'].insert(0, ignore_missing)
        schema['contact_URL'] = [ignore_missing, url_validator, convert_to_extras_kata, unicode, validate_general]
        #schema['maintainer_email'].insert(0, ignore_missing)
        schema['maintainer_email'] = [ignore_missing, validate_email, unicode]
        schema['maintainer'].insert(0, ignore_missing)
        schema['availability'].insert(0, ignore_missing)
        schema['discipline'].insert(0, ignore_missing)
        schema['geographic_coverage'].insert(0, ignore_missing)
        schema['orgauth'] = {'value': [ignore_missing, unicode, org_auth_to_extras_oai, validate_general],
                             'org': [ignore_missing, unicode, org_auth_to_extras_oai, validate_general]}
        
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
        # schema['contact_phone'].insert(0, ignore_missing)
        schema['contact_phone'] = [ignore_missing]
        schema['contact_URL'] = [ignore_missing, url_validator, convert_to_extras_kata, unicode, validate_general]
        schema['discipline'].insert(0, ignore_missing)
        schema['geographic_coverage'].insert(0, ignore_missing)
        # schema['orgauth'] = {'value': [ignore_missing, unicode, org_auth_to_extras_oai, validate_general],
        #                      'org': [ignore_missing, unicode, org_auth_to_extras_oai, validate_general]}

        return schema


    def update_package_schema(self):
        """
        Return the schema for validating updated dataset dicts.
        """

        schema = self.create_package_schema()

        # Taken from ckan.logic.schema.default_update_package_schema():
        schema['id'] = [ignore_missing, package_id_not_changed]
        schema['owner_org'] = [ignore_missing, owner_org_validator, unicode]
        return schema
    
    def update_package_schema_oai_dc(self):
        '''
        Modified schema for datasets imported with oai_dc reader.
        Some fields are missing, as the dublin core format
        doesn't provide so many options
        
        :return schema
        '''
        schema = self.create_package_schema_oai_dc()
        
        schema['id'] = [ignore_missing, package_id_not_changed]
        schema['owner_org'] = [ignore_missing, owner_org_validator, unicode]
        
        return schema

    def show_package_schema(self):
        """
        The data fields that are returned from CKAN for each dataset can be changed with this method.
        This method is called when viewing or editing a dataset.
        """

        schema = default_show_package_schema()

        for key in settings.KATA_FIELDS:
            schema[key] = [convert_from_extras_kata, ignore_missing, unicode]

        schema['version_PID'] = [pid_from_extras, ignore_missing, unicode]

        schema['author'] = [org_auth_from_extras, ignore_missing, unicode]
        schema['organization'] = [org_auth_from_extras, ignore_missing, unicode]
        schema['title'] = [ltitle_from_extras, ignore_missing]
        schema['langdis'] = [unicode]
        schema['projdis'] = [unicode]
        schema['evtype'] = [event_from_extras, ignore_missing, unicode]
        schema['evwho'] = [event_from_extras, ignore_missing, unicode]
        schema['evwhen'] = [event_from_extras, ignore_missing, unicode]
        schema['evdescr'] = [event_from_extras, ignore_missing, unicode]

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
        return data_dict

    def after_search(self, search_results, data_dict):
        '''
        Things to do after querying Solr.
        '''
        return search_results

    def after_show(self, context, pkg_dict):
        '''
        Modifications of package dictionary before viewing it
        
        :param pkg_dict: pkg_dict to modify
        '''
        # ONKI selector is used without the space after comma
        try:
            if pkg_dict.get('tags') and not pkg_dict.get('tag_string'):
                pkg_dict['tag_string'] = ','.join(h.dict_list_reduce(
                    pkg_dict.get('tags', {}), 'name'))  
        except:
            log.debug('tags not found')
            
        return pkg_dict

