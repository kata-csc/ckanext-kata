'''
Selenium tests

Requirements:
    - Firefox installed
    - Xvfb installed

These must be installed manually, they are not part of the Kata RPM packages.

These tests need CKAN to be running so they cannot be combined with normal tests. Ideally run selenium tests after
normal testing to get an empty database.

To run as apache user:
    mkdir /var/www/.gnome2
    chown apache:apache /var/www/.gnome2/
    chown apache:apache /var/www/.mozilla/


To run from pyenv:

    xvfb-run nosetests ckanext-kata/ckanext/kata/testselenium/test_selenium.py

'''

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium import selenium
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from unittest import TestCase
import time


class TestKataSelenium(TestCase):
    """Selenium tests for Kata CKAN extension."""

    @classmethod
    def setup_class(cls):
        cls.browser = webdriver.Firefox() # Get local session of firefox

    @classmethod
    def teardown_class(cls):
        cls.browser.quit()

    def test_front_page_loads(self):
        """Test that Selenium can access the front page."""

        self.browser.get("https://localhost/")
        assert "Kata" in self.browser.title

    def test_0_register_user(self):
        '''Test user registration. Named so because tests are run in alphabetical order.'''

        self.browser.get("https://localhost/en/user/register")

        try:
            element = WebDriverWait(self.browser, 60).until(expected_conditions.presence_of_element_located((By.XPATH, "/body/footer")))
        except TimeoutException:
            self.browser.get_screenshot_as_file('test_0_register_user.png')
        finally:
            field = self.browser.find_element_by_xpath("//input[@id='field-username']")
            field.send_keys('seleniumuser' + str(int(time.time()*100)))

            field = self.browser.find_element_by_xpath("//input[@id='field-fullname']")
            field.send_keys('seleniumuser' + str(int(time.time()*100)))

            field = self.browser.find_element_by_xpath("//input[@id='field-email']")
            field.send_keys('seleniumuser@kata.fi')

            field = self.browser.find_element_by_xpath("//input[@id='field-password']")
            field.send_keys('seleniumuser')

            field = self.browser.find_element_by_xpath("//input[@id='field-confirm-password']")
            field.send_keys('seleniumuser')

            btn = self.browser.find_element_by_xpath("//button[@name='save']")
            btn.click()

            return

        assert 0, "Error processing the user registration page"


    def test_1_add_dataset(self):
        '''
        Add a simple dataset.

        NOTE: This test should handle the "Are you sure you want to leave page" dialog in case of failure.
        '''

        self.browser.get("https://localhost/en/dataset/new")

        try:
            element = WebDriverWait(self.browser, 60).until(expected_conditions.presence_of_element_located((By.XPATH, "/body/footer")))
        except TimeoutException:
            self.browser.get_screenshot_as_file('test_1_add_dataset.png')
        finally:
            try:
                field = self.browser.find_element_by_xpath("//input[@id='title__0__value_id']")
                field.send_keys('Selenium Dataset')

                field = self.browser.find_element_by_xpath("//input[@id='author__0__value_id']")
                field.send_keys('Selenium')

                field = self.browser.find_element_by_xpath("//input[@id='organization__0__value_id']")
                field.send_keys('CSC Oy')

                field = self.browser.find_elements_by_class_name('select2-input')[1]  # hopefully this is keywords input
                field.send_keys('Selenium')
                field.send_keys(Keys.RETURN)

                field = self.browser.find_element_by_xpath("//input[@name='langdis']")
                field.click()

                field = self.browser.find_elements_by_class_name('select2-input')[2]  # hopefully distributor name
                field.send_keys('Selenium')
                field.send_keys(Keys.RETURN)

                field = self.browser.find_element_by_xpath("//input[@id='phone']")
                field.send_keys('+35891234567')

                field = self.browser.find_element_by_xpath("//input[@id='contactURL']")
                field.send_keys('https://localhost/')

                field = self.browser.find_element_by_xpath("//input[@name='projdis']")
                field.click()

                field = self.browser.find_element_by_xpath("//input[@id='owner']")
                field.send_keys('Selenium')

                field = self.browser.find_element_by_xpath("//input[@id='contact']")
                field.click()

                field = self.browser.find_element_by_xpath("//input[@id='licenseURL']")
                field.send_keys('Shareware')

                btn = self.browser.find_element_by_xpath("//button[@name='save']")
                btn.click()

                self.browser.close()
                self.browser = webdriver.Firefox()
                return

                # TODO: Check that the form didn't produce an error

            except NoSuchElementException:
                self.browser.get_screenshot_as_file('test_1_add_dataset.png')

            # finally:
            #     try:
            #         element = WebDriverWait(self.browser, 60).until(expected_conditions.presence_of_element_located((By.XPATH, "/body")))
            #     except TimeoutException:
            #         assert 0, "Dataset creation didn't finish in 30 seconds"
            #     finally:
            #         assert "Kata" in self.browser.title, "Dataset creation failed"
            #     return

        # Get rid of the dialog which pop's up when navigating away.
        self.browser.close()
        self.browser = webdriver.Firefox()

        assert 0, "Error processing the create dataset page"


    def test_2_contact_form_can_go_back(self):
        '''Test that user can go back from contact form and still go forward to send it.'''

        #self.browser.close()
        #self.browser = webdriver.Firefox()

        # Get a new user to test the contacting.
        #self.test_0_register_user()
        pass


