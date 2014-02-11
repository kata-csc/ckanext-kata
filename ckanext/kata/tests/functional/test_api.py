# coding: utf-8
#
# pylint: disable=no-self-use, missing-docstring, too-many-public-methods, invalid-name, star-args

"""
Functional tests for Kata that use CKAN API.
"""

import copy
import logging

import unittest
import paste.fixture
from pylons import config
from ckan import model
from ckan.config.middleware import make_app
from ckan.lib.create_test_data import CreateTestData
from ckan.tests import call_action_api

import ckanext.kata.model as kata_model
import ckanext.kata.settings as settings

TEST_RESOURCE = {'url': u'http://www.helsinki.fi',
                     'algorithm': u'SHA',
                     'hash': u'somehash',
                     'mimetype': u'application/csv',
                     'resource_type': 'file'}

TEST_DATADICT = {'algorithm': u'MD5',
                 'availability': u'direct_download',
                 'checksum': u'f60e586509d99944e2d62f31979a802f',
                 'contact_URL': u'http://www.tdata.fi',
                 'contact_phone': u'05549583',
                 'direct_download_URL': u'http://www.tdata.fi/kata',
                 'discipline': u'Tietojenkäsittely ja informaatiotieteet',
                 'evdescr': [{'value': u'Kerätty dataa'},
                             {'value': u'Alustava julkaistu'},
                             {'value': u'Lisätty dataa'}],
                 'evtype': [{'value': u'creation'},
                            {'value': u'published'},
                            {'value': u'modified'}],
                 'evwhen': [{'value': u'2000-01-01'},
                            {'value': u'2010-04-15'},
                            {'value': u'2013-11-18'}],
                 'evwho': [{'value': u'T. Tekijä'},
                           {'value': u'J. Julkaisija'},
                           {'value': u'M. Muokkaaja'}],
                 'geographic_coverage': u'Keilaniemi (populated place),Espoo (city)',
                 'langdis': 'False',
                 'langtitle': [{u'lang': u'fin', u'value': u'Test Data'},
                               {u'lang': u'abk', u'value': u'Title 2'},
                               {u'lang': u'swe', u'value': u'Title 3'}],
                 'language': u'eng, fin, swe',
                 'license_id': u'notspecified',
                 'maintainer': u'J. Jakelija',
                 'maintainer_email': u'j.jakelija@csc.fi',
                 'mimetype': u'application/csv',
                 'name': u'',
                 'notes': u'Vapaamuotoinen kuvaus aineistosta.',
                 'orgauth': [{u'org': u'CSC Oy', u'value': u'T. Tekijä'},
                             {u'org': u'Helsingin Yliopisto', u'value': u'T. Tutkija'},
                             {u'org': u'Org 3', u'value': u'K. Kolmas'}],
                 'owner': u'Ossi Omistaja',
                 'projdis': 'False',
                 'project_funder': u'NSA',
                 'project_funding': u'1234-rahoituspäätösnumero',
                 'project_homepage': u'http://www.nsa.gov',
                 'project_name': u'Data Jakoon -projekti',
                 'tag_string': u'Python,ohjelmoitunut solukuolema,programming',
                 'temporal_coverage_begin': u'2003-07-10T06:36:27Z',
                 'temporal_coverage_end': u'2010-04-15T03:24:47Z',
                 'title': u'',
                 'type': 'dataset',
                 'version': u'2013-11-18T12:25:53Z',
                 'version_PID': u'aineiston-version-pid'}


class TestCreateDatasetAndResources(unittest.TestCase):
    """Tests for creating datasets and resources through API."""

    @classmethod
    def setup_class(cls):
        """Set up tests."""

        kata_model.setup()
        CreateTestData.create()
        cls.sysadmin_user = model.User.get('testsysadmin')

        wsgiapp = make_app(config['global_conf'], **config['app_conf'])
        cls.app = paste.fixture.TestApp(wsgiapp)

    @classmethod
    def teardown_class(cls):
        model.repo.rebuild_db()

    def test_create_dataset(self):
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
        output = call_action_api(self.app, 'package_create', apikey=self.sysadmin_user.apikey,
                                 status=200, **TEST_DATADICT)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert 'id' in output

        new_res = copy.deepcopy(TEST_RESOURCE)
        new_res['package_id'] = output['id']

        for res_num in range(20):
            print 'Adding resource %r' % (res_num + 1)

            output = call_action_api(self.app, 'resource_create', apikey=self.sysadmin_user.apikey,
                                     status=200, **new_res)
            if '__type' in output:
                assert output['__type'] != 'Validation Error'
            assert output

        print 'Read dataset'
        output = call_action_api(self.app, 'package_show', apikey=self.sysadmin_user.apikey,
                                 status=200, id=new_res['package_id'])
        assert 'id' in output
        assert 'project_name' in output

        # Check that some metadata value is correct. TODO: Check that all fields match when events format is fixed.
        assert output['project_name'] == TEST_DATADICT['project_name']

    def test_create_update_delete_dataset(self):
        '''
        Add, modify and delete a dataset through API
        '''
        print 'Create dataset'
        output = call_action_api(self.app, 'package_create', apikey=self.sysadmin_user.apikey,
                                 status=200, **TEST_DATADICT)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert 'id' in output

        data_dict = copy.deepcopy(TEST_DATADICT)
        data_dict['id'] = output['id']

        print 'Update dataset'
        output = call_action_api(self.app, 'package_update', apikey=self.sysadmin_user.apikey, status=200, **data_dict)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert output

        print 'Update dataset'
        output = call_action_api(self.app, 'package_update', apikey=self.sysadmin_user.apikey, status=200, **data_dict)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert output

        print 'Delete dataset'
        output = call_action_api(self.app, 'package_delete', apikey=self.sysadmin_user.apikey,
                                 status=200, id=data_dict['id'])

    def test_create_dataset_fails(self):
        data = copy.deepcopy(TEST_DATADICT)

        # Make sure we will get a validation error
        data.pop('langtitle')
        data.pop('language')
        data['projdis'] = u'True'

        # Hide validation error message which cannot be silenced with nosetest parameters.
        log = logging.getLogger('ckan.controllers.api')     # pylint: disable=invalid-name
        log.disabled = True

        output = call_action_api(self.app, 'package_create', apikey=self.sysadmin_user.apikey,
                                status=409, **data)
        log.disabled = False

        assert '__type' in output
        assert output['__type'] == 'Validation Error'
        assert 'projdis' in output

    def test_create_and_delete_resources(self):
        '''
        Add a dataset and add and delete a resource through API
        '''
        print 'Create dataset'
        output = call_action_api(self.app, 'package_create', apikey=self.sysadmin_user.apikey,
                                 status=200, **TEST_DATADICT)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert 'id' in output

        print 'Add resource #1'
        new_res = copy.deepcopy(TEST_RESOURCE)
        new_res['package_id'] = output['id']

        output = call_action_api(self.app, 'resource_create', apikey=self.sysadmin_user.apikey,
                                 status=200, **new_res)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert output

        res_id = output['id']

        print 'Delete resource #1'
        output = call_action_api(self.app, 'resource_delete', apikey=self.sysadmin_user.apikey,
                                 status=200, id=res_id)
        if output is not None and '__type' in output:
            assert output['__type'] != 'Validation Error'


class TestDataReading(unittest.TestCase):

    @classmethod
    def setup_class(cls):
        """Set up tests."""

        kata_model.setup()
        CreateTestData.create()
        cls.sysadmin_user = model.User.get('testsysadmin')

        wsgiapp = make_app(config['global_conf'], **config['app_conf'])
        cls.app = paste.fixture.TestApp(wsgiapp)

    @classmethod
    def teardown_class(cls):
        model.repo.rebuild_db()

    def _compare_datadicts(self, output):
        '''
        Compare a CKAN generated datadict to TEST_DATADICT
        '''

        data_dict = copy.deepcopy(TEST_DATADICT)

        # name (data pid) and title are generated so they shouldn't match
        data_dict.pop('name', None)
        data_dict.pop('title', None)

        # Events come back in different format, so skip checking them for now
        # TODO: check events when event format is fixed
        data_dict.pop('evdescr', None)
        data_dict.pop('evtype', None)
        data_dict.pop('evwho', None)
        data_dict.pop('evwhen', None)

        import pprint
        pprint.pprint( output )

        for (key, value) in data_dict.items():
            assert key in output, "Key not found: %r" % key

            output_value = output.get(key)

            assert unicode(output_value) == unicode(value), "Values for key %r not matching: %r versus %r" % (key, value, output_value)

        return True

    def test_create_and_read_dataset(self):
        '''
        Create and read a dataset through API and check that values are correct
        '''
        output = call_action_api(self.app, 'package_create', apikey=self.sysadmin_user.apikey,
                                 status=200, **TEST_DATADICT)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert 'id' in output

        output = call_action_api(self.app, 'package_show', apikey=self.sysadmin_user.apikey,
                                 status=200, id=output['id'])

        assert self._compare_datadicts(output)

    def test_create_update_and_read_dataset(self):
        '''
        Create, update and read a dataset through API and check that values are correct
        '''
        output = call_action_api(self.app, 'package_create', apikey=self.sysadmin_user.apikey,
                                 status=200, **TEST_DATADICT)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert 'id' in output

        data_dict = copy.deepcopy(TEST_DATADICT)
        data_dict['id'] = output['id']

        output = call_action_api(self.app, 'package_update', apikey=self.sysadmin_user.apikey,
                                 status=200, **data_dict)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert 'id' in output

        output = call_action_api(self.app, 'package_show', apikey=self.sysadmin_user.apikey,
                                 status=200, id=output['id'])

        assert self._compare_datadicts(output)


    def test_availability_changing(self):
        '''
        Test that changing availability removes unused availability URL's and dataset resource URL
        '''

        ACCESS_URL = 'http://www.csc.fi/english/'

        output = call_action_api(self.app, 'package_create', apikey=self.sysadmin_user.apikey,
                                 status=200, **TEST_DATADICT)
        assert 'id' in output

        data_dict = copy.deepcopy(TEST_DATADICT)
        data_dict['id'] = output['id']
        data_dict['availability'] = 'access_application'
        data_dict['access_application_URL'] = ACCESS_URL

        # UPDATE AVAILABILITY

        output = call_action_api(self.app, 'package_update', apikey=self.sysadmin_user.apikey,
                                 status=200, **data_dict)
        assert 'id' in output

        output = call_action_api(self.app, 'package_show', apikey=self.sysadmin_user.apikey,
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

        output = call_action_api(self.app, 'package_update', apikey=self.sysadmin_user.apikey,
                                 status=200, **output)
        assert 'id' in output

        output = call_action_api(self.app, 'package_show', apikey=self.sysadmin_user.apikey,
                                 status=200, id=output['id'])

        assert 'access_application_URL' not in output
        assert output.get('direct_download_URL') == settings.DATASET_URL_UNKNOWN, output['direct_download_URL']

        assert output.get('availability') == 'contact_owner'
