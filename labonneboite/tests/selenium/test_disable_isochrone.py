"""
If ENABLE_ISOCHRONES is set to False in settings,
isochrone features should be hidden.
"""

import re

from unittest.mock import patch
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from labonneboite.conf import settings
from .base import LbbSeleniumTestCase


class TestSearchWithoutIsochrone(LbbSeleniumTestCase):

    # @patch.multiple(settings, ENABLE_ISOCHRONES=False)
    # def create_app(self):
    #     """
    #     Override app settings to disable isochrone features.
    #     PROBLEM: it overrides settings for all selenium tests!
    #     """
    #     app = super().create_app()
    #     settings.ENABLE_ISOCHRONES=False
    #     return app.test_client()


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

        # Click on the Memo button.
        memo_button = WebDriverWait(self.driver, 60)\
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


    def test_search(self):
        """
        Test that isochrone features are not active
        but distance filters are still displayed.
        """

        # Store current results
        results_sentence = self.driver.find_element_by_css_selector('h1.lbb-result-info').text
        primitive_results = re.match(r'(\d+)', results_sentence).group()

        # Assert duration filter is not displayed
        duration_filter = self.driver\
            .find_elements_by_css_selector('.switch-element[data-switch-value="duration"]')

        self.assertFalse(duration_filter)

        # Assert distance filter is displayed
        distances_list = self.driver\
            .find_element_by_css_selector('#d')\
            .is_displayed()
        self.assertTrue(distances_list)

        # Click on a duration
        self.driver.find_element_by_css_selector('#d input[value="5"]').click()

        # wait for a new page result to show
        new_title = WebDriverWait(self.driver, 60)\
                    .until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, "h1.lbb-result-info"))
                    )

        # Assert new results
        results_sentence = new_title.text
        last_results = re.match(r'(\d+)', results_sentence).group()

        self.assertEqual(last_results, '7')

        # Make sure we don't have the same results
        self.assertLessEqual(int(last_results), int(primitive_results))


    def test_commute_time_is_not_displayed(self):
        """
        If isochrone features are disabled,
        office details should not include commute time
        but still display the distance.
        """

        travel_distance_duration = self.driver\
            .find_element_by_css_selector('.lbb-result .travel-distance-duration')

        distance_is_displayed = travel_distance_duration.is_displayed()
        self.assertTrue(distance_is_displayed)

        commute_time_is_displayed = travel_distance_duration\
                    .find_element_by_css_selector('.travel-duration')\
                    .is_displayed()

        self.assertFalse(commute_time_is_displayed)
