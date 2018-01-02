# coding: utf8
import unittest

from flask import url_for as flask_url_for
from pyvirtualdisplay import Display
from selenium import webdriver

from labonneboite.conf import settings
from labonneboite.web.app import app


class LbbSeleniumTestCase(unittest.TestCase):
    """
    Sets up the environment for Selenium tests and exposes
    various properties.

    https://docs.python.org/2/library/unittest.html
    http://selenium-python.readthedocs.io/index.html
    """

    HOME_URL = settings.SERVER_NAME

    def setUp(self):
        super(LbbSeleniumTestCase, self).setUp()

        # Disable CSRF validation in unit tests.
        app.config['WTF_CSRF_ENABLED'] = False
        # Setting a SERVER_NAME enables URL generation without a request context but with an application context.
        app.config['SERVER_NAME'] = self.HOME_URL.replace('http://', '')
        self.app = app.test_client()
        self.app_context = app.app_context()

        self.display = Display(visible=0, size=(800, 600))
        self.display.start()
        self.driver = webdriver.Chrome()
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
        with self.app_context:
            url = flask_url_for(endpoint, **kwargs)
            return url
