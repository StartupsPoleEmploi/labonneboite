# coding: utf8
import time

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

from .base import LbbSeleniumTestCase


class TestResetNaf(LbbSeleniumTestCase):

    def test_reset_naf(self):
        """
        Ensure that the NAF filter is reset when a new job search is performed.
        """
        # Search results for `comptabilite` in `Metz`.
        url = self.url_for('search.results', city='metz', zipcode='57000', occupation='comptabilite')
        self.driver.get(url)

        self.assertIn('/entreprises/metz-57000/comptabilite', self.driver.current_url)
        self.assertNotIn('naf=', self.driver.current_url)

        # Filter by NAF `Activités comptables` (`6920Z`).
        select = Select(self.driver.find_element_by_id('naf'))
        select.select_by_value(u'6920Z')

        # The form should be auto-submitted after an option has been selected.
        self.assertIn('/entreprises/metz-57000/comptabilite', self.driver.current_url)
        self.assertIn('naf=6920Z&d', self.driver.current_url)

        # Perform another search on `boucher`.
        job_input = self.driver.find_element_by_id('job')
        job_input.clear()  # Reset the previous `comptabilite` search term.
        job_input.send_keys('boucher')
        time.sleep(3)  # The `staging` is really slow and can take a long time to show results.
        job_input.send_keys(Keys.DOWN)
        job_input.send_keys(Keys.RETURN)

        # Hide the debug toolbar, otherwise it would overlap the submit button of the form.
        # Actually, no. This is only necessary in development mode.
        # self.driver.find_element_by_id('flHideToolBarButton').click()

        # Submit the search form.
        self.driver.find_element_by_css_selector('form.js-search-form div.form-search button').click()

        # The NAF filter should be reset.
        self.assertIn('/entreprises/metz-57000/boucherie', self.driver.current_url)
        self.assertNotIn('naf=', self.driver.current_url)
