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


class TestDatasetAndResources(unittest.TestCase):
    """Tests for adding a dataset and related functionalities."""

    @classmethod
    def setup_class(cls):
        """Set up tests."""

        kata_model.setup()
        CreateTestData.create()
        cls.sysadmin_user = model.User.get('testsysadmin')

        wsgiapp = make_app(config['global_conf'], **config['app_conf'])
        cls.app = paste.fixture.TestApp(wsgiapp)

        cls.some_resource = {'url': u'http://www.helsinki.fi',
                             'algorithm': u'SHA',
                             'hash': u'somehash',
                             'mimetype': u'application/csv',
                             'resource_type': 'file'}

        cls.test_data = {'access_application_URL': u'',
                         'access_request_URL': u'',
                         'algorithm': u'MD5',
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
                         'langtitle': [{'lang': u'fin', 'value': u'Test Data'},
                                       {'lang': u'abk', 'value': u'Title 2'},
                                       {'lang': u'swe', 'value': u'Title 3'}],
                         'language': u'eng, fin, swe',
                         'license_id': u'notspecified',
                         'maintainer': u'J. Jakelija',
                         'maintainer_email': u'j.jakelija@csc.fi',
                         'mimetype': u'application/csv',
                         'name': u'',
                         'notes': u'Vapaamuotoinen kuvaus aineistosta.',
                         'orgauth': [{'org': u'CSC Oy', 'value': u'T. Tekijä'},
                                     {'org': u'Helsingin Yliopisto', 'value': u'T. Tutkija'},
                                     {'org': u'Org 3', 'value': u'K. Kolmas'}],
                         'owner': u'Ossi Omistaja',
                         'pkg_name': u'',
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

    @classmethod
    def teardown_class(cls):
        model.repo.rebuild_db()

    def test_create_dataset(self):
        output = call_action_api(self.app, 'package_create', apikey=self.sysadmin_user.apikey,
                                status=200, **self.test_data)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert output
        assert output['id'].startswith('urn:nbn:fi:csc-kata')

    def test_create_dataset_and_resources(self):
        '''
        Add a dataset and 2 resources through API
        '''
        print 'Create dataset'
        output = call_action_api(self.app, 'package_create', apikey=self.sysadmin_user.apikey,
                                 status=200, **self.test_data)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert 'id' in output

        print 'Add resource #1'
        new_res = copy.deepcopy(self.some_resource)
        new_res['package_id'] = output['id']

        output = call_action_api(self.app, 'resource_create', apikey=self.sysadmin_user.apikey,
                                 status=200, **new_res)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert output

        print 'Add resource #2'
        output = call_action_api(self.app, 'resource_create', apikey=self.sysadmin_user.apikey,
                                 status=200, **new_res)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert output

    def test_create_update_delete_dataset(self):
        '''
        Add, modify and delete a dataset through API
        '''
        print 'Create dataset'
        output = call_action_api(self.app, 'package_create', apikey=self.sysadmin_user.apikey,
                                 status=200, **self.test_data)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert 'id' in output

        data_dict = copy.deepcopy(self.test_data)
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
        data = copy.deepcopy(self.test_data)

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
                                 status=200, **self.test_data)
        if '__type' in output:
            assert output['__type'] != 'Validation Error'
        assert 'id' in output

        print 'Add resource #1'
        new_res = copy.deepcopy(self.some_resource)
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
