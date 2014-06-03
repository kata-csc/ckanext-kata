# pylint: disable=unused-argument

"""
Main plugin file for Kata CKAN extension
"""

import datetime
import logging
import os
import json
import re

from ckan.lib.base import g, c
from ckan.lib.plugins import DefaultDatasetForm
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

from ckanext.kata import actions, auth_functions, settings, utils
import ckanext.kata.schemas as sch

from ckanext.kata import actions, auth_functions, settings, utils, helpers

log = logging.getLogger('ckanext.kata')     # pylint: disable=invalid-name
t = toolkit                                 # pylint: disable=invalid-name

###### Monkey patch for repoze.who ######
# Enables secure setting for cookies
# Part of repoze.who since version 2.0a4

from repoze.who.plugins.auth_tkt import AuthTktCookiePlugin
import datetime

def _now():
    return datetime.datetime.now()

def _get_monkeys(self, environ, value, max_age=None):
    
    if max_age is not None:
        max_age = int(max_age)
        later = _now() + datetime.timedelta(seconds=max_age)
        # Wdy, DD-Mon-YY HH:MM:SS GMT
        expires = later.strftime('%a, %d %b %Y %H:%M:%S')
        # the Expires header is *required* at least for IE7 (IE7 does
        # not respect Max-Age)
        max_age = "; Max-Age=%s; Expires=%s" % (max_age, expires)
    else:
        max_age = ''

    secure = ''
    if self.secure:
        secure = '; secure; HttpOnly'

    cur_domain = environ.get('HTTP_HOST', environ.get('SERVER_NAME'))
    wild_domain = '.' + cur_domain
    cookies = [
        ('Set-Cookie', '%s="%s"; Path=/%s%s' % (
        self.cookie_name, value, max_age, secure)),
        ('Set-Cookie', '%s="%s"; Path=/; Domain=%s%s%s' % (
        self.cookie_name, value, cur_domain, max_age, secure)),
        ('Set-Cookie', '%s="%s"; Path=/; Domain=%s%s%s' % (
        self.cookie_name, value, wild_domain, max_age, secure))
        ]
    return cookies

AuthTktCookiePlugin._get_cookies = _get_monkeys

###### End of Monkey patch ######

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
        map.connect('/api/2/util/media_type_autocomplete',
                    controller=api_controller,
                    conditions=get,
                    action="media_type_autocomplete")
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
        # map.connect('/dataset/import_xml/',
        #             controller="ckanext.harvest.controllers.view:ViewController",
        #             action="import_xml")
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
    
    create_package_schema = sch.create_package_schema
    create_package_schema_oai_dc = sch.create_package_schema_oai_dc
    create_package_schema_ddi = sch.create_package_schema_ddi
    update_package_schema = sch.update_package_schema
    update_package_schema_oai_dc = sch.update_package_schema_oai_dc
    show_package_schema = sch.show_package_schema
    tags_schema = sch.tags_schema
    

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
        return {'get_authors': utils.get_authors,
                'get_contact': utils.get_contact,
                'get_dict_field_errors': helpers.get_dict_field_errors,
                'get_distributor': utils.get_distributor,
                'get_funder': utils.get_funder,
                'get_funders': utils.get_funders,
                'get_owner': utils.get_owner,
                'get_package_ratings': utils.get_package_ratings,
                'has_agents_field': helpers.has_agents_field,
                'has_contacts_field': helpers.has_contacts_field,
                'kata_sorted_extras': helpers.kata_sorted_extras,
                'reference_update': helpers.reference_update,
                'resolve_agent_role': settings.resolve_agent_role,
                }

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

    def update_facet_titles(self, facet_titles):
        """
        Update the dictionary mapping facet names to facet titles.

        Example: {'facet_name': 'The title of the facet'}

        Called after the search operation was performed and
        before the search page will be displayed.
        The titles show up on the search page.
        """

        return self.dataset_facets(facet_titles, None)
    
    def dataset_facets(self, facets_dict, package_type):
        '''
        Updating facets, before rendering search page.
        This is CKAN 2.0.3 hook, 2.1 will use the function above
        '''
        titles = settings.get_field_titles(t._)
        kata_facet_titles = dict((field, title) for (field, title) in titles.iteritems() if field in settings.FACETS)

        # Replace the facet dictionary with Kata facets.
        # CKAN adds 'Groups' and 'Formats' there which we don't want.
        # /harvest page has a 'Frequency' facet which we lose also when replacing the dict here.

        # facets_dict.update(kata_facet_titles)
        facets_dict = kata_facet_titles
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
        extra_advanced_search = False
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
                elif param.startswith('ext_advanced-search'):
                    if value:
                        extra_advanced_search = True
                else: # Extract search terms
                    extra_terms.append((param, value))
        return extra_terms, extra_ops, extra_dates, extra_advanced_search

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
            qdate += '[' + extra_dates['start'] + '-01-01T00:00:00.000Z TO '
            key = 'ext_date-' + extra_dates['field'] + '-start'
            c.current_search_limiters[key] = extra_dates['start']
        else:
            qdate += '[* TO '
        if extra_dates.has_key('end'):
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

            extra_terms, extra_ops, extra_dates, c.advanced_search = self.extract_search_params(data_dict)
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
        q = data_dict.get('q')
        fq = data_dict.get('fq')
        if q or (fq and fq != '+dataset_type:dataset'):
            log.info(u"[{t}] Search query: {q};  constraints: {c}".format(t=datetime.datetime.now(), q=q, c=fq))

        return data_dict

    def before_index(self, pkg_dict):
        '''
        Modification to package dictionary before
        indexing it to Solr index
        
        :param pkg_dict: pkg_dict to modify
        '''
        EMAIL = re.compile(r'.*contact_\d*_email')

        # Add res_mimetype to pkg_dict. Can be removed after res_mimetype is
        # added to CKAN's index function.
        data = json.loads(pkg_dict['data_dict'])
        res_mimetype = []
        for resource in data.get('resources', []):
            if resource['mimetype'] == None:
                res_mimetype.append(u'')
            else:
                res_mimetype.append(resource['mimetype'])
        pkg_dict['res_mimetype'] = res_mimetype

        # Separate agent roles for Solr indexing

        new_items = {}

        for key, value in pkg_dict.iteritems():
            tokens = key.split('_')
            if tokens[0] == 'agent' and tokens[2] == 'role':
                role = value
                role_idx = role + '_' + tokens[1]
                role_idx = str(role_idx)        # Must not be unicode
                org_idx = 'organization_' + tokens[1]

                agent_name = pkg_dict.get('_'.join((tokens[0], tokens[1], 'name')), '')
                agent_org = pkg_dict.get('_'.join((tokens[0], tokens[1], 'organisation')), '')
                agent_id = pkg_dict.get('_'.join((tokens[0], tokens[1], 'id')), '')

                new_items[role_idx] = agent_name
                new_items[org_idx] = agent_org
                new_items['agent_name_' + tokens[1]] = agent_name
                new_items['agent_name_' + tokens[1] + '_org'] = agent_org
                new_items['agent_name_' + tokens[1] + '_id'] = agent_id
            
            # hide sensitive data
            if EMAIL.match(key):
                pkg_dict[key] = u''

        pkg_dict.update(new_items)
        
        # hide sensitive data
        for item in data.get('extras', []):
            if EMAIL.match(item['key']):
                item['value'] = u''

        pkg_dict['data_dict'] = json.dumps(data)

        return pkg_dict
