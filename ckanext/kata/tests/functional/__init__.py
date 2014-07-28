'''Functional test package for Kata'''
import copy
import logging
import unittest

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

        cls.TEST_DATADICT = copy.deepcopy(TEST_DATADICT)

        try:
            output = call_action_api(cls.app, 'organization_create', apikey=cls.sysadmin_user.apikey,
                                     status=200, **TEST_ORGANIZATION_COMMON)
            cls.TEST_DATADICT['owner_org'] = output.get('id')

        except AppError:
            print 'Failed to create a common organization. Perhaps it exists already.'



    @classmethod
    def teardown_class(cls):
        """Get away from testing environment."""
        model.repo.rebuild_db()


