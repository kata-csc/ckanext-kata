"""Test classes for Kata CKAN Extension."""

import pylons
import pylons.config as config

from unittest import TestCase

import ckan.tests as tests
import ckan.config.middleware as middleware
from ckan import plugins 


class TestKataExtension(TestCase):
    """General tests for Kata CKAN extension."""

    def test_reality_check(self):
        """Dummy test which should never fail."""
        self.assertEqual(1+1, 2)
        

'''
class TestKataPlugin(tests.WsgiAppCase):
    """Tests for Kata-plugin."""

    @classmethod
    def setup_class(cls):
        cls._original_config = config.copy()
        config['ckan.plugins'] = 'kata'
        wsgiapp = middleware.make_app(config['global_conf'], **config.local_conf)
        cls.app = paste.fixture.TestApp(wsgiapp)

    @classmethod
    def teardown_class(cls):
        config.clear()
        config.update(cls._original_config)
        
    def test_js_included(self):
        res_id = self.resource['id']
        pack_id = self.package.name
        url = '/dataset/import_xml/'.format(pack_id, res_id)
        result = self.app.get(url, status='*')

        assert result.status == 200, result.status
        
'''