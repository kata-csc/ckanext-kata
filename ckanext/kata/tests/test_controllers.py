#pylint: disable=R0201, R0904

"""Unit tests for controllers"""

from pylons import config
import paste.fixture    # pylint: disable=F0401

from ckan.config.middleware import make_app
from ckan.lib.create_test_data import CreateTestData
from ckan.tests import WsgiAppCase, CommonFixtureMethods, url_for
from ckan.tests.html_check import HtmlCheckMethods
from ckanext.kata import model as kata_model


class TestKataControllers(WsgiAppCase, HtmlCheckMethods, CommonFixtureMethods):
    """
    Tests for Kata's controllers and routing.
    """
    
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

    def test_help_page(self):
        """
        Test that help page is found and rendered.
        """
        offset = url_for('/help')
        res = self.app.post(offset)
        assert res.status == 200, 'Wrong HTTP status code (not 200)'

    def test_faq_page(self):
        """
        Test that faq page is found and rendered.
        """
        offset = url_for('/faq')
        res = self.app.post(offset)
        assert res.status == 200, 'Wrong HTTP status code (not 200)'

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

    def test_contact_controller_no_user(self):
        """
        Test that we get a redirect when there is no user
        """
        offset = url_for("/contact/warandpeace")
        res = self.app.get(offset)
        assert res.status == 302, 'Expecting a redirect when user not logged in'

    def test_contact_controller_user_logged_in(self):
        '''
        Test that we get the contact form when user is logged in

        Note: Form should probably be only visible if the dataset can be requested via the form?
        '''

        extra_environ = {'REMOTE_USER': 'tester'}

        offset = url_for("/contact/warandpeace")
        res = self.app.post(offset, extra_environ=extra_environ)

        print offset
        print res

        assert all(piece in res.body for piece in ['<form', '/contact/send/', '</form>']), 'Contact form not rendered'

    def test_comments_rendered(self):
        '''
        A package should have a comments section
        '''
        offset = url_for(controller='package', action='read', id=u'annakarenina')
        res = self.app.get(offset)
        assert '<section class="module module-narrow comments">' in res, 'A user should see comments section'
    
    def test_comments_rendered_not_logged_in(self):
        '''
        A package should not have a comments section for a user not logged in
        '''
        offset = url_for(controller='package', action='read', id=u'annakarenina')
        res = self.app.get(offset)
        assert '<a class="btn btn-primary" href="/dataset/new_comment/' not in res, 'A non-logged in user should not see add new comment button'

    def test_new_comment_rendered(self):
        '''
        A user should be able to add a comment to a dataset
        '''
        offset = url_for(controller='ckanext.kata.controllers:KataCommentController', action='new_comment', id=u'annakarenina')
        res = self.app.get(offset)
        assert res.status == 302, 'Wrong status code (should be 302), in new_comment'
        extra_environ = {'REMOTE_USER': 'tester'}
        offset = url_for(controller='ckanext.kata.controllers:KataCommentController', action='new_comment', id=u'annakarenina')
        res = self.app.get(offset, extra_environ=extra_environ)
        assert '<label class="control-label" for="new_comment">' in res, 'Text area to add a comment should exist'
        assert '<label for="rating-3"' in res, 'Rating should exist in add comment page'
        assert res.status == 200, 'Wrong status code in new comment page'
