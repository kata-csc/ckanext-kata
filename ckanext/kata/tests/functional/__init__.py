'''Functional test package for Kata'''
import unittest

import paste.fixture
from pylons import config
from ckan import model, tests

from ckan.config.middleware import make_app
from ckan.lib.create_test_data import CreateTestData

import ckanext.kata.model as kata_model


class KataWsgiTestCase(tests.WsgiAppCase):
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


class KataApiTestCase(unittest.TestCase):
    '''
    Class to inherit for Kata's API tests.
    '''

    @classmethod
    def setup_class(cls):
        """Setup for all tests."""

        kata_model.setup()
        CreateTestData.create()
        cls.sysadmin_user = model.User.get('testsysadmin')
        cls.normal_user = model.User.get('tester')

        wsgiapp = make_app(config['global_conf'], **config['app_conf'])
        cls.app = paste.fixture.TestApp(wsgiapp)

    @classmethod
    def teardown_class(cls):
        """Get away from testing environment."""
        model.repo.rebuild_db()


