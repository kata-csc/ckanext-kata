# coding: utf-8
#
# pylint: disable=no-self-use, missing-docstring, too-many-public-methods, star-args

"""
Functional tests for Kata that use CKAN API.
"""

import copy
import testfixtures

from ckan import model
from ckan.lib.helpers import url_for
from ckan.lib import search
from ckan.tests import call_action_api

from ckanext.kata import settings, utils, helpers
from ckanext.kata.tests.functional import KataApiTestCase
from ckanext.kata.tests.test_fixtures.unflattened import TEST_RESOURCE, TEST_ORGANIZATION


class TestCreateDatasetAndResources(KataApiTestCase):
    """Tests for creating datasets and resources through API."""

    def test_create_dataset(self):
        output = call_action_api(self.app, 'package_create', apikey=self.user_normal.apikey,
                                 status=200, **self.TEST_DATADICT)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert output
        assert output['id'].startswith('urn:nbn:fi:csc-kata')

    def test_create_dataset_without_tags(self):
        data = copy.copy(self.TEST_DATADICT)
        data.pop('tag_string')

        output = call_action_api(self.app, 'package_create', apikey=self.user_normal.apikey,
                                 status=409, **data)

        self.assertTrue('__type' in output)
        self.assertEquals(output['__type'], 'Validation Error')

    def test_create_dataset_sysadmin(self):
        output = call_action_api(self.app, 'package_create', apikey=self.user_sysadmin.apikey,
                                 status=200, **self.TEST_DATADICT)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert output
        assert output['id'].startswith('urn:nbn:fi:csc-kata')

    def test_create_dataset_and_resources(self):
        '''
        Add a dataset and 20 resources and read dataset through API
        '''
        print 'Create dataset'
        output = call_action_api(self.app, 'package_create', apikey=self.user_normal.apikey,
                                 status=200, **self.TEST_DATADICT)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert 'id' in output

        new_res = copy.deepcopy(TEST_RESOURCE)
        new_res['package_id'] = output['id']

        for res_num in range(20):
            print 'Adding resource %r' % (res_num + 1)

            output = call_action_api(self.app, 'resource_create', apikey=self.user_normal.apikey,
                                     status=200, **new_res)
            if '__type' in output:
                assert output['__type'] != 'Validation Error'
            assert output

        print 'Read dataset'
        output = call_action_api(self.app, 'package_show', apikey=self.user_normal.apikey,
                                 status=200, id=new_res['package_id'])
        assert 'id' in output

        # Check that some metadata value is correct.
        assert output['checksum'] == self.TEST_DATADICT['checksum']

    def test_create_update_delete_dataset(self):
        '''
        Add, modify and delete a dataset through API
        '''
        print 'Create dataset'
        output = call_action_api(self.app, 'package_create', apikey=self.user_normal.apikey,
                                 status=200, **self.TEST_DATADICT)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert 'id' in output

        data_dict = copy.deepcopy(self.TEST_DATADICT)
        data_dict['id'] = output['id']

        print 'Update dataset'
        output = call_action_api(self.app, 'package_update', apikey=self.user_normal.apikey, status=200, **data_dict)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert output

        print 'Update dataset'
        output = call_action_api(self.app, 'package_update', apikey=self.user_normal.apikey, status=200, **data_dict)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert output

        print 'Delete dataset'
        output = call_action_api(self.app, 'package_delete', apikey=self.user_normal.apikey,
                                 status=200, id=data_dict['id'])

    def test_create_dataset_fails(self):
        data = copy.deepcopy(self.TEST_DATADICT)

        # Make sure we will get a validation error
        data.pop('langtitle')
        data.pop('language')
        data.pop('availability')

        output = call_action_api(self.app, 'package_create', apikey=self.user_normal.apikey,
                                 status=409, **data)

        assert '__type' in output
        assert output['__type'] == 'Validation Error'

    def test_create_and_delete_resources(self):
        '''
        Add a dataset and add and delete a resource through API
        '''
        print 'Create dataset'
        output = call_action_api(self.app, 'package_create', apikey=self.user_normal.apikey,
                                 status=200, **self.TEST_DATADICT)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert 'id' in output

        print 'Add resource #1'
        new_res = copy.deepcopy(TEST_RESOURCE)
        new_res['package_id'] = output['id']

        output = call_action_api(self.app, 'resource_create', apikey=self.user_normal.apikey,
                                 status=200, **new_res)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert output

        res_id = output['id']

        print 'Delete resource #1'
        # For some reason this is forbidden for the user that created the resource
        output = call_action_api(self.app, 'resource_delete', apikey=self.user_sysadmin.apikey,
                                 status=200, id=res_id)
        if output is not None and '__type' in output:
            assert output['__type'] != 'Validation Error'

    def test_create_edit(self):
        '''
        Test and edit dataset via API. Check that immutables stay as they are.
        '''
        output = call_action_api(self.app, 'package_create', apikey=self.user_normal.apikey,
                                 status=200, **self.TEST_DATADICT)

        data_dict = copy.deepcopy(self.TEST_DATADICT)

        orig_id = output['id']
        data_dict['id'] = orig_id
        output = call_action_api(self.app, 'package_update', apikey=self.user_normal.apikey, status=200, **data_dict)
        assert output['id'] == orig_id

        data_dict['name'] = 'new-name-123456'

        output = call_action_api(self.app, 'package_update', apikey=self.user_normal.apikey, status=409, **data_dict)

        assert output
        assert '__type' in output
        assert output['__type'] == 'Validation Error'

    def test_create_dataset_invalid_agents(self):
        '''Test required fields for agents (role, name/organisation/URL)'''

        data_dict = copy.deepcopy(self.TEST_DATADICT)
        data_dict['agent'][2].pop('role')
        output = call_action_api(self.app, 'package_create', apikey=self.user_normal.apikey, status=409, **data_dict)
        assert output
        assert output.get('__type') == 'Validation Error'

        data_dict = copy.deepcopy(self.TEST_DATADICT)
        data_dict.pop('agent', None)
        data_dict['agent'] = [{'role': u'author'}]
        output = call_action_api(self.app, 'package_create', apikey=self.user_normal.apikey, status=409, **data_dict)
        assert output
        assert output.get('__type') == 'Validation Error'

    def test_create_dataset_no_org(self):
        '''A user can not create a dataset with no organisation'''
        data_dict = copy.deepcopy(self.TEST_DATADICT)
        data_dict['owner_org'] = ''
        output = call_action_api(self.app, 'package_create', apikey=self.user_anna.apikey,
                        status=403, **data_dict)

    def test_create_dataset_no_org_2(self):
        '''A user with organization cannot create organizationless dataset'''
        data_dict = copy.deepcopy(self.TEST_DATADICT)
        data_dict['owner_org'] = ''
        data_dict['name'] = 'test'

        output = call_action_api(self.app, 'package_create', apikey=self.user_normal.apikey,
                                 status=409, **data_dict)
        assert output
        assert output.get('__type') == 'Validation Error'

    def test_create_public_dataset_by_member(self):
        '''Organization member can create public dataset'''
        data_dict = copy.deepcopy(self.TEST_DATADICT)
        data_dict['private'] = False

        call_action_api(self.app, 'package_create', apikey=self.user_joe.apikey, status=200, **data_dict)

    def test_create_public_dataset_by_nonmember(self):
        '''
        Anyone can create a public dataset to an organization
        '''
        data_dict = copy.deepcopy(self.TEST_DATADICT)
        data_dict['private'] = False
        call_action_api(self.app, 'package_create', apikey=self.user_anna.apikey, status=200, **data_dict)

    def test_create_public_dataset_by_editor(self):
        '''Organization editor can create public dataset'''
        data_dict = copy.deepcopy(self.TEST_DATADICT)
        data_dict['private'] = False

        output = call_action_api(self.app, 'package_create', apikey=self.user_normal.apikey, status=200, **data_dict)
        assert output


class TestUpdateDataset(KataApiTestCase):
    """Tests for (mainly) dataset updating."""

    def test_update_by_data_pid(self):
        '''Update a dataset by using it's data PID instead of id or name'''

        call_action_api(self.app, 'package_create', apikey=self.user_normal.apikey, status=200, **self.TEST_DATADICT)

        data_dict = copy.deepcopy(self.TEST_DATADICT)
        data_dict['notes'] = "A new description"
        data_dict['private'] = False

        output = call_action_api(self.app, 'package_update', apikey=self.user_normal.apikey, status=200, **data_dict)

        output = call_action_api(self.app, 'package_show', apikey=self.user_anna.apikey, status=200, id=output['id'])

        assert output['notes'] == "A new description"

    def test_update_by_data_pid_fail(self):
        '''Try to update a dataset with wrong PIDs'''

        data_dict = copy.deepcopy(self.TEST_DATADICT)
        data_dict['pids'] = [{'id': unicode(x), 'type': 'data'} for x in range(1, 9)]

        call_action_api(self.app, 'package_update', apikey=self.user_normal.apikey, status=409, **data_dict)


class TestSearchDataset(KataApiTestCase):
    '''
    Tests for checking that indexing and searching the default dataset works.
    '''

    @classmethod
    def setup_class(cls):
        '''
        Set up test class
        '''
        super(TestSearchDataset, cls).setup_class()
        search.clear()

        data_dict = copy.deepcopy(cls.TEST_DATADICT)    # Create public dataset
        data_dict['private'] = False

        # Create a dataset for this test class
        output = call_action_api(cls.app, 'package_create', apikey=cls.user_sysadmin.apikey,
                                 status=200, **data_dict)

        cls.package_id = output.get('id')

    def test_search_dataset(self):
        '''
        Test that agent name was indexed correctly by Solr.
        '''
        output = call_action_api(self.app, 'package_search', status=200,
                                 **{'q': 'Runoilija'})
        print(output)
        assert output['count'] == 1

        output = call_action_api(self.app, 'package_search', status=200,
                                 **{'q': 'R. Runoilija'})
        print(output)
        assert output['count'] == 1

    def test_search_dataset_private(self):
        data = copy.deepcopy(self.TEST_DATADICT)
        data['id'] = self.package_id
        data['private'] = True

        # Make the dataset private
        call_action_api(self.app, 'package_update', apikey=self.user_normal.apikey,
                        status=200, **data)

        output = call_action_api(self.app, 'package_search', status=200,
                                 **{'q': 'Runoilija'})

        # Private dataset should not be found
        assert output['count'] == 0, output['count']

        # Make the dataset public again
        data['private'] = False
        call_action_api(self.app, 'package_update', apikey=self.user_normal.apikey,
                        status=200, **data)

    def test_search_dataset_agent_id(self):
        output = call_action_api(self.app, 'package_search', status=200,
                                 **{'q': 'agent:lhywrt8y08536tq3yq'})
        print(output)
        assert output['count'] == 1

    def test_search_dataset_agent_org(self):
        output = call_action_api(self.app, 'package_search', status=200,
                                 **{'q': 'agent:CSC'})
        print(output)
        assert output['count'] == 1

    def test_search_dataset_agent_not_found(self):
        output = call_action_api(self.app, 'package_search', status=200,
                                 **{'q': 'agent:NSA'})
        print(output)
        assert output['count'] == 0

    def test_search_dataset_funder(self):
        output = call_action_api(self.app, 'package_search', status=200,
                                 **{'q': 'funder:Ahanen'})
        print(output)
        assert output['count'] == 1


class TestDataReading(KataApiTestCase):
    '''
    Tests for checking that values match between original data_dict and package_show output.
    '''

    @classmethod
    def setup_class(cls):
        '''
        Set up test class
        '''
        super(TestDataReading, cls).setup_class()

        cls.public_dataset = copy.deepcopy(cls.TEST_DATADICT)    # Create public dataset
        cls.public_dataset['private'] = False

    def _compare_datadicts(self, original, output):
        '''
        Compare a CKAN generated datadict to original datadict. Returns True if identical,
        otherwise throws an exception with useful output of differences.

        :param original: original datadict
        :param output: a datadict received from CKAN API
        '''

        data_dict = copy.deepcopy(original)

        # name (data pid) and title are generated so they shouldn't match
        data_dict.pop('name', None)
        data_dict.pop('title', None)

        # tag_string is converted into a list of tags, so the result won't match
        # TODO: convert both to the same format and then compare?
        data_dict.pop('tag_string', None)

        # Remove xpaths because xpath-json converter not yet implemented
        data_dict.pop('xpaths', None)

        # Remove all values that are not present in the original data_dict
        output = dict((k, v) for k, v in output.items() if k in data_dict.keys())

        # Take out automatically added distributor (CKAN user)
        output['agent'] = filter(lambda x: x.get('name') not in ['testsysadmin', 'tester'], output['agent'])

        testfixtures.compare(output, data_dict)

        return True

    def test_create_and_read_dataset(self):
        '''
        Create and read a dataset through API and check that values are correct
        '''
        output = call_action_api(self.app, 'package_create', apikey=self.user_normal.apikey,
                                 status=200, **self.TEST_DATADICT)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert 'id' in output

        output = call_action_api(self.app, 'package_show', apikey=self.user_normal.apikey,
                                 status=200, id=output['id'])

        # Make sure user is added as distributor
        assert [agent.get('name') for agent in output['agent']].count('tester') == 1

        assert self._compare_datadicts(self.TEST_DATADICT, output)

    def test_create_and_read_dataset_2(self):
        '''
        Create and read a dataset through API and check that values are correct.
        Read as a different user than dataset creator.
        '''
        output = call_action_api(self.app, 'package_create', apikey=self.user_sysadmin.apikey,
                                 status=200, **self.public_dataset)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert 'id' in output

        output = call_action_api(self.app, 'package_show', apikey=self.user_anna.apikey,
                                 status=200, id=output['id'])

        # Use hide_sensitive_fields() because user is not the creator of the dataset
        original = copy.deepcopy(self.public_dataset)
        assert self._compare_datadicts(utils.hide_sensitive_fields(original), output)

    def test_create_and_read_dataset_private(self):
        '''
        Check that private dataset may not be read by other user
        '''
        output = call_action_api(self.app, 'package_create', apikey=self.user_joe.apikey,
                                 status=200, **self.TEST_DATADICT)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert 'id' in output

        call_action_api(self.app, 'package_show', apikey=self.user_anna.apikey, status=403, id=output['id'])

    def test_create_update_and_read_dataset(self):
        '''
        Create, update and read a dataset through API and check that values are correct
        '''
        output = call_action_api(self.app, 'package_create', apikey=self.user_normal.apikey,
                                 status=200, **self.TEST_DATADICT)
        assert 'id' in output
        output = call_action_api(self.app, 'package_show', apikey=self.user_normal.apikey,
                                 status=200, id=output['id'])
        output = call_action_api(self.app, 'package_update', apikey=self.user_normal.apikey,
                                 status=200, **output)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert 'id' in output

        output = call_action_api(self.app, 'package_show', apikey=self.user_normal.apikey,
                                 status=200, id=output['id'])

        # Make sure CKAN user is still present as distributor
        assert [agent.get('name') for agent in output['agent']].count('tester') == 1

        assert self._compare_datadicts(self.TEST_DATADICT, output)

    def test_secured_fields(self):
        '''
        Test that anonymous user can not read protected data
        '''
        output = call_action_api(self.app, 'package_create', apikey=self.user_sysadmin.apikey,
                                 status=200, **self.public_dataset)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert 'id' in output

        output = call_action_api(self.app, 'package_show', status=200, id=output['id'])
        assert output

        for contact in output.get('contact', []):
            assert 'email' not in contact or \
                   contact['email'] == u'Not authorized to see this information' or \
                   contact['email'] == u'hidden'

    def test_availability_changing(self):
        '''
        Test that changing availability removes unused availability URL's and dataset resource URL
        '''

        ACCESS_URL = 'http://www.csc.fi/english/'

        output = call_action_api(self.app, 'package_create', apikey=self.user_normal.apikey,
                                 status=200, **self.TEST_DATADICT)
        assert 'id' in output

        data_dict = copy.deepcopy(self.TEST_DATADICT)
        data_dict['id'] = output['id']
        data_dict['availability'] = 'access_application'
        data_dict['access_application_URL'] = ACCESS_URL

        # UPDATE AVAILABILITY

        output = call_action_api(self.app, 'package_update', apikey=self.user_normal.apikey,
                                 status=200, **data_dict)
        assert 'id' in output

        output = call_action_api(self.app, 'package_show', apikey=self.user_normal.apikey,
                                 status=200, id=output['id'])

        # import pprint
        # pprint.pprint(output)

        assert output.get('access_application_URL') == ACCESS_URL
        assert output.get('direct_download_URL') == settings.DATASET_URL_UNKNOWN, output['direct_download_URL']

        assert 'algorithm' in output
        assert 'checksum' in output
        assert 'mimetype' in output

        assert output.get('availability') == 'access_application'

        output['availability'] = 'contact_owner'

        # UPDATE AVAILABILITY AGAIN

        output = call_action_api(self.app, 'package_update', apikey=self.user_normal.apikey,
                                 status=200, **output)
        assert 'id' in output

        output = call_action_api(self.app, 'package_show', apikey=self.user_normal.apikey,
                                 status=200, id=output['id'])

        assert 'access_application_URL' not in output
        assert output.get('direct_download_URL') == settings.DATASET_URL_UNKNOWN, output['direct_download_URL']

        assert output.get('availability') == 'contact_owner'

    def test_field_clearing(self):
        '''
        Test that value None will remove a field completely
        '''
        data_dict = copy.deepcopy(self.TEST_DATADICT)
        data_dict['discipline'] = None

        output = call_action_api(self.app, 'package_create', apikey=self.user_normal.apikey,
                                 status=200, **data_dict)
        assert 'id' in output

        data_dict['id'] = output['id']
        data_dict['discipline'] = 'Matematiikka'

        output = call_action_api(self.app, 'package_show', apikey=self.user_normal.apikey,
                                 status=200, id=data_dict['id'])
        assert 'discipline' not in output

        call_action_api(self.app, 'package_update', apikey=self.user_normal.apikey,
                        status=200, **data_dict)
        output = call_action_api(self.app, 'package_show', apikey=self.user_normal.apikey,
                                 status=200, id=data_dict['id'])
        assert 'discipline' in output

        data_dict['discipline'] = None

        call_action_api(self.app, 'package_update', apikey=self.user_normal.apikey,
                        status=200, **data_dict)
        output = call_action_api(self.app, 'package_show', apikey=self.user_normal.apikey,
                                 status=200, id=data_dict['id'])
        assert 'discipline' not in output

    def test_create_and_read_resource(self):
        '''
        Create and read resource data through API and test that 'url' matches. Availability 'through_provider'.
        '''
        data_dict = copy.deepcopy(self.TEST_DATADICT)
        data_dict['availability'] = 'through_provider'
        data_dict['through_provider_URL'] = 'http://www.tdata.fi/'
        data_dict.pop('direct_download_URL')

        output = call_action_api(self.app, 'package_create', apikey=self.user_normal.apikey,
                                 status=200, **data_dict)
        assert 'id' in output

        new_res = copy.deepcopy(TEST_RESOURCE)
        new_res['package_id'] = output['id']

        output = call_action_api(self.app, 'resource_create', apikey=self.user_normal.apikey,
                                 status=200, **new_res)
        assert output

        output = call_action_api(self.app, 'package_show', apikey=self.user_normal.apikey,
                                 status=200, id=new_res['package_id'])
        assert 'id' in output

        resources = output.get('resources')
        assert len(resources) == 2
        assert resources[0]['url'] == TEST_RESOURCE['url'] or \
            resources[1]['url'] == TEST_RESOURCE['url'], resources[0]['url'] + ' --- ' + resources[1]['url']

    def test_create_and_read_resource2(self):
        '''
        Create and read resource data through API and test that 'url' matches. Availability 'direct_download'.
        Test with sysadmin user.
        '''
        output = call_action_api(self.app, 'package_create', apikey=self.user_normal.apikey,
                                 status=200, **self.TEST_DATADICT)
        assert 'id' in output

        new_res = copy.deepcopy(TEST_RESOURCE)
        new_res['package_id'] = output['id']

        output = call_action_api(self.app, 'resource_create', apikey=self.user_normal.apikey,
                                 status=200, **new_res)
        assert output

        output = call_action_api(self.app, 'package_show', apikey=self.user_normal.apikey,
                                 status=200, id=new_res['package_id'])
        assert 'id' in output

        resources = output.get('resources')
        assert len(resources) == 2
        assert resources[0]['url'] == TEST_RESOURCE['url'] or \
            resources[1]['url'] == TEST_RESOURCE['url'], resources[0]['url'] + ' --- ' + resources[1]['url']

    def test_create_and_read_resource3(self):
        '''
        Create and delete a resource data through API and test that dataset still matches.
        '''
        output = call_action_api(self.app, 'package_create', apikey=self.user_sysadmin.apikey,
                                 status=200, **self.TEST_DATADICT)
        assert 'id' in output

        new_res = copy.deepcopy(TEST_RESOURCE)
        new_res['package_id'] = output['id']

        output = call_action_api(self.app, 'resource_create', apikey=self.user_sysadmin.apikey,
                                 status=200, **new_res)

        call_action_api(self.app, 'resource_delete', apikey=self.user_sysadmin.apikey,
                        status=200, id=output['id'])

        output = call_action_api(self.app, 'package_show', apikey=self.user_sysadmin.apikey,
                                 status=200, id=new_res['package_id'])
        assert 'id' in output

        assert self._compare_datadicts(self.TEST_DATADICT, output)

    def test_create_and_read_rdf(self):
        '''
        Create and read a dataset through API and check that RDF generation doesn't break.
        '''
        output = call_action_api(self.app, 'package_create', apikey=self.user_sysadmin.apikey,
                                 status=200, **self.public_dataset)
        assert 'id' in output

        offset = url_for("/dataset/{0}.rdf".format(output['id']))
        res = self.app.get(offset)
        assert res.status == 200, 'Wrong HTTP status code: {0}'.format(res.status)

        # TODO: Check some fields in result rdf, like agent and pids

        # print res
        # for agent in self.TEST_DATADICT['agent']:
        #     assert agent.get('name') in res.body


class TestSchema(KataApiTestCase):
    '''
    Test that schema works like it's supposed to.
    '''

    def test_all_required_fields(self):
        '''
        Remove each of Kata's required fields from a complete data_dict and make sure we get a validation error.
        '''
        fields = settings.KATA_FIELDS_REQUIRED

        for requirement in fields:
            print requirement
            data = self.TEST_DATADICT.copy()
            data.pop(requirement)

            output = call_action_api(self.app, 'package_create', apikey=self.user_normal.apikey,
                                     status=409, **data)
            assert '__type' in output
            assert output['__type'] == 'Validation Error'


class TestOrganizationAdmin(KataApiTestCase):
    """Tests for creating organizations and playing with them through API."""

    def test_create_organization(self):
        output = call_action_api(self.app, 'organization_create', apikey=self.user_sysadmin.apikey,
                                 status=200, **TEST_ORGANIZATION)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'

        assert output
        assert output['title'] == TEST_ORGANIZATION['title'], output
        assert output['image_url'] == TEST_ORGANIZATION['image_url'], output
        assert output['description'] == TEST_ORGANIZATION['description'], output
        assert output['type'] == TEST_ORGANIZATION['type'], output

    def test_organization_members_allowed(self):
        NEW_ORG = copy.deepcopy(TEST_ORGANIZATION)
        NEW_ORG['name'] = 'new-org'

        output = call_action_api(self.app, 'organization_create', apikey=self.user_sysadmin.apikey,
                                 status=200, **NEW_ORG)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert output

        # Sysadmin can create an admin for organization
        call_action_api(self.app, 'organization_member_create', apikey=self.user_sysadmin.apikey,
                                 status=200, **{'id': NEW_ORG['name'],
                                                'username': self.user_normal.name,
                                                'role': 'admin'})
        # organization_member_create doesn't return anything, so no checking...

        # admin can create an editor for organization
        call_action_api(self.app, 'organization_member_create', apikey=self.user_normal.apikey,
                                 status=200, **{'id': NEW_ORG['name'],
                                                'username': self.user_joe.name,
                                                'role': 'editor'})

        # editor can create a member for organization
        call_action_api(self.app, 'organization_member_create', apikey=self.user_joe.apikey,
                                 status=200, **{'id': NEW_ORG['name'],
                                                'username': self.user_anna.name,
                                                'role': 'member'})

        # editor can remove a member from organization
        call_action_api(self.app, 'organization_member_delete', apikey=self.user_joe.apikey,
                                 status=200, **{'id': NEW_ORG['name'],
                                                'username': self.user_anna.name})

        # admin can remove an editor from organization
        call_action_api(self.app, 'organization_member_delete', apikey=self.user_normal.apikey,
                                 status=200, **{'id': NEW_ORG['name'],
                                                'username': self.user_joe.name})

    def test_organization_members_role_changes(self):
        NEW_ORG = copy.deepcopy(TEST_ORGANIZATION)
        NEW_ORG['name'] = 'newest-org'

        output = call_action_api(self.app, 'organization_create', apikey=self.user_sysadmin.apikey,
                                 status=200, **NEW_ORG)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert output

        call_action_api(self.app, 'organization_member_create', apikey=self.user_sysadmin.apikey,
                                 status=200, **{'id': NEW_ORG['name'],
                                                'username': self.user_normal.name,
                                                'role': 'admin'})

        # admin can NOT change self to editor
        call_action_api(self.app, 'organization_member_create', apikey=self.user_normal.apikey,
                                 status=403, **{'id': NEW_ORG['name'],
                                                'username': self.user_normal.name,
                                                'role': 'editor'})

        # Add editor
        call_action_api(self.app, 'organization_member_create', apikey=self.user_normal.apikey,
                                 status=200, **{'id': NEW_ORG['name'],
                                                'username': self.user_anna.name,
                                                'role': 'editor'})

        # editor can not change self to admin
        call_action_api(self.app, 'organization_member_create', apikey=self.user_anna.apikey,
                                 status=403, **{'id': NEW_ORG['name'],
                                                'username': self.user_anna.name,
                                                'role': 'admin'})

        # editor can change self to member
        call_action_api(self.app, 'organization_member_create', apikey=self.user_anna.apikey,
                                 status=200, **{'id': NEW_ORG['name'],
                                                'username': self.user_anna.name,
                                                'role': 'member'})

        # member can not change self back to editor
        call_action_api(self.app, 'organization_member_create', apikey=self.user_anna.apikey,
                                 status=403, **{'id': NEW_ORG['name'],
                                                'username': self.user_anna.name,
                                                'role': 'editor'})

        # member can not change self back to admin
        call_action_api(self.app, 'organization_member_create', apikey=self.user_anna.apikey,
                                 status=403, **{'id': NEW_ORG['name'],
                                                'username': self.user_anna.name,
                                                'role': 'admin'})

    def test_organization_members_role_changes_2(self):
        NEW_ORG = copy.deepcopy(TEST_ORGANIZATION)
        NEW_ORG['name'] = 'even-newer-org'

        output = call_action_api(self.app, 'organization_create', apikey=self.user_sysadmin.apikey,
                                 status=200, **NEW_ORG)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert output

        call_action_api(self.app, 'organization_member_create', apikey=self.user_sysadmin.apikey,
                                 status=200, **{'id': NEW_ORG['name'],
                                                'username': self.user_normal.name,
                                                'role': 'admin'})

        # admin can add an editor
        call_action_api(self.app, 'organization_member_create', apikey=self.user_normal.apikey,
                                 status=200, **{'id': NEW_ORG['name'],
                                                'username': self.user_joe.name,
                                                'role': 'editor'})

        # admin can change editor to member
        call_action_api(self.app, 'organization_member_create', apikey=self.user_normal.apikey,
                                 status=200, **{'id': NEW_ORG['name'],
                                                'username': self.user_joe.name,
                                                'role': 'member'})

        # admin can change member to editor
        call_action_api(self.app, 'organization_member_create', apikey=self.user_normal.apikey,
                                 status=200, **{'id': NEW_ORG['name'],
                                                'username': self.user_joe.name,
                                                'role': 'editor'})

        # admin can not add admin
        call_action_api(self.app, 'organization_member_create', apikey=self.user_normal.apikey,
                                 status=403, **{'id': NEW_ORG['name'],
                                                'username': self.user_anna.name,
                                                'role': 'admin'})

        # editor can not add editor
        call_action_api(self.app, 'organization_member_create', apikey=self.user_joe.apikey,
                                 status=403, **{'id': NEW_ORG['name'],
                                                'username': self.user_anna.name,
                                                'role': 'editor'})

        # editor can not lower the role of admin/editor to member
        call_action_api(self.app, 'organization_member_create', apikey=self.user_joe.apikey,
                                 status=403, **{'id': NEW_ORG['name'],
                                                'username': self.user_normal.name,
                                                'role': 'member'})

    def test_organization_members_sysadmin(self):
        NEW_ORG = copy.deepcopy(TEST_ORGANIZATION)
        NEW_ORG['name'] = 'most-newest-org'

        output = call_action_api(self.app, 'organization_create', apikey=self.user_sysadmin.apikey,
                                 status=200, **NEW_ORG)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert output

        # Sysadmin can create an admin for organization
        call_action_api(self.app, 'organization_member_create', apikey=self.user_sysadmin.apikey,
                                 status=200, **{'id': NEW_ORG['name'],
                                                'username': self.user_normal.name,
                                                'role': 'admin'})

        # Sysadmin can lower an admin to editor
        call_action_api(self.app, 'organization_member_create', apikey=self.user_sysadmin.apikey,
                                 status=200, **{'id': NEW_ORG['name'],
                                                'username': self.user_normal.name,
                                                'role': 'editor'})

        # Sysadmin can lower an editor to member
        call_action_api(self.app, 'organization_member_create', apikey=self.user_sysadmin.apikey,
                                 status=200, **{'id': NEW_ORG['name'],
                                                'username': self.user_normal.name,
                                                'role': 'member'})

    def test_member_delete_as_sysadmin(self):
        NEW_ORG = copy.deepcopy(TEST_ORGANIZATION)
        NEW_ORG['name'] = 'test_member_delete_as_sysadmin-org'

        output = call_action_api(self.app, 'organization_create', apikey=self.user_sysadmin.apikey,
                                 status=200, **NEW_ORG)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert output

        # Sysadmin can create an admin for organization
        call_action_api(self.app, 'organization_member_create', apikey=self.user_sysadmin.apikey,
                                 status=200, **{'id': NEW_ORG['name'],
                                                'username': self.user_normal.name,
                                                'role': 'admin'})

        # Sysadmin can delete an admin
        call_action_api(self.app, 'organization_member_delete', apikey=self.user_sysadmin.apikey,
                                 status=200, **{'id': NEW_ORG['name'],
                                                'username': self.user_normal.name})

    def test_member_delete_oneself(self):
        NEW_ORG = copy.deepcopy(TEST_ORGANIZATION)
        NEW_ORG['name'] = 'test_member_delete_oneself-org'

        output = call_action_api(self.app, 'organization_create', apikey=self.user_sysadmin.apikey,
                                 status=200, **NEW_ORG)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert output

        # Sysadmin create an admin for organization
        call_action_api(self.app, 'organization_member_create', apikey=self.user_sysadmin.apikey,
                                 status=200, **{'id': NEW_ORG['name'],
                                                'username': self.user_normal.name,
                                                'role': 'admin'})

        # Admin can NOT delete herself
        call_action_api(self.app, 'organization_member_delete', apikey=self.user_normal.apikey,
                                 status=403, **{'id': NEW_ORG['name'],
                                                'username': self.user_normal.name})

        # Sysadmin create an editor for organization
        call_action_api(self.app, 'organization_member_create', apikey=self.user_sysadmin.apikey,
                                 status=200, **{'id': NEW_ORG['name'],
                                                'username': self.user_normal.name,
                                                'role': 'editor'})

        # Editor can delete herself
        call_action_api(self.app, 'organization_member_delete', apikey=self.user_normal.apikey,
                                 status=200, **{'id': NEW_ORG['name'],
                                                'username': self.user_normal.name})

    def test_organization_create_not_logged_in(self):
        NEW_ORG = copy.deepcopy(TEST_ORGANIZATION)
        NEW_ORG['name'] = 'test_organization_create_not_logged_in-org'

        output = call_action_api(self.app, 'organization_create', status=403, **NEW_ORG)

    def test_member_delete(self):
        NEW_ORG = copy.deepcopy(TEST_ORGANIZATION)
        NEW_ORG['name'] = 'test_member_delete-org'

        output = call_action_api(self.app, 'organization_create', apikey=self.user_sysadmin.apikey,
                                 status=200, **NEW_ORG)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert output

        # Sysadmin can create an admin for organization
        call_action_api(self.app, 'organization_member_create', apikey=self.user_sysadmin.apikey,
                                 status=200, **{'id': NEW_ORG['name'],
                                                'username': self.user_normal.name,
                                                'role': 'admin'})

        # Unknown user can not add member
        call_action_api(self.app, 'organization_member_create', status=403, **{'id': NEW_ORG['name'],
                                                'username': self.user_anna.name,
                                                'role': 'member'})

        # User without API key can not delete member
        call_action_api(self.app, 'organization_member_delete', status=403,
                        **{'id': NEW_ORG['name'], 'username': self.user_normal.name})

    def test_create_dataset_switch_organization(self):
        # CREATE ORGANIZATION 2
        org2 = copy.deepcopy(TEST_ORGANIZATION)
        org2['name'] = 'someorgan'
        output = call_action_api(self.app, 'organization_create', apikey=self.user_sysadmin.apikey,
                                 status=200, **org2)

        org2_id = output['id']

        # CREATE DATASET
        output = call_action_api(self.app, 'package_create', apikey=self.user_joe.apikey,
                                 status=200, **self.TEST_DATADICT)

        data_dict = output
        data_dict2 = copy.deepcopy(data_dict)
        data_dict2['owner_org'] = org2_id

        # MOVE DATASET TO ORGANIZATION 2 AS SYSADMIN
        call_action_api(self.app, 'package_update', apikey=self.user_sysadmin.apikey, status=200, **data_dict2)

        # MOVE DATASET TO ORGANIZATION 1 AS MEMBER
        call_action_api(self.app, 'package_update', apikey=self.user_joe.apikey, status=200, **data_dict)

        data_dict2['private'] = u'False'

        # TRY TO MOVE DATASET TO ORGANIZATION 2 AS NON MEMBER
        call_action_api(self.app, 'package_update', apikey=self.user_joe.apikey, status=200, **data_dict2)

