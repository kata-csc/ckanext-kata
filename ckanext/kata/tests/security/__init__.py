'''
Security and privacy tests for Kata
'''

import copy
import unittest

from pylons import config
import paste.fixture
import ckanapi

from ckan.model import user as user_model
from ckan.model import repo as repo_model
from ckan import tests
from ckan.lib.create_test_data import CreateTestData
from ckan.config.middleware import make_app

import ckanext.kata.model as kata_model
from ckanext.kata.tests.test_fixtures.unflattened import TEST_DATADICT


class KataPrivacyTestCase(tests.WsgiAppCase, unittest.TestCase):
    @classmethod
    def setup_class(cls):
        kata_model.setup()
        users = [
            {'name': 'test_sysadmin',
             'sysadmin': True,
             'apikey': 'test_sysadmin',
             'password': 'test_sysadmin'},
            {'name': 'test_user',
             'sysadmin': False,
             'apikey': 'test_user',
             'password': 'test_user'},
            {'name': 'test_user2',
             'sysadmin': False,
             'apikey': 'test_user2',
             'password': 'test_user2'}
        ]
        CreateTestData.create_users(users)
        cls.test_user = user_model.User.get('test_user')
        cls.test_user2 = user_model.User.get('test_user2')
        cls.test_sysadmin = user_model.User.get('test_sysadmin')

        wsgiapp = make_app(config['global_conf'], **config['app_conf'])
        cls.app = paste.fixture.TestApp(wsgiapp)

        # Set up API callers

        cls.api_test_user = ckanapi.TestAppCKAN(cls.app, apikey=cls.test_user.apikey)
        cls.api_test_user2 = ckanapi.TestAppCKAN(cls.app, apikey=cls.test_user2.apikey)
        cls.api_test_sysadmin = ckanapi.TestAppCKAN(cls.app, apikey=cls.test_sysadmin.apikey)
        cls.api = ckanapi.TestAppCKAN(cls.app)

        org_dict = {'name': 'test_organisation', 'title': 'Test Organisation'}
        cls.api_test_sysadmin.action.organization_create(**org_dict)

        group_dict = {'name': 'test_group', 'title': 'Test Group'}
        cls.api_test_sysadmin.action.group_create(**group_dict)

        cls.TEST_DATADICT = copy.deepcopy(TEST_DATADICT)
        cls.package_id = u'urn-nbn-fi-csc-kata20140728095757755621'
        cls.TEST_DATADICT['owner_org'] = 'test_organisation'
        cls.TEST_DATADICT['id'] = cls.package_id
        cls.api_test_user.action.package_create(**cls.TEST_DATADICT)

    @classmethod
    def teardown_class(cls):
        repo_model.rebuild_db()
