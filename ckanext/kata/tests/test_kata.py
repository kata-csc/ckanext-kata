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
        
