# coding: utf-8
"""
Test classes for Kata CKAN Extension.
"""

import copy
from unittest import TestCase

from ckanext.kata import utils, helpers
from ckanext.kata.tests.test_fixtures.unflattened import TEST_DATADICT
from ckanext.kata.settings import _FIELD_TITLES
from ckanext.harvest import model as harvest_model
import ckanext.kata.model as kata_model
import ckan.model as model
from ckan.logic import get_action


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

    def test_get_urn_fi_address(self):
        package = copy.deepcopy(TEST_DATADICT)
        self.assertTrue(helpers.get_urn_fi_address(package).startswith('http://urn.fi/urn:nbn:fi:csc-kata'))

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
        assert helpers.split_disciplines('Tiede-, taide- ja liikuntakasvatus')[0] == 'Tiede-, taide- ja liikuntakasvatus'

    def test_disciplines_string_resolved(self):
        disciplines = u'Matematiikka,Fysiikka'
        assert helpers.disciplines_string_resolved(disciplines) == u'Matematiikka, Fysiikka'
        disciplines = u'http://www.yso.fi/onto/okm-tieteenala/ta111,Fysiikka'
        assert helpers.disciplines_string_resolved(disciplines, None, 'en') == u'Mathematics, Fysiikka', helpers.disciplines_string_resolved(disciplines, None, 'en')
        disciplines = u'http://www.yso.fi/onto/okm-tieteenala/xyz1234,Fysiikka'
        assert helpers.disciplines_string_resolved(disciplines, None, 'en') == u'http://www.yso.fi/onto/okm-tieteenala/xyz1234, Fysiikka'

    def test_get_label_for_uri(self):
        discipline = u'Matematiikka'
        assert helpers.get_label_for_uri(discipline, None, 'en') == discipline
        discipline = u'http://www.yso.fi/baldur/okm-tieteenala/ta111'
        assert helpers.get_label_for_uri(discipline, None, 'en') == discipline
        assert helpers.get_label_for_uri(discipline, 'okm-tieteenala') == discipline
        discipline = u'http://www.yso.fi/onto/okm-tieteenala/ta111'
        assert helpers.get_label_for_uri(discipline) == u'Mathematics'
        discipline = u'http://www.yso.fi/onto/okm-tieteenala/xyz1234'
        assert helpers.get_label_for_uri(discipline) == discipline

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
        assert helpers.has_json_content(u'{}') == False
        assert helpers.has_json_content(None) == False
        assert helpers.has_json_content('') == False
        assert helpers.has_json_content('{"fin": ""}') == False
        assert helpers.has_json_content('{"fin": "", "eng": ""}') == False
        assert helpers.has_json_content('{"fin": "jotain"}') == True
        assert helpers.has_json_content('[1, 2, 3]') == True


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
        organization = get_action('organization_create')({'user': 'pidtest'}, {'name': 'test-organization', 'title': "Test organization"})

        data = copy.deepcopy(TEST_DATADICT)
        data['owner_org'] = organization['name']
        data['private'] = False

        data['pids'] = [{'provider': u'http://helda.helsinki.fi/oai/request',
                         'id': u'some_data_pid_1',
                         'primary': u'True',
                         'type': u'data'},
                        {'provider': u'http://helda.helsinki.fi/oai/request',
                         'id': u'some_metadata_pid_1',
                         'primary': u'True',
                         'type': u'metadata'}]

        package_1 = get_action('package_create')({'user': 'pidtest'}, data)

        data['pids'] = [{'provider': u'http://helda.helsinki.fi/oai/request',
                         'id': u'some_data_pid_2',
                         'primary': u'True',
                         'type': u'data'},
                        {'provider': u'http://helda.helsinki.fi/oai/request',
                         'id': u'some_version_pid_2',
                         'primary': u'True',
                         'type': u'version'}]

        package_2 = get_action('package_create')({'user': 'pidtest'}, data)

        return package_1['id'], package_2['id']

    def test_get_package_id_by_pid(self):
        package_1_id, package_2_id = self._create_datasets()
        self.assertEquals(utils.get_package_id_by_pid('some_data_pid_1', 'data'), package_1_id)
        self.assertEquals(utils.get_package_id_by_pid('some_metadata_pid_1', 'metadata'), package_1_id)
        self.assertEquals(utils.get_package_id_by_pid('some_data_pid_1', 'metadata'), None)

        self.assertEquals(utils.get_package_id_by_pid('some_data_pid_2', 'data'), package_2_id)
        self.assertEquals(utils.get_package_id_by_pid('some_version_pid_2', 'version'), package_2_id)
        self.assertEquals(utils.get_package_id_by_pid('some_version_pid_2', 'data'), None)
        self.assertEquals(utils.get_package_id_by_pid('invalid', 'version'), None)

    def test_get_package_id_by_data_pids(self):
        package_1_id, package_2_id = self._create_datasets()

        package_id = utils.get_package_id_by_data_pids({'pids': [{'type': 'data', 'id': 'some_data_pid_1'}]})
        self.assertEquals(package_1_id, package_id[0])

        package_id = utils.get_package_id_by_data_pids({'pids': [{'type': 'data', 'id': 'some_data_pid_2'}]})
        self.assertEquals(package_2_id, package_id[0])

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

    def test_datapid_to_name(self):
        name = utils.datapid_to_name('http://example.com/some/thing?good=true')
        assert name
        assert '/' not in name

    def test_get_pids_by_type(self):
        data_dict = copy.deepcopy(TEST_DATADICT)
        data_dict['id'] = 'some_package.id'
        data_dict['name'] = 'some_package.name'

        pids = utils.get_pids_by_type('data', data_dict)
        assert len(pids) == 2
        pids = utils.get_pids_by_type('data', data_dict, primary=True)
        assert len(pids) == 1
        pids = utils.get_pids_by_type('data', data_dict, primary=True, use_package_id=True)
        assert len(pids) == 1
        pids = utils.get_pids_by_type('data', data_dict, primary=False)
        assert len(pids) == 1

        pids = utils.get_pids_by_type('metadata', data_dict)
        assert len(pids) == 1
        pids = utils.get_pids_by_type('metadata', data_dict, primary=True)
        assert len(pids) == 0
        pids = utils.get_pids_by_type('metadata', data_dict, primary=True, use_package_id=True)
        assert len(pids) == 1
        pids = utils.get_pids_by_type('metadata', data_dict, use_package_id=True)
        assert len(pids) == 2

        pids = utils.get_pids_by_type('version', data_dict)
        assert len(pids) == 1
        pids = utils.get_pids_by_type('version', data_dict, primary=True)
        assert len(pids) == 0
        pids = utils.get_pids_by_type('version', data_dict, primary=True, use_package_id=True)
        assert len(pids) == 0

        pids = utils.get_pids_by_type('some_unknown_type', data_dict)
        assert len(pids) == 0
