'''Main plugin file
'''

import logging
import os

from ckan.plugins import implements, SingletonPlugin
from ckan.plugins import IRoutes
from ckan.plugins import IConfigurer
from ckan.plugins import IMapper

log = logging.getLogger('ckanext.kata')

import ckan.plugins

class KATAPlugin(SingletonPlugin):
    implements(ckan.plugins.IDatasetForm, inherit=True)
    implements(ckan.plugins.IConfigurer, inherit=True)
    
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
    
    def package_form(self):
        return 'package/new_package_form.html'


