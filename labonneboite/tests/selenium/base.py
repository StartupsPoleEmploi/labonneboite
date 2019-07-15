import distutils.spawn
import logging

import easyprocess
from flask import url_for as flask_url_for
from flask_testing import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from labonneboite.conf import settings
from labonneboite.web.app import app


class LbbSeleniumTestCase(LiveServerTestCase):
    """
    Sets up the environment for Selenium tests and exposes
    various properties.

    https://docs.python.org/2/library/unittest.html
    http://selenium-python.readthedocs.io/index.html
    https://pythonhosted.org/Flask-Testing/#testing-with-liveserver
    """

    # Note that this test case expects a working SQL and Elasticsearch database

    def create_app(self):
        # Override settings
        settings.API_ADRESSE_BASE_URL = 'https://api-adresse.data.gouv.fr'

        # Random port generation
        app.config['LIVESERVER_PORT'] = 0
        app.config['SERVER_NAME'] = None
        # Disable logging
        app.logger.setLevel(logging.CRITICAL)
        logging.getLogger('werkzeug').setLevel(logging.CRITICAL)
        logging.getLogger('easyprocess').setLevel(logging.CRITICAL)

        return app

    def setUp(self):
        super(LbbSeleniumTestCase, self).setUp()

        self.display = None
        try:
            from pyvirtualdisplay import Display
            display = Display(visible=0, size=(1600, 1600))
            display.start()
        except easyprocess.EasyProcessCheckInstalledError:
            # On some unreliable and exotic OS (such as Mac OS) installing a
            # headless display server such as Xvfb is highly non-trivial. In
            # those cases, we just run Chrome. It's fun and allows the user to
            # view the tests running in real time.
            print("Xvfb is not available. Running selenium tests in non-virtual display.")

        # Chromedriver is often in /usr/lib/chromium-browser/chromedriver
        chromedriver_path = distutils.spawn.find_executable('chromedriver')
        if not chromedriver_path:
            chromedriver_path = distutils.spawn.find_executable('chromedriver', path='/usr/lib/chromium-browser/')
        if not chromedriver_path:
            raise RuntimeError('Missing chromedriver executable. Did you install the chromium-chromedriver package?')

        # Configure logging
        capabilities = DesiredCapabilities.CHROME
        capabilities['loggingPrefs'] = {'browser': 'ALL'}

        self.driver = webdriver.Chrome(desired_capabilities=capabilities, executable_path=chromedriver_path)

        # Ensure that the window size is large enough so that HTML elements won't overlap.
        self.driver.set_window_size(1600, 1200)

        # Implicitely wait at most 10 seconds when trying to select an element
        # that does not exist yet.
        self.driver.implicitly_wait(10)

    def tearDown(self):
        self.print_js_logs()
        super(LbbSeleniumTestCase, self).tearDown()
        self.driver.quit()
        if self.display:
            self.addCleanup(self.display.stop)

    def url_for(self, endpoint, **kwargs):
        """
        A small helper to generate a URL to the given endpoint in the context of `self.app_context`.
        """
        with app.app_context():
            url = flask_url_for(endpoint, **kwargs)
            return self.get_server_url() + url

    def print_js_logs(self):
        # Convenient utility to print client-side logs
        for entry in self.driver.get_log('browser'):
            print(entry)

def url_has_changed(current_url):
    def check(driver):
        return driver.current_url != current_url
    return check