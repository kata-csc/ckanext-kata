'''Main plugin file
'''

import logging
import os
import datetime
from lxml import etree
import urllib2
import iso8601

from ckan.plugins import implements, SingletonPlugin, toolkit
from ckan.plugins import IPackageController, IDatasetForm, IConfigurer, ITemplateHelpers, IPluginObserver
from ckan.plugins import IRoutes
from ckan.plugins import IConfigurable
from ckan.plugins import IMapper
from ckan.plugins import IActions
from ckan.plugins.core import unload
from ckan.lib.base import g, c
from ckan.model import Package, Group, Session, repo
import ckan.model as model
from ckan.lib.plugins import DefaultDatasetForm
from ckan.logic.schema import db_to_form_package_schema,\
                                form_to_db_package_schema
from ckan.lib.dictization.model_save import group_dict_save


import ckan.logic.converters
from ckan.logic.converters import convert_to_extras, convert_from_extras
from ckan.lib.navl.validators import missing, ignore_missing, keep_extras, ignore, not_empty, not_missing, both_not_empty
from ckan.logic.converters import convert_to_tags, convert_from_tags, free_tags_only

from pylons.decorators.cache import beaker_cache

from validators import check_language, check_project, validate_access,\
                        validate_lastmod, check_junk, check_last_and_update_pid,\
                        validate_language, validate_email, validate_phonenum,\
                        check_project_dis, check_accessrequesturl, check_accessrights,\
                        not_empty_kata, check_author_org

from converters import copy_from_titles, custom_to_extras, event_from_extras,\
                        event_to_extras, ltitle_from_extras, ltitle_to_extras,\
                        org_auth_from_extras, org_auth_to_extras, pid_from_extras,\
                        export_as_related, add_to_group
import actions
import tieteet

log = logging.getLogger('ckanext.kata')

import utils

class KataMetadata(SingletonPlugin):
    implements(IRoutes, inherit=True)
    implements(IMapper, inherit=True)

    def before_map(self, map):
        GET = dict(method=['GET'])
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
                    conditions=GET,
                    action="owner_autocomplete")
        map.connect('/api/2/util/author_autocomplete',
                    controller=api_controller,
                    conditions=GET,
                    action="author_autocomplete")
        map.connect('/api/2/util/organization_autocomplete',
                    controller=api_controller,
                    conditions=GET,
                    action="organization_autocomplete")
        map.connect('/api/2/util/contact_autocomplete',
                    controller=api_controller,
                    conditions=GET,
                    action="contact_autocomplete")
        map.connect('/api/2/util/discipline_autocomplete',
                    controller=api_controller,
                    conditions=GET,
                    action="discipline_autocomplete")
        return map

    def before_insert(self, mapper, connection, instance):
        if isinstance(instance, Package):
            instance.id = utils.generate_pid()

class KataPlugin(SingletonPlugin, DefaultDatasetForm):
    implements(IDatasetForm, inherit=True)
    implements(IConfigurer, inherit=True)
    implements(IConfigurable, inherit=True)
    implements(IPackageController, inherit=True)
    implements(ITemplateHelpers, inherit=True)
    implements(IActions, inherit=True)

    kata_fields_required = ['version', 'language',
                  'publisher', 'phone', 'contactURL',
                  'project_name', 'funder', 'project_funding', 'project_homepage',
                  'access', 'accessRights', 'accessrequestURL', 'licenseURL',
                  'organization', 'author', 'owner']
    kata_fields_recommended = ['geographic_coverage', 'temporal_coverage_begin',
                  'temporal_coverage_end',  'collections',
                  'discipline', 'fformat', 'checksum',
                  'algorithm', 'evwho', 'evdescr', 'evtype', 'evwhen', 'projdis',
                  ]

    kata_field = kata_fields_recommended + kata_fields_required

    def get_actions(self):
        return {'package_show': actions.package_show,
                'group_list': actions.group_list}

    def get_helpers(self):
        ''' Register helpers '''
        return {'is_custom_form': self.is_custom_form,
                'kata_sorted_extras': self.kata_sorted_extras,
                'kata_metadata_fields': self.kata_metadata_fields,
                'reference_update': self.reference_update}

    def reference_update(self, ref):
        #@beaker_cache(type="dbm", expire=2678400)
        def cached_url(url):
            return url
        return cached_url(ref)

    def is_custom_form(self, _dict):
        ''' Template helper, used to identify ckan custom form '''
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
        ''' Used for outputting package extras, skips package_hide_extras '''
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
            
            found=False
            for _k in g.package_hide_extras:
                if extra['key'].startswith(_k):
                    found=True
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

        log.debug("disable search")
        try:
            unload('synchronous_search')
        except:
            pass
        
    def package_types(self):
        return ['dataset']
    
    def is_fallback(self):
        return True
    
    def configure(self, config):
        self.date_format = config.get('kata.date_format', '%Y-%m-%d')
    
    def setup_template_variables(self, context, data_dict):
        c.roles = self.roles
        c.PID = utils.generate_pid()
        c.lastmod = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

    def new_template(self):
        """
        Returns a string representing the location of the template to be
        rendered for the new page
        """
        return 'package/new.html'

    def comments_template(self):
        """
        Returns a string representing the location of the template to be
        rendered for the comments page
        """
        return 'package/comments.html'

    def search_template(self):
        """
        Returns a string representing the location of the template to be
        rendered for the search page (if present)
        """
        return 'package/search.html'

    def read_template(self):
        """
        Returns a string representing the location of the template to be
        rendered for the read page
        """
        return 'package/read.html'

    def history_template(self):
        """
        Returns a string representing the location of the template to be
        rendered for the history page
        """
        return 'package/history.html'

    def package_form(self):
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

    def form_to_db_schema_options(self, package_type=None, options=None):
        schema = form_to_db_package_schema()
        for key in self.kata_fields_required:
            schema[key] = [not_empty, self.convert_to_extras_kata, unicode]
        for key in self.kata_fields_recommended:
            schema[key] = [ignore_missing, self.convert_to_extras_kata, unicode]
        schema['temporal_coverage_begin'].append(validate_lastmod)
        schema['temporal_coverage_end'].append(validate_lastmod)
        schema['language'] = [validate_language, self.convert_to_extras_kata, unicode]
        schema['phone'].append(validate_phonenum)
        schema['maintainer_email'].append(validate_email)
        schema['tag_string'].append(not_empty)
        schema.update({
           'version': [not_empty, unicode, validate_lastmod, check_last_and_update_pid],
           'versionPID': [self.update_pid, unicode, self.pid_to_extras],
           'author': {'value': [not_empty, unicode, org_auth_to_extras]},
           'organization': {'value': [not_empty, unicode, org_auth_to_extras]},
           'access': [not_missing, self.convert_to_extras_kata, validate_access],
           'accessRights': [ignore_missing, self.convert_to_extras_kata, unicode],
           'langdis': [ignore_missing, unicode, check_language],
           '__extras': [check_author_org],
           'projdis': [ignore_missing, unicode, check_project],
           '__junk': [check_junk],
           'name': [unicode, ignore_missing, self.update_name],
           'accessRights': [check_accessrights, self.convert_to_extras_kata, unicode],
           'accessrequestURL': [check_accessrequesturl, self.convert_to_extras_kata, unicode],
           'project_name': [check_project_dis, unicode, self.convert_to_extras_kata],
           'funder': [check_project_dis, unicode, self.convert_to_extras_kata],
           'project_funding': [check_project_dis, unicode, self.convert_to_extras_kata],
           'project_homepage': [check_project_dis, unicode, self.convert_to_extras_kata],
           'resources': [ignore_missing],
           'discipline': [add_to_group],
        })
        schema['title'] = {'value': [not_missing, ltitle_to_extras],
                           'lang': [not_missing]}

        schema['evtype'] = {'value': [ignore_missing, unicode, event_to_extras]}
        schema['evwho'] = {'value': [ignore_missing, unicode, event_to_extras]}
        schema['evwhen'] = {'value': [ignore_missing, unicode, event_to_extras]}
        schema['evdescr'] = {'value': [ignore_missing, unicode, event_to_extras]}
        schema['groups'] = {
                'id': [ignore_missing, unicode],
                'name': [ignore_missing, unicode],
                'title': [ignore_missing, unicode],
                '__extras': [ignore],
            }
        return schema

    def db_to_form_schema_options(self, options = None):
        schema = db_to_form_package_schema()
        context = options['context']
        for key in self.kata_field:
            schema[key] = [self.convert_from_extras_kata, ignore_missing, unicode]
        schema['versionPID'] = [pid_from_extras, ignore_missing, unicode]

        schema['author'] = [org_auth_from_extras, ignore_missing, unicode]
        schema['organization'] = [org_auth_from_extras, ignore_missing, unicode]

        schema['title'] = [ltitle_from_extras, ignore_missing]
        schema['evtype'] = [event_from_extras, ignore_missing, unicode]
        schema['evwho'] = [event_from_extras, ignore_missing, unicode]
        schema['evwhen'] = [event_from_extras, ignore_missing, unicode]
        schema['evdescr'] = [event_from_extras, ignore_missing, unicode]

        return schema

    def convert_from_extras_kata(self, key, data, errors, context):
        for k in data.keys():
            if k[0] == 'extras' and k[-1] == 'key' and data[k] in self.kata_field:
                key = ''.join(data[k])
                data[(key,)] = data[(k[0], k[1], 'value')]
                for _remove in data.keys():
                    if _remove[0] == 'extras' and _remove[1] == k[1]:
                        del data[_remove]

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
