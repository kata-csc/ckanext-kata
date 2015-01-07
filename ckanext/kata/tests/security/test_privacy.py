'''
Test privacy of Kata
'''

from ckan import tests
from ckanext.kata.tests.security import KataPrivacyTestCase


class TestPrivacy(KataPrivacyTestCase):


    def test_user_list_fails(self):
        tests.call_action_api(self.app, 'user_list',
                              apikey=self.test_user.apikey,
                              status=403)

    def test_user_list_succeeds(self):
        tests.call_action_api(self.app, 'user_list',
                              apikey=self.test_sysadmin.apikey,
                              status=200)

    def test_user_activity_stream_fails(self):
        data_dict = {'id': 'test_user2'}
        tests.call_action_api(self.app, 'user_activity_list',
                              apikey=self.test_user.apikey,
                              status=403,
                              **data_dict)

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
        tests.call_action_api(self.app, 'user_activity_list',
                              apikey=self.test_sysadmin.apikey,
                              status=200,
                              **data_dict)

    def test_organization_activity_stream_fails(self):

        tests.call_action_api(self.app, 'organization_activity_list',
                              apikey=self.test_user.apikey,
                              status=403,
                              id='test_organisation')

    def test_organization_activity_stream_succeeds(self):

        # Todo: fix the auth function, it doesn't work for API calls at the moment: requires sysadmin

        data_dict = {'id': 'test_organisation', 'username': 'test_user', 'role': 'admin'}
        tests.call_action_api(self.app, 'organization_member_create',
                              apikey=self.test_sysadmin.apikey,
                              status=200,
                              **data_dict)

    #     tests.call_action_api(self.app, 'organization_activity_list',
    #                           apikey=self.test_user.apikey,
    #                           status=200,
    #                           id='test_organisation')

    def test_group_activity_stream_fails(self):

        tests.call_action_api(self.app, 'group_activity_list',
                              apikey=self.test_user.apikey,
                              status=403,
                              id='test_group')

    def test_group_activity_stream_succeeds(self):

        # Todo: fix the auth function, it doesn't work for API calls at the moment: requires sysadmin

        data_dict = {'id': 'test_group', 'username': 'test_user', 'role': 'admin'}
        tests.call_action_api(self.app, 'group_member_create',
                              apikey=self.test_sysadmin.apikey,
                              status=200,
                              **data_dict)

        # tests.call_action_api(self.app, 'group_activity_list',
        #                       apikey=self.test_user.apikey,
        #                       status=200,
        #                       id='test_group')

    def test_package_activity_stream_fails(self):

        tests.call_action_api(self.app, 'package_activity_list',
                              apikey=self.test_user2.apikey,
                              status=403,
                              id=self.package_id)

    def test_package_activity_stream_succeeds(self):

        # Todo: fix the auth function, it doesn't work for API calls at the moment: requires sysadmin

        tests.call_action_api(self.app, 'package_activity_list',
                              apikey=self.test_sysadmin.apikey,
                              status=200,
                              id=self.package_id)

        # tests.call_action_api(self.app, 'package_activity_list',
        #                       apikey=self.test_user.apikey,
        #                       status=200,
        #                       id=self.package_id)
