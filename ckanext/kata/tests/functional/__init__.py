'''Functional test package for Kata'''

import copy
import unittest

import ckanapi
import paste.fixture
from pylons import config
from pylons.util import AttribSafeContextObj, PylonsContext, pylons
from webtest import AppError

from ckan.config.middleware import make_app
from ckan.lib.create_test_data import CreateTestData

import ckanext.kata.model as kata_model
from ckanext.kata.tests.test_fixtures.unflattened import TEST_ORGANIZATION_COMMON, TEST_DATADICT
import ckanext.ytp.comments.model as comments_model

# Note: all ORM model changes must be imported before WsgiAppCase
from ckan import model
import ckan.tests.legacy as tests


class KataWsgiTestCase(tests.WsgiAppCase, unittest.TestCase):
    '''
    Class to inherit for Kata's WSGI tests.
    '''

    @classmethod
    def setup_class(cls):
        """Set up testing environment."""

        model.repo.rebuild_db()
        kata_model.setup()
        CreateTestData.create()
        comments_model.init_tables()

        wsgiapp = make_app(config['global_conf'], **config['app_conf'])
        cls.app = paste.fixture.TestApp(wsgiapp)

        # The Pylons globals are not available outside a request. This is a hack to provide context object.
        c = AttribSafeContextObj()
        py_obj = PylonsContext()
        py_obj.tmpl_context = c
        pylons.tmpl_context._push_object(c)

    @classmethod
    def teardown_class(cls):
        """Get away from testing environment."""

        kata_model.delete_tables()
        model.repo.rebuild_db()


class KataApiTestCase(unittest.TestCase):
    '''
    Class to inherit for Kata's API tests.
    '''

    @classmethod
    def setup_class(cls):
        """Setup for all tests."""

        model.repo.rebuild_db()
        kata_model.setup()
        CreateTestData.create()

        cls.user_sysadmin = model.User.get('testsysadmin')  # Org admin
        cls.user_normal = model.User.get('tester')          # Org editor
        cls.user_anna = model.User.get('annafan')
        cls.user_joe = model.User.get('joeadmin')           # Org member

        wsgiapp = make_app(config['global_conf'], **config['app_conf'])
        cls.app = paste.fixture.TestApp(wsgiapp)

        # Set up API callers

        cls.api_user_normal = ckanapi.TestAppCKAN(cls.app, apikey=cls.user_normal.apikey)
        cls.api_user_sysadmin = ckanapi.TestAppCKAN(cls.app, apikey=cls.user_sysadmin.apikey)
        cls.api_user_anna = ckanapi.TestAppCKAN(cls.app, apikey=cls.user_anna.apikey)
        cls.api_user_joe = ckanapi.TestAppCKAN(cls.app, apikey=cls.user_joe.apikey)
        cls.api = ckanapi.TestAppCKAN(cls.app)

        cls.TEST_DATADICT = copy.deepcopy(TEST_DATADICT)

        try:
            output = cls.api_user_sysadmin.action.organization_create(**TEST_ORGANIZATION_COMMON)
            cls.TEST_DATADICT['owner_org'] = output.get('id')
        except AppError:
            print 'Failed to create a common organization. Perhaps it exists already.'

    @classmethod
    def teardown_class(cls):
        """Get away from testing environment."""
        model.repo.rebuild_db()

