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
from ckan.lib.navl.validators import ignore_missing, keep_extras

log = logging.getLogger('ckanext.kata')

def get_roles():
    # TODO: read from configuration
    return ['author', 'maintainer', 'publisher', 'sponsor']

class KataMetadata(SingletonPlugin):
    implements(IPackageController, inherit=True)
    implements(IRoutes, inherit=True)

    def create(self, dataset):
        pass
    
#    def edit(self, id, data=None, errors=None, error_summary=None):
#        # Start extras from 200 for example extras__200__key|value
#        request_params = request.params.copy()
#        
#        extras_num = 200
#        for key in request_params:
#            log.debug(key)
#            log.debug(request.params[key])
#            
#            if re.match('roles__\d+__key', key):
#                _key = 'extras__%d__key'
#                _val = 'extras__%d__value'
#                request.params[_key % extras_num] = request.params[key]
#                
#                # set value
#                num = [n for n in key.split('__') if n.isdigit()][0]
#                request.params[_val % extras_num] = request.params['roles__%d__value' % num]
#                
#                extras_num += 1
                
        
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

    def package_types(self):
        return ['dataset']
    
    def is_fallback(self):
        return True
    
    def setup_template_variables(self, context, data_dict):
        g.roles = get_roles()

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
        schema['role'] = {'key': [not_empty, unicode], 'value': [not_missing]}
        return schema
    
    def db_to_form_schema(data, package_type=None):
        schema = db_to_form_package_schema()
        schema['role'] = {'key': [not_empty, unicode], 'value': [not_missing]}
#        for role in get_roles():
#            schema.update({
#                '%s_name' % role : [ignore_missing],
#                '%s_phone' % role : [ignore_missing],
#                '%s_email' % role : [ignore_missing],
#                '%s_type' % role :[ignore_missing],
#            })

        return schema
