# coding: utf-8
#
# pylint: disable=no-self-use, missing-docstring, too-many-public-methods, invalid-name

"""
Test classes for Kata CKAN Extension.
"""

import copy
from unittest import TestCase

from pylons.util import PylonsContext, pylons, AttribSafeContextObj
from pylons import config
import paste.fixture  # pylint: disable=import-error

from ckanext.kata.settings import get_field_titles, _FIELD_TITLES, get_field_title
from ckanext.kata.plugin import KataPlugin
from ckan.tests import WsgiAppCase, CommonFixtureMethods
from ckan.tests.html_check import HtmlCheckMethods
from ckan.config.middleware import make_app
from ckanext.kata import settings, utils, actions


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
    """
    General tests for KataPlugin.

    Provides a a dummy context object to test functions and methods that rely on it.
    """

    @classmethod
    def setup_class(cls):
        """Set up tests."""

        cls.some_data_dict = {'sort': u'metadata_modified desc',
                              'fq': '',
                              'rows': 20,
                              'facet.field': ['groups',
                                              'tags',
                                              'extras_fformat',
                                              'license',
                                              'authorstring',
                                              'organizationstring',
                                              'extras_language'],
                              'q': u'',
                              'start': 0,
                              'extras': {'ext_author-4': u'testauthor',
                                         'ext_date-metadata_modified-end': u'2013',
                                         'ext_date-metadata_modified-start': u'2000',
                                         'ext_groups-6': u'testdiscipline',
                                         'ext_operator-2': u'OR',
                                         'ext_operator-3': u'AND',
                                         'ext_operator-4': u'AND',
                                         'ext_operator-5': u'OR',
                                         'ext_operator-6': u'NOT',
                                         'ext_organization-3': u'testorg',
                                         'ext_tags-1': u'testkeywd',
                                         'ext_tags-2': u'testkeywd2',
                                         'ext_title-5': u'testtitle'}
        }
        cls.short_data_dict = {'sort': u'metadata_modified desc',
                               'fq': '',
                               'rows': 20,
                               'facet.field': ['groups',
                                               'tags',
                                               'extras_fformat',
                                               'license',
                                               'authorstring',
                                               'organizationstring',
                                               'extras_language'],
                               'q': u'',
                               'start': 0,
        }
        cls.test_q_terms = u' ((tags:testkeywd) OR ( tags:testkeywd2 AND ' + \
                           u'organization:testorg AND author:testauthor) OR ' + \
                           u'( title:testtitle NOT groups:testdiscipline))'
        cls.test_q_dates = u' metadata_modified:[2000-01-01T00:00:00.000Z TO ' + \
                           u'2013-12-31T23:59:59.999Z]'
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
        pass

    def test_extract_search_params(self):
        """Test extract_search_params() output parameters number."""
        terms, ops, dates = self.kata_plugin.extract_search_params(self.some_data_dict)
        n_extracted = len(terms) + len(ops) + len(dates)
        assert len(self.some_data_dict['extras']) == n_extracted - 1, \
            "KataPlugin.extract_search_params() parameter number mismatch"
        assert len(terms) == len(ops) + 1, \
            "KataPlugin.extract_search_params() term/operator ratio mismatch"

    def test_parse_search_terms(self):
        """Test parse_search_terms() result string."""
        test_dict = self.some_data_dict.copy()
        terms, ops, dates = self.kata_plugin.extract_search_params(self.some_data_dict)
        self.kata_plugin.parse_search_terms(test_dict, terms, ops)
        assert test_dict['q'] == self.test_q_terms, \
            "KataPlugin.parse_search_terms() error in query parsing q=%s, test_q_terms=%s" % (
                test_dict['q'], self.test_q_terms)

    def test_parse_search_dates(self):
        """Test parse_search_dates() result string."""
        test_dict = self.some_data_dict.copy()
        terms, ops, dates = self.kata_plugin.extract_search_params(self.some_data_dict)
        self.kata_plugin.parse_search_dates(test_dict, dates)
        assert test_dict['q'] == self.test_q_dates, \
            "KataPlugin.parse_search_dates() error in query parsing"

    def test_before_search(self):
        """Test before_search() output type and more."""
        result_dict = self.kata_plugin.before_search(self.some_data_dict.copy())
        assert isinstance(result_dict, dict), "KataPlugin.before_search() didn't output a dict"

        # Test that no errors occur without 'extras'
        self.kata_plugin.before_search(self.short_data_dict)

    def test_get_actions(self):
        """Test get_actions() output type."""
        assert isinstance(self.kata_plugin.get_actions(), dict), "KataPlugin.get_actions() didn't output a dict"

    def test_get_helpers(self):
        """Test get_helpers() output type."""
        assert isinstance(self.kata_plugin.get_helpers(), dict), "KataPlugin.get_helpers() didn't output a dict"

    def test_new_template(self):
        html_location = self.kata_plugin.new_template()
        assert len(html_location) > 0

    def test_comments_template(self):
        html_location = self.kata_plugin.comments_template()
        assert len(html_location) > 0

    def test_search_template(self):
        html_location = self.kata_plugin.search_template()
        assert len(html_location) > 0

    def test_read_template(self):
        html_location = self.kata_plugin.read_template()
        assert len(html_location) > 0

    def test_history_template(self):
        html_location = self.kata_plugin.history_template()
        assert len(html_location) > 0

    def test_package_form(self):
        html_location = self.kata_plugin.package_form()
        assert len(html_location) > 0


    def test_create_package_schema(self):
        schema = self.kata_plugin.create_package_schema()
        assert isinstance(schema, dict)
        assert len(schema) > 0

    def test_update_package_schema(self):
        schema = self.kata_plugin.update_package_schema()
        assert isinstance(schema, dict)
        assert len(schema) > 0

    def test_show_package_schema(self):
        schema = self.kata_plugin.show_package_schema()
        assert isinstance(schema, dict)
        assert len(schema) > 0


class TestResouceConverters(TestCase):
    """Unit tests for resource conversions in actions."""

    @classmethod
    def setup_class(cls):
        """Set up tests."""

        cls.test_data = {
            'id': u'test',
            'direct_download_URL': u'http://www.csc.fi',
            'algorithm': u'MD5',
            'checksum': u'f60e586509d99944e2d62f31979a802f',
            'mimetype': u'application/pdf',
        }

        cls.test_data2 = {
            'id': u'test',
            'resources': [{
                'url': u'http://www.csc.fi',
                'algorithm': u'MD5',
                'hash': u'f60e586509d99944e2d62f31979a802f',
                'format': u'application/pdf',
                'resource_type': settings.RESOURCE_TYPE_DATASET,
            }]}

        cls.test_data3 = {
            'id': u'test',
            'resources': [{
                'url': u'http://www.csc.fi',
                'algorithm': u'MD5',
                'hash': u'f60e586509d99944e2d62f31979a802f',
                'format': u'application/pdf',
                'resource_type': settings.RESOURCE_TYPE_DATASET,
            },
            {
                'url': u'http://www.helsinki.fi',
                'algorithm': u'SHA',
                'hash': u'somehash',
                'format': u'application/csv',
                'resource_type': 'file',
            }]}

    def test_dataset_to_resource(self):
        data_dict = copy.deepcopy(self.test_data)
        assert 'resources' not in data_dict

        utils.dataset_to_resource(data_dict)
        assert 'resources' in data_dict

        utils.dataset_to_resource(data_dict)
        assert 'resources' in data_dict

    def test_dataset_to_resource_invalid(self):
        data_dict = copy.deepcopy(self.test_data)
        data_dict.pop('direct_download_URL')
        data_dict.pop('checksum')
        data_dict.pop('mimetype')
        assert 'resources' not in data_dict

        utils.dataset_to_resource(data_dict)
        # dataset_to_resource can handle missing data, so resources is created
        assert 'resources' in data_dict

    def test_resource_to_dataset(self):
        data_dict = copy.deepcopy(self.test_data2)
        utils.resource_to_dataset(data_dict)
        assert 'direct_download_URL' in data_dict

    def test_resource_to_dataset_invalid(self):
        data_dict = copy.deepcopy(self.test_data2)
        data_dict['resources'][0].pop('resource_type')
        utils.resource_to_dataset(data_dict)
        assert 'direct_download_URL' not in data_dict


class TestUtils(TestCase):
    """Unit tests for functions in utils.py."""

    def test_generate_pid(self):
        pid = utils.generate_pid()
        assert 'urn' in pid
        assert len(pid) >= 10

    def test_generate_pid2(self):
        pid = utils.generate_pid()
        pid2 = utils.generate_pid()
        assert pid != pid2


class TestActions(TestCase):
    """Unit tests for action functions."""

    def test_group_list(self):
        group_list = actions.group_list({}, {})
        assert isinstance(group_list, dict)


