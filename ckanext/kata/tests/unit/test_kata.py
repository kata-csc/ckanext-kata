# coding: utf-8
#
# pylint: disable=no-self-use, missing-docstring, too-many-public-methods, invalid-name, unused-variable

"""
Test classes for Kata CKAN Extension.
"""

import copy
from unittest import TestCase

from pylons.util import PylonsContext, pylons, AttribSafeContextObj

from ckanext.kata.settings import get_field_titles, _FIELD_TITLES, get_field_title
from ckanext.kata.plugin import KataPlugin
from ckanext.kata import settings, utils, helpers, actions
from ckanext.kata.tests.test_fixtures.unflattened import TEST_DATADICT


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

    def test_extract_search_params(self):
        """Test extract_search_params() output parameters number."""
        terms, ops, dates, adv_search = self.kata_plugin.extract_search_params(self.some_data_dict)
        n_extracted = len(terms) + len(ops) + len(dates)
        assert len(self.some_data_dict['extras']) == n_extracted - 1, \
            "KataPlugin.extract_search_params() parameter number mismatch"
        assert len(terms) == len(ops) + 1, \
            "KataPlugin.extract_search_params() term/operator ratio mismatch"

    def test_parse_search_terms(self):
        """Test parse_search_terms() result string."""
        test_dict = self.some_data_dict.copy()
        terms, ops, dates, adv_search = self.kata_plugin.extract_search_params(self.some_data_dict)
        self.kata_plugin.parse_search_terms(test_dict, terms, ops)
        assert test_dict['q'] == self.test_q_terms, \
            "KataPlugin.parse_search_terms() error in query parsing q=%s, test_q_terms=%s" % (
                test_dict['q'], self.test_q_terms)

    def test_parse_search_dates(self):
        """Test parse_search_dates() result string."""
        test_dict = self.some_data_dict.copy()
        terms, ops, dates, adv_search = self.kata_plugin.extract_search_params(self.some_data_dict)
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

    def test_before_index(self):
        pkg_dict = {'access_application_new_form': u'False',
                     'agent_0_URL': u'www.csc.fi',
                     'agent_0_funding-id': u'43096ertjgad\xf6sjgn89q3q4',
                     'agent_0_name': u'F. Under',
                     'agent_0_organisation': u'Agentti-Project',
                     'agent_0_role': u'funder',
                     'agent_1_name': u'o. oWNER',
                     'agent_1_role': u'owner',
                     'agent_2_name': u'M. Merger',
                     'agent_2_role': u'author',
                     'agent_3_name': u'juho',
                     'agent_3_role': u'distributor',
                     'data_dict': '{"dada": "dudu"}'}

        #output = self.kata_plugin.before_index(dict(data_dict=json.dumps(pkg_dict)))
        output = self.kata_plugin.before_index(pkg_dict)

        assert 'funder_0' in output
        assert 'owner_1' in output
        assert 'author_2' in output
        assert 'distributor_3' in output


class TestKataSchemas(TestCase):

    @classmethod
    def setup_class(cls):
        cls.kata_plugin = KataPlugin()

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

    def test_create_package_schema_oai_dc(self):
        schema = self.kata_plugin.create_package_schema_oai_dc()
        assert isinstance(schema, dict)
        assert len(schema) > 0

    def test_update_package_schema_oai_dc(self):
        schema = self.kata_plugin.update_package_schema_oai_dc()
        assert isinstance(schema, dict)
        assert len(schema) > 0

    def test_create_package_schema_ddi(self):
        schema = self.kata_plugin.create_package_schema_ddi()
        assert isinstance(schema, dict)
        assert len(schema) > 0

    def test_tags_schema(self):
        schema = self.kata_plugin.tags_schema()
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
                'mimetype': u'application/pdf',
                'resource_type': settings.RESOURCE_TYPE_DATASET,
            }]}

        cls.test_data3 = {
            'id': u'test',
            'resources': [{
                'url': u'http://www.csc.fi',
                'algorithm': u'MD5',
                'hash': u'f60e586509d99944e2d62f31979a802f',
                'mimetype': u'application/pdf',
                'resource_type': settings.RESOURCE_TYPE_DATASET,
            }, {
                'url': u'http://www.helsinki.fi',
                'algorithm': u'SHA',
                'hash': u'somehash',
                'format': u'application/csv',
                'resource_type': 'file',
            }]
        }

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

    def test_resource_handling(self):
        data_dict = copy.deepcopy(self.test_data3)
        utils.resource_to_dataset(data_dict)
        assert 'direct_download_URL' in data_dict
        assert 'resources' in data_dict

        data_dict['availability'] = 'contact_owner'

        utils.dataset_to_resource(data_dict)
        assert 'resources' in data_dict

        utils.resource_to_dataset(data_dict)
        assert 'resources' in data_dict
        assert data_dict['availability'] == 'contact_owner'

        assert data_dict.get('algorithm') == self.test_data3['resources'][0]['algorithm']
        assert data_dict.get('checksum') == self.test_data3['resources'][0]['hash']
        assert data_dict.get('mimetype') == self.test_data3['resources'][0]['mimetype']
        assert not data_dict.get('direct_download_URL')

    def test_resource_handling_2(self):
        data_dict = copy.deepcopy(self.test_data3)
        utils.resource_to_dataset(data_dict)
        assert 'direct_download_URL' in data_dict
        assert 'resources' in data_dict

        data_dict['availability'] = 'direct_download'

        utils.dataset_to_resource(data_dict)
        assert 'resources' in data_dict

        utils.resource_to_dataset(data_dict)
        assert 'resources' in data_dict

        assert data_dict.get('algorithm') == self.test_data3['resources'][0]['algorithm']
        assert data_dict.get('checksum') == self.test_data3['resources'][0]['hash']
        assert data_dict.get('mimetype') == self.test_data3['resources'][0]['mimetype']
        assert data_dict.get('direct_download_URL') == self.test_data3['resources'][0]['url']


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

    def test_get_funder(self):
        assert utils.get_funder(TEST_DATADICT)['name'] == u'R. Ahanen'

    def test_get_owner(self):
        assert utils.get_owner(TEST_DATADICT)['organisation'] == u'CSC Oy'

    def test_get_authors(self):
        assert utils.get_authors(TEST_DATADICT)[0]['name'] == u'T. Tekijä'


class TestHelpers(TestCase):
    """Unit tests for functions in helpers.py."""

    def test_get_package_ratings(self):
        (rating, stars) = helpers.get_package_ratings(TEST_DATADICT)
        assert rating == 5, rating
        assert stars == u'●●●●●'

    def test_get_package_ratings_2(self):
        data_dict = copy.deepcopy(TEST_DATADICT)
        data_dict.pop('notes')
        data_dict.pop('temporal_coverage_begin')
        data_dict.pop('discipline')
        data_dict.pop('algorithm')
        data_dict.pop('checksum')
        data_dict.pop('geographic_coverage')
        data_dict.pop('mimetype')
        data_dict['license_id'] = u''

        (rating, stars) = helpers.get_package_ratings(data_dict)
        assert rating == 3, rating
        assert stars == u'●●●○○'


class TestActions(TestCase):
    """Unit tests for action functions."""

    def test_group_list(self):
        group_list = actions.group_list({}, {})
        assert isinstance(group_list, dict)


