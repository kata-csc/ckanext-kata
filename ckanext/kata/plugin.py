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

log = logging.getLogger('ckanext.kata')

def dummy_pid():
    import datetime
    return "urn:nbn:fi:csc-kata%s" % datetime.datetime.now().strftime("%Y%m%d%H%M%S")

def role_to_extras(key, data, errors, context):
    if 'role' in key and key in data:
        if not ('extras',) in data:
            data[('extras',)] = []
        
        extras = data[('extras',)]
        
        role_key = data.get(key, None)
        role_value = data.get((key[0], key[1], 'value'), None)
        
        for _key in data:
            if 'role' in _key[0] and ('role', _key[1], 'value') in data:
                # Skip role if deleted is found in data
                if ('role', _key[1], '__extras') in data and data[('role', _key[1], '__extras')]['deleted'] == 'on':
                    continue
                
                # Value for key column
                _keyval = 'role_%d_%s' % (_key[1], data[('role', _key[1], 'key')])
                # Value for value column
                _valval = data[('role', _key[1], 'value')]
                
                # Add if contains data
                if len(_valval) > 0:
                    extras.append({'key':_keyval, 'value':_valval})

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
        return {'is_custom_form':self.is_custom_form,
                'kata_sorted_extras':self.kata_sorted_extras}
    
    def is_custom_form(self, _dict):
        ''' Template helper, used to identify ckan custom form '''
        log.debug(g.package_hide_extras)
        log.debug(_dict)
        
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
        c.PID = dummy_pid()

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
        
    def form_to_db_schema_options(self, package_type=None, options=None):
        schema = form_to_db_package_schema()
        
        schema['author'] = [not_missing, not_empty, unicode]
        schema['author_email'] = [not_missing, not_empty, unicode]
        schema['maintainer'] = [not_missing, not_empty, unicode]
        schema['maintainer_email'] = [not_missing, not_empty, unicode]
        schema['role'] = {'key': [ignore_missing, unicode, role_to_extras], 'value': [ignore_missing]}
        schema['pid'] = [not_missing, not_empty, unicode]
        
        schema.update({'pid': [not_empty, unicode, convert_to_extras] })
        
        """
        'author': [ignore_missing, unicode],
        'author_email': [ignore_missing, unicode],
        'maintainer': [ignore_missing, unicode],
        'maintainer_email': [ignore_missing, unicode],
        """
        
        return schema
    
    def db_to_form_schema_options(self, options = None):
        schema = db_to_form_package_schema()
        context = options['context']
        schema['role'] = {'key': [ignore_missing, unicode], 'value': [ignore_missing]}
        schema.update({'pid': [convert_from_extras, ignore_missing] })
        
        dataset = context['package']
        c.PID = dummy_pid()
        c.revision = dataset.latest_related_revision
        c.date_format = self.date_format
        
        return schema

    def before_view(self, pkg_dict):
        dataset = Package.get(pkg_dict['id'])
        c.revision = dataset.latest_related_revision
        c.date_format = self.date_format
        return pkg_dict
