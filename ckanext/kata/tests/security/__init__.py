'''
Security and privacy tests for Kata
'''

import copy
import ckanext.kata.model as kata_model
from ckan.model import user as user_model
from ckan.model import repo as repo_model
from ckan import tests
from ckan.lib.create_test_data import CreateTestData

from ckanext.kata.tests.test_fixtures.unflattened import TEST_DATADICT

class KataPrivacyTestCase(tests.WsgiAppCase):

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

        org_dict = {'name': 'test_organisation', 'title': 'Test Organisation'}
        tests.call_action_api(cls.app, 'organization_create',
                              apikey=cls.test_sysadmin.apikey,
                              **org_dict)

        group_dict = {'name': 'test_group', 'title': 'Test Group'}
        tests.call_action_api(cls.app, 'group_create',
                              apikey=cls.test_sysadmin.apikey,
                              **group_dict)

        cls.TEST_DATADICT = copy.deepcopy(TEST_DATADICT)
        cls.package_id = u'urn-nbn-fi-csc-kata20140728095757755621'
        cls.TEST_DATADICT['owner_org'] = 'test_organisation'
        cls.TEST_DATADICT['id'] = cls.package_id
        tests.call_action_api(cls.app, 'package_create', apikey=cls.test_user.apikey,
                              status=200, **cls.TEST_DATADICT)


    @classmethod
    def teardown_class(cls):
        repo_model.rebuild_db()
