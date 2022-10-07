import time

from .base import LbbSeleniumTestCase
from selenium.webdriver.common.by import By


class TestResults(LbbSeleniumTestCase):

    def test_toggle_office_details(self):
        """
        Tests the toggle mechanism of the `results` page.
        """
        url = self.url_for(
            'search.results',
            city='metz',
            zipcode='57000',
            occupation='comptabilite',
        )
        self.driver.get(url)

        # Get the HTML element that contains all company informations.
        company_container = self.driver.find_elements(By.CLASS_NAME, 'lbb-company')[0]
        time.sleep(0.5)

        # Inspect default state.
        self.assertNotIn('active', company_container.get_attribute('class').split(' '))
        for element in company_container.find_elements(By.CLASS_NAME, 'lbb-result__details'):
            self.assertEqual(element.value_of_css_property('display'), 'none')

        toggle_details = self.driver.find_elements(By.CLASS_NAME, 'js-result-toggle-details')[0]
        time.sleep(0.5)

        # Display company details.
        toggle_details.click()
        time.sleep(0.5)
        self.assertIn('active', company_container.get_attribute('class').split(' '))
        for element in company_container.find_elements(By.CLASS_NAME, 'lbb-result__details'):
            self.assertEqual(element.value_of_css_property('display'), 'block')

        # Hide company details.
        toggle_details.click()
        time.sleep(0.5)
        self.assertNotIn('active', company_container.get_attribute('class').split(' '))
        for element in company_container.find_elements(By.CLASS_NAME, 'lbb-result__details'):
            self.assertEqual(element.value_of_css_property('display'), 'none')
