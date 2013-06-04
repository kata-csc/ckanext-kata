"""Test classes for Kata CKAN Extension."""

from unittest import TestCase
from ckanext.kata import actions 

class TestKataExtension(TestCase):
    """General tests for Kata CKAN Extension."""
    
    def test_reality_check(self):
        """Dummy test which should never fail."""
        self.assertEqual(1+1, 2)
        

class TestKataActions(TestCase):
    """Tests for Kata CKAN Extension's actions.py."""
    
    pass

