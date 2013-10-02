"""
Main plugin file for Kata CKAN extension
"""

import logging
import os
import datetime

from pylons import config

from ckan.plugins import implements, SingletonPlugin, toolkit
from ckan.plugins import IPackageController, IDatasetForm, IConfigurer, ITemplateHelpers
from ckan.plugins import IRoutes
from ckan.plugins import IConfigurable
from ckan.plugins import IMapper
from ckan.plugins import IActions
from ckan.plugins import IAuthFunctions
from ckan.plugins.core import unload
from ckan.lib.base import g, c
from ckan.model import Package, PackageExtra, user_has_role, repo, Session
from ckan.lib.plugins import DefaultDatasetForm
from ckan.logic.schema import   default_show_package_schema, \
    default_create_package_schema, \
    default_update_package_schema, \
    default_resource_schema
from ckan.logic.validators import no_http, duplicate_extras_key, \
    package_id_not_changed, name_validator, package_name_validator, owner_org_validator
from ckan.lib.navl.validators import missing, ignore_missing, not_empty, not_missing, default, \
    ignore
from ckanext.kata.validators import check_project, validate_access, validate_kata_date, \
    check_junk, check_last_and_update_pid, \
    validate_language, validate_email, validate_phonenum, \
    check_project_dis, check_accessrequesturl, check_accessrights, \
    check_author_org, kata_tag_string_convert, \
    kata_tag_name_validator, \
    validate_discipline, validate_spatial
from ckanext.kata.converters import event_from_extras, \
    event_to_extras, ltitle_from_extras, ltitle_to_extras, \
    org_auth_from_extras, org_auth_to_extras, pid_from_extras, \
    add_to_group
from ckanext.kata import actions, auth_functions, utils
from ckanext.kata.model import KataAccessRequest
from ckanext.kata.settings import FACETS, DEFAULT_SORT_BY, get_field_titles, SEARCH_FIELDS
import ckan.lib.helpers as h
from ckan.logic.validators import tag_length_validator, vocabulary_id_exists


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
        map.connect('/read_data/{id}/{resource_id}',
                    controller="ckanext.kata.controllers:DataMiningController",
                    action="read_data")
        map.connect('/data_mining/save',
                    controller="ckanext.kata.controllers:DataMiningController",
                    action="save")
        map.connect('/contact/send/{pkg_id}',
                    controller="ckanext.kata.controllers:ContactController",
                    action="send")
        map.connect('/contact/{pkg_id}',
                    controller="ckanext.kata.controllers:ContactController",
                    action="render")
        map.connect('/dataset/import_xml/',
                    controller="ckanext.harvest.controllers.view:ViewController",
                    action="import_xml")
        map.connect('add dataset', 
                    '/dataset/new', 
                    controller='package', 
                    action='new')
        map.connect('/dataset/new_comment/{id}',
                    controller='ckanext.kata.controllers:KataCommentController',
                    action="new_comment")
        map.connect('/user/logged_in',
                    controller="ckanext.kata.controllers:KataUserController",
                    action="logged_in")
        map.connect('/dataset/',
                    controller="ckanext.kata.controllers:KataPackageController",
                    action="advanced_search")
        map.connect('dataset_read', 
                    '/dataset/{id}',
                    controller="ckanext.kata.controllers:KataPackageController",
                    action="read")
        map.connect('help',
                    '/help',
                    controller="ckanext.kata.controllers:KataInfoController",
                    action="render_help")
        map.connect('faq',
                    '/faq',
                    controller="ckanext.kata.controllers:KataInfoController",
                    action="render_faq")
        map.connect('ckanadmin_report',
                    '/ckan-admin/report',
                    controller='ckanext.kata.controllers:SystemController',
                    action='report')
        map.connect('applications',
                    '/applications',
                    controller="ckanext.kata.controllers:AVAAController",
                    action="listapps")
        return map

    def before_insert(self, mapper, connection, instance):
        """
        Override IMapper.before_insert(). Receive an object instance before that instance is INSERTed.
        """
        if isinstance(instance, Package):
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

    # Required extras fields
    kata_fields_required = ['version', 'language',
                  'publisher', 'phone', 'contactURL',
                  'project_name', 'funder', 'project_funding', 'project_homepage',
                  'access', 'accessRights', 'accessrequestURL', 'licenseURL',
                  'organization', 'author', 'owner']

    # Recommended extras fields
    kata_fields_recommended = ['geographic_coverage', 'temporal_coverage_begin',
                  'temporal_coverage_end', 'discipline', 'fformat', 'checksum',
                  'algorithm', 'evwho', 'evdescr', 'evtype', 'evwhen', 'langdis',
                  'projdis']

    kata_field = kata_fields_recommended + kata_fields_required


    def get_auth_functions(self):
        """
        Returns a dict of all the authorization functions which the
        implementation overrides
        """
        return {'package_update': auth_functions.is_owner}


    def get_actions(self):
        """ Register actions. """
        return {'package_show': actions.package_show,
                'package_create': actions.package_create,
                'package_update': actions.package_update,
                'group_list': actions.group_list,
                'accessreq_show': actions.accessreq_show,
                'related_create': actions.related_create,
                'related_update': actions.related_update,
                }


    def get_helpers(self):
        """ Register helpers """
        return {'is_custom_form': self.is_custom_form,
                'kata_sorted_extras': self.kata_sorted_extras,
                'kata_metadata_fields': self.kata_metadata_fields,
                'reference_update': self.reference_update,
                'request_access': self.request_access,
                }


    def request_access(self, pkg_id):
        """If the user is logged in show the access request button"""
        pkg = Package.get(pkg_id)
        if c.user and not user_has_role(c.userobj, 'admin', pkg) and\
                        not user_has_role(c.userobj, 'editor', pkg) and\
                        not c.userobj.sysadmin and\
                        not config.get('smtp_server', False):
            following = KataAccessRequest.is_requesting(c.userobj.id, pkg_id)
            if not following:
                return snippet('snippets/access_button.html',
                           obj_id=pkg_id,
                           following=following)
        return ''


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


    def kata_metadata_fields(self, list_):
        output = []
        for extra in sorted(list_, key=lambda x:x['key']):
            if extra.get('state') == 'deleted':
                continue
            k, v = extra['key'], extra['value']
            if k in self.kata_field:
                output.append((k, v))
        return output


    def kata_sorted_extras(self, list_):
        '''
        Used for outputting package extras, skips package_hide_extras
        '''
        output = []
        for extra in sorted(list_, key=lambda x:x['key']):
            if extra.get('state') == 'deleted':
                continue
            
            k, v = extra['key'], extra['value']
            if k in g.package_hide_extras and\
                k in self.kata_field and\
                k.starswith('author_') and\
                k.startswith('organization_'):
                continue
            
            found = False
            for _k in g.package_hide_extras:
                if extra['key'].startswith(_k):
                    found = True
            if found:
                continue
            
            if isinstance(v, (list, tuple)):
                v = ", ".join(map(unicode, v))
            output.append((k, v))
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
        config['package_hide_extras'] = ' '.join(self.kata_field)
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
        return ['dataset']


    def is_fallback(self):
        """
        Overrides IDatasetForm.is_fallback()
        From CKAN documentation:  "Returns true iff this provides the fallback behaviour,
        when no other plugin instance matches a package's type."
        """
        return True


    def configure(self, config):
        self.date_format = config.get('kata.date_format', '%Y-%m-%d')


    def setup_template_variables(self, context, data_dict):
        c.roles = self.roles
        c.PID = utils.generate_pid()
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


    def pid_to_extras(self, key, data, errors, context):
        """
        Check's that pid exists in data, if not then pid element is created with kata pid.
        """
#        extra_number = 0
#        for k in data.keys():
#            if k[0] == 'extras' and k[-1] == 'key':
#                extra_number = max(extra_number, k[1] + 1)
#
#        for k in data.keys():
#            if k[-1] == 'pid':
#                data[('extras', extra_number, 'key')] = 'pid'
#                data[('extras', extra_number, 'value')] = data[k]

        extras = data.get(('extras',), [])
        if not extras:
            data[('extras',)] = extras

        for k in data.keys():
            if k[-1] == 'versionPID':
                extras.append({'key': 'versionPID', 'value': data[k]})

                if k in data:
                    del data[k]


    def update_pid(self, key, data, errors, context):
        if type(data[key]) == unicode:
            if len(data[key]) == 0:
                data[key] = utils.generate_pid()


    def update_name(self, key, data, errors, context):
        if len(data[key]) == 0:
            data[key] = utils.generate_pid()

    def default_tags_schema(self):
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
    
    def create_package_schema(self):
        """
        Return the schema for validating new dataset dicts.
        """

        schema = default_create_package_schema()

        for key in self.kata_fields_required:
            schema[key] = [not_empty, self.convert_to_extras_kata, unicode]
        for key in self.kata_fields_recommended:
            schema[key] = [ignore_missing, self.convert_to_extras_kata, unicode]

        # When adding a resource the data comes straight from DB and 'title' is not in the same format
        # than the title data coming from the dataset form.

        if c.action in ['new_resource']:
            schema['title'] = [not_missing]
        else:
            schema['title'] = {'value': [not_missing, ltitle_to_extras],
                               'lang': [not_missing]}

        schema['temporal_coverage_begin'].append(validate_kata_date)
        schema['temporal_coverage_end'].append(validate_kata_date)
        schema['language'] = [validate_language, self.convert_to_extras_kata, unicode]
        schema['phone'].append(validate_phonenum)
        schema['maintainer_email'].append(validate_email)
        schema['tag_string'] = [not_missing, not_empty, kata_tag_string_convert]
        # otherwise the tags would be validated with default tag validator during update
        schema['tags'] = self.default_tags_schema()
        schema.update({
           'version': [not_empty, unicode, validate_kata_date, check_last_and_update_pid],
           'versionPID': [self.update_pid, unicode, self.pid_to_extras],
           'author': {'value': [not_empty, unicode, org_auth_to_extras]},
           'organization': {'value': [not_empty, unicode, org_auth_to_extras]},
           'access': [not_missing, self.convert_to_extras_kata, validate_access],
           'langdis': [default(u'False'), unicode],
           '__extras': [check_author_org],
           'projdis': [default(u'False'), unicode, check_project],
           '__junk': [check_junk],
           'name': [ignore_missing, unicode, self.update_name],
           'accessRights': [check_accessrights, self.convert_to_extras_kata, unicode],
           'accessrequestURL': [check_accessrequesturl, self.convert_to_extras_kata, unicode],
           'project_name': [check_project_dis, unicode, self.convert_to_extras_kata],
           'funder': [check_project_dis, unicode, self.convert_to_extras_kata],
           'project_funding': [check_project_dis, unicode, self.convert_to_extras_kata],
           'project_homepage': [check_project_dis, unicode, self.convert_to_extras_kata],
           'resources': default_resource_schema(),
           'discipline': [validate_discipline, unicode, self.convert_to_extras_kata],
           'geographic_coverage': [validate_spatial, self.convert_to_extras_kata, unicode],
        })

        schema['evtype'] = {'value': [ignore_missing, unicode, event_to_extras]}
        schema['evwho'] = {'value': [ignore_missing, unicode, event_to_extras]}
        schema['evwhen'] = {'value': [ignore_missing, unicode, event_to_extras]}
        schema['evdescr'] = {'value': [ignore_missing, unicode, event_to_extras]}
        schema['groups'].update({
                'name': [ignore_missing, unicode, add_to_group]
                })

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


    def show_package_schema(self):
        """
        The data fields that are returned from CKAN for each dataset can be changed with this method.
        This method is called when viewing or editing a dataset.
        """

        #schema = self._db_to_form_package_schema()
        schema = default_show_package_schema()

        for key in self.kata_field:
            schema[key] = [self.convert_from_extras_kata, ignore_missing, unicode]

        schema['versionPID'] = [pid_from_extras, ignore_missing, unicode]

        schema['author'] = [org_auth_from_extras, ignore_missing, unicode]
        schema['organization'] = [org_auth_from_extras, ignore_missing, unicode]
        schema['langdis'] = [default(False), unicode]
        schema['projdis'] = [default(False), unicode]
        schema['title'] = [ltitle_from_extras, ignore_missing]
        schema['evtype'] = [event_from_extras, ignore_missing, unicode]
        schema['evwho'] = [event_from_extras, ignore_missing, unicode]
        schema['evwhen'] = [event_from_extras, ignore_missing, unicode]
        schema['evdescr'] = [event_from_extras, ignore_missing, unicode]

        return schema


    def convert_from_extras_kata(self, key, data, errors, context):

        #import pprint
        #pprint.pprint(data)
        #print("Key: " + repr(key))

        for k in data.keys():
            if k[0] == 'extras' and k[-1] == 'key' and data[k] in self.kata_field:
                key = ''.join(data[k])
                data[(key,)] = data[(k[0], k[1], 'value')]
                for _remove in data.keys():
                    if _remove[0] == 'extras' and _remove[1] == k[1]:
                        del data[_remove]

        #pprint.pprint(data)


    def convert_to_extras_kata(self, key, data, errors, context):
        if data.get(('extras',)) is missing:
            return
        extras = data.get(('extras',), [])
        if not extras:
            data[('extras',)] = extras
        for k in data.keys():
            if k[-1] in self.kata_field:
                if not {'key': k[-1], 'value': data[k]} in extras:
                    extras.append({'key': k[-1], 'value': data[k]})


    def update_facet_titles(self, facet_titles):
        """
        Update the dictionary mapping facet names to facet titles.

        Example: {'facet_name': 'The title of the facet'}

        Called after the search operation was performed and
        before the search page will be displayed.
        The titles show up on the search page.
        """

        facet_titles.update(get_field_titles(t._))
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
        c.current_search_rows.append({'field':p_no_index, 'text':value})

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

        data_dict['facet.field'] = FACETS
        if data_dict.has_key('sort') and data_dict['sort'] is None:
            data_dict['sort'] = DEFAULT_SORT_BY
            c.sort_by_selected = DEFAULT_SORT_BY  # This is to get the correct one pre-selected on the HTML form.

        c.search_fields = SEARCH_FIELDS
        c.translated_field_titles = get_field_titles(t._)

        # Start advanced search parameter parsing
        if data_dict.has_key('extras') and len(data_dict['extras']) > 0:
            log.debug("before_search(): data_dict['extras']: %r" %
                      data_dict['extras'].items())

            extra_terms, extra_ops, extra_dates = self.extract_search_params(data_dict)
            log.debug("before_search(): extra_terms: %r; extra_ops: %r; "
                      + "extra_dates: %r", extra_terms, extra_ops, extra_dates)

            if len(extra_terms) > 0:
                self.parse_search_terms(data_dict, extra_terms, extra_ops)
            if len(extra_dates) > 0:
                self.parse_search_dates(data_dict, extra_dates)

            log.debug("before_search(): c.current_search_rows: %s; \
                c.current_search_limiters: %s" % (c.current_search_rows,
                c.current_search_limiters))
        # End advanced search parameter parsing

        log.debug("before_search(): data_dict: %r" % data_dict)
        # Uncomment below to show query with results and in the search field
        #c.q = data_dict['q']
        return data_dict


    def after_search(self, search_results, data_dict):
        '''
        Things to do after querying Solr.

        :param search_results: ?
        :param data_dict: data_dict to modify
        '''

        #log.debug("search_results: %r" % search_results)
        #log.debug("data_dict: %r" % data_dict)
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
            