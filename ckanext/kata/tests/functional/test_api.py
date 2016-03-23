# coding: utf-8
"""
Functional tests for Kata that use CKAN API.
"""

import copy

from rdflib import Graph, RDF, URIRef

import ckan.model as model
from ckan.lib import search
from ckan.lib.helpers import url_for
from ckan.logic import ValidationError, NotAuthorized
from ckanext.kata import settings, utils
from ckanext.kata.tests.functional import KataApiTestCase
from ckanext.kata.tests.test_fixtures.unflattened import TEST_RESOURCE, TEST_ORGANIZATION


class TestCreateDatasetAndResources(KataApiTestCase):
    """Tests for creating datasets and resources through API."""

    def test_create_dataset(self):
        data = copy.deepcopy(self.TEST_DATADICT)
        data = self.get_unique_pids(data)
        output = self.api_user_normal.action.package_create(**data)
        assert output
        assert output['id'].startswith('urn:nbn:fi:csc-kata')

    def test_create_dataset_without_tags(self):
        data = copy.deepcopy(self.TEST_DATADICT)
        data.pop('tag_string')

        self.assertRaises(ValidationError, self.api_user_normal.action.package_create, **data)

    def test_create_dataset_sysadmin(self):
        data = copy.deepcopy(self.TEST_DATADICT)
        data = self.get_unique_pids(data)
        output = self.api_user_sysadmin.action.package_create(**data)
        assert output
        assert output['id'].startswith('urn:nbn:fi:csc-kata')

    def test_create_dataset_and_resources(self):
        '''
        Add a dataset and 20 resources and read dataset through API
        '''
        print 'Create dataset'
        data = copy.deepcopy(self.TEST_DATADICT)
        data = self.get_unique_pids(data)
        output = self.api_user_normal.action.package_create(**data)
        assert 'id' in output

        new_res = copy.deepcopy(TEST_RESOURCE)
        new_res['package_id'] = output['id']

        for res_num in range(20):
            print 'Adding resource %r' % (res_num + 1)

            output = self.api_user_normal.call_action('resource_create', data_dict=new_res)
            assert output

        print 'Read dataset'
        output = self.api_user_normal.call_action('package_show', data_dict={'id': new_res['package_id']})
        assert 'id' in output

        # Check that data dict is correct.
        assert self._compare_datadicts(data, output)

    def test_create_update_delete_dataset(self):
        '''
        Add, modify and delete a dataset through API
        '''
        print 'Create dataset'
        data = copy.deepcopy(self.TEST_DATADICT)
        data = self.get_unique_pids(data)
        output = self.api_user_normal.action.package_create(**data)
        assert 'id' in output

        data_dict = copy.deepcopy(data)
        data_dict['id'] = output['id']

        print 'Update dataset'
        output = self.api_user_normal.call_action('package_update', data_dict=data_dict)
        assert output

        print 'Update dataset'
        output = self.api_user_normal.call_action('package_update', data_dict=data_dict)
        assert output

        print 'Delete dataset'
        self.api_user_normal.call_action('package_delete', data_dict={'id': data_dict['id']})

    def test_create_dataset_fails(self):
        data = copy.deepcopy(self.TEST_DATADICT)

        # Make sure we will get a validation error
        data.pop('langtitle', None)
        data.pop('language')
        data.pop('availability')

        self.assertRaises(ValidationError, self.api_user_normal.call_action, 'package_create', data_dict=data)

    def test_create_and_delete_resources(self):
        '''
        Add a dataset and add and delete a resource through API
        '''
        print 'Create dataset'
        output = self.api_user_normal.call_action('package_create', data_dict=self.TEST_DATADICT)
        assert 'id' in output

        print 'Add resource #1'
        new_res = copy.deepcopy(TEST_RESOURCE)
        new_res['package_id'] = output['id']

        output = self.api_user_normal.call_action('resource_create', data_dict=new_res)
        assert output

        res_id = output['id']

        print 'Delete resource #1'
        # For some reason this is forbidden for the user that created the resource
        self.api_user_normal.call_action('resource_delete', data_dict={'id': res_id})

    def test_create_edit(self):
        '''
        Test and edit dataset via API. Check that immutables stay as they are.
        '''

        data_dict = copy.deepcopy(self.TEST_DATADICT)
        data_dict = self.get_unique_pids(data_dict)
        output = self.api_user_normal.call_action('package_create', data_dict=data_dict)

        orig_id = output['id']
        data_dict['id'] = orig_id
        output = self.api_user_normal.call_action('package_update', data_dict=data_dict)
        assert output['id'] == orig_id

        data_dict['name'] = 'new-name-123456'

        self.assertRaises(ValidationError, self.api_user_normal.call_action, 'package_update', data_dict=data_dict)

    def test_create_dataset_invalid_agents(self):
        '''Test required fields for agents (role, name/organisation/URL)'''

        data_dict = copy.deepcopy(self.TEST_DATADICT)
        data_dict = self.get_unique_pids(data_dict)
        data_dict['agent'][2].pop('role')

        self.assertRaises(ValidationError, self.api_user_normal.call_action, 'package_create', data_dict=data_dict)

        data_dict = copy.deepcopy(self.TEST_DATADICT)
        data_dict = self.get_unique_pids(data_dict)
        data_dict.pop('agent', None)
        data_dict['agent'] = [{'role': u'author'}]

        self.assertRaises(ValidationError, self.api_user_normal.call_action, 'package_create', data_dict=data_dict)

    def test_create_dataset_no_org(self):
        '''A user can not create a dataset with no organisation'''
        data_dict = copy.deepcopy(self.TEST_DATADICT)
        data_dict = self.get_unique_pids(data_dict)
        data_dict['owner_org'] = ''

        self.assertRaises(ValidationError, self.api_user_anna.call_action, 'package_create', data_dict=data_dict)

    def test_create_dataset_no_org_2(self):
        '''A user with organization cannot create organizationless dataset'''
        data_dict = copy.deepcopy(self.TEST_DATADICT)
        data_dict = self.get_unique_pids(data_dict)
        data_dict['owner_org'] = ''
        data_dict['name'] = 'test'

        self.assertRaises(ValidationError, self.api_user_normal.call_action, 'package_create', data_dict=data_dict)

    def test_create_public_dataset_by_member(self):
        '''Organization member can create public dataset'''
        data_dict = copy.deepcopy(self.TEST_DATADICT)
        data_dict = self.get_unique_pids(data_dict)

        self.api_user_joe.call_action('package_create', data_dict=data_dict)

    def test_create_public_dataset_by_nonmember(self):
        '''
        Anyone can create a public dataset to an organization
        '''
        data_dict = copy.deepcopy(self.TEST_DATADICT)
        data_dict = self.get_unique_pids(data_dict)
        self.api_user_anna.call_action('package_create', data_dict=data_dict)

    def test_create_public_dataset_by_editor(self):
        '''Organization editor can create public dataset'''
        data_dict = copy.deepcopy(self.TEST_DATADICT)
        data_dict = self.get_unique_pids(data_dict)

        output = self.api_user_normal.call_action('package_create', data_dict=data_dict)
        assert output

    def test_create_dataset_without_accepting_terms_of_usage(self):
        data = copy.deepcopy(self.TEST_DATADICT)
        data = self.get_unique_pids(data)
        data.pop('accept-terms')

        self.assertRaises(ValidationError, self.api_user_normal.action.package_create, **data)

    def test_create_dataset_minimal(self):
        '''
        Create minimal dataset. Tests especially API usage, a case where a user drops the non-required fields
        altogether.
        '''
        data = copy.deepcopy(self.TEST_DATADICT)
        data = self.get_unique_pids(data)
        data_dict = dict()
        for key in data:
            if key in settings.KATA_FIELDS_REQUIRED:
                data_dict[key] = data.get(key)

        data_dict['owner_org'] = u'New Horizons'
        data_dict['accept-terms'] = u'True'
        data_dict['title'] = u'{"fin": "Pluton ohitus 14.7.2015", "eng": "Passing Pluto 14.7.2015"}'
        data_dict['version'] = u'2015-07-14T14:50:00+03:00'
        data_dict['availability'] = u'direct_download'
        data_dict['direct_download_URL'] = u'https://www.nasa.gov/mission_pages/newhorizons/main/index.html'
        data_dict['tag_string'] = u'Space probe,New Horizons,Pluto,Charon,Space exploration,Solar system'
        data_dict['license_id'] = u'cc-by'
        data_dict['private'] = u'False'

        output = self.api_user_anna.call_action('package_create', data_dict=data_dict)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'

        data_dict['private'] = u'True'
        output = self.api_user_anna.call_action('package_create', data_dict=data_dict)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'


class TestUpdateDataset(KataApiTestCase):
    """Tests for (mainly) dataset updating."""

    def test_update_by_data_pid(self):
        '''Update a dataset by using it's data PID instead of id or name'''

        data_dict = copy.deepcopy(self.TEST_DATADICT)
        data_dict = self.get_unique_pids(data_dict)
        self.api_user_normal.call_action('package_create', data_dict=data_dict)

        data_dict['langnotes'] = [
            {'lang': 'eng', 'value': 'A new description'}
        ]

        output = self.api_user_normal.call_action('package_update', data_dict=data_dict)

        self.api_user_normal.call_action('package_show', data_dict=dict(id=output['id']))

        assert output['notes'] == '{"eng": "A new description"}'

    def test_update_by_data_pid_fail(self):
        '''Try to update a dataset with wrong PIDs'''

        data_dict = copy.deepcopy(self.TEST_DATADICT)
        data_dict['pids'] = [{'id': unicode(x), 'type': 'data'} for x in range(1, 9)]

        self.assertRaises(ValidationError, self.api_user_normal.call_action, 'package_update', data_dict=data_dict)


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

        data_dict = copy.deepcopy(cls.TEST_DATADICT)  # Create public dataset

        # Create a dataset for this test class
        output = cls.api_user_sysadmin.call_action('package_create', data_dict=data_dict)

        cls.package_id = output.get('id')

    def test_search_dataset(self):
        '''
        Test that agent name was indexed correctly by Solr.
        '''
        output = self.api.call_action('package_search', data_dict={'q': 'Runoilija'})
        print(output)
        assert output['count'] == 1

        output = self.api.call_action('package_search', data_dict={'q': 'R. Runoilija'})
        print(output)
        assert output['count'] == 1

    def test_search_dataset_private(self):
        data = copy.deepcopy(self.TEST_DATADICT)
        data['id'] = self.package_id
        data['private'] = True

        # Make the dataset private
        self.api_user_normal.call_action('package_update', data_dict=data)

        output = self.api.call_action('package_search', data_dict={'q': 'Runoilija'})

        # Private dataset should not be found
        assert output['count'] == 0, output['count']

        # Make the dataset public again
        data['private'] = False
        self.api_user_normal.call_action('package_update', data_dict=data)

    def test_search_dataset_agent_id(self):
        output = self.api.call_action('package_search', data_dict={'q': 'agent:lhywrt8y08536tq3yq'})
        print(output)
        assert output['count'] == 1

    def test_search_dataset_agent_org(self):
        output = self.api.call_action('package_search', data_dict={'q': 'agent:CSC'})
        assert output['count'] == 1, output

    def test_search_dataset_agent_not_found(self):
        output = self.api.call_action('package_search', data_dict={'q': 'agent:NSA'})
        assert output['count'] == 0, output

    def test_search_dataset_funder(self):
        output = self.api.call_action('package_search', data_dict={'q': 'funder:Ahanen'})
        assert output['count'] == 1, output


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

        cls.public_dataset = copy.deepcopy(cls.TEST_DATADICT)  # Create public dataset

    def test_create_and_read_dataset(self):
        '''
        Create and read a dataset through API and check that values are correct
        '''
        data = copy.deepcopy(self.TEST_DATADICT)
        data = self.get_unique_pids(data)
        output = self.api_user_normal.action.package_create(**data)

        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert 'id' in output

        output = self.api_user_normal.action.package_show(id=output['id'])

        assert self._compare_datadicts(data, output)

    def test_create_and_read_dataset_2(self):
        '''
        Create and read a dataset through API and check that values are correct.
        Read as a different user than dataset creator.
        '''
        data = copy.deepcopy(self.public_dataset)
        data = self.get_unique_pids(data)
        output = self.api_user_normal.action.package_create(**data)

        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert 'id' in output

        output = self.api_user_anna.action.package_show(id=output['id'])

        # Use hide_sensitive_fields() because user is not the creator of the dataset
        original = copy.deepcopy(data)
        assert self._compare_datadicts(utils.hide_sensitive_fields(original), output)

    def test_create_and_read_dataset_private(self):
        '''
        Check that private dataset may not be read by other user
        '''
        data = copy.deepcopy(self.TEST_DATADICT)
        data = self.get_unique_pids(data)
        data['private'] = u'True'
        output = self.api_user_joe.action.package_create(**data)

        assert 'id' in output

        self.assertRaises(NotAuthorized, self.api_user_anna.action.package_show, id=output['id'])

    def test_create_and_update_and_read_dataset_private(self):

        data = copy.deepcopy(self.TEST_DATADICT)
        data = self.get_unique_pids(data)
        data['private'] = True
        data_dict = {
            'owner_org': u'',
            'private': u'True',
            'langtitle': [{}],
            'title': [{}]
        }

        self.assertRaises(ValidationError, self.api_user_joe.action.package_create, **data_dict)

        data_dict['owner_org'] = data['owner_org']

        self.assertRaises(ValidationError, self.api_user_joe.action.package_create, **data_dict)

        data_dict['langtitle'] = [{'lang': u'fin', 'value': u'Test Data'}]
        output = self.api_user_joe.action.package_create(**data_dict)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        data_dict['langtitle'] = [{}]
        data_dict['title'] = u'{"fin": "Test Data", "abk": "Title 2", "swe": "Title 3", "tlh": \
                  "\\u143c\\u1450\\u1464\\u1478\\u148c\\u14a0\\u14b4\\u14c8\\u14dc\\u14f0\\u1504\\u1518\\u152c"}'

        output = self.api_user_joe.action.package_create(**data_dict)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'

        output = self.api_user_joe.action.package_create(**data_dict)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        # Remove some random stuff from the dict for authentic testing experience
        data['agent'] = [{'role': u'author',
                          'name': u'T. Tekijä',
                          'organisation': u'O-Org'
                          }]
        data['accept-terms'] = u'False'
        data.pop('availability')
        data['direct_download_URL'] = u'http://'
        output = self.api_user_joe.action.package_create(**data)
        output = self.api_user_joe.action.package_show(id=output['id'])
        output = self.api_user_joe.action.package_update(**output)
        output = self.api_user_joe.action.package_show(id=output['id'])

        assert self._compare_datadicts(data, output)

    def test_create_update_and_read_dataset(self):
        '''
        Create, update and read a dataset through API and check that values are correct
        '''
        data = copy.deepcopy(self.TEST_DATADICT)
        data = self.get_unique_pids(data)
        output = self.api_user_normal.action.package_create(**data)
        output = self.api_user_normal.action.package_show(id=output['id'])

        output['accept-terms'] = 'true'
        output = self.api_user_normal.action.package_update(**output)
        output = self.api_user_normal.action.package_show(id=output['id'])

        assert self._compare_datadicts(data, output)

    def test_secured_fields(self):
        '''
        Test that anonymous user can not read protected data
        '''
        data = copy.deepcopy(self.public_dataset)
        data = self.get_unique_pids(data)
        output = self.api_user_sysadmin.action.package_create(**data)

        output = self.api.action.package_show(id=output['id'])

        for contact in output.get('contact', []):
            assert 'email' not in contact or \
                   contact['email'] == u'Not authorized to see this information' or \
                   contact['email'] == u'hidden'

    def test_availability_changing(self):
        '''
        Test that changing availability removes unused availability URL's and dataset resource URL
        '''

        ACCESS_URL = 'http://www.csc.fi/english/'
        data_dict = copy.deepcopy(self.TEST_DATADICT)
        data_dict = self.get_unique_pids(data_dict)

        output = self.api_user_normal.action.package_create(**data_dict)

        data_dict['id'] = output['id']
        data_dict['availability'] = 'access_application'
        data_dict['access_application_URL'] = ACCESS_URL

        # UPDATE AVAILABILITY

        output = self.api_user_normal.action.package_update(**data_dict)

        output = self.api_user_normal.action.package_show(id=output['id'])

        # import pprint
        # pprint.pprint(output)

        assert output.get('access_application_URL') == ACCESS_URL
        assert output.get('direct_download_URL') == settings.DATASET_URL_UNKNOWN, output['direct_download_URL']

        assert 'algorithm' in output
        assert 'checksum' in output
        assert 'mimetype' in output

        assert output.get('availability') == 'access_application'

        output['availability'] = 'contact_owner'
        output['accept-terms'] = 'yes'

        # UPDATE AVAILABILITY AGAIN

        output = self.api_user_normal.action.package_update(**output)

        output = self.api_user_normal.action.package_show(id=output['id'])

        assert 'access_application_URL' not in output
        assert output.get('direct_download_URL') == settings.DATASET_URL_UNKNOWN, output['direct_download_URL']

        assert output.get('availability') == 'contact_owner'

    def test_field_clearing(self):
        '''
        Test that value None will remove a field completely
        '''
        data_dict = copy.deepcopy(self.TEST_DATADICT)
        data_dict = self.get_unique_pids(data_dict)
        data_dict['discipline'] = None

        output = self.api_user_normal.action.package_create(**data_dict)

        data_dict['id'] = output['id']
        data_dict['discipline'] = 'Matematiikka'

        output = self.api_user_normal.action.package_show(id=data_dict['id'])
        assert 'discipline' not in output

        output = self.api_user_normal.action.package_update(**data_dict)
        output = self.api_user_normal.action.package_show(id=data_dict['id'])
        assert 'discipline' in output

        data_dict['discipline'] = None

        output = self.api_user_normal.action.package_update(**data_dict)
        output = self.api_user_normal.action.package_show(id=data_dict['id'])
        assert 'discipline' not in output

    def test_create_and_read_resource(self):
        '''
        Create and read resource data through API and test that 'url' matches. Availability 'through_provider'.
        '''
        data_dict = copy.deepcopy(self.TEST_DATADICT)
        data_dict = self.get_unique_pids(data_dict)
        data_dict['availability'] = 'through_provider'
        data_dict['through_provider_URL'] = 'http://www.tdata.fi/'
        data_dict.pop('direct_download_URL')

        output = self.api_user_normal.action.package_create(**data_dict)

        new_res = copy.deepcopy(TEST_RESOURCE)
        new_res['package_id'] = output['id']

        output = self.api_user_normal.action.resource_create(**new_res)
        output = self.api_user_normal.action.package_show(id=new_res['package_id'])

        resources = output.get('resources')
        assert len(resources) == 2
        assert resources[0]['url'] == TEST_RESOURCE['url'] or \
               resources[1]['url'] == TEST_RESOURCE['url'], resources[0]['url'] + ' --- ' + resources[1]['url']

    def test_create_and_read_resource_2(self):
        '''
        Create and read resource data through API and test that 'url' matches. Availability 'direct_download'.
        '''
        data = copy.deepcopy(self.TEST_DATADICT)
        data = self.get_unique_pids(data)
        output = self.api_user_normal.action.package_create(**data)

        new_res = copy.deepcopy(TEST_RESOURCE)
        new_res['package_id'] = output['id']

        output = self.api_user_normal.action.resource_create(**new_res)
        output = self.api_user_normal.action.package_show(id=new_res['package_id'])

        resources = output.get('resources')
        assert len(resources) == 2
        assert resources[0]['url'] == TEST_RESOURCE['url'] or \
               resources[1]['url'] == TEST_RESOURCE['url'], resources[0]['url'] + ' --- ' + resources[1]['url']

    def test_create_and_read_resource_3(self):
        '''
        Create and delete a resource data through API and test that dataset still matches.
        '''
        output = self.api_user_sysadmin.action.package_create(**self.TEST_DATADICT)

        new_res = copy.deepcopy(TEST_RESOURCE)
        new_res['package_id'] = output['id']

        output = self.api_user_sysadmin.action.resource_create(**new_res)
        output = self.api_user_sysadmin.action.resource_delete(id=output['id'])
        output = self.api_user_sysadmin.action.package_show(id=new_res['package_id'])

        assert self._compare_datadicts(self.TEST_DATADICT, output)

    def test_create_and_read_rdf(self):
        '''
        Create and read a dataset through API and check that RDF generation doesn't break.
        '''
        data = copy.deepcopy(self.public_dataset)
        data = self.get_unique_pids(data)
        output = self.api_user_sysadmin.action.package_create(**data)

        offset = url_for("/dataset/{0}.rdf".format(output['id']))
        res = self.app.get(offset)
        assert res.status == 200, 'Wrong HTTP status code: {0}'.format(res.status)

        g = Graph()
        g.parse(data=res.body)

        assert len(list(g.subjects(RDF.type, URIRef("http://www.w3.org/ns/dcat#CatalogRecord")))) == 1
        assert len(list(g.subjects(RDF.type, URIRef("http://www.w3.org/ns/dcat#Dataset")))) == 1
        assert len(list(g.subject_objects(URIRef("http://purl.org/dc/terms/contributor")))) == 2

        # Test also turtle format
        offset = url_for("/dataset/{0}.ttl".format(output['id']))
        res = self.app.get(offset)
        assert res.status == 200, 'Wrong HTTP status code: {0}'.format(res.status)


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

            self.assertRaises(ValidationError, self.api_user_normal.action.package_create, **data)


class TestOrganizationAdmin(KataApiTestCase):
    """Tests for creating organizations and playing with them through API."""

    def test_create_organization(self):
        output = self.api_user_sysadmin.action.organization_create(**TEST_ORGANIZATION)

        assert output['title'] == TEST_ORGANIZATION['title'], output
        assert output['image_url'] == TEST_ORGANIZATION['image_url'], output
        assert output['description'] == TEST_ORGANIZATION['description'], output
        assert output['type'] == TEST_ORGANIZATION['type'], output

    def test_organization_members_allowed(self):
        NEW_ORG = copy.deepcopy(TEST_ORGANIZATION)
        NEW_ORG['name'] = 'new-org'

        output = self.api_user_sysadmin.action.organization_create(**NEW_ORG)

        assert output

        # Sysadmin can create an admin for organization
        self.api_user_sysadmin.action.organization_member_create(id=NEW_ORG['name'],
                                                                 username=self.user_normal.name,
                                                                 role='admin')

        # admin can create an editor for organization
        self.api_user_normal.action.organization_member_create(id=NEW_ORG['name'],
                                                               username=self.user_joe.name,
                                                               role='editor')

        # editor can create a member for organization
        self.api_user_joe.action.organization_member_create(id=NEW_ORG['name'],
                                                            username=self.user_anna.name,
                                                            role='member')

        # editor can remove a member from organization
        self.api_user_joe.action.organization_member_delete(id=NEW_ORG['name'],
                                                            username=self.user_anna.name)

        # admin can remove an editor from organization
        self.api_user_sysadmin.action.organization_member_delete(id=NEW_ORG['name'],
                                                                 username=self.user_joe.name)

    def test_organization_members_role_changes(self):
        NEW_ORG = copy.deepcopy(TEST_ORGANIZATION)
        NEW_ORG['name'] = 'newest-org'

        self.api_user_sysadmin.action.organization_create(**NEW_ORG)

        self.api_user_sysadmin.action.organization_member_create(id=NEW_ORG['name'],
                                                                 username=self.user_normal.name,
                                                                 role='admin')

        # admin can NOT change self to editor
        self.assertRaises(NotAuthorized, self.api_user_normal.action.organization_member_create,
                          id=NEW_ORG['name'], username=self.user_normal.name, role='editor')

        # Add editor
        self.api_user_normal.action.organization_member_create(id=NEW_ORG['name'],
                                                               username=self.user_anna.name,
                                                               role='editor')

        # editor can not change self to admin
        self.assertRaises(NotAuthorized, self.api_user_anna.action.organization_member_create,
                          id=NEW_ORG['name'], username=self.user_anna.name, role='admin')

        # editor can change self to member
        self.api_user_anna.action.organization_member_create(id=NEW_ORG['name'],
                                                             username=self.user_anna.name,
                                                             role='member')

        # member can not change self back to editor
        self.assertRaises(NotAuthorized, self.api_user_anna.action.organization_member_create,
                          id=NEW_ORG['name'], username=self.user_anna.name, role='editor')

        # member can not change self back to admin
        self.assertRaises(NotAuthorized, self.api_user_anna.action.organization_member_create,
                          id=NEW_ORG['name'], username=self.user_anna.name, role='admin')

    def test_organization_members_role_changes_2(self):
        NEW_ORG = copy.deepcopy(TEST_ORGANIZATION)
        NEW_ORG['name'] = 'even-newer-org'

        self.api_user_sysadmin.action.organization_create(**NEW_ORG)

        self.api_user_sysadmin.action.organization_member_create(id=NEW_ORG['name'],
                                                                 username=self.user_normal.name,
                                                                 role='admin')

        # admin can add an editor
        self.api_user_normal.action.organization_member_create(id=NEW_ORG['name'],
                                                               username=self.user_joe.name,
                                                               role='editor')

        # admin can change editor to member
        self.api_user_normal.action.organization_member_create(id=NEW_ORG['name'],
                                                               username=self.user_joe.name,
                                                               role='member')

        # admin can change member to editor
        self.api_user_normal.action.organization_member_create(id=NEW_ORG['name'],
                                                               username=self.user_joe.name,
                                                               role='editor')

        # admin can not add admin
        self.assertRaises(NotAuthorized, self.api_user_normal.action.organization_member_create,
                          id=NEW_ORG['name'], username=self.user_anna.name, role='admin')

        # editor can not add editor
        self.assertRaises(NotAuthorized, self.api_user_joe.action.organization_member_create,
                          id=NEW_ORG['name'], username=self.user_anna.name, role='editor')

        # editor can not lower the role of admin/editor to member
        self.assertRaises(NotAuthorized, self.api_user_joe.action.organization_member_create,
                          id=NEW_ORG['name'], username=self.user_normal.name, role='member')

    def test_organization_members_sysadmin(self):
        NEW_ORG = copy.deepcopy(TEST_ORGANIZATION)
        NEW_ORG['name'] = 'most-newest-org'

        self.api_user_sysadmin.action.organization_create(**NEW_ORG)

        # Sysadmin can create an admin for organization
        self.api_user_sysadmin.action.organization_member_create(id=NEW_ORG['name'],
                                                                 username=self.user_normal.name,
                                                                 role='admin')

        # Sysadmin can lower an admin to editor
        self.api_user_sysadmin.action.organization_member_create(id=NEW_ORG['name'],
                                                                 username=self.user_normal.name,
                                                                 role='editor')

        # Sysadmin can lower an editor to member
        self.api_user_sysadmin.action.organization_member_create(id=NEW_ORG['name'],
                                                                 username=self.user_normal.name,
                                                                 role='member')

    def test_member_delete_as_sysadmin(self):
        NEW_ORG = copy.deepcopy(TEST_ORGANIZATION)
        NEW_ORG['name'] = 'test_member_delete_as_sysadmin-org'

        self.api_user_sysadmin.action.organization_create(**NEW_ORG)

        # Sysadmin can create an admin for organization
        self.api_user_sysadmin.action.organization_member_create(id=NEW_ORG['name'],
                                                                 username=self.user_normal.name,
                                                                 role='admin')

        # Sysadmin can delete an admin
        self.api_user_sysadmin.action.organization_member_delete(id=NEW_ORG['name'],
                                                                 username=self.user_normal.name)

    def test_member_delete_oneself(self):
        NEW_ORG = copy.deepcopy(TEST_ORGANIZATION)
        NEW_ORG['name'] = 'test_member_delete_oneself-org'

        self.api_user_sysadmin.action.organization_create(**NEW_ORG)

        # Sysadmin create an admin for organization
        self.api_user_sysadmin.action.organization_member_create(id=NEW_ORG['name'],
                                                                 username=self.user_normal.name,
                                                                 role='admin')

        # Admin can NOT delete herself
        self.assertRaises(NotAuthorized, self.api_user_normal.action.organization_member_delete,
                          id=NEW_ORG['name'], username=self.user_normal.name)

        # Sysadmin create an editor for organization
        self.api_user_sysadmin.action.organization_member_create(id=NEW_ORG['name'],
                                                                 username=self.user_normal.name,
                                                                 role='editor')

        # Editor can delete herself
        self.api_user_normal.action.organization_member_delete(id=NEW_ORG['name'],
                                                               username=self.user_normal.name)

    def test_organization_create_not_logged_in(self):
        NEW_ORG = copy.deepcopy(TEST_ORGANIZATION)
        NEW_ORG['name'] = 'test_organization_create_not_logged_in-org'

        self.assertRaises(NotAuthorized, self.api.action.organization_create, **NEW_ORG)

    def test_member_delete(self):
        NEW_ORG = copy.deepcopy(TEST_ORGANIZATION)
        NEW_ORG['name'] = 'test_member_delete-org'

        self.api_user_sysadmin.action.organization_create(**NEW_ORG)

        # Sysadmin can create an admin for organization
        self.api_user_sysadmin.action.organization_member_create(id=NEW_ORG['name'],
                                                                 username=self.user_normal.name,
                                                                 role='admin')

        # User without API key can not add member
        self.assertRaises(NotAuthorized, self.api.action.organization_member_create,
                          id=NEW_ORG['name'], username=self.user_anna.name, role='member')

        # User without API key can not delete member
        self.assertRaises(NotAuthorized, self.api.action.organization_member_delete,
                          id=NEW_ORG['name'], username=self.user_normal.name)

    def test_create_dataset_switch_organization(self):
        # CREATE ORGANIZATION 2
        org2 = copy.deepcopy(TEST_ORGANIZATION)
        org2['name'] = 'someorgan'

        output = self.api_user_sysadmin.action.organization_create(**org2)

        org2_id = output['id']

        # CREATE DATASET
        output = self.api_user_joe.action.package_create(**self.TEST_DATADICT)

        data_dict = output
        data_dict['accept-terms'] = 'true'
        data_dict2 = copy.deepcopy(data_dict)
        data_dict2['owner_org'] = org2_id

        # MOVE DATASET TO ORGANIZATION 2 AS SYSADMIN
        self.api_user_sysadmin.action.package_update(**data_dict2)

        # MOVE DATASET TO ORGANIZATION 1 AS MEMBER
        self.api_user_joe.action.package_update(**data_dict)

        data_dict2['private'] = u'False'

        # TRY TO MOVE DATASET TO ORGANIZATION 2 AS NON MEMBER
        self.api_user_joe.action.package_update(**data_dict2)


class TestOrganizationChangeAndCreate(KataApiTestCase):
    '''Tests for creating organizations when creating or updating the data set.

        This tests following:
             ckanext.kata.actions.package_owner_org_update()
             ckanext.kata.validators.kata_owner_org_validator()
    '''

    def test_create_owner_org_existing(self):
        '''Create dataset with some existing organization.'''

        existing_org = copy.deepcopy(TEST_ORGANIZATION)
        existing_org['title'] = 'Existing org for create'
        existing_org['name'] = 'existing-org-for-create'
        org_dict = self.api_user_sysadmin.action.organization_create(**existing_org)

        data_dict = copy.deepcopy(self.TEST_DATADICT)
        data_dict['owner_org'] = existing_org['title']
        pkg_dict = self.api_user_normal.call_action('package_create', data_dict=data_dict)

        assert pkg_dict['owner_org'] == org_dict['id'], "%s != %s" % (model.Session.query(model.Group).
                                                                      filter(model.Group.id == pkg_dict['owner_org']).
                                                                      first().title, org_dict['title'])

    def test_create_owner_org_new(self):
        '''Create dataset with a new organization.'''

        data_dict = copy.deepcopy(self.TEST_DATADICT)
        data_dict = self.get_unique_pids(data_dict)
        data_dict['title'] = u'{"fin": "A new dataset to create"}'
        data_dict['owner_org'] = 'A New Org for create'
        pkg_dict = self.api_user_joe.action.package_create(**data_dict)

        neworg = model.Session.query(model.Group).filter(model.Group.id == pkg_dict['owner_org']).first()

        assert neworg.title == data_dict['owner_org'], "%s != %s" % (neworg.title, data_dict['owner_org'])

    def test_update_owner_org_existing(self):
        '''Change owner organization to some existing organization.'''

        existing_org = copy.deepcopy(TEST_ORGANIZATION)
        existing_org['title'] = 'Existing org for update'
        existing_org['name'] = 'existing-org-for-update'
        org_dict = self.api_user_sysadmin.action.organization_create(**existing_org)

        data = copy.deepcopy(self.TEST_DATADICT)
        data = self.get_unique_pids(data)
        pkg_dict = self.api_user_normal.call_action('package_create', data_dict=data)
        pkg_dict['owner_org'] = existing_org['title']
        updated_dict = self.api_user_normal.call_action('package_update', data_dict=pkg_dict)

        assert updated_dict['owner_org'] == org_dict['id'], "%s != %s" % (updated_dict['owner_org'], org_dict['id'])

    def test_update_owner_org_new(self):
        '''Change owner organization to non-existing organization. A new
        organisation should be created.
        '''
        data = copy.deepcopy(self.TEST_DATADICT)
        data = self.get_unique_pids(data)
        output = self.api_user_normal.call_action('package_create', data_dict=data)
        output['owner_org'] = 'A Brand New Org'
        pkg_dict = self.api_user_normal.call_action('package_update', data_dict=output)
        neworg = model.Session.query(model.Group).filter(model.Group.id == pkg_dict['owner_org']).first()

        assert neworg.title == output['owner_org'], "%s != %s" % (neworg.title, output['owner_org'])
