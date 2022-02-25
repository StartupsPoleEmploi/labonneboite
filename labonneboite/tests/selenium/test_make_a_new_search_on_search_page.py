import time
import re

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from .base import LbbSeleniumTestCase


class TestMakeANewSearchOnSearchPage(LbbSeleniumTestCase):

    def setUp(self):
        super().setUp()
        url = self.url_for(
            'search.entreprises',
            l='Metz+57050',
            occupation='comptabilite',
            tr='car',
            lat='49.119146',
            lon='6.176026',
        )
        self.driver.get(url)

        # Wait a little bit more to ensure things are less flaky
        time.sleep(3)

    def fail_if_no_results(self):
        """
        Fail if there is no result to the search
        This is a check to make sure that the problem lies in the data or in the code
        """
        results_sentence = self.driver.find_element_by_css_selector('body').text
        self.assertNotIn("Nous n'avons pas de résultat", results_sentence,
                         'There is no result for the current search (' + self.driver.current_url + ')')

    def test_make_a_new_search_changing_location(self):
        """
        Test that a user can change location directly
        in a search results page using a form.
        """
        city = 'Nancy'
        current_url = self.driver.current_url

        # utils
        wait = WebDriverWait(self.driver, 5)
        title_selector = (By.CSS_SELECTOR, "h1.lbb-result-info")
        title_present = EC.visibility_of_element_located(title_selector)

        # tests
        self.fail_if_no_results()
        results_sentence = self.driver.find_element(*title_selector).text
        primitive_results = re.match(r'(\d+)', results_sentence).group()

        shown_search_form = self.driver.find_element_by_css_selector('#shown-search-form')

        location_field = shown_search_form.find_element_by_css_selector('#l')
        location_field.clear()
        location_field.send_keys(city)
        time.sleep(2)
        location_field.send_keys(Keys.DOWN)
        location_field.send_keys(Keys.RETURN)

        shown_search_form.find_element_by_css_selector('button').click()

        try:
            wait.until(EC.url_changes(current_url))
        except TimeoutException:
            self.fail('On submit the location didn\'t change')

        self.fail_if_no_results()

        try:
            wait.until(title_present)
        except TimeoutException:
            self.fail('The result title is not locatable')
        
        try:
            wait.until(EC.text_to_be_present_in_element(title_selector, city))
        except TimeoutException:
            results_sentence = self.driver.find_element(*title_selector).text
            self.fail('City (' + city + ') is not in the results (' + results_sentence + ')')

        results_sentence = self.driver.find_element(*title_selector).text
        last_results = re.match(r'(\d+)', results_sentence).group()
        self.assertEqual(last_results, '3', results_sentence)
        self.assertNotEqual(last_results, primitive_results)

    def test_make_a_new_search_changing_occupation(self):
        """
        Test that a user can change occupation directly
        in a search results page using a form.
        """
        occupation = 'Boucher'
        results_sentence = self.driver.find_element_by_css_selector('h1.lbb-result-info').text
        primitive_results = re.match(r'(\d+)', results_sentence).group()

        shown_search_form = self.driver.find_element_by_css_selector('#shown-search-form')

        occupation_field = shown_search_form.find_element_by_css_selector('#j')
        occupation_field.clear()
        occupation_field.send_keys(occupation)
        time.sleep(2)
        occupation_field.send_keys(Keys.DOWN)
        occupation_field.send_keys(Keys.RETURN)

        shown_search_form.find_element_by_css_selector('button').click()

        WebDriverWait(self.driver, 60)\
            .until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "h1.lbb-result-info"))
            )

        results_sentence = self.driver.find_element_by_css_selector('h1.lbb-result-info').text
        last_results = re.match(r'(\d+)', results_sentence).group()

        self.assertIn(occupation, results_sentence)
        self.assertEqual(last_results, '1')
        self.assertNotEqual(last_results, primitive_results)
