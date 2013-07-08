'''
Selenium tests

Requirements:
    - Firefox installed
    - Xvfb installed

These tests need CKAN to be running so they cannot be combined with normal tests. Ideally run selenium tests after
normal testing to get an empty database. Also, for some reason must be run as root user, otherwise seems to hang.

To run from pyenv:

    xvfb-run nosetests ckanext-kata/ckanext/kata/testselenium/test_selenium.py

'''

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys

#from pyvirtualdisplay import Display

class TestKataSelenium():
    """Selenium tests for Kata CKAN extension."""

    @classmethod
    def setup_class(cls):
        #cls.display = Display(visible=0, size=(800, 600))
        #cls.display.start()
        cls.browser = webdriver.Firefox() # Get local session of firefox

    @classmethod
    def teardown_class(cls):
        cls.browser.close()

    def test_front_page_loads(self):
        """Test that Selenium can access the front page."""

        self.browser.get("http://localhost/") # Load page
        assert "Kata" in self.browser.title

    def test_front_page_loads(self):
        """Test that Selenium can access the front page."""

        self.browser.get("http://localhost/") # Load page
        assert "Kata" in self.browser.title
