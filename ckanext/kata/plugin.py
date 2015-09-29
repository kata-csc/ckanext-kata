"""
Main plugin file for Kata CKAN extension. Compatible with CKAN 2.1 and 2.2.
"""

import logging
import os
import json
import re
import datetime
import iso8601

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

from ckanext.kata import actions, auth_functions, extractor, helpers, settings, utils

from ckanext.kata.middleware import NotAuthorizedMiddleware

log = logging.getLogger('ckanext.kata')

# ##### MONKEY PATCH FOR REPOZE.WHO ######
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
# ##### END OF MONKEY PATCH ######


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
        map.connect('/dataset/{id:.*?}.{format:ttl}',
                    controller="ckanext.kata.controllers:KataPackageController",
                    action='read_ttl')
        map.connect('/browse',
                    controller="ckanext.kata.controllers:KataPackageController",
                    action='browse')
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
        # TODO Juho: Temporary organisation autocomplete implementation in
        # kata..plugin.py, kata..controllers.py, kata/actions.py, kata/auth_functions.py
        map.connect('/api/2/util/organization/autocomplete',
                    controller=api_controller,
                    conditions=get,
                    action='organization_autocomplete')
        map.connect('/api/2/util/language/autocomplete',
                    controller=api_controller,
                    conditions=get,
                    action='language_autocomplete')
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
        map.connect('data-model',
                    '/data-model',
                    controller="ckanext.kata.controllers:KataInfoController",
                    action="render_data_model")
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
        map.connect('home',
                    '/',
                    controller="ckanext.kata.controllers:KataHomeController",
                    action="index")

        # Hide resource_read page
        map.redirect('/dataset/{id}/resource/{resource_id}', '/dataset/{id}')
        return map

    def get_auth_functions(self):
        """
        Returns a dict of all the authorization functions which the
        implementation overrides
        """
        return {
            'current_package_list_with_resources': logic.auth.get.sysadmin,
            'package_delete': auth_functions.package_delete,
            'package_revision_list': auth_functions.package_revision_list,
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
            'organization_autocomplete': auth_functions.organization_autocomplete,
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
            'organization_autocomplete': actions.organization_autocomplete,
            'organization_create': actions.organization_create,
            'organization_delete': actions.organization_delete,
            'organization_list': actions.organization_list,
            'organization_list_for_user': actions.organization_list_for_user,
            'organization_member_create': actions.organization_member_create,
            'organization_update': actions.organization_update,
            'package_create': actions.package_create,
            'package_delete': actions.package_delete,
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
            'disciplines_string_resolved': helpers.disciplines_string_resolved,
            'filter_system_users': helpers.filter_system_users,
            'format_facet_labels': helpers.format_facet_labels,
            'get_active_facets': helpers.get_active_facets,
            'get_authors': helpers.get_authors,
            'get_contacts': helpers.get_contacts,
            'get_contributors': helpers.get_contributors,
            'get_dataset_paged_order': helpers.get_dataset_paged_order,
            'get_description': helpers.get_description,
            'get_dict_errors': helpers.get_dict_errors,
            'get_dict_field_errors': helpers.get_dict_field_errors,
            'get_distributor': helpers.get_distributor,
            'get_download_url': helpers.get_download_url,
            'get_fields_grouped': helpers.get_fields_grouped,
            'get_funder': helpers.get_funder,
            'get_funders': helpers.get_funders,
            'get_ga_id': helpers.get_ga_id,
            'get_if_url': helpers.get_if_url,
            'get_iso_datetime': helpers.get_iso_datetime,
            'get_label_for_uri': helpers.get_label_for_uri,
            'get_labels_for_uri': helpers.get_labels_for_uri,
            'get_labels_for_uri_nocache': helpers.get_labels_for_uri_nocache,
            'get_owners': helpers.get_owners,
            'get_package_ratings': helpers.get_package_ratings,
            'get_package_ratings_for_data_dict': helpers.get_package_ratings_for_data_dict,
            'get_pids_by_type': utils.get_pids_by_type,
            'get_pid_types': helpers.get_pid_types,
            'get_primary_pid': utils.get_primary_pid,
            'get_related_urls': helpers.get_related_urls,
            'get_rightscategory': helpers.get_rightscategory,
            'get_tab_errors': helpers.get_tab_errors,
            'get_translation': helpers.get_translation,
            'get_translation_from_extras': helpers.get_translation_from_extras,
            'get_language': helpers.get_language,
            'get_urn_fi_address': helpers.get_urn_fi_address,
            'get_dummy_title': helpers.get_dummy_title,
            'get_visibility_options': helpers.get_visibility_options,
            'has_json_content': helpers.has_json_content,
            'is_active_facet': helpers.is_active_facet,
            'is_allowed_org_member_edit': helpers.is_allowed_org_member_edit,
            'is_backup_instance': helpers.is_backup_instance,
            'is_url': helpers.is_url,
            'kata_build_nav_main': helpers.kata_build_nav_main,
            'multilang_to_json': helpers.multilang_to_json,
            'json_to_list': helpers.json_to_list,
            'list_organisations': helpers.list_organisations,
            'modify_error_summary': helpers.modify_error_summary,
            'reference_update': helpers.reference_update,
            'resolve_agent_role': helpers.resolve_agent_role,
            'resolve_org_name': helpers.resolve_org_name,
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

    def reference_update(self, ref):
        # Todo: this can be found from helpers as well!
        # @beaker_cache(type="dbm", expire=2678400)
        def cached_url(url):
            return url
        return cached_url(ref)

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

        config['package_hide_extras'] = ' '.join(settings.KATA_FIELDS)
        config['ckan.i18n_directory'] = os.path.join(rootdir, 'ckanext', 'kata')

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

    def setup_template_variables(self, context, data_dict):
        """
        Override ``DefaultDatasetForm.setup_template_variables()`` form  method from :file:`ckan.lib.plugins.py`.
        """
        super(KataPlugin, self).setup_template_variables(context, data_dict)

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

    def constrain_by_temporal_coverage(self, extras):
        """
        Add temporal coverage constraint to Solr query if fields are given in extras
        -(-temporal_coverage_begin:[* TO 2100-01-01T00:00:00Z] AND temporal_coverage_begin:[* TO *]) AND
        -(-temporal_coverage_end:[1600-01-01T00:00:00Z TO *] AND temporal_coverage_end:[* TO *])
        --------------------------
        :param extras: data_dict['extras']
        :returns: Solr query that constrains by temporal coverage
        :rtype : str
        """
        START_FIELD = 'temporal_coverage_begin'
        END_FIELD = 'temporal_coverage_end'
        EXTRAS_START_FIELD = 'ext_' + START_FIELD
        EXTRAS_END_FIELD = 'ext_' + END_FIELD

        if not c.current_search_limiters:
            c.current_search_limiters = {}

        start_date = extras.get(EXTRAS_START_FIELD)
        end_date = extras.get(EXTRAS_END_FIELD)

        query = ''

        if start_date or end_date:
            if start_date:
                c.current_search_limiters[START_FIELD] = extras.pop(EXTRAS_START_FIELD)
            if end_date:
                c.current_search_limiters[END_FIELD] = extras.pop(EXTRAS_END_FIELD)

            start_date = start_date + '-01-01T00:00:00Z' if start_date else '*'
            end_date = end_date + '-12-31T23:59:59.999Z' if end_date else '*'

            query = ('-(-{sf}:[* TO {e}] AND {sf}:[* TO *]) AND '
                     '-(-{ef}:[{s} TO *] AND {ef}:[* TO *])').\
                format(s=start_date, e=end_date, sf=START_FIELD, ef=END_FIELD)

        return query

    def before_search(self, data_dict):
        '''
        Things to do before querying Solr. Basically used by
        the advanced search feature.

        :param data_dict: data_dict to modify
        '''

        extras = data_dict.get('extras')
        if extras:
            query = data_dict.get('q', '')
            data_dict['q'] = ('(({q})) '.format(q=query) if query else '') + self.constrain_by_temporal_coverage(extras)

        if 'sort' in data_dict and data_dict['sort'] is None:
            data_dict['sort'] = settings.DEFAULT_SORT_BY

            # This is to get the correct one pre-selected on the HTML form.
            c.sort_by_selected = settings.DEFAULT_SORT_BY

        c.translated_field_titles = utils.get_field_titles(toolkit._)

        if data_dict.get('q') and 'owner_org' not in data_dict['q']:
            data_dict['defType'] = 'edismax'

        data_dict['facet.field'] = settings.FACETS

        # log.debug("before_search(): data_dict: %r" % data_dict)
        # Uncomment below to show query with results and in the search field
        # c.q = data_dict['q']

        # Log non-empty search queries and constraints (facets)
        q = data_dict.get('q')
        fq = data_dict.get('fq')
        if q or (fq and fq != '+dataset_type:dataset'):
            log.info(u"[{t}] Search query: {q};  constraints: {c}".format(t=datetime.datetime.now(), q=q, c=fq))

        return data_dict

    def _handle_titles(self, pkg_dict):

        title = pkg_dict.get('title')
        if not title:
            return
        titles = list()
        try:
            titlejson = json.loads(title)
            for key, value in titlejson.items():
                dictkey = "title_" + (key if len(key) > 0 else 'fin')
                pkg_dict[dictkey] = value
                titles.append(value)
            pkg_dict['title'] = ", ".join(titles)
            pkg_dict['title_string'] = pkg_dict['title']
        except (ValueError, TypeError):
            try:
                titles = list()
                keys_to_remove = list()
                for key, value in pkg_dict.items():
                    if re.search(r'^title_[\d]+$', key):
                        items = key.split("_")
                        d = "lang_title_" + items[-1]
                        keys_to_remove.extend([d, key])
                        dictkey = "title_" + (pkg_dict.get(d) or 'fin')
                        pkg_dict[dictkey] = value
                        titles.append(value)
                # handle titles of harvest sources with 'else'
                pkg_dict['title'] = ", ".join(titles) if titles else title
                pkg_dict['title_string'] = pkg_dict['title']
                 # Remove duplicate entries from index
                for rem in keys_to_remove:
                    if rem in pkg_dict:
                        del pkg_dict[rem]
                    if "extras_" + rem in pkg_dict:
                        del pkg_dict["extras_" + rem]
            except:
                return
            return

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
        pkg_dict['isopen'] = data.get('isopen')

        pkg_dict['res_mimetype'] = [res['mimetype'] for res in data.get('resources', []) if res.get('mimetype')]

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
                role_idx = '{role}_{id}'.format(role=value, id=tokens[1])        # Must not be unicode
                org_idx = 'organization_{id}'.format(id=tokens[1])

                agent_name = pkg_dict.get('agent_{id}_name'.format(id=tokens[1]))
                agent_org = pkg_dict.get('agent_{id}_organisation'.format(id=tokens[1]))
                agent_id = pkg_dict.get('agent_{id}_id'.format(id=tokens[1]))

                if agent_name:
                    new_items[role_idx] = agent_name
                    new_items['agent_name_' + tokens[1]] = agent_name
                if agent_org:
                    new_items[org_idx] = agent_org
                    new_items['agent_name_' + tokens[1] + '_org'] = agent_org
                if agent_id:
                    new_items['agent_name_' + tokens[1] + '_id'] = agent_id

            # hide sensitive data
            if EMAIL.match(key):
                pkg_dict[key] = u''

        pkg_dict.update(new_items)

        # hide sensitive data
        for item in data.get('extras', []):
            if EMAIL.match(item['key']):
                item['value'] = u''

        # Resolve uri labels and add them to the Solr index.
        # Discipline field in pkg_dict is of type comma-separated-string, while
        # tags are given already as a list
        split_disciplines = helpers.split_disciplines(pkg_dict.get('discipline'))
        pkg_dict['extras_discipline_resolved'] = self._resolve_labels(split_disciplines, 'okm-tieteenala')
        pkg_dict['extras_keywords_resolved'] = self._resolve_labels(pkg_dict.get('tags'), 'koko')

        # Make dates compliant with ISO 8601 used by Solr.
        # We assume here that what we get is partial date (YYYY or YYYY-MM) that is compliant with the standard.
        # Eg. the standard always uses 4-digit year (1583-9999) and two-digit month
        DATE_TEMPLATES = {'temporal_coverage_begin': '2000-01-01T00:00:00Z',
                          'temporal_coverage_end': '2000-12-31T23:59:59Z'}

        for temporal_field, date_template in DATE_TEMPLATES.iteritems():
            temporal_date = pkg_dict.get(temporal_field)

            # Remove time zone as Solr doesn't support it.
            # NOTE: Date time is not converted to UTC, but time zone is just stripped. Could be converted with arrow.
            if temporal_date:
                try:
                    datetime_obj = iso8601.parse_date(temporal_date)
                    temporal_date = datetime_obj.replace(tzinfo=None).isoformat()

                    pkg_dict[temporal_field] = temporal_date + date_template[len(temporal_date):]
                except iso8601.ParseError:
                    temporal_date = ''

            if temporal_date == '':
                # Remove empty strings as they won't fit into Solr's TrieDateField
                pkg_dict.pop(temporal_field)

        self._handle_titles(pkg_dict)

        pkg_dict['data_dict'] = json.dumps(data)

        return pkg_dict

    def make_middleware(self, app, config):
        ''' See `ckan.plugins.interfaces.IMiddleware.make_middleware
            Add handling for NotAuthorized exceptions.
        '''
        return NotAuthorizedMiddleware(app, config)

    def _resolve_labels(self, entries, vocab):
        '''
        A helper function to resolve lables for discplines and tag_strings

        :param entries: the comma-separated pkg_dict entries for a set of uris as a string
        :param vocab: the vocabulary of the query
        :returns: a comma-separated string of resolved entries.
        unresolved entries are left as-is.
        '''

        resolved_entries = []

        # resolve entries by URI from FINTO
        if entries:
            for entry in entries:
                try:
                    labels = helpers.get_labels_for_uri(entry, vocab)
                except TypeError:
                    labels = helpers.get_labels_for_uri_nocache(entry, vocab)
                if labels:
                    for label in labels:
                        resolved_entries.append(label.get('value'))

        return ",".join(resolved_entries)
