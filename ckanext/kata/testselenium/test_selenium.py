'''
Selenium tests

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
        cls.browser = webdriver.Firefox()  # Get local session of firefox

    @classmethod
    def teardown_class(cls):
        cls.browser.quit()

    def _register_user(self, reg_browser):
        '''Register a new user, will be logged in automatically.'''

        reg_browser.get("https://localhost/en/user/register")

        try:
            element = WebDriverWait(reg_browser, 60).until(expected_conditions.presence_of_element_located((By.XPATH, "/body/footer")))
        except TimeoutException:
            reg_browser.get_screenshot_as_file('test_0_register_user.png')
        finally:
            field = reg_browser.find_element_by_xpath("//input[@id='field-username']")
            field.send_keys('seleniumuser' + str(int(time.time()*100)))

            field = reg_browser.find_element_by_xpath("//input[@id='field-fullname']")
            field.send_keys('seleniumuser' + str(int(time.time()*100)))

            field = reg_browser.find_element_by_xpath("//input[@id='field-email']")
            field.send_keys('seleniumuser@kata.fi')

            field = reg_browser.find_element_by_xpath("//input[@id='field-password']")
            field.send_keys('seleniumuser')

            field = reg_browser.find_element_by_xpath("//input[@id='field-confirm-password']")
            field.send_keys('seleniumuser')

            btn = reg_browser.find_element_by_xpath("//button[@name='save']")
            btn.click()

            return

        assert 0, "Error processing the user registration page"
        

    def test_front_page_loads(self):
        """Test that Selenium can access the front page."""

        self.browser.get("https://localhost/")
        assert "Kata" in self.browser.title

    def test_0_register_user(self):
        '''Test user registration. Named so because tests are run in alphabetical order.'''

        self._register_user(self.browser)


    def test_1_add_dataset(self):
        '''
        Add a simple dataset.
        '''

        test_browser = webdriver.Firefox()  # Get a new session because of a possible dialog pop-up
        self._register_user(test_browser)
        
        test_browser.get("https://localhost/en/dataset/new")

        try:
            element = WebDriverWait(test_browser, 60).until(expected_conditions.presence_of_element_located((By.XPATH, "/body/footer")))
        except TimeoutException:
            test_browser.get_screenshot_as_file('test_1_add_dataset.png')
        finally:
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

                field = test_browser.find_elements_by_class_name('select2-input')[2]  # hopefully distributor name
                field.send_keys('Selenium')
                field.send_keys(Keys.RETURN)

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

                btn = test_browser.find_element_by_xpath("//button[@name='save']")
                btn.click()

            except NoSuchElementException:
                test_browser.get_screenshot_as_file('test_1_add_dataset.png')
            finally:

                try:
                    element = WebDriverWait(test_browser, 30).until(expected_conditions.presence_of_element_located((By.LINK_TEXT, "RDF")))
                except TimeoutException:
                    assert 0, "Dataset creation didn't finish"
                    return
                finally:
                    assert "Kata" in test_browser.title, "Dataset creation failed"

                    test_browser.quit()
                    return


        test_browser.quit()

        assert 0, "Error processing the create dataset page"


    def test_2_contact_form_can_go_back(self):
        '''Test that user can go back from contact form and still go forward to send it.'''

        #self.browser.close()
        #self.browser = webdriver.Firefox()

        # Get a new user to test the contacting.
        #self.test_0_register_user()
        pass


