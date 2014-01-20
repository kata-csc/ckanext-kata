'''Functional test package for Kata'''

import paste.fixture
from pylons import config

from ckan.config.middleware import make_app
from ckan.lib.create_test_data import CreateTestData

from ckan.tests import WsgiAppCase
import ckanext.kata.model as kata_model


class KataWsgiTestCase(WsgiAppCase):
    '''
    Class to inherit for Kata's WSGI tests.
    '''

    @classmethod
    def setup_class(cls):
        """Set up testing environment."""

        kata_model.setup()
        CreateTestData.create()

        wsgiapp = make_app(config['global_conf'], **config['app_conf'])
        cls.app = paste.fixture.TestApp(wsgiapp)

    @classmethod
    def teardown_class(cls):
        """Get away from testing environment."""

        kata_model.delete_tables()
        CreateTestData.delete()

