'''Main plugin file
'''

import logging
import os

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
from ckan.lib.navl.validators import ignore_missing, keep_extras, ignore, not_empty, not_missing
from ckan.logic.converters import convert_to_tags, convert_from_tags, free_tags_only

log = logging.getLogger('ckanext.kata')

import utils

class KataMetadata(SingletonPlugin):
    implements(IRoutes, inherit=True)
    implements(IMapper, inherit=True)

    def before_map(self, map):
        map.connect('/dataset/{id}.{format}',
                    controller="ckanext.kata.controllers:MetadataController",
                    action='tordf')
        return map

class KataPlugin(SingletonPlugin, DefaultDatasetForm):
    implements(IDatasetForm, inherit=True)
    implements(IConfigurer, inherit=True)
    implements(IConfigurable, inherit=True)
    implements(IPackageController, inherit=True)
    implements(ITemplateHelpers, inherit=True)
    
    def get_helpers(self):
        ''' Register helpers '''
        return {'is_custom_form':self.is_custom_form,
                'kata_sorted_extras':self.kata_sorted_extras}
    
    def is_custom_form(self, _dict):
        ''' Template helper, used to identify ckan custom form '''
        for key in self.hide_extras_form:
            if _dict.get('key', None) and _dict['key'].find(key) > -1:
                return False
        return True
    
    def kata_sorted_extras(self, list_):
        ''' Used for outputting package extras, skips package_hide_extras '''
        output = []
        for extra in sorted(list_, key=lambda x:x['key']):
            if extra.get('state') == 'deleted':
                continue
            
            k, v = extra['key'], extra['value']
            if k in g.package_hide_extras:
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
        extra_number = 0
        for k in data.keys():
            if k[0] == 'extras':
                extra_number = max(extra_number, k[1] + 1)

        for k in data.keys():
            if k[-1] == 'pid':
                data[('extras', extra_number, 'key')] = 'pid'
                data[('extras', extra_number, 'value')] = data[k]


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
        extra_number = 0
        for k in data.keys():
            if k[0] == 'extras':
                extra_number = max(extra_number, k[1] + 1)
        
        role_number = 0
        for k in data.keys():
            if k[0] == 'role' and k[-1] == 'key' and (k[0], k[1], 'value') in data \
                and len(data[(k[0], k[1], 'value')]) > 0:
                
                _keyval = 'role_%d_%s' % (k[1], data[('role', k[1], 'key')])
                _valval = data[('role', k[1], 'value')]
                
                data[('extras', extra_number, 'key')] = 'role_%d_%s' % (role_number, _keyval)
                data[('extras', extra_number, 'value')] = _valval
                
                extra_number += 1
                role_number += 1
                    
                        
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
                        
                    
    def form_to_db_schema_options(self, package_type=None, options=None):
        schema = form_to_db_package_schema()
        schema['author'] = [not_missing, not_empty, unicode]
        schema['author_email'] = [not_missing, not_empty, unicode]
        schema['maintainer'] = [not_missing, not_empty, unicode]
        schema['maintainer_email'] = [not_missing, not_empty, unicode]
        schema['extras'] = {'key': [ignore_missing, unicode, convert_to_extras], 'value': [ignore_missing]}
        schema['role'] = {'key': [ignore_missing, unicode, self.roles_to_extras], 'value': [ignore_missing]}
        schema['pid'] = [self.add_pid_if_missing, unicode, self.pid_to_extras]
        schema['__junk'] = [ignore]
        schema['__extras'] = [ignore]
        
        return schema
    
    def db_to_form_schema_options(self, options = None):
        schema = db_to_form_package_schema()
        context = options['context']
        schema['role'] = [self.roles_from_extras, ignore_missing, unicode]
        schema['pid'] = [self.pid_from_extras, ignore_missing, unicode]
        
        try:
            dataset = context['package']
            c.revision = dataset.latest_related_revision
            c.date_format = self.date_format
            c.PID = utils.generate_pid()
            c.roles = self.roles
        except TypeError:
                return schema
        
        return schema

    def before_view(self, pkg_dict):
        return pkg_dict
