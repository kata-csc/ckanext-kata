# coding: utf-8
#
# pylint: disable=no-self-use, missing-docstring, too-many-public-methods, star-args

"""
Functional tests for Kata that use CKAN API.
"""

import copy
import logging
import testfixtures

from ckan.lib.helpers import url_for
from ckan.lib import search
from ckan.tests import call_action_api

from ckanext.kata import settings, utils, helpers
from ckanext.kata.tests.functional import KataApiTestCase
from ckanext.kata.tests.test_fixtures.unflattened import TEST_DATADICT, TEST_RESOURCE


class TestCreateDatasetAndResources(KataApiTestCase):
    """Tests for creating datasets and resources through API."""

    def test_create_dataset(self):
        output = call_action_api(self.app, 'package_create', apikey=self.normal_user.apikey,
                                 status=200, **TEST_DATADICT)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert output
        assert output['id'].startswith('urn:nbn:fi:csc-kata')

    def test_create_dataset_sysadmin(self):
        output = call_action_api(self.app, 'package_create', apikey=self.sysadmin_user.apikey,
                                 status=200, **TEST_DATADICT)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert output
        assert output['id'].startswith('urn:nbn:fi:csc-kata')

    def test_create_dataset_and_resources(self):
        '''
        Add a dataset and 20 resources and read dataset through API
        '''
        print 'Create dataset'
        output = call_action_api(self.app, 'package_create', apikey=self.normal_user.apikey,
                                 status=200, **TEST_DATADICT)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert 'id' in output

        new_res = copy.deepcopy(TEST_RESOURCE)
        new_res['package_id'] = output['id']

        for res_num in range(20):
            print 'Adding resource %r' % (res_num + 1)

            output = call_action_api(self.app, 'resource_create', apikey=self.normal_user.apikey,
                                     status=200, **new_res)
            if '__type' in output:
                assert output['__type'] != 'Validation Error'
            assert output

        print 'Read dataset'
        output = call_action_api(self.app, 'package_show', apikey=self.normal_user.apikey,
                                 status=200, id=new_res['package_id'])
        assert 'id' in output

        # Check that some metadata value is correct.
        assert output['checksum'] == TEST_DATADICT['checksum']

    def test_create_update_delete_dataset(self):
        '''
        Add, modify and delete a dataset through API
        '''
        print 'Create dataset'
        output = call_action_api(self.app, 'package_create', apikey=self.normal_user.apikey,
                                 status=200, **TEST_DATADICT)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert 'id' in output

        data_dict = copy.deepcopy(TEST_DATADICT)
        data_dict['id'] = output['id']

        print 'Update dataset'
        output = call_action_api(self.app, 'package_update', apikey=self.normal_user.apikey, status=200, **data_dict)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert output

        print 'Update dataset'
        output = call_action_api(self.app, 'package_update', apikey=self.normal_user.apikey, status=200, **data_dict)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert output

        print 'Delete dataset'
        output = call_action_api(self.app, 'package_delete', apikey=self.normal_user.apikey,
                                 status=200, id=data_dict['id'])

    def test_create_dataset_fails(self):
        data = copy.deepcopy(TEST_DATADICT)

        # Make sure we will get a validation error
        data.pop('langtitle')
        data.pop('language')
        data.pop('availability')

        # Hide validation error message which cannot be silenced with nosetest parameters. Has to be done here.
        logg = logging.getLogger('ckan.controllers.api')
        logg.disabled = True

        output = call_action_api(self.app, 'package_create', apikey=self.normal_user.apikey,
                                 status=409, **data)

        logg.disabled = False

        assert '__type' in output
        assert output['__type'] == 'Validation Error'

    def test_create_and_delete_resources(self):
        '''
        Add a dataset and add and delete a resource through API
        '''
        print 'Create dataset'
        output = call_action_api(self.app, 'package_create', apikey=self.normal_user.apikey,
                                 status=200, **TEST_DATADICT)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert 'id' in output

        print 'Add resource #1'
        new_res = copy.deepcopy(TEST_RESOURCE)
        new_res['package_id'] = output['id']

        output = call_action_api(self.app, 'resource_create', apikey=self.normal_user.apikey,
                                 status=200, **new_res)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert output

        res_id = output['id']

        print 'Delete resource #1'
        # For some reason this is forbidden for the user that created the resource
        output = call_action_api(self.app, 'resource_delete', apikey=self.sysadmin_user.apikey,
                                 status=200, id=res_id)
        if output is not None and '__type' in output:
            assert output['__type'] != 'Validation Error'
            
    def test_create_edit(self):
        '''
        Test and edit dataset via API. Check that immutables stay as they are.
        '''
        print 'Create dataset'
        output = call_action_api(self.app, 'package_create', apikey=self.normal_user.apikey,
                                 status=200, **TEST_DATADICT)
        
        data_dict = copy.deepcopy(TEST_DATADICT)
        
        orig_id = output['id']
        data_dict['id'] = orig_id
        output = call_action_api(self.app, 'package_update', apikey=self.normal_user.apikey, status=200, **data_dict)
        assert output['id'] == orig_id
        
        data_dict['name'] = 'new-name-123456'

        print 'Update dataset'
        
        log = logging.getLogger('ckan.controllers.api')     # pylint: disable=invalid-name
        log.disabled = True
        output = call_action_api(self.app, 'package_update', apikey=self.normal_user.apikey, status=409, **data_dict)
        log.disabled = False
        
        assert output
        assert '__type' in output
        assert output['__type'] == 'Validation Error'
        
    def test_create_dataset_invalid_agents(self):
        '''Test required fields for agents (role, name/organisation/URL)'''

        log = logging.getLogger('ckan.controllers.api')     # pylint: disable=invalid-name
        log.disabled = True

        data_dict = copy.deepcopy(TEST_DATADICT)
        data_dict['agent'][2].pop('role')
        output = call_action_api(self.app, 'package_create', apikey=self.normal_user.apikey, status=409, **data_dict)
        assert output
        assert '__type' in output
        assert output['__type'] == 'Validation Error'

        data_dict = copy.deepcopy(TEST_DATADICT)
        data_dict.pop('agent', None)
        data_dict['agent'] = [{'role': u'author'}]
        output = call_action_api(self.app, 'package_create', apikey=self.normal_user.apikey, status=409, **data_dict)
        assert output
        assert '__type' in output
        assert output['__type'] == 'Validation Error'

        log.disabled = False


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

        # Create a dataset for this test class
        call_action_api(cls.app, 'package_create', apikey=cls.normal_user.apikey,
                        status=200, **TEST_DATADICT)

    def test_search_dataset(self):
        '''
        Test that terms in TEST_SEARCH_QUERY were indexed correctly by Solr and
        that dataset is found by the terms.
        '''
        output = call_action_api(self.app, 'package_search', status=200,
                                 **{'q': 'Runoilija'})
        print(output)
        assert output['count'] == 1

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

    def _compare_datadicts(self, input, output):
        '''
        Compare a CKAN generated datadict to TEST_DATADICT
        '''

        data_dict = copy.deepcopy(input)

        # name (data pid) and title are generated so they shouldn't match
        data_dict.pop('name', None)
        data_dict.pop('title', None)

        # tag_string is converted into a list of tags, so the result won't match
        # TODO: convert both to the same format and then compare?
        data_dict.pop('tag_string', None)

        # TODO: Removed because: xpath-json converter not working
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
        output = call_action_api(self.app, 'package_create', apikey=self.normal_user.apikey,
                                 status=200, **TEST_DATADICT)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert 'id' in output

        output = call_action_api(self.app, 'package_show', apikey=self.normal_user.apikey,
                                 status=200, id=output['id'])

        # Make sure user is added as distributor
        assert [agent.get('name') for agent in output['agent']].count('tester') == 1

        assert self._compare_datadicts(TEST_DATADICT, output)

    def test_create_and_read_dataset_2(self):
        '''
        Create and read a dataset through API and check that values are correct.
        Read as a different user than dataset creator.
        '''
        output = call_action_api(self.app, 'package_create', apikey=self.sysadmin_user.apikey,
                                 status=200, **TEST_DATADICT)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert 'id' in output

        output = call_action_api(self.app, 'package_show', apikey=self.normal_user.apikey,
                                 status=200, id=output['id'])

        # Use hide_sensitive_fields() because user is not the creater of the dataset
        input = copy.deepcopy(TEST_DATADICT)
        assert self._compare_datadicts(utils.hide_sensitive_fields(input), output)

    def test_create_update_and_read_dataset(self):
        '''
        Create, update and read a dataset through API and check that values are correct
        '''
        output = call_action_api(self.app, 'package_create', apikey=self.normal_user.apikey,
                                 status=200, **TEST_DATADICT)
        assert 'id' in output
        output = call_action_api(self.app, 'package_show', apikey=self.normal_user.apikey,
                                 status=200, id=output['id'])
        output = call_action_api(self.app, 'package_update', apikey=self.normal_user.apikey,
                                 status=200, **output)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert 'id' in output

        output = call_action_api(self.app, 'package_show', apikey=self.normal_user.apikey,
                                 status=200, id=output['id'])

        # Make sure CKAN user is still present as distributor
        assert [agent.get('name') for agent in output['agent']].count('tester') == 1

        assert self._compare_datadicts(TEST_DATADICT, output)
        
    def test_secured_fields(self):
        '''
        Test that anonymous user can not read protected data
        '''
        output = call_action_api(self.app, 'package_create', apikey=self.normal_user.apikey,
                                 status=200, **TEST_DATADICT)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert 'id' in output
        
        output = call_action_api(self.app, 'package_show', status=200, id=output['id'])
        assert output

        for contact in output.get('contact', []):
            assert 'email' not in contact or \
                   contact['email'] == u'Not authorized to see this information' or \
                   contact['email'] == u'hidden'

        for funder in helpers.get_funders(output):
            assert 'fundingid' not in funder or \
                   funder['fundingid'] == u'Not authorized to see this information'

    def test_availability_changing(self):
        '''
        Test that changing availability removes unused availability URL's and dataset resource URL
        '''

        ACCESS_URL = 'http://www.csc.fi/english/'

        output = call_action_api(self.app, 'package_create', apikey=self.normal_user.apikey,
                                 status=200, **TEST_DATADICT)
        assert 'id' in output

        data_dict = copy.deepcopy(TEST_DATADICT)
        data_dict['id'] = output['id']
        data_dict['availability'] = 'access_application'
        data_dict['access_application_URL'] = ACCESS_URL

        # UPDATE AVAILABILITY

        output = call_action_api(self.app, 'package_update', apikey=self.normal_user.apikey,
                                 status=200, **data_dict)
        assert 'id' in output

        output = call_action_api(self.app, 'package_show', apikey=self.normal_user.apikey,
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

        output = call_action_api(self.app, 'package_update', apikey=self.normal_user.apikey,
                                 status=200, **output)
        assert 'id' in output

        output = call_action_api(self.app, 'package_show', apikey=self.normal_user.apikey,
                                 status=200, id=output['id'])

        assert 'access_application_URL' not in output
        assert output.get('direct_download_URL') == settings.DATASET_URL_UNKNOWN, output['direct_download_URL']

        assert output.get('availability') == 'contact_owner'

    def test_field_clearing(self):
        '''
        Test that value None will remove a field completely
        '''
        data_dict = copy.deepcopy(TEST_DATADICT)
        data_dict['discipline'] = None

        output = call_action_api(self.app, 'package_create', apikey=self.normal_user.apikey,
                                 status=200, **data_dict)
        assert 'id' in output

        data_dict['id'] = output['id']
        data_dict['discipline'] = 'Matematiikka'

        output = call_action_api(self.app, 'package_show', apikey=self.normal_user.apikey,
                                 status=200, id=data_dict['id'])
        assert 'discipline' not in output

        call_action_api(self.app, 'package_update', apikey=self.normal_user.apikey,
                        status=200, **data_dict)
        output = call_action_api(self.app, 'package_show', apikey=self.normal_user.apikey,
                                 status=200, id=data_dict['id'])
        assert 'discipline' in output

        data_dict['discipline'] = None

        call_action_api(self.app, 'package_update', apikey=self.normal_user.apikey,
                        status=200, **data_dict)
        output = call_action_api(self.app, 'package_show', apikey=self.normal_user.apikey,
                                 status=200, id=data_dict['id'])
        assert 'discipline' not in output


    def test_create_and_read_resource(self):
        '''
        Create and read resource data through API and test that 'url' matches. Availability 'through_provider'.
        '''
        data_dict = copy.deepcopy(TEST_DATADICT)
        data_dict['availability'] = 'through_provider'
        data_dict['through_provider_URL'] = 'http://www.tdata.fi/'
        data_dict.pop('direct_download_URL')

        output = call_action_api(self.app, 'package_create', apikey=self.normal_user.apikey,
                                 status=200, **data_dict)
        assert 'id' in output

        new_res = copy.deepcopy(TEST_RESOURCE)
        new_res['package_id'] = output['id']

        output = call_action_api(self.app, 'resource_create', apikey=self.normal_user.apikey,
                                 status=200, **new_res)
        assert output

        output = call_action_api(self.app, 'package_show', apikey=self.normal_user.apikey,
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
        output = call_action_api(self.app, 'package_create', apikey=self.normal_user.apikey,
                                 status=200, **TEST_DATADICT)
        assert 'id' in output

        new_res = copy.deepcopy(TEST_RESOURCE)
        new_res['package_id'] = output['id']

        output = call_action_api(self.app, 'resource_create', apikey=self.normal_user.apikey,
                                 status=200, **new_res)
        assert output

        output = call_action_api(self.app, 'package_show', apikey=self.normal_user.apikey,
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
        output = call_action_api(self.app, 'package_create', apikey=self.sysadmin_user.apikey,
                                 status=200, **TEST_DATADICT)
        assert 'id' in output

        new_res = copy.deepcopy(TEST_RESOURCE)
        new_res['package_id'] = output['id']

        output = call_action_api(self.app, 'resource_create', apikey=self.sysadmin_user.apikey,
                                 status=200, **new_res)

        call_action_api(self.app, 'resource_delete', apikey=self.sysadmin_user.apikey,
                        status=200, id=output['id'])

        output = call_action_api(self.app, 'package_show', apikey=self.sysadmin_user.apikey,
                                 status=200, id=new_res['package_id'])
        assert 'id' in output

        assert self._compare_datadicts(TEST_DATADICT, output)

    def test_create_and_read_rdf(self):
        '''
        Create and read a dataset through API and check that RDF generation doesn't break.
        '''
        output = call_action_api(self.app, 'package_create', apikey=self.sysadmin_user.apikey,
                                 status=200, **TEST_DATADICT)
        assert 'id' in output

        offset = url_for("/dataset/{0}.rdf".format(output['id']))
        res = self.app.get(offset)
        assert res.status == 200, 'Wrong HTTP status code: {0}'.format(res.status)

        # TODO: Check some fields in result rdf, like agent and pids

        # print res
        # for agent in TEST_DATADICT['agent']:
        #     assert agent.get('name') in res.body


class TestSchema(KataApiTestCase):
    '''
    Test that schema works like it's supposed to.
    '''

    def test_all_required_fields(self):
        '''
        Remove each of Kata's required fields from a complete data_dict and make sure we get a validation error.
        '''
        # Hide validation error message which cannot be silenced with nosetest parameters. Has to be done here.
        logg = logging.getLogger('ckan.controllers.api')
        logg.disabled = True

        fields = settings.KATA_FIELDS_REQUIRED

        for requirement in fields:
            print requirement
            data = TEST_DATADICT.copy()
            data.pop(requirement)

            output = call_action_api(self.app, 'package_create', apikey=self.normal_user.apikey,
                                     status=409, **data)
            assert '__type' in output
            assert output['__type'] == 'Validation Error'

        logg.disabled = False


class TestOrganizations(KataApiTestCase):
    """Tests for creating organizations and playing with them through API."""

    TEST_ORG = {
        'description': u'Description, blah blah...',
        'title': u'Test Organization',
        'image_url': u'http://192.168.56.101:5000/base/images/kata-logo.png',
        'users': [{'capacity': 'admin', 'name': u'testsysadmin'}],
        'type': 'organization',
        'name': u'testi-org'
    }

    def test_create_organization(self):
        output = call_action_api(self.app, 'organization_create', apikey=self.sysadmin_user.apikey,
                                 status=200, **self.TEST_ORG)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'

        assert output
        assert output['title'] == self.TEST_ORG['title'], output
        assert output['image_url'] == self.TEST_ORG['image_url'], output
        assert output['description'] == self.TEST_ORG['description'], output
        assert output['type'] == self.TEST_ORG['type'], output

    def test_organization_members_allowed(self):
        NEW_ORG = self.TEST_ORG
        NEW_ORG['name'] = 'new-org'

        output = call_action_api(self.app, 'organization_create', apikey=self.sysadmin_user.apikey,
                                 status=200, **NEW_ORG)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert output

        # Sysadmin can create an admin for organization
        call_action_api(self.app, 'group_member_create', apikey=self.sysadmin_user.apikey,
                                 status=200, **{'id': NEW_ORG['name'],
                                                'username': self.normal_user.name,
                                                'role': 'admin'})
        # group_member_create doesn't return anything, so no checking...

        # admin can create an editor for organization
        call_action_api(self.app, 'group_member_create', apikey=self.normal_user.apikey,
                                 status=200, **{'id': NEW_ORG['name'],
                                                'username': 'joeadmin',
                                                'role': 'editor'})

        # editor can create a member for organization
        call_action_api(self.app, 'group_member_create', apikey=self.normal_user.apikey,
                                 status=200, **{'id': NEW_ORG['name'],
                                                'username': 'annafan',
                                                'role': 'member'})

    def test_organization_members_role_changes(self):
        NEW_ORG = self.TEST_ORG
        NEW_ORG['name'] = 'newest-org'

        output = call_action_api(self.app, 'organization_create', apikey=self.sysadmin_user.apikey,
                                 status=200, **NEW_ORG)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert output

        call_action_api(self.app, 'group_member_create', apikey=self.sysadmin_user.apikey,
                                 status=200, **{'id': NEW_ORG['name'],
                                                'username': self.normal_user.name,
                                                'role': 'admin'})

        # admin can change self to editor
        call_action_api(self.app, 'group_member_create', apikey=self.normal_user.apikey,
                                 status=200, **{'id': NEW_ORG['name'],
                                                'username': self.normal_user.name,
                                                'role': 'editor'})

        # editor can not change self back to admin
        call_action_api(self.app, 'group_member_create', apikey=self.normal_user.apikey,
                                 status=403, **{'id': NEW_ORG['name'],
                                                'username': self.normal_user.name,
                                                'role': 'admin'})

        # editor can change self to member
        call_action_api(self.app, 'group_member_create', apikey=self.normal_user.apikey,
                                 status=200, **{'id': NEW_ORG['name'],
                                                'username': self.normal_user.name,
                                                'role': 'member'})

        # member can not change self back to editor
        call_action_api(self.app, 'group_member_create', apikey=self.normal_user.apikey,
                                 status=403, **{'id': NEW_ORG['name'],
                                                'username': self.normal_user.name,
                                                'role': 'editor'})
