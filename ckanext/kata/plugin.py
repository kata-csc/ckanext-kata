'''Main plugin file
'''

import logging
import os
import datetime
from lxml import etree
import urllib2

from ckan.plugins import implements, SingletonPlugin
from ckan.plugins import IPackageController, IDatasetForm, IConfigurer, ITemplateHelpers
from ckan.plugins import IRoutes
from ckan.plugins import IConfigurable
from ckan.plugins import IMapper
from ckan.lib.base import g, c
from ckan.model import Package
from ckan.lib.plugins import DefaultDatasetForm
from ckan.logic.schema import db_to_form_package_schema,\
                                form_to_db_package_schema
import ckan.logic.converters
from ckan.logic.converters import convert_to_extras, convert_from_extras
from ckan.lib.navl.validators import ignore_missing, keep_extras, ignore, not_empty, not_missing, both_not_empty
from ckan.logic.converters import convert_to_tags, convert_from_tags, free_tags_only

log = logging.getLogger('ckanext.kata')
mets_schema = etree.XMLSchema(etree.parse(urllib2.urlopen('http://www.loc.gov/standards/rights/METSRights.xsd')))

import utils

class KataMetadata(SingletonPlugin):
    implements(IRoutes, inherit=True)
    implements(IMapper, inherit=True)

    def before_map(self, map):
        GET = dict(method=['GET'])
        controller = "ckanext.kata.controllers:MetadataController"
        api_controller = "ckanext.kata.controllers:KATAApiController"
        map.connect('/dataset/{id}.{format}',
                    controller=controller,
                    action='tordf')
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
        return map

class KataPlugin(SingletonPlugin, DefaultDatasetForm):
    implements(IDatasetForm, inherit=True)
    implements(IConfigurer, inherit=True)
    implements(IConfigurable, inherit=True)
    implements(IPackageController, inherit=True)
    implements(ITemplateHelpers, inherit=True)

    kata_field = ['lastmod', 'language',
                  'contact_name', 'contact_phone', 'contact_email', 'contact_form',
                  'project_name', 'project_funder', 'project_funding', 'project_homepage',
                  'owner_name', 'owner_phone', 'owner_homepage',
                  'access', 'accessRights',]

    def get_helpers(self):
        ''' Register helpers '''
        return {'is_custom_form':self.is_custom_form,
                'kata_sorted_extras':self.kata_sorted_extras,
                'kata_metadata_fields':self.kata_metadata_fields}
    
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
        
        roles = config.get('kata.contact_roles', 'Please, Configure')
        roles = [r for r in roles.split(', ')]
        self.roles = roles
        self.hide_extras_form = config.get('kata.hide_extras_form', '').split()
        
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
            if k[-1] == 'pid':
                extras.append({'key': 'pid', 'value': data[k]})

                if k in data:
                    del data[k]

    def add_pid_if_missing(self, key, data, errors, context):
        if not key in data or len(data.get(key, '')) < 1:
            data[key] = utils.generate_pid()

    def pid_from_extras(self, key, data, errors, context):
        for k in data.keys():
            if k[0] == 'extras' and k[-1] == 'key' and data[k] == 'pid':
                data[('pid',)] = data[(k[0], k[1], 'value')]

                for _remove in data.keys():
                    if _remove[0] == 'extras' and _remove[1] == k[1]:
                        del data[_remove]

        if not ('pid',) in data:
            data[('pid',)] = utils.generate_pid()

    def roles_to_extras(self, key, data, errors, context):
        extras = data.get(('extras',), [])
        if not extras:
            data[('extras',)] = extras

        extra_number = 0
        for k in data.keys():
            if k[0] == 'extras' and k[-1] == 'key':
                extra_number = max(extra_number, k[1] + 1)

        role_number = 0
        for k in data.keys():
            try:
                if k[0] == 'role' and k[-1] == 'key' and (k[0], k[1], 'value') in data \
                    and len(data[(k[0], k[1], 'value')]) > 0:

                    _keyval = data[('role', k[1], 'key')]
                    _valval = data[('role', k[1], 'value')]

                    extras.append({'key': 'role_%d_%s' % (role_number, _keyval),
                                   'value': _valval})

                    for _del in data.keys():
                        if _del[0] == 'role' and _del[1] == k[1] and k in data:
                            del data[k]

                    role_number += 1
            except:
                pass

    def roles_from_extras(self, key, data, errors, context):
        if not ('roles',) in data:
            data[('roles',)] = []
        roles = data[('roles',)]

        for k in data.keys():
            if k[0] == 'extras' and k[-1] == 'key':
                if 'role_' in data[k]:
                    role = {}
                    role['key'] = data[k]
                    role['value'] = data[(k[0], k[1], 'value')]
                    roles.append(role)

                    if context.get('for_edit', False):
                        del data[k]
                        del data[(k[0], k[1], 'value')]

    def custom_to_extras(self, key, data, errors, context):
        extras = data.get(('extras',), [])
        if not extras:
            data[('extras',)] = extras
        for k in data.keys():
            try:
                if k[0] == 'extras' and k[-1] == 'key' and (k[0], k[1], 'value') in data:
                    if type(data[(k[0], k[1], 'key')]) == unicode \
                        and len(data[(k[0], k[1], 'key')]) > 0 \
                        and type(data[(k[0], k[1], 'value')]) == unicode \
                        and len(data[(k[0], k[1], 'value')]) > 0:
                        extras.append({'key':data[(k[0], k[1], 'key')],
                                   'value':data[(k[0], k[1], 'value')]})
                    for _del in data.keys():
                        if len(_del) == 3 and _del[0] == 'extras' and _del[1] == k[1]:
                            del data[_del]
            except:
                pass

    def validate_lastmod(self, key, data, errors, context):
        format = '%Y-%m-%dT%H:%M:%S'
        errs = []
        try:
            datetime.datetime.strptime(data[key], format)
        except ValueError:
            errs.append(1)
        if len(errs) == 2:
            errors[key].append('Invalid date format, must be like 2012-12-31T13:12:11')

    def convert_from_extras_kata(self, key, data, errors, context):
        for k in data.keys():
            if k[0] == 'extras' and k[-1] == 'key' and data[k] in self.kata_field:
                key = ''.join(data[k])
                data[(key,)] = data[(k[0], k[1], 'value')]
                for _remove in data.keys():
                    if _remove[0] == 'extras' and _remove[1] == k[1]:
                        del data[_remove]

    def convert_to_extras_kata(self, key, data, errors, context):
        extras = data.get(('extras',), [])
        if not extras:
            data[('extras',)] = extras
        for k in data.keys():
            if k[-1] in self.kata_field:
                if not {'key': k[-1], 'value': data[k]} in extras:
                    extras.append({'key': k[-1], 'value': data[k]})

    def org_auth_to_extras(self, key, data, errors, context):
        extras = data.get(('extras',), [])
        if not extras:
            data[('extras',)] = extras
        authnum = 1
        orgnum = 1
        for k in data.keys():
            try:
                if k[0] == 'author' \
                and (k[0], k[1], 'value') in data \
                and len(data[(k[0], k[1], 'value')]) > 0:
                    extras.append({'key': "%s_%d" % (k[0], authnum),
                                   'value': data[(k[0], k[1], 'value')]
                                })
                    authnum += 1
                if k[0] == 'organization' \
                and (k[0], k[1], 'value') in data \
                and len(data[(k[0], k[1], 'value')]) > 0:
                    extras.append({'key': "%s_%d" % (k[0], orgnum),
                                   'value': data[(k[0], k[1], 'value')]
                                })
                    orgnum += 1
            except:
                pass

    def org_auth_from_extras(self, key, data, errors, context):
        if not ('orgauths',) in data:
            data[('orgauths',)] = []
        auths = []
        orgs = []
        orgauths = data[('orgauths',)]
        for k in data.keys():
            if k[0] == 'extras' and k[-1] == 'key':
                if 'author_' in data[k]:
                    val = data[(k[0], k[1], 'value')]
                    auth = {}
                    auth['key'] = data[k]
                    auth['value'] = val
                    if not {'key': data[k], 'value': val} in auths:
                        auths.append(auth)

                if 'organization_' in data[k]:
                    org = {}
                    val = data[(k[0], k[1], 'value')]
                    org['key'] = data[k]
                    org['value'] = val
                    if not {'key': data[k], 'value': val} in orgs:
                        orgs.append(org)
        orgs = sorted(orgs, key=lambda ke: int(ke['key'][-1]))
        auths = sorted(auths, key=lambda ke: int(ke['key'][-1]))
        for org, auth in zip(orgs, auths):
            if not (auth, org) in orgauths:
                orgauths.append((auth, org))

    def validate_access(self, key, data, errors, context):
        if data[key] == 'form':
            if not data[('accessRights',)]:
                errors[key].append('You must fill up the form URL')

    def check_language(self, key, data, errors, context):
        if data[('language',)]:
            errors[key].append('Language received even if disabled.')

    def check_project(self, key, data, errors, context):
        if data[('project_name',)] or data[('project_funder',)] or data[('project_funding',)] or data[('project_homepage',)]:
            errors[key].append('Project data received even if no project is associated.')

    def form_to_db_schema_options(self, package_type=None, options=None):
        schema = form_to_db_package_schema()
        for key in self.kata_field:
            schema[key] = [not_missing, self.convert_to_extras_kata, unicode]
        schema.update({
           'lastmod':[not_missing, self.convert_to_extras_kata, unicode, self.validate_lastmod],
           'extras':{
                'id': [ignore],
                'key': [self.custom_to_extras],
                'value': [ignore_missing],
                'state': [ignore],
                'deleted': [ignore_missing],
                'revision_timestamp': [ignore],
                '__extras':[ignore],
            },
           'role':{'key': [ignore_missing, unicode, self.roles_to_extras], 'value': [ignore_missing]},
           'pid':[self.add_pid_if_missing, unicode, self.pid_to_extras],
           'author': {'value': [ignore_missing, unicode, self.org_auth_to_extras]},
           'organization': {'value': [ignore_missing, unicode, self.org_auth_to_extras]},
           'access': [not_missing, self.convert_to_extras_kata, self.validate_access],
           'accessRights': [ignore_missing, self.convert_to_extras_kata, unicode],
           'langdis': [ignore_missing, unicode, self.check_language],
           'projdis': [ignore_missing, unicode, self.check_project],
           '__junk':[ignore],
           '__extras':[ignore],
        })
        return schema

    def db_to_form_schema_options(self, options = None):
        schema = db_to_form_package_schema()
        context = options['context']
        for key in self.kata_field:
            schema[key] = [self.convert_from_extras_kata, ignore_missing, unicode]
        schema['role'] = [self.roles_from_extras, ignore_missing, unicode]
        schema['pid'] = [self.pid_from_extras, ignore_missing, unicode]
        schema['author'] = [self.org_auth_from_extras, ignore_missing, unicode]
        schema['organization'] = [self.org_auth_from_extras, ignore_missing, unicode]
        try:
            dataset = context['package']
            c.revision = dataset.latest_related_revision
            c.date_format = self.date_format
            c.PID = utils.generate_pid()
            c.roles = self.roles
            c.lastmod = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        except TypeError:
                return schema
        
        return schema

    def before_view(self, pkg_dict):
        return pkg_dict
