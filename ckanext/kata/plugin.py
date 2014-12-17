"""
Main plugin file for Kata CKAN extension. Compatible with CKAN 2.1 and 2.2.
"""

import logging
import os
import json
import re
import datetime

from ckan import logic
from ckan.lib.base import g, c, _
from ckan.common import OrderedDict
from ckan.lib.plugins import DefaultDatasetForm
from ckan.plugins import (implements,
                          toolkit,
                          IActions,
                          IAuthFunctions,
                          IConfigurable,
                          IConfigurer,
                          IDatasetForm,
                          IPackageController,
                          IRoutes,
                          IFacets,
                          ITemplateHelpers,
                          IMiddleware,
                          SingletonPlugin)

from ckan.plugins.core import unload

from ckanext.kata.schemas import Schemas

from ckanext.kata import actions, auth_functions, settings, utils, helpers

import ckanext.kata.extractor as extractor

from ckanext.kata.middleware import NotAuthorizedMiddleware

log = logging.getLogger('ckanext.kata')

###### MONKEY PATCH FOR REPOZE.WHO ######
# Enables secure setting for cookies
# Part of repoze.who since version 2.0a4
from repoze.who.plugins.auth_tkt import AuthTktCookiePlugin

def _get_monkeys(self, environ, value, max_age=None):
    
    if max_age is not None:
        max_age = int(max_age)
        later = datetime.datetime.now() + datetime.timedelta(seconds=max_age)
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
        ('Set-Cookie', '%s="%s"; Path=/%s%s' % (self.cookie_name, value, max_age, secure)),
        ('Set-Cookie', '%s="%s"; Path=/; Domain=%s%s%s' % (self.cookie_name, value, cur_domain, max_age, secure)),
        ('Set-Cookie', '%s="%s"; Path=/; Domain=%s%s%s' % (self.cookie_name, value, wild_domain, max_age, secure))
    ]
    return cookies

AuthTktCookiePlugin._get_cookies = _get_monkeys
###### END OF MONKEY PATCH ######


class KataPlugin(SingletonPlugin, DefaultDatasetForm):
    """
    Kata functionality and UI plugin.
    """
    implements(IDatasetForm, inherit=True)
    implements(IConfigurer, inherit=True)
    implements(IConfigurable, inherit=True)
    implements(IPackageController, inherit=True)
    implements(ITemplateHelpers, inherit=True)
    implements(IActions, inherit=True)
    implements(IAuthFunctions, inherit=True)
    implements(IFacets, inherit=True)
    implements(IRoutes, inherit=True)
    implements(IMiddleware, inherit=True)

    create_package_schema = Schemas.create_package_schema
    create_package_schema_oai_dc = Schemas.create_package_schema_oai_dc
    create_package_schema_oai_dc_ida = Schemas.create_package_schema_oai_dc_ida
    create_package_schema_ddi = Schemas.create_package_schema_ddi
    update_package_schema = Schemas.update_package_schema
    update_package_schema_oai_dc = Schemas.update_package_schema_oai_dc
    update_package_schema_oai_dc_ida = Schemas.update_package_schema_oai_dc_ida
    show_package_schema = Schemas.show_package_schema
    tags_schema = Schemas.tags_schema
    create_package_schema_oai_cmdi = Schemas.create_package_schema_oai_cmdi

    def before_map(self, map):
        """
        Override IRoutes.before_map()
        """
        get = dict(method=['GET'])
        controller = "ckanext.kata.controllers:MetadataController"
        api_controller = "ckanext.kata.controllers:KATAApiController"
        # Full stops from harvested objects screw up the read method
        # when using the default ckan route
        map.connect('/dataset/{id:.*?}.{format:rdf}',
                    controller="ckanext.kata.controllers:KataPackageController",
                    action='read_rdf')
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
        map.connect('/api/2/util/funder_autocomplete',
                    controller=api_controller,
                    conditions=get,
                    action="funder_autocomplete")
        map.connect('/unlock_access/{id}',
                    controller="ckanext.kata.controllers:EditAccessRequestController",
                    action="unlock_access")
        map.connect('/create_request/{pkg_id}',
                    controller="ckanext.kata.controllers:EditAccessRequestController",
                    action="create_request")
        map.connect('/render_edit_request/{pkg_id}',
                    controller="ckanext.kata.controllers:EditAccessRequestController",
                    action="render_edit_request")
        map.connect('/request_dataset/send/{pkg_id}',
                    controller="ckanext.kata.controllers:ContactController",
                    action="send_request_message")
        map.connect('/request_dataset/{pkg_id}',
                    controller="ckanext.kata.controllers:ContactController",
                    action="render_request_form")
        map.connect('/contact/send/{pkg_id}',
                    controller="ckanext.kata.controllers:ContactController",
                    action="send_contact_message")
        map.connect('/contact/{pkg_id}',
                    controller="ckanext.kata.controllers:ContactController",
                    action="render_contact_form")
        map.connect('/user/logged_in',
                    controller="ckanext.kata.controllers:KataUserController",
                    action="logged_in")
        map.connect('/user/logged_out_redirect',
                    controller="ckanext.kata.controllers:KataUserController",
                    action='logged_out_page')
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
        map.connect('/package_administration/{name}',
                    controller="ckanext.kata.controllers:KataPackageController",
                    action="dataset_editor_manage")
        map.connect('/dataset_editor_delete/{name}',
                    controller="ckanext.kata.controllers:KataPackageController",
                    action="dataset_editor_delete")
        map.connect('/storage/upload_handle',
                    controller="ckanext.kata.controllers:MalwareScanningStorageController",
                    action='upload_handle')
        map.connect('add dataset with upload_xml',
                    '/dataset/new',
                    controller="ckanext.kata.controllers:KataPackageController",
                    action="new")
        return map

    def get_auth_functions(self):
        """
        Returns a dict of all the authorization functions which the
        implementation overrides
        """
        return {
            'current_package_list_with_resources': logic.auth.get.sysadmin,
            'package_delete': auth_functions.package_delete,
            'package_update': auth_functions.is_owner,
            'resource_update': auth_functions.edit_resource,
            'package_create': auth_functions.package_create,
            'package_show': auth_functions.package_show,
            'user_list': logic.auth.get.sysadmin,
            'user_autocomplete': auth_functions.user_autocomplete,
            'user_activity_list': auth_functions.user_activity_list,
            'package_activity_list': logic.auth.get.sysadmin,
            'group_activity_list': logic.auth.get.sysadmin,
            'organization_activity_list': logic.auth.get.sysadmin,
            'member_list': auth_functions.member_list,
        }

    def get_actions(self):
        """ Register actions. """
        return {
            'dataset_editor_add': actions.dataset_editor_add,
            'dataset_editor_delete': actions.dataset_editor_delete,
            'group_create': actions.group_create,
            # 'group_list': actions.group_list,
            'group_update': actions.group_update,
            'group_delete': actions.group_delete,
            'member_create': actions.member_create,
            'member_delete': actions.member_delete,
            'member_list': actions.member_list,
            'organization_create': actions.organization_create,
            'organization_delete': actions.organization_delete,
            'organization_list_for_user': actions.organization_list_for_user,
            'organization_member_create': actions.organization_member_create,
            'organization_update': actions.organization_update,
            'package_create': actions.package_create,
            'package_delete': actions.package_delete,
            'package_owner_org_update': actions.package_owner_org_update,
            'package_search': actions.package_search,
            'package_show': actions.package_show,
            'package_update': actions.package_update,
            'related_create': actions.related_create,
            'related_delete': actions.related_delete,
            'related_update': actions.related_update,
            'resource_create': actions.resource_create,
            'resource_delete': actions.resource_delete,
            'resource_update': actions.resource_update,
            'user_activity_list': actions.user_activity_list,
            'user_activity_list_html': actions.user_activity_list_html,
            'package_activity_list': actions.package_activity_list,
            'package_activity_list_html': actions.package_activity_list_html,
            'group_activity_list': actions.group_activity_list,
            'group_activity_list_html': actions.group_activity_list_html,
            'organization_activity_list': actions.organization_activity_list,
            'organization_activity_list_html': actions.organization_activity_list_html,
        }

    def get_helpers(self):
        """ Register helpers """
        return {
            'convert_language_code': helpers.convert_language_code,
            'create_loop_index': helpers.create_loop_index,
            'dataset_is_valid': helpers.dataset_is_valid,
            'filter_system_users': helpers.filter_system_users,
            'get_authors': helpers.get_authors,
            'get_contacts': helpers.get_contacts,
            'get_contributors': helpers.get_contributors,
            'get_dict_errors': helpers.get_dict_errors,
            'get_dict_field_errors': helpers.get_dict_field_errors,
            'get_distributor': helpers.get_distributor,
            'get_download_url': helpers.get_download_url,
            'get_first_admin': helpers.get_first_admin,
            'get_funder': helpers.get_funder,
            'get_funders': helpers.get_funders,
            'get_if_url': helpers.get_if_url,
            'get_owners': helpers.get_owners,
            'get_package_ratings': helpers.get_package_ratings,
            'get_package_ratings_for_data_dict': helpers.get_package_ratings_for_data_dict,
            'get_pids_by_type': utils.get_pids_by_type,
            'get_pid_types': helpers.get_pid_types,
            'get_primary_pid': utils.get_primary_pid,
            'get_related_urls': helpers.get_related_urls,
            'get_rightscategory': helpers.get_rightscategory,
            'get_urn_fi_address': helpers.get_urn_fi_address,
            'get_visibility_options': helpers.get_visibility_options,
            'has_agents_field': helpers.has_agents_field,
            'has_contacts_field': helpers.has_contacts_field,
            'is_allowed_org_member_edit': helpers.is_allowed_org_member_edit,
            'is_backup_instance': helpers.is_backup_instance,
            'kata_sorted_extras': helpers.kata_sorted_extras,
            'list_organisations': helpers.list_organisations,
            'modify_error_summary': helpers.modify_error_summary,
            'reference_update': helpers.reference_update,
            'resolve_agent_role': helpers.resolve_agent_role,
            'split_disciplines': helpers.split_disciplines,
            'string_to_list': helpers.string_to_list,
            'organizations_available': helpers.organizations_available,
        }

    def get_dict_field_errors(self, errors, field, index, name):
        '''Get errors correctly for fields that are represented as nested dict fields in data_dict.

        :param errors: errors dictionary
        :param field: field name
        :param index: index
        :param name:
        :returns: `[u'error1', u'error2']`
        '''
        error = []
        error_dict = errors.get(field)
        if error_dict and error_dict[index]:
            error = error_dict[index].get(name)
        return error

    # Todo: some of these can be found from helpers, too. This shouldn't be
    def has_agents_field(self, data_dict, field):
        '''
        Return true if some of the data dict's agents has attribute given in field.

        :rtype: boolean
        '''
        return [] != filter(lambda x : x.get(field), data_dict.get('agent', []))

    def has_contacts_field(self, data_dict, field):
        '''
        Return true if some of the data dict's contacts has attribute given in field'.

        :rtype: boolean
        '''
        return [] != filter(lambda x : x.get(field), data_dict.get('contact', []))

    def reference_update(self, ref):
        # Todo: this can be found from helpers as well!
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
        Used for outputting package extras, skips `package_hide_extras`
        '''
        output = []
        for extra in sorted(list_, key=lambda x:x['key']):
            if extra.get('state') == 'deleted':
                continue

            # Todo: the AND makes no sense. Isn't this in helpers too?
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
        `templates` directory when looking for the `package_form()`
        """
        toolkit.add_template_directory(config, 'theme/templates')
        toolkit.add_public_directory(config, 'theme/public')
        toolkit.add_resource('theme/public', 'kata-resources')      # Fanstatic resource library

        here = os.path.dirname(__file__)
        rootdir = os.path.dirname(os.path.dirname(here))

        roles = config.get('kata.contact_roles', 'Please, Configure')
        config['package_hide_extras'] = ' '.join(settings.KATA_FIELDS)
        config['ckan.i18n_directory'] = os.path.join(rootdir, 'ckanext', 'kata')
        roles = [r for r in roles.split(', ')]
        self.roles = roles
        self.hide_extras_form = config.get('kata.hide_extras_form', '').split()

        try:
            # This controls the operation of the CKAN search indexing. If you don't define this option
            # then indexing is on. You will want to turn this off if you have a non-synchronous search
            # index extension installed.
            unload('synchronous_search')
            log.debug("Disabled synchronous search")
            # Note: in CKAN 2.2, disabling this plugin causes other plugins to be reloaded
        except:
            log.debug("Failed to disable synchronous search!")

    def package_types(self):
        '''
        Return an iterable of package types that this plugin handles.
        '''
        return ['dataset']

    def is_fallback(self):
        '''
        Overrides ``IDatasetForm.is_fallback()``
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
        Override ``DefaultDatasetForm.setup_template_variables()`` form  method from :file:`ckan.lib.plugins.py`.
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

    def _get_common_facets(self):
        titles = utils.get_field_titles(toolkit._)
        return OrderedDict((field, titles[field]) for field in settings.FACETS)

    def dataset_facets(self, facets_dict, package_type):
        '''
        Update the dictionary mapping facet names to facet titles.
        The dict supplied is actually an ordered dict.

        Example: ``{'facet_name': 'The title of the facet'}``

        :param facets_dict: the facets dictionary
        :param package_type: eg. `dataset`
        :returns: the modified facets_dict
        '''
        # /harvest page has a 'Frequency' facet which we lose also when replacing the dict here.
        return self._get_common_facets()

    def organization_facets(self, facets_dict, organization_type, package_type):
        """ See :meth:`ckan.plugins.IFacets.organization_facets`. """
        return self._get_common_facets()

    def extract_search_params(self, data_dict):
        """
        Extracts parameters beginning with ``ext_`` from `data_dict['extras']`
        for advanced search.

        :param data_dict: contains all parameters from search.html
        :rtype: unordered lists extra_terms and extra_ops, dict extra_dates
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
        `data_dict['q']: ((author:*onstabl*) OR (title:*edliest jok* AND
        tags:*somekeyword*) OR (title:sometitle NOT tags:*otherkeyword*))`
        Note that all ANDs and NOTs are enclosed in parenthesis by ORs.
        Outer parenthesis are for date limits to work correctly.

        :param data_dict: full data_dict from package:search
        :param extra_terms: `[(ext_organization-2, u'someOrg'), ...]`
        :param extra_ops: `[(ext_operator-2, u'AND'), ...]`
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
        `data_dict['q']: ((author:*onstabl*) OR (title:*edliest jok* AND
        tags:*somekeyword*) OR (title:sometitle NOT tags:*otherkeyword*)) AND
        metadata_modified:[1900-01-01T00:00:00.000Z TO 2000-12-31T23:59:59.999Z]`

        :param data_dict: full data_dict from package:search
        :param extra_dates: ``{'start': 1991,
                             'end': 1994,
                             'field': 'metadata_modified'}``
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
        Things to do before querying Solr. Basically used by
        the advanced search feature.

        :param data_dict: data_dict to modify
        '''

        if data_dict.has_key('sort') and data_dict['sort'] is None:
            data_dict['sort'] = settings.DEFAULT_SORT_BY
            c.sort_by_selected = settings.DEFAULT_SORT_BY  # This is to get the correct one pre-selected on the HTML form.

        c.search_fields = settings.SEARCH_FIELDS
        c.translated_field_titles = utils.get_field_titles(toolkit._)

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
        indexing it to Solr index. For example, we
        add resource mimetype to the index, modify
        agents and hide the email address
        
        :param pkg_dict: pkg_dict to modify
        :returns: the modified package dict to be indexed
        '''
        EMAIL = re.compile(r'.*contact_\d*_email')

        # Add res_mimetype to pkg_dict. Can be removed after res_mimetype is
        # added to CKAN's index function.
        data = json.loads(pkg_dict['data_dict'])
        # We do not want owner_org to organization facets. Note that owner_org.name
        # is an id in our case and thus not human readable
        pkg_dict['organization'] = ''

        res_mimetype = []
        for resource in data.get('resources', []):
            if resource['mimetype'] == None:
                res_mimetype.append(u'')
            else:
                res_mimetype.append(resource['mimetype'])
        pkg_dict['res_mimetype'] = res_mimetype

        # Extract plain text from resources and add to the data dict for indexing
        for resource in data.get('resources', []):
            if resource['resource_type'] in ('file', 'file.upload'):
                try:
                    text = extractor.extract_text(resource['url'], resource['format'])
                except IOError as ioe:
                    log.debug(str(ioe))
                    text = ""
                if text:
                    all_text = pkg_dict.get('res_text_contents', '')
                    all_text += (text + '\n')
                    pkg_dict['res_text_contents'] = all_text

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

    def make_middleware(self, app, config):
        ''' See `ckan.plugins.interfaces.IMiddleware.make_middleware
            Add handling for NotAuthorized exceptions.
        '''
        return NotAuthorizedMiddleware(app, config)

