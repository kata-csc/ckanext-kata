'''Main plugin file
'''

import logging
import os

from ckan.plugins import implements, SingletonPlugin
from ckan.plugins import IPackageController, IDatasetForm, IConfigurer
from ckan.plugins import IRoutes
from ckan.plugins import IConfigurer
from ckan.plugins import IMapper
from ckan.lib.base import g, c
from ckan.lib.plugins import DefaultDatasetForm
from ckan.logic.schema import db_to_form_package_schema,\
                                form_to_db_package_schema
import ckan.logic.converters
from ckan.lib.navl.validators import ignore_missing, keep_extras, ignore, not_empty, not_missing

log = logging.getLogger('ckanext.kata')

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
    implements(IPackageController, inherit=True)
    implements(IRoutes, inherit=True)

    def create(self, dataset):
        pass
    
    def edit(self, id, data=None, errors=None, error_summary=None):
        pass
        
    def read(self, dataset):
        g.dataset = dataset
        
        return dataset
        
    def delete(self, dataset):
        pass

    def before_map(self, map):
        map.connect('/dataset/{id}.{format}',
                    controller="ckanext.kata.controllers:MetadataController",
                    action='tordf')
        return map


class KataPlugin(SingletonPlugin, DefaultDatasetForm):
    implements(IDatasetForm, inherit=True)
    implements(IConfigurer, inherit=True)
    
    def update_config(self, config):
        """
        This IConfigurer implementation causes CKAN to look in the
        ```templates``` directory when looking for the package_form()
        """
        here = os.path.dirname(__file__)
        rootdir = os.path.dirname(os.path.dirname(here))
        template_dir = os.path.join(rootdir, 'ckanext', 'kata', 'theme', 'templates')
        config['extra_template_paths'] = ','.join([template_dir,
                config.get('extra_template_paths', '')])
        
        roles = config['kata.contact_roles']
        roles = [r.lower() for r in roles.split(', ')]
        self.roles = roles

    def package_types(self):
        return ['dataset']
    
    def is_fallback(self):
        return True
    
    def setup_template_variables(self, context, data_dict):
        g.roles = self.roles

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
        schema['role'] = {'key': [ignore_missing, unicode, role_to_extras], 'value': [ignore_missing]}
        
        return schema
    
    def db_to_form_schema(data, package_type=None):
        schema = db_to_form_package_schema()
        schema['role'] = {'key': [ignore_missing, unicode], 'value': [ignore_missing]}
        
        return schema
