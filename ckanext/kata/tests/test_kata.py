# pylint: disable=R0201

"""Test classes for Kata CKAN Extension."""

from unittest import TestCase
from ckanext.kata.settings import get_field_titles, _FIELD_TITLES, \
    get_field_title
from ckanext.kata.plugin import KataPlugin


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


class TestKataPlugin(TestCase):
    """General tests for KataPlugin."""

    @classmethod
    def setup_class(cls):
        """Set up tests."""
        cls.some_data_dict = {'sort': u'metadata_modified desc', 'fq': '', 'rows': 20, 'facet.field': ['groups', 'tags', 'extras_fformat', 'license', 'authorstring', 'organizationstring', 'extras_language'], 'q': u'Selenium', 'start': 0, 'extras': {}}
        cls.kata_plugin = KataPlugin()

    @classmethod
    def teardown_class(cls):
        """Get away from testing environment."""
        pass

#    def test_before_search(self):
#        """Test before_search() output type."""
#
#        assert isinstance( self.kata_plugin.before_search(self.some_data_dict), dict), "KataPlugin.before_search() didn't output a dict"

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

