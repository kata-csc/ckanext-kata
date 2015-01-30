'''Functional test package for Kata'''

import copy
import unittest
import ckanapi

import paste.fixture
from pylons import config
from webtest import AppError

from ckan.config.middleware import make_app
from ckan.lib.create_test_data import CreateTestData
from ckan.tests import call_action_api

import ckanext.kata.model as kata_model
from ckanext.kata.tests.test_fixtures.unflattened import TEST_ORGANIZATION_COMMON, TEST_DATADICT

# Note: all ORM model changes must be imported before WsgiAppCase
from ckan import model, tests


class KataWsgiTestCase(tests.WsgiAppCase, unittest.TestCase):
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
        cls.user_sysadmin = model.User.get('testsysadmin')  # Org admin
        cls.user_normal = model.User.get('tester')          # Org editor
        cls.user_anna = model.User.get('annafan')
        cls.user_joe = model.User.get('joeadmin')           # Org member

        wsgiapp = make_app(config['global_conf'], **config['app_conf'])
        cls.app = paste.fixture.TestApp(wsgiapp)

        cls.api_user_normal = ckanapi.TestAppCKAN(cls.app, apikey=cls.user_normal.apikey)
        cls.api_user_sysadmin = ckanapi.TestAppCKAN(cls.app, apikey=cls.user_sysadmin.apikey)
        cls.api_user_anna = ckanapi.TestAppCKAN(cls.app, apikey=cls.user_anna.apikey)
        cls.api_user_joe = ckanapi.TestAppCKAN(cls.app, apikey=cls.user_joe.apikey)

        cls.TEST_DATADICT = copy.deepcopy(TEST_DATADICT)

        try:
            output = call_action_api(cls.app, 'organization_create', apikey=cls.user_sysadmin.apikey,
                                     status=200, **TEST_ORGANIZATION_COMMON)
            cls.TEST_DATADICT['owner_org'] = output.get('id')

        except AppError:
            print 'Failed to create a common organization. Perhaps it exists already.'



    @classmethod
    def teardown_class(cls):
        """Get away from testing environment."""
        model.repo.rebuild_db()


