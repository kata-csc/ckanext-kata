'''
Test privacy of Kata
'''

from ckan.logic import NotAuthorized
from ckanext.kata.tests.functional.security import KataPrivacyTestCase


class TestPrivacy(KataPrivacyTestCase):

    def test_user_list_fails(self):
        self.assertRaises(NotAuthorized, self.api_test_user.action.user_list)

    def test_user_list_succeeds(self):
        output = self.api_test_sysadmin.action.user_list()

        assert len(output) > 2

    def test_user_activity_stream_fails(self):
        data_dict = {'id': 'test_user2'}
        self.assertRaises(NotAuthorized, self.api_test_user.action.user_activity_list, **data_dict)

    # def test_user_activity_stream_succeeds_1(self):
    #     '''
    #     Todo: fix the auth function, it doesn't work for API calls at the moment
    #     '''
    #     tests.call_action_api(self.app, 'user_activity_list',
    #                           apikey=self.test_user.apikey,
    #                           status=200,
    #                           id='test_user')

    def test_user_activity_stream_succeeds_2(self):
        data_dict = {'id': 'test_user'}
        self.api_test_sysadmin.action.user_activity_list(**data_dict)

    def test_organization_activity_stream_fails(self):

        self.assertRaises(NotAuthorized, self.api_test_user.action.organization_activity_list, id='test_organisation')

    def test_organization_activity_stream_succeeds(self):

        # Todo: fix the auth function, it doesn't work for API calls at the moment: requires sysadmin

        data_dict = {'id': 'test_organisation', 'username': 'test_user', 'role': 'admin'}
        self.api_test_sysadmin.action.organization_member_create(**data_dict)

    #     tests.call_action_api(self.app, 'organization_activity_list',
    #                           apikey=self.test_user.apikey,
    #                           status=200,
    #                           id='test_organisation')

    def test_group_activity_stream_fails(self):

        self.assertRaises(NotAuthorized, self.api_test_user.action.group_activity_list, id='test_group')

    def test_group_activity_stream_succeeds(self):

        # Todo: fix the auth function, it doesn't work for API calls at the moment: requires sysadmin

        data_dict = {'id': 'test_group', 'username': 'test_user', 'role': 'admin'}
        self.api_test_sysadmin.action.group_member_create(**data_dict)

        # tests.call_action_api(self.app, 'group_activity_list',
        #                       apikey=self.test_user.apikey,
        #                       status=200,
        #                       id='test_group')

    def test_package_activity_stream_fails(self):

        self.assertRaises(NotAuthorized, self.api_test_user2.action.package_activity_list, id=self.package_id)

    def test_package_activity_stream_succeeds(self):

        # Todo: fix the auth function, it doesn't work for API calls at the moment: requires sysadmin

        self.api_test_sysadmin.action.package_activity_list(id=self.package_id)

        # tests.call_action_api(self.app, 'package_activity_list',
        #                       apikey=self.test_user.apikey,
        #                       status=200,
        #                       id=self.package_id)
