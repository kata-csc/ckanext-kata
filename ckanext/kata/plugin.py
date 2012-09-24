'''Main plugin file
'''

import logging
import os

from ckan.plugins import implements, SingletonPlugin
from ckan.plugins import IRoutes
from ckan.plugins import IConfigurer
from ckan.plugins import IMapper

log = logging.getLogger('ckanext.kata')


class KATAPlugin(SingletonPlugin):
    '''Plugin class for KATA.
    '''
    implements(IRoutes, inherit=True)
    implements(IConfigurer)
    implements(IMapper, inherit=True)

    def update_config(self, config):
        """This IConfigurer implementation causes CKAN to look in the
        ```public``` and ```templates``` directories present in this
        package for any customisations.

        It also shows how to set the site title here (rather than in
        the main site .ini file), and causes CKAN to use the
        customised package form defined in ``package_form.py`` in this
        directory.
        """
        here = os.path.dirname(__file__)
        rootdir = os.path.dirname(os.path.dirname(here))
        template_dir = os.path.join(rootdir, 'ckanext',
                                    'kata', 'templates')
        config['extra_template_paths'] = ','.join([template_dir,
                config.get('extra_template_paths', '')])