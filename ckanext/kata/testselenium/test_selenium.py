#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Selenium tests for Kata (Etsin).

Requirements:
    - Firefox installed
    - Xvfb installed
    - ONKI component needs to be in kata.ini ckan footer with HTTPS protocol

These must be installed manually, they are not part of the Kata RPM packages.

To run as apache user do these also:
    mkdir /var/www/.gnome2
    chown apache:apache /var/www/.gnome2/
    chown apache:apache /var/www/.mozilla/

These tests need CKAN to be running so they cannot be combined with normal tests. Also they use your
main CKAN database.

To run from pyenv:
    xvfb-run nosetests ckanext-kata/ckanext/kata/testselenium/test_selenium.py
or
    ./ckanext-kata/nose.sh selenium
"""

from functools import partial
import pexpect

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementNotVisibleException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By

import time

from unittest import TestCase


class TestBasics(TestCase):
    """Some basic Selenium tests for Kata's user interface without logged in user."""

    @classmethod
    def setup_class(cls):
        """Initialize tests."""
        cls.browser = webdriver.Firefox()  # Get local session of firefox

    @classmethod
    def teardown_class(cls):
        """Uninitialize tests."""
        cls.browser.quit()

    def test_front_page_loads(self):
        """Test that Selenium can access the front page."""

        self.browser.get("https://localhost/")
        assert "Etsin" in self.browser.title

    def test_navigation(self):
        """
        Test that Selenium can access the navigation and all are present.
        """
        # These tests are very clumsy and should be made more sane in the future

        self.browser.get("https://localhost/")
        try:
            search = self.browser.find_element_by_xpath("//a[contains(@href, '/dataset')]")
        except NoSuchElementException:
            assert 0, 'Search (dataset) navigation not found for anonymous user'
        try:
            search = self.browser.find_element_by_xpath("//a[contains(@href, '/dataset/new')]")
        except NoSuchElementException:
            assert 0, 'Add dataset navigation not found for anonymous user'
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
            search = self.browser.find_element_by_xpath("//a[contains(@href, '/user/login')]")
        except NoSuchElementException:
            assert 0, 'Log in link not found for anonymous user'


class TestWithUser(TestCase):
    """Some basic Selenium tests for user interface with a logged in user."""

    @classmethod
    def setup_class(cls):
        """Initialize tests."""

        cls.sysadmin = 'selenium_admin'
        cls.sysadmin_pwd = 'selenium'

        # Create a sysadmin user using paster. Required for adding an organization.
        try:
            child = pexpect.spawn('paster', ['--plugin=ckan', 'sysadmin', 'add', cls.sysadmin, '-c', '/etc/kata.ini'])
            # child.logfile = sys.stderr    # Uncomment to show output
            child.expect('Create new user: .+')
            child.sendline('y')
            child.expect('Password: ')
            child.sendline(cls.sysadmin_pwd)
            child.expect('Confirm password: ')
            child.sendline(cls.sysadmin_pwd)
            child.expect('Added .+ as sysadmin')
        except pexpect.EOF:
            # Sysadmin probably exists already
            pass

    @classmethod
    def teardown_class(cls):
        """Uninitialize tests."""

        # Remove sysadmin user using paster.
        try:
            child = pexpect.spawn('paster', ['--plugin=ckan', 'sysadmin', 'remove', cls.sysadmin, '-c', '/etc/kata.ini'])
            # child.logfile = sys.stderr    # Uncomment to show output
            child.expect('Access OK.')
        except pexpect.EOF:
            # Sysadmin probably exists already
            pass

    def _register_user(self, reg_browser, username=u'seleniumuser', fullname=u'seleniumuser'):
        """Register a new user, will be logged in automatically."""

        reg_browser.get("https://localhost/en/user/register")

        try:
            field = reg_browser.find_element_by_xpath("//input[@id='field-username']")
            field.send_keys(username)

            field = reg_browser.find_element_by_xpath("//input[@id='field-fullname']")
            field.send_keys(fullname)

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
            WebDriverWait(reg_browser, 30).until(expected_conditions.presence_of_element_located((By.XPATH, "//i[contains(@class, 'icon-signout')]")))
        except TimeoutException:
            reg_browser.get_screenshot_as_file('_register_user.png')
            reg_browser.quit()
            assert 0, "User registration didn't finish"

    def _add_dataset(self, browser, organization):
        """
        Add a simple dataset. Return dataset address.
        """

        browser.get("https://localhost/en/dataset/new")
        browser.implicitly_wait(8)  # Wait for javascript magic to alter fields

        try:
            field = browser.find_element_by_xpath("//input[@id='langtitle__0__value_id']")
            field.send_keys('Selenium Dataset')

            field = browser.find_element_by_xpath("//input[@name='agent__0__name']")
            field.send_keys('Selenium')

            field = browser.find_element_by_xpath("//input[@name='agent__0__organisation']")
            field.send_keys('CSC Oy')

            # Keywords -- the actual autocomplete field lacks the id attribute, so find it through an ancestor's sibling
            field = browser.find_element_by_xpath(
                "//input[@id='field-tags']/../div[@class='select2-container select2-container-multi']//input")
            field.send_keys('Selenium')
            field.send_keys(Keys.RETURN)

            field = browser.find_element_by_xpath("//input[@name='langdis']")
            field.click()

            field = browser.find_element_by_xpath("//input[@id='contact__0__name']")
            field.send_keys('Selenium contact')
            field = browser.find_element_by_xpath("//input[@id='contact__0__email']")
            field.send_keys('kata.selenium@gmail.com')
            field = browser.find_element_by_xpath("//input[@id='contact__0__URL']")
            field.send_keys('https://localhost/')
            field = browser.find_element_by_xpath("//input[@id='contact__0__phone']")
            field.send_keys('+35891234567')

            field = browser.find_element_by_xpath("//input[@id='contact_owner']")
            field.click()

            field = browser.find_element_by_xpath("//input[@name='agent__3__name']")
            field.send_keys('Selenium')

            # field = browser.find_element_by_xpath("//select[@id='field-kata-pr']/option[@value='False']")
            # field.click()
            # field.send_keys('Published')

            field = browser.find_element_by_xpath(
                "//section/div/div/div/div[label[text()='Organization']]/div/div/a")  # CKAN Generated field

            ac = ActionChains(browser)
            ac.move_to_element_with_offset(field, 0.1, 0.1).click().perform()

            browser.implicitly_wait(2)
            for o in list(organization) + [Keys.RETURN]:
                ac.send_keys(o).perform()
                browser.implicitly_wait(2)

            browser.find_element_by_name("kata-accept-terms").click()
            browser.find_element_by_xpath("//*[contains(text(), 'Save and publish')]").click()

        except NoSuchElementException:
            browser.get_screenshot_as_file('_add_dataset.png')
            assert 0, "Error processing the create dataset page"

        try:
            WebDriverWait(browser, 30).until(expected_conditions.presence_of_element_located((By.XPATH, "//article/div/a[.='Hide/show']")))
        except TimeoutException:
            browser.get_screenshot_as_file('_add_dataset.png')
            browser.quit()
            assert 0, "Dataset creation didn't finish"

        if not "Selenium Dataset" in browser.title:
            browser.get_screenshot_as_file('_add_dataset.png')
            browser.quit()
            assert 0, "Dataset creation failed somehow"

        return ''.join(browser.current_url)

    def _create_organization(self, organization_name, user_name, user_role):
        '''
        Create an organization and add a user to it.
        :return:
        '''

        driver = webdriver.Firefox()

        try:
            driver.get("https://localhost/en/user/login")
            driver.find_element_by_link_text("Log in").click()
            WebDriverWait(driver, 30).until(expected_conditions.presence_of_element_located((By.ID, "field-login")))
            driver.find_element_by_id("field-login").clear()
            driver.find_element_by_id("field-login").send_keys(self.sysadmin)
            driver.find_element_by_id("field-password").clear()
            driver.find_element_by_id("field-password").send_keys(self.sysadmin_pwd)
            driver.find_element_by_css_selector("button.btn.btn-primary").click()

            WebDriverWait(driver, 30).until(expected_conditions.presence_of_element_located((By.XPATH, "//i[contains(@class, 'icon-signout')]")))
            driver.get("https://localhost/en/organization/new")

            driver.find_element_by_id("field-title").clear()
            driver.find_element_by_id("field-title").send_keys(organization_name)
            WebDriverWait(driver, 30).until(expected_conditions.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Edit')]")))
            driver.find_element_by_xpath("//button[contains(text(), 'Edit')]").click()
            driver.find_element_by_id("field-url").clear()
            driver.find_element_by_id("field-url").send_keys(organization_name)
            driver.find_element_by_id("field-description").clear()
            driver.find_element_by_id("field-description").send_keys("Doing some testing")
            driver.find_element_by_name("save").click()

            WebDriverWait(driver, 30).until(expected_conditions.presence_of_element_located((By.PARTIAL_LINK_TEXT, "Follow")))

            driver.get("https://localhost/en/organization/members/" + organization_name)

            driver.find_element_by_partial_link_text("Add Member").click()
            WebDriverWait(driver, 30).until(expected_conditions.presence_of_element_located((By.XPATH, "//div/a/span[text()='Username']")))

            member_element = driver.find_element_by_xpath("//div/a/span[text()='Username']")
            member_element.send_keys(Keys.RETURN)

            member_element = driver.find_element_by_xpath("html/body/div/div/input")
            member_element.send_keys(user_name)

            member_element.send_keys(Keys.RETURN)

            role_element = driver.find_element_by_xpath("//div/a/span[text()='Member']")
            role_element.send_keys(Keys.RETURN)

            role_element = driver.find_element_by_xpath("html/body/div/div/input")
            role_element.send_keys(user_role)

            role_element.send_keys(Keys.RETURN)

            driver.find_element_by_name("submit").click()

            WebDriverWait(driver, 30).until(expected_conditions.presence_of_element_located((By.XPATH, "//h3[contains(text(), '2 members')]")))

        except (TimeoutException, NoSuchElementException):
            driver.get_screenshot_as_file('_create_organization.png')
            driver.quit()
            raise

        driver.quit()

    def test_register_user_fullname_utf8(self):
        """
        Test for user registration with special characters.
        """
        browser = webdriver.Firefox()
        self._register_user(browser, username=u'selenium_unicode_user' + str(int(time.time()*100)), fullname=u'АБВГДЕЁЖЗИЙ κόσμε...')
        browser.quit()

    def test_add_dataset_and_contact_form(self):
        """Test that user can go back from contact form and still go forward to send it."""

        browser = webdriver.Firefox()
        username = u'selenium_contact_user' + str(int(time.time()*100))
        self._register_user(browser, username=username)

        org_name = 'seleniumtesting' + str(int(time.time()*100))
        self._create_organization(org_name, username, 'editor')

        dataset_url = self._add_dataset(browser, org_name)
        browser.quit()

        browser = webdriver.Firefox()  # Get a new session
        self._register_user(browser, username='selenium_contact_user' + str(int(time.time()*100)))

        assert dataset_url is not None, "dataset url not found"

        # Go to contact form
        contact_form_url = dataset_url.replace('/dataset/', '/contact/')
        browser.get(dataset_url)

        browser.get(contact_form_url)
        try:
            browser.find_element_by_xpath("//textarea[@name='msg']")
        except NoSuchElementException:
            browser.get_screenshot_as_file('test_2_contact_form_can_go_back.png')
            assert 0, 'Contact form expected but not found (first visit)'

        browser.back()
        browser.get(contact_form_url)

        try:
            field = browser.find_element_by_xpath("//textarea[@name='msg']")
            field.send_keys('Selenium is a testing')

            btn = browser.find_element_by_xpath("//input[@value='Send']")
            btn.click()

        except NoSuchElementException:
            browser.get_screenshot_as_file('test_2_contact_form_can_go_back.png')
            assert 0, 'Contact form expected but not found (second visit)'

        try:
            WebDriverWait(browser, 20).until(expected_conditions.presence_of_element_located(
                (By.XPATH, "//div[contains(text(),'Message sent')]")))
        except TimeoutException:
            browser.get_screenshot_as_file('test_2_contact_form_can_go_back.png')
            assert 0, "Sending contact form didn't finish"

        browser.quit()

    def test_navigation(self):
        """
        Test that navigation is ok for logged in user.
        """
        # These should match often twice, clumsy, fix in the future
        browser = webdriver.Firefox()
        self._register_user(browser, username=u'selenium_navigator' + str(int(time.time()*100)))

        browser.get("https://localhost/")
        try:
            search = browser.find_element_by_xpath("//a[contains(@href, '/dataset')]")
        except NoSuchElementException:
            assert 0, 'Search (dataset) navigation not found for logged in user'
        try:
            search = browser.find_element_by_xpath("//a[contains(@href, '/dataset/new')]")
        except NoSuchElementException:
            assert 0, 'Add dataset navigation not found for logged in user'
        try:
            search = browser.find_element_by_xpath("//a[contains(@href, '/about')]")
        except NoSuchElementException:
            assert 0, 'About navigation not found for logged in user'
        try:
            search = browser.find_element_by_xpath("//a[contains(@href, '/help')]")
        except NoSuchElementException:
            assert 0, 'Help navigation not found for logged in user'
        try:
            search = browser.find_element_by_xpath("//a[contains(@href, '/faq')]")
        except NoSuchElementException:
            assert 0, 'FAQ navigation not found for logged in user'
        try:
            search = browser.find_element_by_xpath("//a[contains(@href, '/dashboard')]")
        except NoSuchElementException:
            assert 0, 'Notifications link not found for logged in user'
        try:
            search = browser.find_element_by_xpath("//a[contains(@href, '/user/_logout')]")
        except NoSuchElementException:
            assert 0, 'Log out link not found for logged in user'
#        try:
#            search = browser.find_element_by_xpath("//a[contains(@href, '/#')]")
#        except NoSuchElementException:
#            assert 0, 'Drop down (profile menu) link not found for logged in user'
        try:
            search = browser.find_element_by_xpath("//a[contains(@href, '/user/selenium')]")
        except NoSuchElementException:
            assert 0, 'My datasets link not found for logged in user'

        browser.quit()

    def test_logout(self):
        """
        Test logout for Selenium user.
        """

        browser = webdriver.Firefox()
        self._register_user(browser, username=u'selenium_logoutter' + str(int(time.time()*100)))

        browser.get("https://localhost/en/user/_logout")

        try:

            assert browser.current_url, "https://localhost/"
        except NoSuchElementException:
            browser.get_screenshot_as_file('test_9_test_logout.png')
            assert 0, "Error logging out"

        browser.quit()

    def _add_dataset_advanced(self, browser, dataset_list):
        """
        Create a dataset with values from argument dataset_list.

        dataset_list element format:
        (element_search_function, function_parameter, keyboard_input_to_element (or WebElement.click), wait_for)

        :return dataset url
        """

        browser.get("https://localhost/en/dataset/new")

        # TODO: rather wait for a certain element that the js creates
        browser.implicitly_wait(15)  # Wait for javascript magic to alter fields

        try:
            for (funct, param, values, wait_for) in dataset_list:

                print ("%r ( %r ) : %r " % (funct, param, values))
                field = funct(param)

                for value in values:
                    if value == WebElement.click:
                        field.click()
                    else:
                        field.send_keys(value)
                    if wait_for:
                        wait_for()

        except (NoSuchElementException, ElementNotVisibleException, TimeoutException):
            browser.get_screenshot_as_file('_add_dataset_advanced.png')
            browser.quit()
            raise

        if not "Selenium Dataset" in browser.title:
            browser.get_screenshot_as_file('_add_dataset_advanced.png')
            browser.quit()
            assert 0, "Dataset creation failed somehow"

        return browser.current_url



    # TODO: Fix this test

    # def test_add_dataset_all_fields(self):
    #     """
    #     Create a dataset with all fields filled.
    #
    #     Also test that advanced search can find the dataset.
    #     """
    #
    #     browser = webdriver.Firefox()
    #
    #     username = u'selenium_advanced_user' + str(int(time.time()*100))
    #     self._register_user(browser, username=username)
    #
    #     org_name = 'seleniumtesting' + str(int(time.time()*100))
    #     self._create_organization(org_name, username, 'editor')
    #
    #     def _choose_organization(organization):
    #         '''
    #         Choose an organization from dropdown menu
    #         '''
    #         element = browser.find_element_by_xpath(
    #             "//section/div/div/div[label[text()='Choose an organization']]/div/div/a")  # CKAN Generated field
    #
    #         ac = ActionChains(browser)
    #         ac.move_to_element_with_offset(element, 0.1, 0.1).click().perform()
    #
    #         browser.implicitly_wait(2)
    #         for o in list(organization) + [Keys.RETURN]:
    #             ac.send_keys(o).perform()
    #             browser.implicitly_wait(2)
    #
    #     def _choose_visibility(visibility):
    #         '''
    #         Choose visibility
    #         '''
    #         element = browser.find_element_by_xpath(
    #             "//section/div/div/div[label[text()='Choose an organization']]/div/div/a")
    #
    #         ac = ActionChains(browser)
    #         ac.move_to_element_with_offset(element, 0.1, 0.1).click().perform()
    #
    #         browser.implicitly_wait(2)
    #         for o in list(visibility) + [Keys.RETURN]:
    #             ac.send_keys(o).perform()
    #             browser.implicitly_wait(2)
    #
    #     def wait_for_element(wait_for):
    #         '''Wrap WebDriverWait
    #         :param wait_for: tuple containing locator strategy and element name, for example (By.NAME, 'agent__4__name')
    #         '''
    #         WebDriverWait(browser, 30).until(expected_conditions.presence_of_element_located(wait_for))
    #
    #     # TODO: Use all fields.
    #
    #     dataset_to_add = [
    #         # Add titles
    #         (browser.find_element_by_id, 'langtitle__0__value_id', [u'Advanced Selenium Dataset'], None),
    #         (browser.find_element_by_name, 'langtitle__0__lang', [u'en'], None),
    #         # (browser.find_element_by_id, 'title__1__value_id', [u'Selenium-tietoaineisto'], None),
    #         # (browser.find_element_by_name, 'title__1__lang', [u'fi'], None),
    #         # (browser.find_element_by_id, 'title__2__value_id', [u'Selenium ÅÄÖ'], None),
    #         # (browser.find_element_by_name, 'title__2__lang', [u'sv'], None),
    #
    #         # Add authors
    #         (browser.find_element_by_name, 'agent__0__name', [u'Ascii Author'], None),
    #         (browser.find_element_by_name, 'agent__0__organisation', [u'CSC Oy'], None),
    #
    #         (browser.find_element_by_id, 'authors_add', [WebElement.click],
    #          partial(wait_for_element, (By.NAME, 'agent__4__name'))),
    #         (browser.find_element_by_name, 'agent__4__name', [u'Åke Author'], None),
    #         (browser.find_element_by_name, 'agent__4__organisation', [u'Organization 2'], None),
    #
    #         (browser.find_element_by_id, 'authors_add', [WebElement.click],
    #          partial(wait_for_element, (By.NAME, 'agent__5__name'))),
    #         (browser.find_element_by_name, 'agent__5__name', [u'прстуфхцчшчьыъэюя Author'], None),
    #         (browser.find_element_by_name, 'agent__5__organisation', [u'Organization 3'], None),
    #
    #         # keywords
    #         (browser.find_element_by_xpath,
    #          "//input[@id='field-tags']/../div[@class='select2-container select2-container-multi']//input",
    #          ['Selenium', Keys.RETURN, 'Keyword2', Keys.RETURN], None),
    #
    #         (browser.find_element_by_id, 'language', [u'eng, fin, swe, tlh'], None),
    #
    #         (browser.find_element_by_id, 'contact__0__name', [u'Selenium'], None),
    #         (browser.find_element_by_id, 'contact__0__phone', [u'+35891234567'], None),
    #         (browser.find_element_by_id, 'contact__0__email', [u'kata.selenium@gmail.com'], None),
    #         (browser.find_element_by_id, 'contact__0__URL', [u'https://localhost/'], None),
    #
    #         (browser.find_element_by_id, 'contacts_add', [WebElement.click],
    #          partial(wait_for_element, (By.NAME, 'contact__1__name'))),
    #
    #         (browser.find_element_by_id, 'contact__1__name', [u'Selenium 2'], None),
    #         (browser.find_element_by_id, 'contact__1__phone', [u'+35881234567'], None),
    #         (browser.find_element_by_id, 'contact__1__email', [u'kata.selenium@gmail.com'], None),
    #         (browser.find_element_by_id, 'contact__1__URL', [u'https://localhost/test2'], None),
    #
    #         (browser.find_element_by_name, 'projdis', [WebElement.click], None),
    #
    #         (browser.find_element_by_name, 'agent__2__organisation', [u'Selenium Project'], None),
    #         (browser.find_element_by_name, 'agent__2__name', [u'Selenium Funder'], None),
    #         (browser.find_element_by_name, 'agent__2__fundingid', [u'Selenium Funding'], None),
    #         (browser.find_element_by_name, 'agent__2__URL', [u'https://localhost/'], None),
    #
    #         (browser.find_element_by_id, 'funders_add', [WebElement.click],
    #          partial(wait_for_element, (By.NAME, 'agent__6__organisation'))),
    #         (browser.find_element_by_name, 'agent__6__organisation', [u'Selenium Project 2'], None),
    #         (browser.find_element_by_name, 'agent__6__fundingid', [u'Selenium Funding 2'], None),
    #
    #         (browser.find_element_by_name, 'agent__3__name', [u'прстуфхцчшчьыъэюя'], None),
    #         (browser.find_element_by_id, 'owners_add', [WebElement.click],
    #          partial(wait_for_element, (By.NAME, 'agent__7__name'))),
    #         (browser.find_element_by_name, 'agent__7__name', [u'прстуфхцчшчьыъэюя 2'], None),
    #
    #         (browser.find_element_by_id, 'pids__0__id', [u'data-pid-' + str(int(time.time() * 100))], None),
    #         # (browser.find_element_by_id, 'pids__0__provider', [u'Selenium'], None),
    #         (browser.find_element_by_name, 'pids__1__type', [u'Metadata'], None),
    #         (browser.find_element_by_name, 'pids__1__id', [u'metadata-pid-' + str(int(time.time() * 100))], None),
    #         # (browser.find_element_by_id, 'pids__1__provider', [u'Selenium'], None),
    #         (browser.find_element_by_id, 'pids_add', [WebElement.click],
    #          partial(wait_for_element, (By.NAME, 'pids__2__type'))),
    #         (browser.find_element_by_name, 'pids__2__type', [u'Version'], None),
    #         (browser.find_element_by_name, 'pids__2__id', [u'version-pid-' + str(int(time.time() * 100))], None),
    #         # (browser.find_element_by_id, 'pids__2__provider', [u'Selenium'], None),
    #
    #         (browser.find_element_by_id, 'direct_download', [Keys.SPACE], None),
    #         (browser.find_element_by_id, 'direct_download_URL', [u'https://localhost/'], None),
    #
    #         (_choose_organization, org_name, [], None),
    #
    #         # THIS IS THE PROPER WAY TO CHOOSE AN OPTION FROM SELECT ELEMENT
    #         (browser.find_element_by_xpath, "//select[@name='private']/option[text()='Published']",
    #          [WebElement.click], None),
    #
    #         # recommended info
    #
    #         (browser.find_element_by_xpath,
    #          "//input[@id='geographic_coverage_field']/../div[@class='select2-container select2-container-multi']//input",
    #          [u'Espoo, Finland', Keys.RETURN], None),
    #         # (browser.find_element_by_id, 'geographic_coverage_field', [u'Espoo, Finland', Keys.RETURN], None),
    #
    #         #(find_select2_choice_inputs, 2, ['Ultimate Selenium collection', Keys.ENTER], None),  # collection / series
    #         #(find_select2_choice_inputs, 2, ['Selenium discipline', Keys.RETURN], None),  # discipline
    #
    #         (browser.find_element_by_xpath,
    #          "//input[@id='discipline_field']/../div[@class='select2-container select2-container-multi']//input",
    #          [u'Matematiikka', Keys.RETURN], None),
    #         # (browser.find_element_by_id, 'discipline_field', [u'Matematiikka', Keys.RETURN], None),
    #
    #         (browser.find_element_by_xpath,
    #          "//input[@id='mimetype']/../div[@class='select2-container select2-container-multi']//input",
    #          [u'application/pdf', Keys.RETURN], None),
    #         (browser.find_element_by_id, 'checksum', [u'f60e586509d99944e2d62f31979a802f'], None),
    #         (browser.find_element_by_id, 'algorithm', [u'md5'], None),
    #
    #         (browser.find_element_by_id, 'field-notes', [u'Some description about this dataset'], None),
    #
    #         (browser.find_element_by_xpath, "//button[@name='save']", [WebElement.click], None)
    #     ]
    #
    #     dataset_url = self._add_dataset_advanced(browser, dataset_to_add)
    #
    #     # Use search to test that the new dataset (or some other similar dataset...) is found from index.
    #
    #     browser.get("https://localhost/en/dataset")
    #
    #     try:
    #         btn = browser.find_element_by_xpath("//a[contains(@href, '#advanced-search-tab')]")
    #         btn.click()
    #
    #         WebDriverWait(browser, 30).until(expected_conditions.presence_of_element_located((By.ID, 'advanced-search-date-end')))
    #
    #         field = browser.find_element_by_id("advanced-search-text-1")
    #         field.send_keys('Advanced Selenium')
    #         field.send_keys(Keys.ENTER)
    #
    #         WebDriverWait(browser, 30).until(expected_conditions.presence_of_element_located((By.XPATH, "//footer")))
    #
    #         browser.find_element_by_xpath("//li/div/h3/a[contains(text(),'Advanced Selenium Dataset')]")
    #
    #     except (TimeoutException, NoSuchElementException):
    #         browser.get_screenshot_as_file('test_3_advanced_search.png')
    #         raise
    #
    #     browser.quit()
