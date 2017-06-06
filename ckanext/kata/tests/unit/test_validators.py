# coding: utf-8
"""
Test classes for Kata's validators.
"""

import copy
import json
import random
from collections import defaultdict
from unittest import TestCase

from ckan.lib.navl.dictization_functions import Invalid, flatten_dict
from ckanext.kata import settings
from ckanext.kata.converters import remove_disabled_languages, checkbox_to_boolean, convert_languages, from_extras_json, to_extras_json, \
    flattened_to_extras, flattened_from_extras, to_license_id, gen_translation_str_from_langtitle, populate_license_URL_if_license_id_not_resolved, convert_external_id
from ckanext.kata.tests.test_fixtures.flattened import TEST_DATA_FLATTENED
from ckanext.kata.tests.test_fixtures.unflattened import TEST_DATADICT
from ckanext.kata.validators import validate_kata_date, validate_kata_interval_date, \
    validate_email, validate_phonenum, \
    validate_discipline, validate_spatial, validate_algorithm, \
    validate_mimetype, validate_general, validate_kata_date_relaxed, \
    validate_title_duplicates, validate_title, check_resource_url_for_direct_download_url, validate_access_application_url, \
    validate_license_url, validate_external_id_uniqueness, validate_primary_pid_uniqueness, \
validate_pid_relation_type, validate_pid_type, validate_package_id_format, validate_availability
from ckan.logic import get_action
import ckan.model as model
from ckanext.kata.utils import get_unique_package_id



class TestValidators(TestCase):
    """Tests for Kata validators."""

    @classmethod
    def setup_class(cls):
        pass

    def test_validate_kata_interval_date_valid(self):
        errors = defaultdict(list)
        validate_kata_interval_date('date', {'date': '2012-12-31T13:12:11/2013'}, errors, None)
        assert len(errors) == 0

    def test_validate_kata_interval_date_valid_2(self):
        errors = defaultdict(list)
        validate_kata_interval_date('date', {'date': '2012-12-31T13:12:11/2013-01-01'}, errors, None)
        assert len(errors) == 0

    def test_validate_kata_interval_date_valid_3(self):
        errors = defaultdict(list)
        validate_kata_interval_date('date', {'date': '2012-12-31T13:12:11/2013-01-01T12:00:00Z'}, errors, None)
        assert len(errors) == 0

    def test_validate_kata_interval_date_invalid(self):
        errors = defaultdict(list)
        validate_kata_interval_date('date', {'date': '2012-12-31T13:12:11/'}, errors, None)
        assert len(errors) > 0

    def test_validate_kata_interval_date_invalid_2(self):
        errors = defaultdict(list)
        validate_kata_interval_date('date', {'date': '2012-12-31T13:12:11/ABC'}, errors, None)
        assert len(errors) > 0

    def test_validate_kata_interval_date_invalid_3(self):
        errors = defaultdict(list)
        validate_kata_interval_date('date', {'date': '2012-12-31T13:12:11/2011-01-01T12:00:00Z'}, errors, None)
        assert len(errors) > 0

    def test_validate_kata_interval_date_invalid_4(self):
        errors = defaultdict(list)
        validate_kata_interval_date('date', {'date': '2012-12-31/T13:12:11'}, errors, None)
        assert len(errors) > 0

    def test_validate_kata_date_valid(self):
        errors = defaultdict(list)
        validate_kata_date('date', {'date': '2012-12-31T13:12:11'}, errors, None)
        assert len(errors) == 0

    def test_validate_kata_date_invalid(self):
        errors = defaultdict(list)
        validate_kata_date('date', {'date': '20xx-xx-31T13:12:11'}, errors, None)
        assert len(errors) > 0

    def test_validate_kata_date_invalid_2(self):
        errors = defaultdict(list)
        validate_kata_date('date', {'date': '2013-02-29T13:12:11'}, errors, None)
        assert len(errors) > 0

    def test_validate_kata_date_relaxed_valid(self):
        errors = defaultdict(list)
        validate_kata_date_relaxed('date', {'date': '2012-12-31T13:12:11'}, errors, None)
        assert len(errors) == 0

    def test_validate_kata_date_relaxed_valid_2(self):
        errors = defaultdict(list)
        validate_kata_date_relaxed('date', {'date': '2012-12'}, errors, None)
        assert len(errors) == 0

    def test_validate_kata_date_relaxed_valid_3(self):
        errors = defaultdict(list)
        validate_kata_date_relaxed('date', {'date': '2012-12-31'}, errors, None)
        assert len(errors) == 0

    def test_validate_kata_date_relaxed_invalid(self):
        errors = defaultdict(list)
        validate_kata_date_relaxed('date', {'date': '2001-12-45'}, errors, None)
        assert len(errors) > 0

    def test_validate_kata_date_relaxed_invalid_2(self):
        errors = defaultdict(list)
        validate_kata_date_relaxed('date', {'date': '2013-02-99T13:12:11'}, errors, None)
        assert len(errors) > 0

    def test_validate_language_valid(self):
        errors = defaultdict(list)
        convert_languages(('language',), TEST_DATA_FLATTENED, errors, None)
        assert len(errors) == 0

    def test_remove_disabled_languages_valid(self):
        errors = defaultdict(list)
        remove_disabled_languages(('language',), TEST_DATA_FLATTENED, errors, None)
        assert len(errors) == 0

    def test_validate_language_valid_2(self):
        errors = defaultdict(list)

        dada = copy.deepcopy(TEST_DATA_FLATTENED)
        dada[('language',)] = u''
        dada[('langdis',)] = 'True'

        convert_languages(('language',), dada, errors, None)
        assert len(errors) == 0

        remove_disabled_languages(('language',), dada, errors, None)
        assert len(errors) == 0

    def test_validate_language_valid_3(self):
        errors = defaultdict(list)

        dada = copy.deepcopy(TEST_DATA_FLATTENED)
        dada[('language',)] = u'fin, swe, eng, isl'
        dada[('langdis',)] = 'False'

        convert_languages(('language',), dada, errors, None)
        assert len(errors) == 0

        remove_disabled_languages(('language',), dada, errors, None)
        assert len(errors) == 0
        assert dada[('language',)] == u'fin, swe, eng, isl'

    def test_validate_language_delete(self):
        errors = defaultdict(list)

        dada = copy.deepcopy(TEST_DATA_FLATTENED)
        dada[('language',)] = u'fin, swe, eng, ita'
        dada[('langdis',)] = 'True'

        convert_languages(('language',), dada, errors, None)
        assert len(errors) == 0

        remove_disabled_languages(('language',), dada, errors, None)
        assert len(errors) == 0
        assert dada[('language',)] == u''

    def test_validate_language_invalid(self):
        errors = defaultdict(list)

        dada = copy.deepcopy(TEST_DATA_FLATTENED)
        dada[('language',)] = u'aa, ab, ac, ad, ae, af'
        dada[('langdis',)] = 'False'

        convert_languages(('language',), dada, errors, None)
        assert len(errors) == 1

    def test_validate_language_invalid_2(self):
        errors = defaultdict(list)

        dada = copy.deepcopy(TEST_DATA_FLATTENED)
        dada[('language',)] = u''
        dada[('langdis',)] = 'False'

        convert_languages(('language',), dada, errors, None)
        remove_disabled_languages(('language',), dada, errors, None)
        assert len(errors) == 1

    def test_validate_language_invalid_3(self):
        errors = defaultdict(list)

        dada = copy.deepcopy(TEST_DATA_FLATTENED)
        dada[('language',)] = u'finglish, sv, en'
        dada[('langdis',)] = 'True'

        convert_languages(('language',), dada, errors, None)
        assert len(errors) == 1

    # def test_project_valid(self):
    #     errors = defaultdict(list)
    #     dada = copy.deepcopy(self.test_data)
    #     # dada[('projdis',)] = 'False'
    #     dada[('funder',)] = u'funder'
    #     dada[('project_name',)] = u'project name'
    #     dada[('project_funding',)] = u'project_funding'
    #     dada[('project_homepage',)] = u'www.google.fi'
    #
    #     check_project_dis(('project_name',),
    #                       dada, errors, None)
    #     assert len(errors) == 0
    #     check_project_dis(('funder',),
    #                       dada, errors, None)
    #     assert len(errors) == 0
    #     check_project_dis(('project_funding',),
    #                       dada, errors, None)
    #     assert len(errors) == 0
    #     check_project_dis(('project_homepage',),
    #                       dada, errors, None)
    #     assert len(errors) == 0
    #
    # def test_project_invalid(self):
    #     errors = defaultdict(list)
    #     dada = copy.deepcopy(self.test_data)
    #     # dada[('projdis',)] = 'False'
    #     dada[('funder',)] = u''
    #     dada[('project_name',)] = u'project name'
    #     dada[('project_funding',)] = u'project_funding'
    #     dada[('project_homepage',)] = u'www.google.fi'
    #
    #     check_project_dis(('project_name',),
    #                       dada, errors, None)
    #     assert len(errors) == 0
    #     check_project_dis(('funder',),
    #                       dada, errors, None)
    #     assert len(errors) > 0
    #
    # def test_project_notgiven(self):
    #     errors = defaultdict(list)
    #     dada = copy.deepcopy(self.test_data)
    #     # dada[('projdis',)] = 'True'
    #     dada[('project_name',)] = u'project name'
    #     check_project(('project_name',),
    #                   dada, errors, None)
    #     print errors
    #     assert len(errors) > 0
    #
    def test_validate_email_valid(self):
        errors = defaultdict(list)

        validate_email(('contact', 0, 'email'), TEST_DATA_FLATTENED, errors, None)

        assert len(errors) == 0

    def test_validate_email_valid_2(self):
        errors = defaultdict(list)

        dada = copy.deepcopy(TEST_DATA_FLATTENED)
        dada[('contact', 0, 'email')] = u'a.b.c.d@e.com'

        validate_email(('contact', 0, 'email'), dada, errors, None)

        assert len(errors) == 0

    def test_validate_email_invalid(self):
        errors = defaultdict(list)

        dada = copy.deepcopy(TEST_DATA_FLATTENED)
        dada[('contact', 0, 'email')] = u'a.b.c.d'

        validate_email(('contact', 0, 'email'), dada, errors, None)

        assert len(errors) == 1

    def test_validate_email_invalid_2(self):
        errors = defaultdict(list)

        dada = copy.deepcopy(TEST_DATA_FLATTENED)
        dada[('contact', 0, 'email')] = u'a.b@com'

        validate_email(('contact', 0, 'email'), dada, errors, None)

        assert len(errors) == 1

    def test_validate_phonenum_valid(self):
        errors = defaultdict(list)
        validate_phonenum(('contact', 0, 'phone'), TEST_DATA_FLATTENED, errors, None)
        assert len(errors) == 0

    def test_validate_phonenum_valid_2(self):
        errors = defaultdict(list)
        validate_phonenum('phone', {'phone': '+61 8 82326262'}, errors, None)
        assert len(errors) == 0

    def test_validate_phonenum_valid_3(self):
        errors = defaultdict(list)
        validate_phonenum('phone', {'phone': '+61 8 8232-6262'}, errors, None)
        assert len(errors) == 0

    def test_validate_phonenum_valid_4(self):
        errors = defaultdict(list)
        validate_phonenum('phone', {'phone': '(555) 123-4567'}, errors, None)
        assert len(errors) == 0

    def test_validate_phonenum_valid_5(self):
        errors = defaultdict(list)
        validate_phonenum('phone', {'phone': '+1 555 123-4567'}, errors, None)
        assert len(errors) == 0

    def test_validate_phonenum_valid_6(self):
        errors = defaultdict(list)
        validate_phonenum('phone', {'phone': '61 (0)8 82326262'}, errors, None)
        assert len(errors) == 0

    def test_validate_phonenum_invalid(self):
        errors = defaultdict(list)
        dada = copy.deepcopy(TEST_DATA_FLATTENED)
        dada[('contact', 0, 'phone')] = u'123_notgood_456'
        validate_phonenum(('contact', 0, 'phone'), dada, errors, None)
        assert len(errors) == 1

    def test_validate_phonenum_invalid_2(self):
        errors = defaultdict(list)
        validate_phonenum('phone', {'phone': '+()1234'}, errors, None)
        assert len(errors) == 1

    def test_validate_phonenum_invalid_3(self):
        errors = defaultdict(list)
        validate_phonenum('phone', {'phone': '()1234'}, errors, None)
        assert len(errors) == 1

    def test_validate_phonenum_invalid_4(self):
        errors = defaultdict(list)
        validate_phonenum('phone', {'phone': '123('}, errors, None)
        assert len(errors) == 1

    def test_validate_phonenum_invalid_5(self):
        errors = defaultdict(list)
        validate_phonenum('phone', {'phone': '+-123'}, errors, None)
        assert len(errors) == 1

    def test_validate_phonenum_invalid_6(self):
        errors = defaultdict(list)
        validate_phonenum('phone', {'phone': '123-34(56'}, errors, None)
        assert len(errors) == 1

    def test_validate_phonenum_invalid_7(self):
        errors = defaultdict(list)
        validate_phonenum('phone', {'phone': '+23 (3) 45 (4)-22'}, errors, None)
        assert len(errors) == 1

    def test_general_validator_invalid(self):
        errors = defaultdict(list)

        dada = copy.deepcopy(TEST_DATA_FLATTENED)
        dada[('agent', 2, 'URL')] = u'http://www.<asdf123456>'

        validate_general(('agent', 2, 'URL'), dada, errors, None)
        assert len(errors) == 1

    def test_validate_discipline(self):
        errors = defaultdict(list)

        dada = copy.deepcopy(TEST_DATA_FLATTENED)
        dada[('discipline',)] = u'http://www.yso.fi/onto/okm-tieteenala/ta111'

        validate_discipline(('discipline',), dada, errors, None)
        assert len(errors) == 0

        del dada[('discipline',)]
        validate_discipline(('discipline',), dada, errors, None)
        assert len(errors) == 0

        dada[('discipline',)] = u'Matematiikka (Logiikka!)'
        self.assertRaises(Invalid, validate_discipline, ('discipline',), dada, errors, None)

        dada[('discipline',)] = u'Matematiikka'
        self.assertRaises(Invalid, validate_discipline, ('discipline',), dada, errors, None)

        dada[('discipline',)] = u'http://www.yso.fi/onto/okm-tieteenala/xyz123'
        self.assertRaises(Invalid, validate_discipline, ('discipline',), dada, errors, None)

    def test_validate_spatial(self):
        errors = defaultdict(list)

        dada = copy.deepcopy(TEST_DATA_FLATTENED)
        dada[('geographic_coverage',)] = u'Uusimaa (laani)'

        validate_spatial(('geographic_coverage',), dada, errors, None)
        assert len(errors) == 0

        del dada[('geographic_coverage',)]
        validate_spatial(('geographic_coverage',), dada, errors, None)
        assert len(errors) == 0

        dada[('geographic_coverage',)] = u'Uusimaa ([]!)'
        self.assertRaises(Invalid, validate_spatial, ('geographic_coverage',), dada, errors, None)

        # Test DCMI-point
        dada[('geographic_coverage',)] = u'DCMI-point: name=Paikka X; east=12.3456; north=78.90; elevation=9900;'
        assert len(errors) == 0

    def test_checkbox_to_boolean(self):
        errors = defaultdict(list)

        dada = copy.deepcopy(TEST_DATA_FLATTENED)
        dada[('langdis',)] = u'True'
        checkbox_to_boolean(('langdis',), dada, errors, None)
        assert dada[('langdis',)] == u'True'

        dada[('langdis',)] = u'False'
        checkbox_to_boolean(('langdis',), dada, errors, None)
        assert dada[('langdis',)] == u'False'

        dada[('langdis',)] = u'on'
        checkbox_to_boolean(('langdis',), dada, errors, None)
        assert dada[('langdis',)] == u'True'

        dada[('langdis',)] = u''
        checkbox_to_boolean(('langdis',), dada, errors, None)
        assert dada[('langdis',)] == u'False'
        
    def test_validate_duplicate_titles_valid(self):
        errors = defaultdict(list)
        dada = copy.deepcopy(TEST_DATA_FLATTENED)
        dada[('langtitle', 1, 'lang')] = u'fi'
        dada[('langtitle', 1, 'value')] = u'diedo'
        try:
            validate_title_duplicates(('langtitle', 0, 'value'), dada, errors, None)
        except:
            raise AssertionError('Duplicate titles check raised exception, it should not')
        
    def test_validate_duplicate_titles_invalid(self):
        errors = defaultdict(list)
        dada = copy.deepcopy(TEST_DATA_FLATTENED)
        dada[('langtitle', 1, 'lang')] = u'sv'
        dada[('langtitle', 1, 'value')] = u'diedo'
        self.assertRaises(Invalid, validate_title_duplicates, ('langtitle', 0, 'value'), dada, errors, None)
        
    def test_validate_title_invalid(self):
        errors = defaultdict(list)
        dada = copy.deepcopy(TEST_DATA_FLATTENED)
        dada[('langtitle', 0, 'lang')] = u''
        dada[('langtitle', 0, 'value')] = u''
        self.assertRaises(Invalid, validate_title, ('langtitle', 0, 'lang'), dada, errors, None)

    def test_license_url(self):
        errors = defaultdict(list)
        dada = copy.deepcopy(TEST_DATA_FLATTENED)
        dada[('license_id',)] = u'notspecified'
        self.assertRaises(Invalid, validate_license_url, ('license_URL',), dada, errors, None)
        dada[('license_URL',)] = u'Only usable before collision with the Andromeda galaxy.'
        validate_license_url(('license_URL',), dada, errors, None)
        assert len(errors) == 0

    def test_citation_invalid(self):
        errors = defaultdict(list)
        dada = copy.deepcopy(TEST_DATA_FLATTENED)
        dada[('citation',)] = u'<invalid>'
        validate_general(('citation',), dada, errors, None)
        assert len(errors) == 1

    def test_citation_valid(self):
        errors = defaultdict(list)
        dada = copy.deepcopy(TEST_DATA_FLATTENED)
        dada[('citation',)] = u'T. Tekijä. Test Data. 2000/01/01.'
        validate_general(('citation',), dada, errors, None)
        assert len(errors) == 0

    def test_validate_availability(self):
        errors = defaultdict(list)
        dada = copy.deepcopy(TEST_DATA_FLATTENED)
        dada[('availability',)] = u'unknown_value'

        #The below does not work since ckan url_validator wants context object
        # dada[('access_application',)] = u'access_application_other'
        # dada[('access_application_URL',)] = u'http://test.fi/url'
        # validate_access_application_url(('access_application_URL',), dada, errors, {})
        # assert len(errors) == 0

        self.assertRaises(Invalid, validate_availability, ('availability',), dada, errors, {})

    def test_validate_pid_relation_type(self):
        errors = defaultdict(list)
        dada = copy.deepcopy(TEST_DATA_FLATTENED)
        # Validate with valid relation type
        validate_pid_relation_type(('pids',1,'relation'), dada, errors, None)
        assert len(errors) == 0
        # Validate with invalid relation type
        dada[('pids',1,'relation')] = u'invalid_relation_type'
        self.assertRaises(Invalid, validate_pid_relation_type, ('pids',1,'relation'), dada, errors, {})

    def test_validate_pid_type(self):
        errors = defaultdict(list)
        dada = copy.deepcopy(TEST_DATA_FLATTENED)
        # Validate with type as relation and having a relation value
        validate_pid_type(('pids', 1, 'type'), dada, errors, None)
        assert len(errors) == 0
        # Validate with invalid relation type
        dada[('pids', 1, 'relation')] = None
        self.assertRaises(Invalid, validate_pid_type, ('pids', 1, 'type'), dada, errors, {})

    def test_validate_package_id_format(self):
        errors = defaultdict(list)
        dada = copy.deepcopy(TEST_DATA_FLATTENED)
        dada[('id',)] = u'invalid_package_id_format'
        self.assertRaises(Invalid, validate_package_id_format, ('id',), dada, errors, {})

    def test_convert_external_id(self):
        errors = defaultdict(list)
        dada = copy.deepcopy(TEST_DATA_FLATTENED)
        package_id = 'urn:nbn:fi:csc-kata29387492874'
        dada[('id',)] = package_id
        dada[('availability',)] = 'access_application_rems'
        convert_external_id(('external_id',), dada, errors, None)
        assert dada[('id',)] == dada[('external_id',)]


class TestPidUniquenessValidator(TestCase):
    '''
    Test pid uniqueness validator
    '''

    @classmethod
    def setup_class(cls):
        model.User(name="test_sysadmin", sysadmin=True).save()
        cls.organization = get_action('organization_create')({'user': 'test_sysadmin'},
                                                         {'name': 'test-organization', 'title': "Test organization"})

    @classmethod
    def teardown_class(cls):
        model.repo.rebuild_db()

    def _get_flat_data(self):
        flat_dada = copy.deepcopy(TEST_DATA_FLATTENED)
        return flat_dada

    def _set_flat_data_id(self, flat_data):
        flat_data[('id',)] = get_unique_package_id()

    def _get_unflattened_data(self):
        unflattened_data = copy.deepcopy(TEST_DATADICT)
        unflattened_data['owner_org'] = self.organization['name']
        return unflattened_data

    def _set_unflattened_data_id(self, unflattened_data):
        unflattened_data['id'] = get_unique_package_id()

    def _set_random_pids_for_unflattened_data(self, unflattened_data, exceptNo=0):
        for idx, pid in enumerate(unflattened_data.get('pids', [])):
            if exceptNo > 0 and idx != exceptNo:
                pid['id'] = pid.get('id') + self._get_random_no()
            else:
                pid['id'] = pid.get('id') + self._get_random_no()

    def _create_package_with_unflattened_data(self, unflattened_data):
        return get_action('package_create')({'user': 'test_sysadmin'}, unflattened_data)

    def test_validate_external_id_uniqueness(self):
        errors = defaultdict(list)
        unflattened_data = self._get_unflattened_data()
        ext_id_1 = u'urn:nbn:fi:csc-ida9238572983572398s'
        ext_id_2 = u'urn:nbn:fi:csc-ida9238572983572399s'
        flat_data = flatten_dict(copy.deepcopy(unflattened_data))
        unflattened_data['external_id'] = ext_id_1
        flat_data[('external_id',)] = ext_id_2
        self._set_unflattened_data_id(unflattened_data)
        self._set_flat_data_id(flat_data)

        # Validate against empty database == no other datasets with the same external id
        validate_external_id_uniqueness(('external_id',), flat_data, errors, None)
        assert len(errors) == 0
        self._create_package_with_unflattened_data(unflattened_data)
        # Validate against database containing one dataset that has different external id
        validate_external_id_uniqueness(('external_id',), flat_data, errors, None)
        assert len(errors) == 0
        # Validate against database containing one dataset having the same external id
        flat_data[('external_id',)] = ext_id_1
        self.assertRaises(Invalid, validate_external_id_uniqueness, ('external_id',), flat_data, errors, None)

    def test_validate_primary_pid_uniqueness(self):
        errors = defaultdict(list)
        unflattened_data = self._get_unflattened_data()
        ppid_1 = u'primary_pid_1'
        ppid_2 = u'primary_pid_2'
        flat_data = flatten_dict(copy.deepcopy(unflattened_data))
        unflattened_data['pids'][0]['id'] = ppid_1
        flat_data[('pids',0,'id')] = ppid_2
        self._set_unflattened_data_id(unflattened_data)
        self._set_flat_data_id(flat_data)

        # Validate against empty database == no other datasets with the same primary pid
        validate_primary_pid_uniqueness(('pids',0,'id'), flat_data, errors, None)
        assert len(errors) == 0
        self._create_package_with_unflattened_data(unflattened_data)
        # Validate against database containing one dataset that has different primary pid
        validate_primary_pid_uniqueness(('pids',0,'id'), flat_data, errors, None)
        assert len(errors) == 0
        # Validate against database containing one dataset having the same primary pid
        flat_data[('pids',0,'id')] = ppid_1
        self.assertRaises(Invalid, validate_primary_pid_uniqueness, ('pids',0,'id'), flat_data, errors, None)


class TestResourceValidators(TestCase):
    '''
    Test validators for resources
    '''

    @classmethod
    def setup_class(cls):
        '''
        Using the resource's format for resource validator tests
        '''
        cls.test_data = {
            'resources': [{
                'url' : u'http://www.csc.fi',
                'algorithm': u'MD5',
                'hash': u'f60e586509d99944e2d62f31979a802f',
                'mimetype': u'application/pdf',
                'resource_type' : settings.RESOURCE_TYPE_DATASET,
                }]
            }

    def test_validate_mimetype_valid(self):
        errors = defaultdict(list)

        data_dict = copy.deepcopy(self.test_data)
        data_dict['resources'][0]['format'] = u'vnd.3gpp2.bcmcsinfo+xml/'
        # flatten dict (or change test_data to flattened form?)
        data = flatten_dict(data_dict)
        try:
            validate_mimetype(('resources', 0, 'mimetype',), data, errors, None)
        except Invalid:
            raise AssertionError('Mimetype raised exception, it should not')

    def test_validate_mimetype_invalid(self):
        errors = defaultdict(list)

        data_dict = copy.deepcopy(self.test_data)
        data_dict['resources'][0]['format'] = u'application/pdf><'
        data = flatten_dict(data_dict)

        self.assertRaises(Invalid, validate_mimetype, ('resources', 0, 'format',), data, errors, None)

    def test_validate_algorithm_valid(self):
        errors = defaultdict(list)

        data_dict = copy.deepcopy(self.test_data)
        data_dict['resources'][0]['algorithm'] = u'RadioGatún-1216'
        data = flatten_dict(data_dict)

        try:
            validate_algorithm(('resources', 0, 'algorithm',), data, errors, None)
        except Invalid:
            raise AssertionError('Algorithm raised exception, it should not')

    def test_validate_algorithm_invalid(self):
        errors = defaultdict(list)

        data_dict = copy.deepcopy(self.test_data)
        data_dict['resources'][0]['algorithm'] = u'RadioGatún-1216!>'
        data = flatten_dict(data_dict)

        self.assertRaises(Invalid, validate_algorithm, ('resources', 0, 'algorithm',), data, errors, None)
        
    def test_check_direct_download_url_invalid(self):
        errors = defaultdict(list)
        dada = copy.deepcopy(self.test_data)
        dada['availability'] = u'direct_download'
        dada['resources'][0]['url'] = u''
        data = flatten_dict(dada)
        self.assertRaises(Exception, check_resource_url_for_direct_download_url, ('resources', 0, 'url'), data, errors, None)


class TestJSONConverters(TestCase):
    '''
    Test JSON converters
    '''

    PIDS = {
        u'http://helda.helsinki.fi/oai/request': {
            u'data': [u'some_data_pid', u'another_data_pid'],
            u'metadata': [u'metadata_pid', u'another_metadata_pid', u'third_metadata_pid'],
            u'version': [u'version_pid', u'another_version_pid'],
        },
        u'kata': {
            u'version': [u'kata_version_pid'],
        },
    }

    @classmethod
    def setup_class(cls):
        cls.test_data = {}
        cls.serialized = json.dumps(cls.PIDS)

        assert isinstance(cls.serialized, basestring)

    def test_from_extras_json(self):

        data = copy.deepcopy(self.test_data)
        data[('extras', '0', 'key')] = 'pids'
        data[('extras', '0', 'value')] = self.serialized

        from_extras_json(('pids',), data, {}, {})

        assert ('pids',) in data
        assert isinstance(data['pids',], dict)

    def test_to_extras_json(self):
        data = copy.deepcopy(self.test_data)
        data[('pids',)] = self.PIDS

        to_extras_json(('pids',), data, {}, {})

        assert ('extras',) in data
        assert data[('extras',)]
        assert data[('extras',)][0]['key'] == 'pids'
        assert data[('extras',)][0]['value'] == self.serialized, data[('extras',)][0]['value']

    def test_gen_translation_str_from_langtitle(self):
        data = copy.deepcopy(self.test_data)
        data[('langtitle', 0, 'lang')] = u'sv'
        data[('langtitle', 0, 'value')] = u'testdata'
        data[('langtitle', 1, 'lang')] = u'fi'
        data[('langtitle', 1, 'value')] = u'testidata'
        data[('title',)] = u''

        gen_translation_str_from_langtitle(('title',), data, {}, {})

        assert data[('title',)]

        # check that the title field contains json and is well formed
        d = data[('title',)]
        titles_json = json.loads(d)

        assert titles_json.get('sv') == 'testdata'
        assert titles_json.get('fi') == 'testidata'

        # check that the title is of type string
        assert isinstance(d, basestring)

    def test_gen_translation_str_from_langtitle2(self):
        # test that the title field is not updated, if the
        # JSON string is already given in 'title'

        json_string = '{"fin":"otsikko", "eng":"title"}'

        data = copy.deepcopy(self.test_data)
        errors = defaultdict(list)

        data[('title',)] = json_string
        gen_translation_str_from_langtitle(('title',), data, errors, {})

        assert data[('title',)]
        assert data[('title',)] == json_string

        # test that the ISO language codes are validated
        json_string = '{"fin":"otsikko", "invalid_lang_code":"title"}'
        errors = defaultdict(list)

        data[('title',)] = json_string
        gen_translation_str_from_langtitle(('title',), data, errors, {})

        assert data[('title',)]
        assert len(errors) > 0


class TestExtrasFlatteners(TestCase):

    @classmethod
    def setup_class(cls):
        pass

    def test_flattened_from_extras(self):
        data = {
            ('extras', 0, 'key'): u'pids_0_id',
            ('extras', 0, 'value'): u'first_PID',
            ('extras', 1, 'key'): u'pids_0_type',
            ('extras', 1, 'value'): u'data',
            ('extras', 2, 'key'): u'pids_0_provider',
            ('extras', 2, 'value'): u'kata',

            ('extras', 3, 'key'): u'pids_1_id',
            ('extras', 3, 'value'): u'second_PID',
            ('extras', 4, 'key'): u'pids_1_type',
            ('extras', 4, 'value'): u'version',
            ('extras', 5, 'key'): u'pids_1_provider',
            ('extras', 5, 'value'): u'ida',
            }

        flattened_from_extras(('pids',), data, None, None)

        assert ('pids',) in data
        assert len(data[('pids',)]) == 2

    def test_flattened_to_extras(self):
        data = {
            ('pids', 0, 'id'):  u'first_PID',
            ('pids', 0, 'type'): u'data',
            ('pids', 0, 'provider'): u'kata',
            ('pids', 1, 'id'):  u'second',
            ('pids', 1, 'type'): u'version',
            ('pids', 1, 'provider'): u'ida',
            }

        flattened_to_extras(('pids', 1, 'id'), data, None, None)
        flattened_to_extras(('pids', 1, 'provider'), data, None, None)
        flattened_to_extras(('pids', 1, 'type'), data, None, None)

        import pprint
        pprint.pprint(data)

        assert ('extras',) in data
        for i in [0,1,2]:
            assert data[('extras',)][i]['key'].startswith('pids_1_')
            assert data[('extras',)][i]['value'] in data.values()

class TestLicenseConverters(TestCase):
    """Unit tests for license identification and conversion"""

    @classmethod
    def setup_class(cls):
        """Set up tests."""

        cls.id_key = ('license_id',)
        cls.url_key = ('license_URL',)

        cls.test_data1 = {cls.id_key: "CLARIN_RES" }
        cls.test_data2 = {cls.id_key: "underNegotiation" }
        cls.test_data3 = {cls.id_key: "CLARIN_ACA-NC"}
        cls.test_data4 = {cls.id_key: "creative commons attribution-noncommmercial 1.0"}
        cls.test_data5 = {cls.id_key: "other"}
        cls.test_data6 = {cls.id_key: "CC-BY-NC-3.0"}
        cls.test_data7 = {cls.id_key: "CC-BY-3.0"}
        cls.test_data8 = {cls.id_key: "ApacheLicense_2.0"}
        cls.test_data9 = {cls.id_key: "CC-BY-ND-3.0"}
        cls.test_data10 = {cls.id_key: "CC-BY-SA-3.0"}
        cls.test_data11 = {cls.id_key: "CLARIN_PUB"}
        cls.test_data12 = {cls.id_key: "CLARIN_ACA"}
        cls.test_data13 = {cls.id_key: "notspecified"}
        cls.test_data14 = {cls.id_key: "CC-BY-NC-SA-3.0"}
        cls.test_data15 = {cls.id_key: "CC-BY-NC-ND-3.0"}
        cls.test_data16 = {cls.id_key: "CC-ZERO"}
        cls.test_data17 = {cls.id_key: "CC0"}
        cls.test_data18 = {cls.id_key: "CC-BY-3.0"}
        cls.test_data19 = {cls.id_key: "https://creativecommons.org/licenses/by/4.0/"}
        cls.test_data20 = {cls.id_key: "cc-by-1"}
        cls.test_data21 = {cls.id_key: "cc-by-nc-sa-3"}
        cls.test_data22 = {cls.id_key: "cc-by-nc-sa-3", cls.url_key: 'some license info'}
        cls.test_data23 = {cls.id_key: "cc-by"}
        cls.test_data24 = {cls.id_key: "badly_written_license"}
        cls.test_data25 = {cls.id_key: "badly_written_license", cls.url_key: 'some license info'}
        cls.test_data26 = {cls.id_key: "badly_written_license", cls.url_key: 'some license info'}

    def test_license_conversion(self):

        to_license_id(self.id_key, self.test_data1, {}, {})
        assert self.test_data1.get(self.id_key) == 'ClarinRES-1.0'

        to_license_id(self.id_key, self.test_data2, {}, {})
        assert self.test_data2.get(self.id_key) == 'undernegotiation'

        to_license_id(self.id_key, self.test_data3, {}, {})
        assert self.test_data3.get(self.id_key) == 'ClarinACA+NC-1.0'

        to_license_id(self.id_key, self.test_data4, {}, {})
        assert self.test_data4.get(self.id_key) == 'CC-BY-NC-1.0'

        to_license_id(self.id_key, self.test_data5, {}, {})
        assert self.test_data5.get(self.id_key) == 'other'

        to_license_id(self.id_key, self.test_data6, {}, {})
        assert self.test_data6.get(self.id_key) == 'CC-BY-NC-3.0'

        to_license_id(self.id_key, self.test_data7, {}, {})
        assert self.test_data7.get(self.id_key) == 'CC-BY-3.0'

        to_license_id(self.id_key, self.test_data8, {}, {})
        assert self.test_data8.get(self.id_key) == 'Apache-2.0'

        to_license_id(self.id_key, self.test_data9, {}, {})
        assert self.test_data9.get(self.id_key) == 'CC-BY-ND-3.0'

        to_license_id(self.id_key, self.test_data10, {}, {})
        assert self.test_data10.get(self.id_key) == 'CC-BY-SA-3.0'

        to_license_id(self.id_key, self.test_data11, {}, {})
        assert self.test_data11.get(self.id_key) == 'ClarinPUB-1.0'

        to_license_id(self.id_key, self.test_data12, {}, {})
        assert self.test_data12.get(self.id_key) == 'ClarinACA-1.0'

        to_license_id(self.id_key, self.test_data13, {}, {})
        assert self.test_data13.get(self.id_key) == 'notspecified'

        to_license_id(self.id_key, self.test_data14, {}, {})
        assert self.test_data14.get(self.id_key) == 'CC-BY-NC-SA-3.0'

        to_license_id(self.id_key, self.test_data15, {}, {})
        assert self.test_data15.get(self.id_key) == 'CC-BY-NC-ND-3.0'

        to_license_id(self.id_key, self.test_data16, {}, {})
        assert self.test_data16.get(self.id_key) == 'CC0-1.0'

        to_license_id(self.id_key, self.test_data17, {}, {})
        assert self.test_data17.get(self.id_key) == 'CC0-1.0'

        to_license_id(self.id_key, self.test_data18, {}, {})
        assert self.test_data18.get(self.id_key) == 'CC-BY-3.0'

        to_license_id(self.id_key, self.test_data19, {}, {})
        assert self.test_data19.get(self.id_key) == 'CC-BY-4.0'

        to_license_id(self.id_key, self.test_data20, {}, {})
        populate_license_URL_if_license_id_not_resolved(self.url_key, self.test_data20, {}, {})
        assert self.test_data20.get(self.id_key) == 'CC-BY-1.0'
        assert self.test_data20.get(self.url_key) is None

        populate_license_URL_if_license_id_not_resolved(self.url_key, self.test_data21, {}, {})
        to_license_id(self.id_key, self.test_data21, {}, {})
        assert self.test_data21.get(self.id_key) == 'CC-BY-NC-SA-3.0'
        assert self.test_data21.get(self.url_key) is None

        populate_license_URL_if_license_id_not_resolved(self.url_key, self.test_data22, {}, {})
        to_license_id(self.id_key, self.test_data22, {}, {})
        assert self.test_data22.get(self.id_key) == 'CC-BY-NC-SA-3.0'
        assert self.test_data22.get(self.url_key) == 'some license info'

        to_license_id(self.id_key, self.test_data23, {}, {})
        populate_license_URL_if_license_id_not_resolved(self.url_key, self.test_data23, {}, {})
        assert self.test_data23.get(self.id_key) == 'other'
        assert self.test_data23.get(self.url_key) == 'cc-by'

        populate_license_URL_if_license_id_not_resolved(self.url_key, self.test_data24, {}, {})
        to_license_id(self.id_key, self.test_data24, {}, {})
        assert self.test_data24.get(self.id_key) == 'other'
        assert self.test_data24.get(self.url_key) == 'badly_written_license'

        to_license_id(self.id_key, self.test_data25, {}, {})
        populate_license_URL_if_license_id_not_resolved(self.url_key, self.test_data25, {}, {})
        assert self.test_data25.get(self.id_key) == 'other'
        assert self.test_data25.get(self.url_key) == 'badly_written_license. some license info'

        populate_license_URL_if_license_id_not_resolved(self.url_key, self.test_data26, {}, {})
        to_license_id(self.id_key, self.test_data26, {}, {})
        assert self.test_data26.get(self.id_key) == 'other'
        assert self.test_data26.get(self.url_key) == 'badly_written_license. some license info'