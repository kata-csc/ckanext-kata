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

    def test_organization_user_list_succeeds(self):
        output = self.api_test_user.call_action('organization_show', data_dict={'id': 'test_organisation'})
        assert output.get('users'), output

    def test_organization_user_list_fails(self):
        output = self.api_test_user2.call_action('organization_show', data_dict={'id': 'test_organisation'})
        assert not output.get('users'), output

    def test_group_user_list_succeeds(self):
        output = self.api_test_user.call_action('group_show', data_dict={'id': 'test_group'})
        assert output.get('users'), output

    def test_group_user_list_fails(self):
        output = self.api_test_user2.call_action('group_show', data_dict={'id': 'test_group'})
        assert not output.get('users'), output

    def test_user_activity_stream_fails(self):
        data_dict = {'id': 'test_user2'}
        self.assertRaises(NotAuthorized, self.api_test_user.action.user_activity_list, **data_dict)

    def test_user_activity_stream_succeeds_1(self):
        activity = self.api_test_sysadmin.action.user_activity_list(**dict(id='test_user'))
        assert len(activity), activity

    def test_user_activity_stream_succeeds_2(self):
        data_dict = {'id': 'test_user'}
        self.api_test_sysadmin.action.user_activity_list(**data_dict)

    def test_organization_activity_stream_fails(self):

        self.assertRaises(NotAuthorized, self.api_test_user.action.organization_activity_list, id='test_organisation')

    def test_organization_activity_stream_succeeds(self):
        activity = self.api_test_sysadmin.action.organization_activity_list(**dict(id='test_organisation'))
        assert len(activity), activity

    def test_group_activity_stream_fails(self):

        self.assertRaises(NotAuthorized, self.api_test_user.action.group_activity_list, id='test_group')

    def test_group_activity_stream_succeeds(self):
        activity = self.api_test_sysadmin.action.group_activity_list(**dict(id='test_group'))
        assert len(activity), activity

    def test_package_activity_stream_fails(self):

        self.assertRaises(NotAuthorized, self.api_test_user2.action.package_activity_list, id=self.package_id)

    def test_package_activity_stream_succeeds(self):
        self.api_test_sysadmin.action.package_activity_list(id=self.package_id)

        activity = self.api_test_sysadmin.action.package_activity_list(**dict(id=self.package_id))
        assert len(activity), activity
