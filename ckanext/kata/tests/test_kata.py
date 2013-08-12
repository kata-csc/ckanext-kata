# pylint: disable=R0201
"""
Test classes for Kata CKAN Extension.
"""

from unittest import TestCase
from pylons.util import ContextObj, PylonsContext, pylons, AttribSafeContextObj

from ckanext.kata.settings import get_field_titles, _FIELD_TITLES, get_field_title
from ckanext.kata.plugin import KataPlugin

from ckan.tests import WsgiAppCase, CommonFixtureMethods, url_for
from ckan.tests.html_check import HtmlCheckMethods
from pylons import config
import paste.fixture
from paste.registry import RegistryManager
from ckan.config.middleware import make_app

class TestKataExtension(TestCase):
    """General tests for Kata CKAN extension."""

    def test_get_field_titles(self):
        """Test settings.get_field_titles()"""

        titles = get_field_titles(lambda x: x)

        assert len(titles) > 2, 'Found less than 3 field titles'
        assert 'tags' in titles, 'No tags field found in field titles'
        assert 'authorstring' in titles, 'No authorstring field found in field titles'

    def test_get_field_titles_translate(self):
        """Test settings.get_field_titles() translation"""

        translator = lambda x: x[::-1]  # Reverse string

        titles = get_field_titles(translator)

        assert translator(_FIELD_TITLES['tags']) in titles.values(), 'No tags field found in field titles'
        assert translator(_FIELD_TITLES['authorstring']) in titles.values(), 'No authorstring found in field titles'

    def test_get_field_title(self):
        """Test settings.get_field_title()"""

        translator = lambda x: x[::-1]  # Reverse string

        title = get_field_title('tags', translator)

        assert translator(_FIELD_TITLES['tags']) == title


class TestKataPlugin(WsgiAppCase, HtmlCheckMethods, CommonFixtureMethods):
    """
    General tests for KataPlugin.

    Provides a a dummy context object to test functions and methods that rely on it.
    """

    @classmethod
    def setup_class(cls):
        """Set up tests."""

        wsgiapp = make_app(config['global_conf'], **config['app_conf'])
        cls.app = paste.fixture.TestApp(wsgiapp)

        cls.some_data_dict = {'sort': u'metadata_modified desc', 'fq': '', 'rows': 20, 'facet.field': ['groups', 'tags', 'extras_fformat', 'license', 'authorstring', 'organizationstring', 'extras_language'], 'q': u'Selenium', 'start': 0, 'extras': {}}
        cls.kata_plugin = KataPlugin()

        # The Pylons globals are not available outside a request. This is a hack to provide context object.
        c = AttribSafeContextObj()
        py_obj = PylonsContext()
        py_obj.tmpl_context = c
        pylons.tmpl_context._push_object(c)

    @classmethod
    def teardown_class(cls):
        """Get away from testing environment."""

        pylons.tmpl_context._pop_object()

    def test_before_search(self):
        """Test before_search() output type."""

        assert isinstance( self.kata_plugin.before_search(self.some_data_dict), dict), "KataPlugin.before_search() didn't output a dict"

    def test_get_actions(self):
        """Test get_actions() output type."""
        assert isinstance( self.kata_plugin.get_actions(), dict), "KataPlugin.get_actions() didn't output a dict"

    def test_get_helpers(self):
        """Test get_helpers() output type."""
        assert isinstance( self.kata_plugin.get_helpers(), dict), "KataPlugin.get_helpers() didn't output a dict"

    def test_new_template(self):
        """Test new_template()."""
        html_location = self.kata_plugin.new_template()
        assert len( html_location ) > 0

    def test_comments_template(self):
        """Test comments_template()."""
        html_location = self.kata_plugin.comments_template()
        assert len( html_location ) > 0

    def test_search_template(self):
        """Test search_template()."""
        html_location = self.kata_plugin.search_template()
        assert len( html_location ) > 0

    def test_form_to_db_schema_options(self):
        """Test Kata schema."""
        schema = self.kata_plugin.form_to_db_schema_options()
        assert isinstance(schema, dict) and len(schema) > 0

    def test_db_to_form_schema_options(self):
        """Test Kata schema."""
        schema = self.kata_plugin.db_to_form_schema_options()
        assert isinstance(schema, dict) and len(schema) > 0
