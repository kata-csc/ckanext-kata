# coding: utf-8
"""
Test classes for Kata CKAN Extension.
"""

import copy
from unittest import TestCase

from ckanext.harvest import model as harvest_model

from ckanext.kata.controllers import ContactController
import ckan.model as model
import ckanext.kata.actions as actions
import ckanext.kata.model as kata_model
from ckan.lib.create_test_data import CreateTestData
from ckan.logic import get_action, NotAuthorized, ValidationError, NotFound
from ckanext.kata import settings, utils
from ckanext.kata.plugin import KataPlugin
from ckanext.kata.tests.test_fixtures.unflattened import TEST_DATADICT


class TestKataPlugin(TestCase):
    """
    General tests for KataPlugin.
    """

    @classmethod
    def setup_class(cls):
        """Set up tests."""

        cls.kata_plugin = KataPlugin()

    @classmethod
    def teardown_class(cls):
        """Get away from testing environment."""
        pass

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
        pkg_dict = {'agent_0_URL': u'www.csc.fi',
                    'agent_0_fundingid': u'43096ertjgad\xf6sjgn89q3q4',
                    'agent_0_name': u'F. Under',
                    'agent_0_organisation': u'Agentti-Project',
                    'agent_0_role': u'funder',
                    'agent_1_name': u'o. oWNER',
                    'agent_1_role': u'owner',
                    'agent_2_name': u'M. Merger',
                    'agent_2_role': u'author',
                    'agent_3_name': u'juho',
                    'agent_3_role': u'distributor',
                    'data_dict': '{"dada": "dudu"}',
                    'validated_data_dict': '{"data": "dudu"}'}

        # output = self.kata_plugin.before_index(dict(data_dict=json.dumps(pkg_dict)))
        output = self.kata_plugin.before_index(pkg_dict)

        assert 'funder_0' in output
        assert 'owner_1' in output
        assert 'author_2' in output
        assert 'distributor_3' in output


class TestDatasetHandling(TestCase):
    """
    Tests for dataset handling
    """

    @classmethod
    def setup_class(cls):
        kata_model.setup()
        harvest_model.setup()

        model.User(name="test_sysadmin", sysadmin=True).save()

    @classmethod
    def teardown_class(cls):
        model.repo.rebuild_db()

    def test_add_dataset_without_name(self):
        organization = get_action('organization_create')({'user': 'test_sysadmin'},
                                                         {'name': 'test-organization', 'title': "Test organization"})

        data = copy.deepcopy(TEST_DATADICT)
        data['owner_org'] = organization['name']
        data['private'] = False

        data['name'] = ''

        pkg = get_action('package_create')({'user': 'test_sysadmin'}, data)

        assert pkg.get('name').startswith('urn')  # Should be generated from package.id
        assert pkg.get('name').count(':') == 0


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


class TestHarvestSource(TestCase):

    @classmethod
    def setup_class(cls):
        harvest_model.setup()

    def test_harvest_source_update(self):
        model.User(name='test', sysadmin=True).save()
        get_action('organization_create')({'user': 'test'}, {'name': 'test'})
        context = {'user': 'test'}
        data_dict = {'url': "http://example.com/test", 'name': 'test', 'owner_org': 'test', 'source_type': 'oai-pmh',
                     'title': 'test'}
        response = get_action('harvest_source_create')(context, data_dict)
        self.assertEquals(response.get('name', None), 'test')
        data_dict['id'] = response['id']
        data_dict['title'] = 'test update'
        response = get_action('harvest_source_update')(context, data_dict)


class TestContactController(TestCase):

    @classmethod
    def setup_class(cls):
        '''Set up testing environment.'''
        kata_model.setup()
        harvest_model.setup()

    @classmethod
    def teardown_class(cls):
        '''Get away from testing environment.'''
        kata_model.delete_tables()

    def test_pad(self):
        cc = ContactController()
        dummy_string = '0123456789abcdefghijklmno'

        for x in range(len(dummy_string)):
            assert len(cc._pad(dummy_string[:x])) == 8 + 8 * (x / 8)

