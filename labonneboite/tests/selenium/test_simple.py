import time

from selenium.webdriver.common.by import By

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .base import LbbSeleniumTestCase


class TestSimple(LbbSeleniumTestCase):

    def test_search(self):
        """
        Tests the search mechanism of the home page.
        """
        wait = WebDriverWait(self.driver, 5)

        self.driver.get(self.url_for('root.home'))
        job_element = self.driver.find_element_by_id('j')
        location_element = self.driver.find_element_by_id('l')
        submit_element = self.driver.find_element_by_css_selector('.lbb-home-form-search button')

        self.assertTrue(submit_element.is_enabled(), 'By default the submit button should be enable')

        job_element.send_keys('boucher')
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, '#ui-id-1 .ui-menu-item:first-child')))
        job_element.send_keys(Keys.DOWN)
        job_element.send_keys(Keys.RETURN)
        self.assertElementIsFocus(location_element, 'When selecting a job, the location should be focus')

        location_element.send_keys('metz')
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, '#ui-id-2 .ui-menu-item:first-child')))
        location_element.send_keys(Keys.DOWN)
        location_element.send_keys(Keys.RETURN)

        self.assertElementIsFocus(submit_element, 'When selecting a location, the submit button should be focus')
        submit_element.click()
        elements = self.driver.find_elements_by_class_name('lbb-company')
        self.assertEqual(1, len(elements))
