# coding: utf8
import time

from .base import LbbSeleniumTestCase


class TestResults(LbbSeleniumTestCase):

    def test_toggle_office_details(self):
        """
        Tests the toggle mechanism of the `results` page.
        """
        url = self.url_for('search.results', city='metz', zipcode='57000', occupation='comptabilite')
        self.driver.get(url)

        # Get the HTML element that contains all company informations.
        company_container = self.driver.find_elements_by_class_name('lbb-result')[0]
        time.sleep(0.5)

        # Inspect default state.
        self.assertNotIn('active', company_container.get_attribute('class').split(' '))
        for element in company_container.find_elements_by_class_name('lbb-result__details'):
            self.assertEqual(element.value_of_css_property('display'), 'none')

        toggle_details = self.driver.find_elements_by_class_name('js-result-toggle-details')[0]
        time.sleep(0.5)

        # Hide Memo tooltip (show only the first time)
        memo_button_close_button = self.driver.find_elements_by_class_name('introjs-donebutton')
        if memo_button_close_button:
            memo_button_close_button[0].click()
            time.sleep(0.5)

        # Display company details.
        toggle_details.click()
        time.sleep(0.5)
        self.assertIn('active', company_container.get_attribute('class').split(' '))
        for element in company_container.find_elements_by_class_name('lbb-result__details'):
            self.assertEqual(element.value_of_css_property('display'), 'block')

        # Hide company details.
        toggle_details.click()
        time.sleep(0.5)
        self.assertNotIn('active', company_container.get_attribute('class').split(' '))
        for element in company_container.find_elements_by_class_name('lbb-result__details'):
            self.assertEqual(element.value_of_css_property('display'), 'none')
