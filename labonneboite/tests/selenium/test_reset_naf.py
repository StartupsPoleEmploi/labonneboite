import time
import urllib.parse

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select, WebDriverWait

from .base import LbbSeleniumTestCase, url_has_changed


class TestResetNaf(LbbSeleniumTestCase):
    def test_reset_naf(self):
        """
        Ensure that the NAF filter is reset when a new job search is performed.
        """
        # Search results for `comptabilite` in `Metz`.
        url = self.url_for("search.results", city="metz", zipcode="57000", occupation="comptabilite")
        self.driver.get(url)

        current_url = self.driver.current_url
        url = urllib.parse.urlparse(current_url)
        parameters = dict(urllib.parse.parse_qsl(url.query))
        self.assertEqual("/entreprises", url.path)
        self.assertEqual("comptabilite", parameters["occupation"])
        self.assertEqual("metz", parameters["city"])  # city parameter is defined on redirect
        self.assertEqual("57000", parameters["zipcode"])
        self.assertNotIn("naf", parameters)

        # Filter by NAF `Activités des agents et courtiers d'assurances` (`6622Z`).
        select = Select(self.driver.find_element_by_id("naf"))
        select.select_by_value("6622Z")
        WebDriverWait(self.driver, 60).until(url_has_changed(current_url))

        # The form should be auto-submitted after an option has been selected.
        current_url = self.driver.current_url
        url = urllib.parse.urlparse(current_url)
        parameters = dict(urllib.parse.parse_qsl(url.query))
        self.assertEqual("/entreprises", url.path)
        self.assertEqual("comptabilite", parameters["occupation"])
        self.assertEqual("Metz (57000)", parameters["l"])
        self.assertEqual("6622Z", parameters["naf"])

        # Perform another search on `boucher`.
        job_input = self.driver.find_element_by_name("j")
        job_input.clear()  # Reset the previous `comptabilite` search term.
        job_input.send_keys("boucher")
        time.sleep(3)
        job_input.send_keys(Keys.DOWN)
        job_input.send_keys(Keys.RETURN)

        # Hide the debug toolbar, otherwise it would overlap the submit button of the form.
        # Actually, no. This is only necessary in development mode.
        # self.driver.find_element_by_id('flHideToolBarButton').click()

        # Submit the search form.
        self.driver.find_element_by_css_selector("#shown-search-form button").click()

        # The NAF filter should be reset.
        WebDriverWait(self.driver, 60).until(url_has_changed(current_url))
        current_url = self.driver.current_url
        url = urllib.parse.urlparse(current_url)
        parameters = dict(urllib.parse.parse_qsl(url.query))
        self.assertEqual("/entreprises", url.path)
        self.assertEqual("boucherie", parameters["occupation"])
        self.assertEqual("Metz (57000)", parameters["l"])  # form value is now full city name
        self.assertNotIn("naf", parameters)
