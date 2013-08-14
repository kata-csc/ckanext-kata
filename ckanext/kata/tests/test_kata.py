# pylint: disable=no-self-use, missing-docstring
#
# no-self-use = *Method could be a function*

"""
Test classes for Kata CKAN Extension.
"""

from unittest import TestCase
from pylons.util import ContextObj, PylonsContext, pylons, AttribSafeContextObj

from ckanext.kata.settings import get_field_titles, _FIELD_TITLES, get_field_title
from ckanext.kata.plugin import KataPlugin

from ckan.tests import WsgiAppCase, CommonFixtureMethods, url_for
from ckan.tests.html_check import HtmlCheckMethods
from pylons import config
import paste.fixture
from paste.registry import RegistryManager
from ckan.config.middleware import make_app

from collections import defaultdict
from ckanext.kata.validators import validate_kata_date, validate_language

from pylons import session

class TestKataExtension(TestCase):
    """General tests for Kata CKAN extension."""

    def test_get_field_titles(self):
        """Test settings.get_field_titles()"""

        titles = get_field_titles(lambda x: x)

        assert len(titles) > 2, 'Found less than 3 field titles'
        assert 'tags' in titles, 'No tags field found in field titles'
        assert 'authorstring' in titles, 'No authorstring field found in field titles'

    def test_get_field_titles_translate(self):
        """Test settings.get_field_titles() translation"""

        translator = lambda x: x[::-1]  # Reverse string

        titles = get_field_titles(translator)

        assert translator(_FIELD_TITLES['tags']) in titles.values(), 'No tags field found in field titles'
        assert translator(_FIELD_TITLES['authorstring']) in titles.values(), 'No authorstring found in field titles'

    def test_get_field_title(self):
        """Test settings.get_field_title()"""

        translator = lambda x: x[::-1]  # Reverse string

        title = get_field_title('tags', translator)

        assert translator(_FIELD_TITLES['tags']) == title


class TestKataPlugin(WsgiAppCase, HtmlCheckMethods, CommonFixtureMethods):
    """
    General tests for KataPlugin.

    Provides a a dummy context object to test functions and methods that rely on it.
    """

    @classmethod
    def setup_class(cls):
        """Set up tests."""

        wsgiapp = make_app(config['global_conf'], **config['app_conf'])
        cls.app = paste.fixture.TestApp(wsgiapp)

        cls.some_data_dict = {'sort': u'metadata_modified desc', 'fq': '', 'rows': 20, 'facet.field': ['groups', 'tags', 'extras_fformat', 'license', 'authorstring', 'organizationstring', 'extras_language'], 'q': u'Selenium', 'start': 0, 'extras': {}}
        cls.kata_plugin = KataPlugin()

        # The Pylons globals are not available outside a request. This is a hack to provide context object.
        c = AttribSafeContextObj()
        py_obj = PylonsContext()
        py_obj.tmpl_context = c
        pylons.tmpl_context._push_object(c)

    @classmethod
    def teardown_class(cls):
        """Get away from testing environment."""

        pylons.tmpl_context._pop_object()

    def test_before_search(self):
        """Test before_search() output type."""

        assert isinstance( self.kata_plugin.before_search(self.some_data_dict), dict), "KataPlugin.before_search() didn't output a dict"

    def test_get_actions(self):
        """Test get_actions() output type."""
        assert isinstance( self.kata_plugin.get_actions(), dict), "KataPlugin.get_actions() didn't output a dict"

    def test_get_helpers(self):
        """Test get_helpers() output type."""
        assert isinstance( self.kata_plugin.get_helpers(), dict), "KataPlugin.get_helpers() didn't output a dict"

    def test_new_template(self):
        """Test new_template()."""
        html_location = self.kata_plugin.new_template()
        assert len( html_location ) > 0

    def test_comments_template(self):
        """Test comments_template()."""
        html_location = self.kata_plugin.comments_template()
        assert len( html_location ) > 0

    def test_search_template(self):
        """Test search_template()."""
        html_location = self.kata_plugin.search_template()
        assert len( html_location ) > 0

    def test_form_to_db_schema_options(self):
        """Test Kata schema."""
        schema = self.kata_plugin.form_to_db_schema_options()
        assert isinstance(schema, dict) and len(schema) > 0

    def test_db_to_form_schema_options(self):
        """Test Kata schema."""
        schema = self.kata_plugin.db_to_form_schema_options()
        assert isinstance(schema, dict) and len(schema) > 0


class TestKataValidators(TestCase):
    """Tests for Kata validators."""

    @classmethod
    def setup_class(cls):
        """Set up tests."""

        # Some test data from Add dataset.

        cls.test_data = {('__extras',): {'_ckan_phase': u'', \
        'evdescr': [], \
        'evwhen': [], \
        'evwho': [], \
        'groups': [], \
        'pkg_name': u''}, \
        ('access',): u'contact', \
        ('accessRights',): u'', \
        ('accessrequestURL',): u'', \
        ('algorithm',): u'', \
        ('author', 0, 'value'): u'dada', \
        ('checksum',): u'', \
        ('contactURL',): u'http://google.com', \
        ('discipline',): u'', \
        ('evtype', 0, 'value'): u'collection', \
        ('extras',): [{'key': 'funder', 'value': u''}, \
        {'key': 'discipline', 'value': u''}, \
        {'key': 'publisher', 'value': u'dada'}, \
        {'key': 'fformat', 'value': u''}, \
        {'key': 'project_funding', 'value': u''}, \
        {'key': 'project_homepage', 'value': u''}, \
        {'key': 'owner', 'value': u'dada'}, \
        {'key': 'version', 'value': u'2013-08-14T10:37:09Z'}, \
        {'key': 'temporal_coverage_begin', 'value': u''}, \
        {'key': 'accessrequestURL', 'value': u''}, \
        {'key': 'phone', 'value': u'+35805050505'}, \
        {'key': 'licenseURL', 'value': u'dada'}, \
        {'key': 'geographic_coverage', 'value': u''}, \
        {'key': 'access', 'value': u'contact'}, \
        {'key': 'algorithm', 'value': u''}, \
        {'key': 'langdis', 'value': u'True'}, \
        {'key': 'accessRights', 'value': u''}, \
        {'key': 'contactURL', 'value': u'http://google.com'}, \
        {'key': 'project_name', 'value': u''}, \
        {'key': 'checksum', 'value': u''}, \
        {'key': 'temporal_coverage_end', 'value': u''}, \
        {'key': 'projdis', 'value': u'True'}, \
        {'key': 'language', 'value': u''}], \
        ('fformat',): u'', \
        ('funder',): u'', \
        ('geographic_coverage',): u'', \
        ('langdis',): u'False', \
        ('language',): u'sv', \
        ('licenseURL',): u'dada', \
        ('license_id',): u'', \
        ('log_message',): u'', \
        ('name',): u'', \
        ('notes',): u'', \
        ('organization', 0, 'value'): u'dada', \
        ('owner',): u'dada', \
        ('phone',): u'+35805050505', \
        ('projdis',): u'True', \
        ('project_funding',): u'', \
        ('project_homepage',): u'', \
        ('project_name',): u'', \
        ('publisher',): u'dada', \
        ('save',): u'finish', \
        ('tag_string',): u'dada', \
        ('temporal_coverage_begin',): u'', \
        ('temporal_coverage_end',): u'', \
        ('title', 0, 'lang'): u'sv', \
        ('title', 0, 'value'): u'dada', \
        ('type',): None, \
        ('version',): u'2013-08-14T10:37:09Z', \
        ('versionPID',): u''}

    def test_validate_kata_date_valid(self):
        errors = defaultdict(list)
        validate_kata_date('date', {'date': '2012-12-31T13:12:11'}, errors, None)
        assert len( errors ) == 0

    def test_validate_kata_date_invalid(self):
        errors = defaultdict(list)
        validate_kata_date('date', {'date': '20xx-xx-31T13:12:11'}, errors, None)
        assert len( errors ) > 0

    def test_validate_kata_date_invalid_2(self):
        errors = defaultdict(list)
        validate_kata_date('date', {'date': '2013-02-29T13:12:11'}, errors, None)
        assert len( errors ) > 0


    def test_validate_language_valid(self):
        errors = defaultdict(list)
        validate_language(('language',), self.test_data, errors, None)
        assert len( errors ) == 0

    def test_validate_language_valid_2(self):
        errors = defaultdict(list)

        dada = self.test_data.copy()
        dada[('language',)] = u''
        dada[('langdis',)] = 'True'

        validate_language(('language',), dada, errors, None)
        assert len( errors ) == 0

    def test_validate_language_valid_3(self):
        errors = defaultdict(list)

        dada = self.test_data.copy()
        dada[('language',)] = u'fi, sv, en, aa'
        dada[('langdis',)] = 'False'

        validate_language(('language',), dada, errors, None)
        assert len( errors ) == 0
        assert dada[('language',)] == u'fi, sv, en, aa'

    def test_validate_language_valid_4(self):
        errors = defaultdict(list)

        dada = self.test_data.copy()
        dada[('language',)] = u'fi, sv, en, aa'
        dada[('langdis',)] = 'True'

        validate_language(('language',), dada, errors, None)
        assert len( errors ) == 0
        assert dada[('language',)] == u''

    def test_validate_language_invalid(self):
        errors = defaultdict(list)

        dada = self.test_data.copy()
        dada[('language',)] = u'aa, ab, ac, ad, ae, af'
        dada[('langdis',)] = 'False'

        validate_language(('language',), dada, errors, None)
        assert len( errors ) == 1

    def test_validate_language_invalid_2(self):
        errors = defaultdict(list)

        dada = self.test_data.copy()
        dada[('language',)] = u''
        dada[('langdis',)] = 'False'

        validate_language(('language',), dada, errors, None)
        assert len( errors ) == 1

    def test_validate_language_invalid_3(self):
        errors = defaultdict(list)

        dada = self.test_data.copy()
        dada[('language',)] = u'fin, sve, eng'
        dada[('langdis',)] = 'True'

        validate_language(('language',), dada, errors, None)
        assert len( errors ) == 0
