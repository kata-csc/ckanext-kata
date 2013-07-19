"""Test classes for Kata CKAN Extension."""

from unittest import TestCase
from ckanext.kata.settings import get_field_titles, FIELD_TITLES, get_field_title


class TestKataExtension(TestCase):
    """General tests for Kata CKAN extension."""

    def test_get_field_titles(self):
        '''Test settings.get_field_titles()'''

        titles = get_field_titles(lambda x: x)

        assert len(titles) > 2, 'Found less than 3 field titles'
        assert 'tags' in titles, 'No tags field found in field titles'
        assert 'authorstring' in titles, 'No authorstring field found in field titles'

    def test_get_field_titles_translate(self):
        '''Test settings.get_field_titles() translation'''

        translator = lambda x: x[::-1]  # Reverse string

        titles = get_field_titles(translator)

        assert translator(FIELD_TITLES['tags']) in titles.values(), 'No tags field found in field titles'
        assert translator(FIELD_TITLES['authorstring']) in titles.values(), 'No authorstring found in field titles'

    def test_get_field_title(self):
        '''Test settings.get_field_title()'''

        translator = lambda x: x[::-1]  # Reverse string

        title = get_field_title('tags', translator)

        assert translator(FIELD_TITLES['tags']) == title
