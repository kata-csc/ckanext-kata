'''Main plugin file
'''

import logging
import os

from ckan.plugins import implements, SingletonPlugin
from ckan.plugins import IPackageController
from ckan.plugins import IRoutes
from ckan.plugins import IConfigurer
from ckan.plugins import IMapper

from ckan.lib.base import g, c

log = logging.getLogger('ckanext.kata')

import ckan.plugins
import ckan.lib.plugins

def get_roles():
    return ['author', 'maintainer', 'publisher', 'sponsor']

class KataMetadata(SingletonPlugin):
    implements(IPackageController, inherit=True)
    
    def create(self, dataset):
        pass
        
    def edit(self, dataset):
        pass
    
    def delete(self, dataset):
        pass

class KataPlugin(SingletonPlugin, ckan.lib.plugins.DefaultDatasetForm):
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
    
    def setup_template_variables(self, context, data_dict):
        log.debug(context)
        log.debug(data_dict)
        log.debug(c)
        
        context['roles'] = get_roles()
        data_dict['roles'] = get_roles()
        c.roles = get_roles()
        
        return {'roles':get_roles()}
        

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
        
    def form_to_db_schema(self, package_type=None):
        from ckan.logic.schema import package_form_schema
        from ckan.lib.navl.validators import ignore_missing
    
        schema = package_form_schema()

        for role in get_roles():
            schema.update({
                '%s_name' % role : [ignore_missing, unicode, convert_to_extras],
                '%s_phone' % role : [ignore_missing, unicode, convert_to_extras],
                '%s_email' % role : [ignore_missing, unicode, convert_to_extras],
                '%s_type' % role : [ignore_missing, unicode, convert_to_extras],
            })
        return schema
    
    def db_to_form_schema(data, package_type=None):
        from ckan.lib.navl.validators import ignore_missing, keep_extras
    
        schema = package_form_schema()
        
        for role in get_roles():
            schema.update({
                '%s_name' % role : [ignore_missing],
                '%s_phone' % role : [ignore_missing],
                '%s_email' % role : [ignore_missing],
                '%s_type' % role :[ignore_missing],
            })
            
        return schema
