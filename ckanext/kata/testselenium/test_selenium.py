"""
Selenium tests for Kata.

Requirements:
    - Firefox installed
    - Xvfb installed

These must be installed manually, they are not part of the Kata RPM packages.

To run as apache user do these also:
    mkdir /var/www/.gnome2
    chown apache:apache /var/www/.gnome2/
    chown apache:apache /var/www/.mozilla/


These tests need CKAN to be running so they cannot be combined with normal tests. Ideally run selenium tests after
normal testing to get an empty database.

To run from pyenv:

    xvfb-run nosetests ckanext-kata/ckanext/kata/testselenium/test_selenium.py

or

    ./ckanext-kata/nose.sh selenium

"""

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from unittest import TestCase
import time


class TestKataBasics(TestCase):
    """Some basic Selenium tests for Kata's user interface without logged in user."""

    @classmethod
    def setup_class(cls):
        """
        Initialize tests.
        """
        cls.browser = webdriver.Firefox()  # Get local session of firefox

    @classmethod
    def teardown_class(cls):
        """
        Uninitialize tests.
        """
        cls.browser.quit()


    def test_front_page_loads(self):
        """Test that Selenium can access the front page."""

        self.browser.get("https://localhost/")
        assert "Kata" in self.browser.title


    def test_navigation(self):
        """
        Test that Selenium can access the navigation and all are present.
        """
        # These tests are very clumsy and should be made more sane in the future

        self.browser.get("https://localhost/")
        #assert "Kata" in self.browser.title
        try:
            search = self.browser.find_element_by_xpath("//a[contains(@href, '/dataset')]")
        except NoSuchElementException:
            assert 0, 'Search (dataset) navigation not found for anonymous user'
        try:
            search = self.browser.find_element_by_xpath("//a[contains(@href, '/group')]")
        except NoSuchElementException:
            assert 0, 'Group navigation not found for anonymous user'
        try:
            search = self.browser.find_element_by_xpath("//a[contains(@href, '/about')]")
        except NoSuchElementException:
            assert 0, 'About navigation not found for anonymous user'
        try:
            search = self.browser.find_element_by_xpath("//a[contains(@href, '/help')]")
        except NoSuchElementException:
            assert 0, 'Help navigation not found for anonymous user'
        try:
            search = self.browser.find_element_by_xpath("//a[contains(@href, '/faq')]")
        except NoSuchElementException:
            assert 0, 'FAQ navigation not found for anonymous user'
        try:
            search = self.browser.find_element_by_xpath("//a[contains(@href, '/applications')]")
        except NoSuchElementException:
            assert 0, 'Applications navigation not found for anonymous user'
        try:
            search = self.browser.find_element_by_xpath("//a[contains(@href, '/user/login')]")
        except NoSuchElementException:
            assert 0, 'Log in link not found for anonymous user'





class TestKataBasicsWithUser(TestCase):
    """Some basic Selenium tests for Kata's user interface with a logged in user."""

    # TODO: Modify tests so that they don't depend on the order in which they are run.

    @classmethod
    def setup_class(cls):
        """
        Initialize tests.
        """
        cls.browser = webdriver.Firefox()  # Get local session of firefox
        cls.dataset_url = None

    @classmethod
    def teardown_class(cls):
        """
        Uninitialize tests.
        """
        cls.browser.quit()

    def _register_user(self, reg_browser):
        """Register a new user, will be logged in automatically."""

        reg_browser.get("https://localhost/en/user/register")

        try:
            field = reg_browser.find_element_by_xpath("//input[@id='field-username']")
            field.send_keys('seleniumuser' + str(int(time.time()*100)))

            field = reg_browser.find_element_by_xpath("//input[@id='field-fullname']")
            field.send_keys('seleniumuser' + str(int(time.time()*100)))

            field = reg_browser.find_element_by_xpath("//input[@id='field-email']")
            field.send_keys('kata.selenium@gmail.com')

            field = reg_browser.find_element_by_xpath("//input[@id='field-password']")
            field.send_keys('seleniumuser')

            field = reg_browser.find_element_by_xpath("//input[@id='field-confirm-password']")
            field.send_keys('seleniumuser')

            btn = reg_browser.find_element_by_xpath("//button[@name='save']")
            btn.click()

        except NoSuchElementException:
            reg_browser.get_screenshot_as_file('_register_user.png')
            assert 0, "Error processing the user registration page"

        try:
            WebDriverWait(reg_browser, 30).until(expected_conditions.presence_of_element_located((By.XPATH, "//div[contains(text(),' logged in')]")))
        except TimeoutException:
            reg_browser.get_screenshot_as_file('_register_user.png')
            reg_browser.quit()
            assert 0, "User registration didn't finish"



    def _add_dataset(self):
        """
        Add a simple dataset.
        """

        test_browser = webdriver.Firefox()  # Get a new session because of a possible dialog pop-up
        self._register_user(test_browser)
        
        test_browser.get("https://localhost/en/dataset/new")
        test_browser.implicitly_wait(8)  # Wait for javascript magic to alter fields

        try:
            field = test_browser.find_element_by_xpath("//input[@id='title__0__value_id']")
            field.send_keys('Selenium Dataset')

            field = test_browser.find_element_by_xpath("//input[@id='author__0__value_id']")
            field.send_keys('Selenium')

            field = test_browser.find_element_by_xpath("//input[@id='organization__0__value_id']")
            field.send_keys('CSC Oy')

            field = test_browser.find_elements_by_class_name('select2-input')[1]  # hopefully this is keywords input
            field.send_keys('Selenium')
            field.send_keys(Keys.RETURN)

            field = test_browser.find_element_by_xpath("//input[@name='langdis']")
            field.click()

            #field = test_browser.find_elements_by_class_name('select2-input')[2]  # hopefully distributor name
            #field.send_keys('Selenium')
            #field.send_keys(Keys.RETURN)

            field = test_browser.find_element_by_xpath("//input[@id='phone']")
            field.send_keys('+35891234567')

            field = test_browser.find_element_by_xpath("//input[@id='contactURL']")
            field.send_keys('https://localhost/')

            field = test_browser.find_element_by_xpath("//input[@name='projdis']")
            field.click()

            field = test_browser.find_element_by_xpath("//input[@id='owner']")
            field.send_keys('Selenium')

            field = test_browser.find_element_by_xpath("//input[@id='contact']")
            field.click()

            field = test_browser.find_element_by_xpath("//input[@id='licenseURL']")
            field.send_keys('Shareware')
            field.send_keys(Keys.ENTER)

            #btn = test_browser.find_element_by_xpath("//button[@name='save']")
            #btn.click()

        except NoSuchElementException:
            test_browser.get_screenshot_as_file('_add_dataset.png')
            assert 0, "Error processing the create dataset page"

        try:
            WebDriverWait(test_browser, 30).until(expected_conditions.presence_of_element_located((By.XPATH, "//ul/li/a[.='RDF']")))
        except TimeoutException:
            test_browser.get_screenshot_as_file('_add_dataset.png')
            test_browser.quit()
            assert 0, "Dataset creation didn't finish"

        assert "Kata" in test_browser.title, "Dataset creation failed somehow"

        self.dataset_url = ''.join(test_browser.current_url)

        test_browser.quit()


    def test_1_register_user(self):
        """
        Test for user registration. Named so because tests are run in alphabetical order.
        The test user is needed when testing contact form functionality.
        """

        self._register_user(self.browser)


    # def test_2_add_dataset(self):
    #     '''Test that user can add a dataset.'''
    #
    #     self._add_dataset()
    #
    #     assert self.dataset_url is not None, "dataset url not found"
    #

    def test_3_contact_form_can_go_back(self):
        """Test that user can go back from contact form and still go forward to send it."""

        # Dataset must be added first. There is some issue with the self.dataset_url value being cleared between
        # tests.

        if self.dataset_url is None:
            self._add_dataset()

        assert self.dataset_url is not None, "dataset url not found"

        # Go to contact form
        contact_form_url = self.dataset_url.replace('/dataset/', '/contact/')
        self.browser.get(self.dataset_url)

        self.browser.get(contact_form_url)
        try:
            self.browser.find_element_by_xpath("//textarea[@name='msg']")
        except NoSuchElementException:
            self.browser.get_screenshot_as_file('test_2_contact_form_can_go_back.png')
            assert 0, 'Contact form expected but not found (first visit)'

        self.browser.back()
        self.browser.get(contact_form_url)

        try:
            field = self.browser.find_element_by_xpath("//textarea[@name='msg']")
            field.send_keys('Selenium is a testing')

            btn = self.browser.find_element_by_xpath("//input[@value='Send']")
            btn.click()

        except NoSuchElementException:
            self.browser.get_screenshot_as_file('test_2_contact_form_can_go_back.png')
            assert 0, 'Contact form expected but not found (second visit)'

        try:
            WebDriverWait(self.browser, 30).until(expected_conditions.presence_of_element_located((By.XPATH, "//div[contains(text(),'Message sent')]")))
        except TimeoutException:
            self.browser.get_screenshot_as_file('test_2_contact_form_can_go_back.png')
            assert 0, "Sending contact form didn't finish"


    def test_4_navigation(self):
        """
        Test that navigation is ok for logged in user.
        """
        # These should match often twice, clumsy, fix in the future
        self.browser.get("https://localhost/")
        try:
            search = self.browser.find_element_by_xpath("//a[contains(@href, '/dataset')]")           
        except NoSuchElementException:
            assert 0, 'Search (dataset) navigation not found for logged in user'
        try:
            search = self.browser.find_element_by_xpath("//a[contains(@href, '/group')]")           
        except NoSuchElementException:
            assert 0, 'Group navigation not found for logged in user'
        try:
            search = self.browser.find_element_by_xpath("//a[contains(@href, '/about')]")
        except NoSuchElementException:
            assert 0, 'About navigation not found for logged in user'
        try:
            search = self.browser.find_element_by_xpath("//a[contains(@href, '/help')]")           
        except NoSuchElementException:
            assert 0, 'Help navigation not found for logged in user'
        try:
            search = self.browser.find_element_by_xpath("//a[contains(@href, '/faq')]")
        except NoSuchElementException:
            assert 0, 'FAQ navigation not found for logged in user'   
        try:
            search = self.browser.find_element_by_xpath("//a[contains(@href, '/applications')]")
        except NoSuchElementException:
            assert 0, 'Applications navigation not found for logged in user'
        try:
            search = self.browser.find_element_by_xpath("//a[contains(@href, '/dashboard')]")
        except NoSuchElementException:
            assert 0, 'Notifications link not found for logged in user'
        try:
            search = self.browser.find_element_by_xpath("//a[contains(@href, '/user/_logout')]")
        except NoSuchElementException:
            assert 0, 'Log out link not found for logged in user'
#        try:
#            search = self.browser.find_element_by_xpath("//a[contains(@href, '/#')]")
#        except NoSuchElementException:
#            assert 0, 'Drop down (profile menu) link not found for logged in user'
        try:
            search = self.browser.find_element_by_xpath("//a[contains(@href, '/user/selenium')]")
        except NoSuchElementException:
            assert 0, 'My datasets link not found for logged in user'


    def test_5_advanced_search(self):
        """Test that advanced search returns our shiny new dataset."""

        self.browser.get("https://localhost/en/dataset")

        try:
            btn = self.browser.find_element_by_xpath("//a[contains(@href, '#advanced-search-tab')]")
            btn.click()

        except NoSuchElementException:
            self.browser.get_screenshot_as_file('test_3_advanced_search.png')
            assert 0, 'Advanced search tab not found'

        try:
            WebDriverWait(self.browser, 30).until(expected_conditions.presence_of_element_located((By.ID, 'advanced-search-date-end')))
        except TimeoutException:
            self.browser.get_screenshot_as_file('test_3_advanced_search.png')
            assert 0, "Error switching to advanced search"

        try:
            field = self.browser.find_element_by_id("advanced-search-text-1")
            field.send_keys('Selenium')
            field.send_keys(Keys.ENTER)
        except NoSuchElementException:
            self.browser.get_screenshot_as_file('test_3_advanced_search.png')
            assert 0, 'Search text field not found'

        try:
            WebDriverWait(self.browser, 30).until(expected_conditions.presence_of_element_located((By.XPATH, "//footer")))
        except TimeoutException:
            self.browser.get_screenshot_as_file('test_3_advanced_search.png')
            assert 0, "Didn't get the expected search result"

        result = self.browser.find_element_by_xpath("//div/strong[contains(text(),' datasets')]")

        # As the Solr index seems to live it's own life and the database might not have been cleared,
        # we cannot be sure how many hits should be expected. So this works for 1 or more results.

        assert u'no datasets' not in result.text, result.text
        assert u' datasets' in result.text, result.text


    def test_9_logout(self):
        """
        Test logout for Selenium user.
        """

        self.browser.get("https://localhost/en/user/_logout")

        try:
            search = self.browser.find_element_by_xpath("//h1[.='Logged Out']")
        except NoSuchElementException:
            self.browser.get_screenshot_as_file('test_9_test_logout.png')
            assert 0, "Error logging out"


