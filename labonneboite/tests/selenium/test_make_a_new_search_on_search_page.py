
import time
import re

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC

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

        # Accept RGPD, otherwise selecting isochrone filters is not possible. ¯\_(ツ)_/¯
        self.driver.find_element_by_xpath("//button[@class='rgpd-accept']").click()


    def test_make_a_new_search_changing_location(self):
        """
        Test that a user can change location directly
        in a search results page using a form.
        """
        city = 'Nancy'
        results_sentence = self.driver.find_element_by_css_selector('h1.lbb-result-info').text
        primitive_results = re.match(r'(\d+)', results_sentence).group()

        shown_search_form = self.driver.find_element_by_css_selector('#shown-search-form')

        location_field = shown_search_form.find_element_by_css_selector('#l')
        location_field.clear()
        location_field.send_keys(city)
        time.sleep(2)
        location_field.send_keys(Keys.DOWN)
        location_field.send_keys(Keys.RETURN)

        shown_search_form.find_element_by_css_selector('button').click()

        WebDriverWait(self.driver, 60)\
            .until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "h1.lbb-result-info"))
            )

        results_sentence = self.driver.find_element_by_css_selector('h1.lbb-result-info').text
        last_results = re.match(r'(\d+)', results_sentence).group()

        self.assertIn(city, results_sentence)
        self.assertEqual(last_results, '3')
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



    def test_make_a_new_search_using_isochronous_features(self):
        """
        Test that changing a search field does not affect
        isochronous features.
        """
        city = 'Nancy'
        shown_search_form = self.driver.find_element_by_css_selector('#shown-search-form')

        location_field = shown_search_form.find_element_by_css_selector('#l')
        location_field.clear()
        location_field.send_keys(city)
        time.sleep(2)
        location_field.send_keys(Keys.DOWN)
        location_field.send_keys(Keys.RETURN)

        shown_search_form.find_element_by_css_selector('button').click()

        WebDriverWait(self.driver, 60)\
            .until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "h1.lbb-result-info"))
            )

        results_sentence = self.driver.find_element_by_css_selector('h1.lbb-result-info').text
        primitive_results = re.match(r'(\d+)', results_sentence).group()

        # Click on "min"
        self.driver.find_element_by_css_selector('.switch-element[data-switch-value="duration"]')\
            .click()

        # Travel modes should be visible now
        self.driver.find_element_by_css_selector(
            '.travelmode-choices a.visible[data-travelmode="car"]'
        ).click()

        durations_options = self.driver.find_element_by_css_selector('#isochrone-durations')

        durations_options.find_element_by_css_selector(f'input[value="45"]').click()

        WebDriverWait(self.driver, 60)\
            .until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "h1.lbb-result-info"))
            )

        results_sentence = self.driver.find_element_by_css_selector('h1.lbb-result-info').text
        last_results = re.match(r'(\d+)', results_sentence).group()

        self.assertEqual(last_results, '16')
        self.assertNotEqual(last_results, primitive_results)
