'''Functional test package for Kata'''

import copy
import unittest
import testfixtures

import ckanapi
import paste.fixture
from pylons import config
from pylons.util import AttribSafeContextObj, PylonsContext, pylons
from webtest import AppError

from ckan.config.middleware import make_app
from ckan.lib.create_test_data import CreateTestData
import ckan.lib.navl.dictization_functions as df

import ckanext.kata.model as kata_model
from ckanext.kata.tests.test_fixtures.unflattened import TEST_ORGANIZATION_COMMON, TEST_DATADICT
import ckanext.ytp.comments.model as comments_model

# Note: all ORM model changes must be imported before WsgiAppCase
from ckan import model
import ckan.tests.legacy as tests
from ckanext.kata.validators import kata_tag_string_convert


class KataWsgiTestCase(tests.WsgiAppCase, unittest.TestCase):
    '''
    Class to inherit for Kata's WSGI tests.
    '''

    @classmethod
    def setup_class(cls):
        """Set up testing environment."""

        model.repo.rebuild_db()
        kata_model.setup()
        CreateTestData.create()
        comments_model.init_tables()

        wsgiapp = make_app(config['global_conf'], **config['app_conf'])
        cls.app = paste.fixture.TestApp(wsgiapp)

        # The Pylons globals are not available outside a request. This is a hack to provide context object.
        c = AttribSafeContextObj()
        py_obj = PylonsContext()
        py_obj.tmpl_context = c
        pylons.tmpl_context._push_object(c)

    @classmethod
    def teardown_class(cls):
        """Get away from testing environment."""

        kata_model.delete_tables()
        model.repo.rebuild_db()


class KataApiTestCase(unittest.TestCase):
    '''
    Class to inherit for Kata's API tests.
    '''

    @classmethod
    def setup_class(cls):
        """Setup for all tests."""

        model.repo.rebuild_db()
        kata_model.setup()
        CreateTestData.create()

        cls.user_sysadmin = model.User.get('testsysadmin')  # Org admin
        cls.user_normal = model.User.get('tester')          # Org editor
        cls.user_anna = model.User.get('annafan')
        cls.user_joe = model.User.get('joeadmin')           # Org member

        wsgiapp = make_app(config['global_conf'], **config['app_conf'])
        cls.app = paste.fixture.TestApp(wsgiapp)

        # Set up API callers

        cls.api_user_normal = ckanapi.TestAppCKAN(cls.app, apikey=cls.user_normal.apikey)
        cls.api_user_sysadmin = ckanapi.TestAppCKAN(cls.app, apikey=cls.user_sysadmin.apikey)
        cls.api_user_anna = ckanapi.TestAppCKAN(cls.app, apikey=cls.user_anna.apikey)
        cls.api_user_joe = ckanapi.TestAppCKAN(cls.app, apikey=cls.user_joe.apikey)
        cls.api = ckanapi.TestAppCKAN(cls.app)

        cls.TEST_DATADICT = copy.deepcopy(TEST_DATADICT)

        try:
            output = cls.api_user_sysadmin.action.organization_create(**TEST_ORGANIZATION_COMMON)
            cls.TEST_DATADICT['owner_org'] = output.get('id')
        except AppError:
            print 'Failed to create a common organization. Perhaps it exists already.'

    @classmethod
    def teardown_class(cls):
        """Get away from testing environment."""
        model.repo.rebuild_db()

    def _compare_datadicts(self, original, output):
        '''
        Compare a CKAN generated datadict to original datadict. Returns True if identical,
        otherwise throws an exception with useful output of differences.

        :param original: original datadict
        :param output: a datadict received from CKAN API
        '''

        def convert_tags(tag_string):
            ''' Convert tag_string to tags dict. Copy-paste from ckan.tests.legacy.logic.test_tag_vocab.py. '''
            key = 'vocab_tags'
            data = {key: tag_string}
            errors = []
            context = {'model': model, 'session': model.Session}
            kata_tag_string_convert(key, data, errors, context)
            del data[key]
            return data

        data_dict = copy.deepcopy(original)

        # name (data pid), title and notes are generated so they shouldn't match
        data_dict.pop('name', None)
        data_dict.pop('title', None)
        data_dict.pop('notes', None)

        # lang* fields are converted to translation JSON strings and
        # after that they are not needed anymore
        data_dict.pop('langtitle', None)
        data_dict.pop('langnotes', None)

        # Terms of usage acceptance is checked but not saved
        data_dict.pop('accept-terms', None)

        # Create tags from original dataset's tag_string
        if not data_dict.get('tags'):
            data_dict['tags'] = df.unflatten(convert_tags(data_dict.get('tag_string'))).get('tags')
            data_dict.pop('tag_string', None)

        print data_dict['tags']

        for tag_dict in output.get('tags'):
            # These are not provided from kata_tag_string_convert, so remove them
            tag_dict.pop('display_name')
            tag_dict.pop('id')
            tag_dict.pop('state')
            tag_dict.pop('vocabulary_id')

        # Remove xpaths because xpath-json converter not yet implemented
        data_dict.pop('xpaths', None)

        # Remove all values that are not present in the original data_dict
        output = dict((k, v) for k, v in output.items() if k in data_dict.keys())

        # Take out automatically added distributor (CKAN user)
        output['agent'] = filter(lambda x: x.get('name') not in ['testsysadmin', 'tester'], output['agent'])

        testfixtures.compare(output, data_dict)

        return True
