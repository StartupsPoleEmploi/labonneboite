"""
Test search using this isochrone filter: public transports.
Data used in these tests are generated by this SQL script:
docker/alembic/etablissements_tests_selenium.
"""

import re
import urllib.parse

from parameterized import parameterized
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from labonneboite.common.maps.constants import ISOCHRONE_DURATIONS_MINUTES
from .base import LbbSeleniumTestCase


DURATIONS = [(str(duration), ) for duration in ISOCHRONE_DURATIONS_MINUTES]


class TestSearchSelectingPublicTransport(LbbSeleniumTestCase):


    def setUp(self):
        super().setUp()

        url = self.url_for(
            'search.entreprises',
            l='Metz+57000',
            occupation='comptabilite',
            tr='car',
            lat='49.119146',
            lon='6.176026',
        )
        self.driver.get(url)

        # Click on the Memo button.
        memo_button = WebDriverWait(self.driver, 20)\
            .until(
                EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "J'ai compris"))
            )
        memo_button.click()

        # Wait until the Memo overlay is invisible.
        WebDriverWait(self.driver, 60)\
            .until(
                EC.invisibility_of_element_located((By.XPATH, "//div[@class='introjs-overlay']"))
            )

        # Accept RGPD, otherwise selecting isochrone filters is not possible. ¯\_(ツ)_/¯
        self.driver.find_element_by_xpath("//button[@class='rgpd-accept']").click()


    @parameterized.expand(DURATIONS)
    def test_isochrone_search(self, duration):
        """
        Test an isochrone search selecting "public transport" and "{duration} minutes".
        """

        # Store current results
        results_sentence = self.driver.find_element_by_css_selector('h1.lbb-result-info').text
        primitive_results = re.match(r'(\d+)', results_sentence).group()

        # Click on "min"
        self.driver.find_element_by_css_selector('.switch-element[data-switch-value="duration"]')\
            .click()

        # Travel modes should be visible now
        public_button = self.driver.find_element_by_css_selector(
            '.travelmode-choices a.visible[data-travelmode="public"]'
        )
        self.assertTrue(public_button.is_displayed())
        public_button.click()

        # The page should reload with a new search. Wait for it.
        durations_options = WebDriverWait(self.driver, 20)\
            .until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#isochrone-durations"))
            )

        # Filtering by duration should be available now
        durations_options = self.driver.find_element_by_css_selector('#isochrone-durations')
        self.assertTrue(durations_options.is_displayed())

        # click on another duration
        durations_options.find_element_by_css_selector(f'input[value="{duration}"]').click()

        # The page should reload with a new search. Wait for it.
        WebDriverWait(self.driver, 40)\
            .until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#isochrone-durations"))
            )

        # Assert the selected duration and its mode are part of the url.
        current_url = self.driver.current_url
        url = urllib.parse.urlparse(current_url)
        parameters = dict(urllib.parse.parse_qsl(url.query))

        self.assertEqual(parameters['tr'], 'public')
        self.assertEqual(parameters['dur'], duration)

        results_sentence = self.driver.find_element_by_css_selector('h1.lbb-result-info').text
        last_results = re.match(r'(\d+)', results_sentence).group()

        expected_results = {
            '15': '3',
            '30': '4',
            '45': '6',
        }

        self.assertEqual(last_results, expected_results[duration])
        self.assertLessEqual(int(last_results), int(primitive_results))


    def test_commute_time_is_displayed(self):
        """
        Each office details should have a commute time
        displayed along with other information.
        As default transport mode is car, we need to switch
        to public transports to make it appear on details.
        """

        # Click on "min"
        self.driver.find_element_by_css_selector('.switch-element[data-switch-value="duration"]')\
            .click()

        # Travel modes should be visible now
        self.driver.find_element_by_css_selector(
            '.travelmode-choices a.visible[data-travelmode="public"]'
        ).click()

        # Click on any duration to reload the page
        self.driver\
            .find_element_by_css_selector(
                f'#isochrone-durations input[value="{ISOCHRONE_DURATIONS_MINUTES[-1]}"]'
            ).click()

        # Find the first element that matches this CSS selector.
        enterprise_details = self.driver.find_element_by_css_selector('.lbb-result')
        travel_duration_text = enterprise_details.find_element_by_css_selector('.travel-duration').text

        # Make sure duration is displayed.
        self.assertRegex(travel_duration_text, r'(\d+)')

        # Make sure travel mode is displayed
        self.assertIn('transports en commun', travel_duration_text)
