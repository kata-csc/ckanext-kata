'''Controller unit tests''' 

from nose.tools import assert_equal, assert_raises

import paste.fixture

import ckan
from ckan.lib.create_test_data import CreateTestData
from ckan.lib.field_types import DateType
import ckan.model as model
from ckan.tests import WsgiAppCase, CommonFixtureMethods, url_for, assert_in, assert_not_in
from ckan.tests.html_check import HtmlCheckMethods
from ckan.lib.helpers import url_for
from ckan.lib.create_test_data import CreateTestData
from ckanext.kata import model as kata_model


class TestPackageController(WsgiAppCase, HtmlCheckMethods, CommonFixtureMethods):
    '''
    Tests for CKAN's package controller, to which Kata makes some changes by overriding templates.
    ''' 
    
    @classmethod
    def setup_class(cls):
        CreateTestData.create()
        # Set up Kata's additions to CKAN database (user_extra, etc.)
        kata_model.setup()

    @classmethod
    def teardown_class(cls):
        #kata_model.drop_tables()
        CreateTestData.delete()
    
    def test_data_and_resources_not_rendered(self):
        offset = url_for(controller='package', action='read', id=u'warandpeace')
        res = self.app.get(offset)
        assert '<section id="dataset-resources"' not in res, 'A package with no resources should not render Data and Resources section'

    def test_data_and_resources_rendered(self):
        offset = url_for(controller='package', action='read', id=u'annakarenina')
        res = self.app.get(offset)
        assert '<section id="dataset-resources"' in res, 'A package with resources should render Data and Resources section'


class TestContactController(WsgiAppCase, HtmlCheckMethods, CommonFixtureMethods):
    '''
    Tests for Kata's ContactController.
    '''
    
    @classmethod
    def setup_class(cls):
        #CreateTestData.create()
        # Set up Kata's additions to CKAN database (user_extra, etc.)
        #kata_model.setup()
        pass

    @classmethod
    def teardown_class(cls):
        #kata_model.drop_tables()
        #CreateTestData.delete()
        pass

    
    def test_contact_controller_found(self):
        #offset = url_for(controller="ContactController", action='render')
        #res = self.app.get(offset)
        #print res
        pass
        #assert 'Data and Resources' not in res, 'A package with no resources should not render Data and Resources section'
        