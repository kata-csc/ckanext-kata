# pylint: disable=R0201

"""Unit tests for controllers"""

from ckan.lib.create_test_data import CreateTestData
from ckan.tests import WsgiAppCase, CommonFixtureMethods, url_for
from ckan.tests.html_check import HtmlCheckMethods
from ckanext.kata import model as kata_model


class TestPackageController(WsgiAppCase, HtmlCheckMethods, CommonFixtureMethods):
    """
    Tests for CKAN's package controller, to which Kata makes some changes by overriding templates.
    """
    
    @classmethod
    def setup_class(cls):
        """Set up tests."""

        # Set up Kata's additions to CKAN database (user_extra, etc.)
        kata_model.setup()

        CreateTestData.create()

    @classmethod
    def teardown_class(cls):
        """Get away from testing environment."""

        kata_model.delete_tables()
        CreateTestData.delete()
    
    def test_data_and_resources_not_rendered(self):
        """
        A package with no resources should not render Data and Resources section
        """

        offset = url_for(controller='package', action='read', id=u'warandpeace')
        res = self.app.get(offset)
        assert '<section id="dataset-resources"' not in res, 'A package with no resources should not render Data and Resources section'

    def test_data_and_resources_rendered(self):
        """
        A package with resources should render Data and Resources section
        """

        offset = url_for(controller='package', action='read', id=u'annakarenina')
        res = self.app.get(offset)
        assert '<section id="dataset-resources"' in res, 'A package with resources should render Data and Resources section'


class TestContactController(WsgiAppCase, HtmlCheckMethods, CommonFixtureMethods):
    """
    Tests for Kata's ContactController.
    """
    
#     _users = [
#         {'name': 'tester',
#          'fullname': 'Testi Testaaja',
#          'password': 'pass'},
#         ]
    
    @classmethod
    def setup_class(cls):
        """Set up Kata's additions to CKAN database (user_extra, etc.)"""

        kata_model.setup()
        CreateTestData.create()

        # Couldn't get the session to work properly with a logged in user...

        #tester = model.User(name=u'tester', apikey=u'tester',
            #password=u'tester')
        #model.Session.add(tester)
        #model.Session.commit()
#         CreateTestData.create_users(cls._users)
#         model.repo.commit_and_remove() # due to bug in create_users
#
#         #model.Session.remove()
#         user = model.User.by_name('tester')
#         cls.extra_environ = {'Authorization': str(user.apikey)}

    @classmethod
    def teardown_class(cls):
        kata_model.delete_tables()
        CreateTestData.delete()
    
    def test_contact_controller_found(self):
        offset = url_for(controller="contact", action='render', pkg_id=u'warandpeace')
        assert offset[0] == '/', 'No URL received for contact controller' 

    def test_contact_controller_no_user(self):
        """
        Test that we get a redirect when there is no user
        """
        
        offset = url_for(controller="contact", action='render', pkg_id=u'warandpeace')
        res = self.app.get(offset)
        assert res.status == 302, 'Expecting a redirect when user not logged in'

#     def test_contact_controller_user_logged_in(self):
#         '''
#         Test that we get the contact form when user is logged in
#          
#         TODO: Form should probably be only visible if the dataset can be requested via the form.
#         '''
#          
#         #package = model.Package.get(u'warandpeace')
#          
#         #CreateTestData.create_test_user()
#         #model.Session.remove()
#          
#         #model.Session.add(model.User.by_name(u'tester'))
#         #model.Session.commit()
#          
#         #self.normal_user = model.User.by_name('tester')
#         #auth = {'Authorization': str(self.normal_user.api_key)}
#          
#         offset = url_for(controller="contact", action='render', pkg_id=u'warandpeace')
#         res = self.app.get(offset, extra_environ=self.extra_environ)
#          
#         #assert res.status == 200, 'Not OK'
#          
#         assert all(piece in res.body for piece in ['<form', '/contact/send/', '</form>']), 'Contact form not rendered'
#                  