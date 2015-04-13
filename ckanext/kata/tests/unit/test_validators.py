# coding: utf-8
"""
Test classes for Kata's validators.
"""

import copy
import json
from unittest import TestCase
from collections import defaultdict

from ckanext.kata.validators import validate_kata_date, \
    validate_email, validate_phonenum, \
    validate_discipline, validate_spatial, validate_algorithm, \
    validate_mimetype, validate_general, validate_kata_date_relaxed, \
    validate_title_duplicates, validate_title, check_direct_download_url, check_pids
from ckan.lib.navl.dictization_functions import Invalid, flatten_dict, StopOnError
from ckanext.kata.converters import remove_disabled_languages, checkbox_to_boolean, convert_languages, from_extras_json, to_extras_json, \
    flattened_to_extras, flattened_from_extras
from ckanext.kata import settings
from ckanext.kata.tests.test_fixtures.flattened import TEST_DATA_FLATTENED


class TestValidators(TestCase):
    """Tests for Kata validators."""

    @classmethod
    def setup_class(cls):
        """Set up tests."""

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

    def test_validate_phonenum_invalid(self):
        errors = defaultdict(list)

        dada = copy.deepcopy(TEST_DATA_FLATTENED)
        dada[('contact', 0, 'phone')] = u'123_notgood_456'

        validate_phonenum(('contact', 0, 'phone'), dada, errors, None)

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
        dada[('discipline',)] = u'Matematiikka'

        validate_discipline(('discipline',), dada, errors, None)
        assert len(errors) == 0

        del dada[('discipline',)]
        validate_discipline(('discipline',), dada, errors, None)
        assert len(errors) == 0

        dada[('discipline',)] = u'Matematiikka (Logiikka!)'
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

    def test_check_pids(self):
        errors = defaultdict(list)
        dada = copy.deepcopy(TEST_DATA_FLATTENED)

        check_pids(None, dada, errors, None)
        assert len(errors) == 0

        dada[('pids', 0, 'primary')] = u'False'
        dada[('pids', 1, 'primary')] = u'True'
        self.assertRaises(Invalid, check_pids, None, dada, errors, None)

        dada[('pids', 2, 'primary')] = u'True'

        check_pids(None, dada, errors, None)
        assert len(errors) == 0



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
        self.assertRaises(Exception, check_direct_download_url, ('resources', 0, 'url'), data, errors, None)


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

class TestLincenseConverters(TestCase):
    """Unit tests for license identification and conversion"""

    import ckanext.kata.converters as co

    @classmethod
    def setup_class(cls):
        """Set up tests."""
        cls.key=('license_id',)
        cls.test_data1 = {('license_id',): None }
        cls.test_data2 = {('license_id',): "" }
        cls.test_data3 = {('license_id',): "CC-BY-SA-4.0" }
        cls.test_data4 = {('license_id',): "https://creativecommons.org/licenses/by/4.0/"}

    def test_license_conversion(self):
        co.to_licence_id(('licence_id', 0,), )
        pass

