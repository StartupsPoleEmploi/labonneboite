import time

from selenium.webdriver.common.keys import Keys

from .base import LbbSeleniumTestCase


class TestSimple(LbbSeleniumTestCase):

    def test_search(self):
        """
        Tests the search mechanism of the home page.
        """
        self.driver.get(self.url_for('root.home'))
        time.sleep(3)
        self.driver.find_element_by_name('j').send_keys('boucher')
        time.sleep(3)
        self.driver.find_element_by_id('j').send_keys(Keys.DOWN)
        self.driver.find_element_by_id('j').send_keys(Keys.RETURN)
        self.driver.find_element_by_id('l').send_keys('metz')
        time.sleep(3)
        self.driver.find_element_by_id('l').send_keys(Keys.DOWN)
        self.driver.find_element_by_id('l').send_keys(Keys.RETURN)
        self.driver.find_element_by_css_selector('.lbb-home-form-search button').click()
        time.sleep(3)
        self.driver.find_element_by_name('j').send_keys('boucher')
        time.sleep(3)
        self.driver.find_element_by_id('j').send_keys(Keys.DOWN)
        self.driver.find_element_by_id('j').send_keys(Keys.RETURN)
        self.driver.find_element_by_css_selector('.lbb-home-form-search button').click()
        time.sleep(3)
        print('\n\n____________')
        self.driver.save_screenshot("screenshot.png")
        print('\n\n')
        elements = self.driver.find_elements_by_class_name('lbb-result')
        self.assertEqual(1, len(elements))
