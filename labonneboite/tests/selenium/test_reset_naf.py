# coding: utf8
import time
import urlparse

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

        url = urlparse.urlparse(self.driver.current_url)
        parameters = dict(urlparse.parse_qsl(url.query))
        self.assertEqual('/entreprises', url.path)
        self.assertEqual('comptabilite', parameters['occupation'])
        self.assertEqual('metz', parameters['city']) # city parameter is defined on redirect
        self.assertEqual('57000', parameters['zipcode'])
        self.assertNotIn('naf', parameters)

        # Filter by NAF `Activités comptables` (`6920Z`).
        select = Select(self.driver.find_element_by_id('naf'))
        select.select_by_value(u'6920Z')

        # The form should be auto-submitted after an option has been selected.
        url = urlparse.urlparse(self.driver.current_url)
        parameters = dict(urlparse.parse_qsl(url.query))
        self.assertEqual('/entreprises', url.path)
        self.assertEqual('comptabilite', parameters['occupation'])
        self.assertEqual('Metz (57000)', parameters['l']) # form value is now full city name
        self.assertEqual('6920Z', parameters['naf'])

        # Perform another search on `boucher`.
        job_input = self.driver.find_element_by_name('j')
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
        url = urlparse.urlparse(self.driver.current_url)
        parameters = dict(urlparse.parse_qsl(url.query))
        self.assertEqual('/entreprises', url.path)
        self.assertEqual('boucherie', parameters['occupation'])
        self.assertEqual('Metz (57000)', parameters['l']) # form value is now full city name
        self.assertNotIn('naf', parameters)
