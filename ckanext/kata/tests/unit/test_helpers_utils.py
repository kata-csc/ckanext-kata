# coding: utf-8
"""
Test classes for Kata CKAN Extension.
"""

import copy
from unittest import TestCase

from ckanext.harvest import model as harvest_model

import ckan.model as model
import ckanext.kata.model as kata_model
from ckan.logic import get_action
from ckanext.kata import utils, helpers
from ckanext.kata.settings import _FIELD_TITLES
from ckanext.kata.tests.test_fixtures.unflattened import TEST_DATADICT


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

    def test_get_owners(self):
        assert helpers.get_owners(TEST_DATADICT)[0]['organisation'] == u'CSC Oy'

    def test_get_authors(self):
        assert helpers.get_authors(TEST_DATADICT)[0]['name'] == u'T. Tekijä'

    def test_get_contributors(self):
        assert helpers.get_contributors(TEST_DATADICT)[0]['name'] == u'R. Runoilija'

    def test_get_contacts(self):
        assert helpers.get_contacts(TEST_DATADICT)[0]['name'] == u'Jali Jakelija'

    def test_get_funder(self):
        assert helpers.get_funder(TEST_DATADICT)['name'] == u'R. Ahanen'

    def test_get_dataset_permanent_address(self):
        data_dict = copy.deepcopy(TEST_DATADICT)
        model.User(name="pidtest", sysadmin=True).save()
        organization = get_action('organization_create')({'user': 'pidtest'},
                                                         {'name': 'test-organization', 'title': "Test organization"})
        data_dict['owner_org'] = organization['name']
        package = get_action('package_create')({'user': 'pidtest'}, data_dict)
        self.assertTrue(helpers.get_dataset_permanent_address(package).startswith('http://urn.fi/urn:nbn:fi:csc-kata'))

    def test_convert_language_code(self):
        assert helpers.convert_language_code('fin', 'alpha2') == 'fi'
        assert helpers.convert_language_code('fin', 'alpha3') == 'fin'
        assert helpers.convert_language_code('fi', 'alpha2') == 'fi'
        assert helpers.convert_language_code('fi', 'alpha3') == 'fin'

        assert helpers.convert_language_code('eng', 'alpha2') == 'en'
        assert helpers.convert_language_code('eng', 'alpha3') == 'eng'
        assert helpers.convert_language_code('en', 'alpha2') == 'en'
        assert helpers.convert_language_code('en', 'alpha3') == 'eng'

    def test_discipline_split(self):
        '''
        RDF export would look odd if discipline splitting function would break
        '''
        disciplines = helpers.split_disciplines('Matematiikka,Fysiikka')
        assert disciplines[1] == 'Fysiikka'
        assert helpers.split_disciplines('Tiede-, taide- ja liikuntakasvatus')[
                   0] == 'Tiede-, taide- ja liikuntakasvatus'

    def test_disciplines_string_resolved(self):
        disciplines = u'Matematiikka,Fysiikka'
        assert helpers.disciplines_string_resolved(disciplines) == u'Matematiikka, Fysiikka'
        disciplines = u'http://www.yso.fi/onto/okm-tieteenala/ta111,Fysiikka'
        assert helpers.disciplines_string_resolved(disciplines, None,
                                                   'en') == u'Mathematics, Fysiikka', helpers.disciplines_string_resolved(
            disciplines, None, 'en')
        disciplines = u'http://www.yso.fi/onto/okm-tieteenala/xyz1234,Fysiikka'
        assert helpers.disciplines_string_resolved(disciplines, None,
                                                   'en') == u'http://www.yso.fi/onto/okm-tieteenala/xyz1234, Fysiikka'

    def test_get_label_for_uri(self):
        discipline = u'http://www.yso.fi/onto/okm-tieteenala/ta111'
        assert helpers.get_label_for_uri(discipline, None, 'en') == u'Mathematics'
        assert helpers.get_label_for_uri(discipline, 'okm-tieteenala', 'en') == u'Mathematics'

    def test_get_translation(self):
        translation_json = '{"fin":"otsikko", "eng":"title"}'

        translation_fi = helpers.get_translation(translation_json, 'fi')
        assert translation_fi == "otsikko"

        translation_en = helpers.get_translation(translation_json, 'en')
        assert translation_en == "title"

        # this should default to en
        translation_def_en = helpers.get_translation(translation_json, 'sv')
        assert translation_def_en == "title"

        translation_json = '{"fin":"otsikko"}'
        translation_def_fi = helpers.get_translation(translation_json, 'sv')
        assert translation_def_fi == "otsikko"

    def test_has_json_content(self):
        assert helpers.has_json_content(u'{}') is False
        assert helpers.has_json_content(None) is False
        assert helpers.has_json_content('') is False
        assert helpers.has_json_content('{"fin": ""}') is False
        assert helpers.has_json_content('{"fin": "", "eng": ""}') is False
        assert helpers.has_json_content('{"fin": "jotain"}') == True
        assert helpers.has_json_content('[1, 2, 3]') == True

    def test_multilang_to_json(self):
        datadict = {'langtitle': [{'lang': u'fin', 'value': u'foobar'}]}
        assert helpers.multilang_to_json(datadict, 'langtitle', 'title') == '{"fin": "foobar"}'
        assert datadict.get('title') == '{"fin": "foobar"}'


class TestUtils(TestCase):
    """Unit tests for functions in utils.py."""

    @classmethod
    def setUpClass(cls):
        harvest_model.setup()
        kata_model.setup()

    def tearDown(self):
        model.repo.rebuild_db()

    def _create_datasets(self):
        model.User(name="pidtest", sysadmin=True).save()
        organization = get_action('organization_create')({'user': 'pidtest'},
                                                         {'name': 'test-organization', 'title': "Test organization"})

        data = copy.deepcopy(TEST_DATADICT)
        data['owner_org'] = organization['name']
        data['private'] = False

        data['pids'] = [{'provider': u'http://helda.helsinki.fi/oai/request',
                         'id': u'some_primary_pid_1',
                         'type': u'primary'},
                        {'provider': u'http://helda.helsinki.fi/oai/request',
                         'id': u'some_metadata_pid_1',
                         'type': u'relation',
                         'relation': u'isMetadataFor'}]

        package_1 = get_action('package_create')({'user': 'pidtest'}, data)

        data['pids'] = [{'provider': u'http://helda.helsinki.fi/oai/request',
                         'id': u'some_data_pid_2',
                         'type': u'relation',
                         'relation': u'generalRelation'},
                        {'provider': u'http://helda.helsinki.fi/oai/request',
                         'id': u'some_part_pid_2',
                         'type': u'relation',
                         'relation': u'hasPart'}]

        package_2 = get_action('package_create')({'user': 'pidtest'}, data)

        return package_1['id'], package_2['id']

    def test_get_package_id_by_pid(self):
        package_1_id, package_2_id = self._create_datasets()
        self.assertEquals(utils.get_package_id_by_pid('some_primary_pid_1', 'primary'), package_1_id)
        self.assertEquals(utils.get_package_id_by_pid('some_metadata_pid_1', 'relation'), package_1_id)
        self.assertEquals(utils.get_package_id_by_pid('some_data_pid_1', 'unknown_type'), None)

        self.assertEquals(utils.get_package_id_by_pid('some_data_pid_2', 'relation'), package_2_id)
        self.assertEquals(utils.get_package_id_by_pid('some_part_pid_2', 'relation'), package_2_id)
        self.assertEquals(utils.get_package_id_by_pid('some_unknown_pid_2', 'relation'), None)
        self.assertEquals(utils.get_package_id_by_pid('invalid', 'invalid'), None)


    def test_generate_pid(self):
        pid = utils.generate_pid()
        assert pid.startswith('urn')
        assert len(pid) >= 10

    def test_generate_pid2(self):
        pid = utils.generate_pid()
        pid2 = utils.generate_pid()
        assert pid != pid2

    def test_get_funder(self):
        assert helpers.get_funder(TEST_DATADICT)['name'] == u'R. Ahanen'

    def test_get_field_titles(self):
        """Test settings.get_field_titles()"""

        titles = utils.get_field_titles(lambda x: x)

        assert len(titles) > 2, 'Found less than 3 field titles'
        assert 'tags' in titles, 'No tags field found in field titles'
        assert 'authorstring' in titles, 'No authorstring field found in field titles'

    def test_get_field_titles_translate(self):
        """Test settings.get_field_titles() translation"""

        translator = lambda x: x[::-1]  # Reverse string

        titles = utils.get_field_titles(translator)

        assert translator(_FIELD_TITLES['tags']) in titles.values(), 'No tags field found in field titles'
        assert translator(_FIELD_TITLES['authorstring']) in titles.values(), 'No authorstring found in field titles'

    def test_get_field_title(self):
        """Test settings.get_field_title()"""

        translator = lambda x: x[::-1]  # Reverse string

        title = utils.get_field_title('tags', translator)

        assert translator(_FIELD_TITLES['tags']) == title

    def test_pid_to_name(self):
        name = utils.pid_to_name('http://example.com/some/thing?good=true')
        assert name
        assert '/' not in name

    def test_get_pids_by_type(self):
        data_dict = copy.deepcopy(TEST_DATADICT)
        data_dict['id'] = 'some_package.id'

        pids = utils.get_pids_by_type(u'relation', data_dict)
        assert len(pids) == 3
        pids = utils.get_pids_by_type(u'primary', data_dict)
        assert len(pids) == 1
        pids = utils.get_pids_by_type(u'relation', data_dict, relation='isPreviousVersionOf')
        assert len(pids) == 1
        pids = utils.get_pids_by_type(u'relation', data_dict, relation='isPartOf')
        assert len(pids) == 1
        pids = utils.get_pids_by_type(u'relation', data_dict, relation='generalRelation')
        assert len(pids) == 1

        pids = utils.get_pids_by_type('some_unknown_type', data_dict)
        assert len(pids) == 0


    def test_get_primary_pid(self):
        data_dict = copy.deepcopy(TEST_DATADICT)
        data_dict['id'] = 'some_package.id'

        ppid = utils.get_primary_pid(data_dict)
        assert ppid == 'some_primary_pid'
        ppid = utils.get_primary_pid(data_dict, True)
        assert ppid.get('type') == 'primary'


    def test_get_package_id_by_primary_pid(self):
        model.User(name="pidtest", sysadmin=True).save()
        data_dict = copy.deepcopy(TEST_DATADICT)
        organization = get_action('organization_create')({'user': 'pidtest'},
                                                         {'name': 'test-organization', 'title': "Test organization"})
        data_dict['owner_org'] = organization['name']
        get_action('package_create')({'user': 'pidtest'}, data_dict)

        assert utils.get_package_id_by_primary_pid(data_dict)