# coding: utf8
import distutils.spawn
import logging
import os

from flask import url_for as flask_url_for
from flask_testing import LiveServerTestCase
from pyvirtualdisplay import Display
from selenium import webdriver

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
        # Random port generation
        app.config['LIVESERVER_PORT'] = 0
        # Disable logging
        app.logger.setLevel(logging.CRITICAL)
        logging.getLogger('werkzeug').setLevel(logging.CRITICAL)

        return app

    def setUp(self):
        super(LbbSeleniumTestCase, self).setUp()

        self.display = Display(visible=0, size=(800, 600))
        self.display.start()

        # Chromedriver is often in /usr/lib/chromium-browser/chromedriver
        chromedriver_path = distutils.spawn.find_executable('chromedriver')
        if not chromedriver_path:
            chromedriver_path = distutils.spawn.find_executable('chromedriver', path='/usr/lib/chromium-browser/')
        if not chromedriver_path:
            raise RuntimeError('Missing chromedriver executable. Did you install the chromium-chromedriver package?')
        self.driver = webdriver.Chrome(executable_path=chromedriver_path)

        # Ensure that the window size is large enough so that HTML elements won't overlap.
        self.driver.set_window_size(1600, 1200)
        self.addCleanup(self.display.stop)
        self.addCleanup(self.driver.quit)

    def tearDown(self):
        super(LbbSeleniumTestCase, self).tearDown()
        self.driver.quit()

    def url_for(self, endpoint, **kwargs):
        """
        A small helper to generate a URL to the given endpoint in the context of `self.app_context`.
        """
        with app.app_context():
            url = flask_url_for(endpoint, **kwargs)
            return self.get_server_url() + url
