import ipaddress
from unittest import mock

from flask import current_app

from labonneboite.common import pro
from labonneboite.common.models import User
from labonneboite.conf import settings
from labonneboite.tests.test_base import DatabaseTest


class ProVersionTest(DatabaseTest):
    def setUp(self):
        super().setUp()
        self.pro_user = User.create(email="john.doe@pole-emploi.fr", gender="male", first_name="John", last_name="Doe")
        self.public_user = User.create(email="john.doe@gmail.com", gender="male", first_name="John", last_name="Doe")
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:52.0) Gecko/20100101 Firefox/52.0"
        allowed_ip = settings.VERSION_PRO_ALLOWED_IPS[1]  # IP address // should not be a range
        self.headers = {"X-Forwarded-For": allowed_ip, "User_Agent": user_agent}

    def test_user_is_pro(self):
        """
        Test that the Pro user is correctly detected in various cases.
        """

        # Email detection, without IP detection
        with self.test_request_context():
            # User which is not logged in should not be considered a pro user.
            self.assertFalse(pro.user_is_pro())

            # # User with a pro email should be considered as a pro user.
            self.login(self.pro_user)
            self.assertTrue(pro.user_is_pro())
            self.logout()
            self.assertFalse(pro.user_is_pro())

            # User with a non pro email should not be considered a pro user.
            self.login(self.public_user)
            self.assertFalse(pro.user_is_pro())
            self.logout()
            self.assertFalse(pro.user_is_pro())

        # a public user logging in with the right IP address
        # and NOT from a Pila machine should be considered a pro user.
        with self.test_request_context(headers=self.headers):
            self.assertTrue(pro.user_is_pro())

    def test_enable_disable_pro_version_view(self):
        """
        Test that the Pro Version is correctly enabled/disabled.
        """

        next_url_without_domain = "/entreprises/metz-57000/boucherie?sort=score&d=10&h=1&p=0&f_a=0"
        next_url_with_domain = "http://labonneboite.pole-emploi.fr" + next_url_without_domain
        url = self.url_for("user.pro_version", **{"next": next_url_without_domain})

        with self.test_request_context(headers=self.headers):
            # Log the user in.
            self.login(self.pro_user)
            self.assertTrue(pro.user_is_pro())
            self.assertFalse(pro.pro_version_enabled())

            with self.app.session_transaction() as sess:
                self.assertNotIn(pro.PRO_VERSION_SESSION_KEY, sess)

            # Enable pro version.
            rv = self.app.get(url)
            self.assertEqual(rv.status_code, 302)
            self.assertEqual(rv.location, next_url_with_domain)
            # It is unclear what is the root cause of the following test
            # failure. The session object manipulated in the
            # pro_version_enabled function is different from the session
            # provided by the self.app.session_transaction context manager, but
            # I don't know why.
            # self.assertTrue(pro.pro_version_enabled())

            with self.app.session_transaction() as sess:
                self.assertIn(pro.PRO_VERSION_SESSION_KEY, sess)
                self.assertEqual(True, sess[pro.PRO_VERSION_SESSION_KEY])

            # Disable pro version.
            rv = self.app.get(url)
            self.assertEqual(rv.status_code, 302)
            self.assertEqual(rv.location, next_url_with_domain)
            self.assertFalse(pro.pro_version_enabled())

            with self.app.session_transaction() as sess:
                self.assertNotIn(pro.PRO_VERSION_SESSION_KEY, sess)

    def test_pro_version_in_a_pila_machine(self):
        """
        Pila machines are used publicly by job seekers in Pole Emploi offices.
        Of course, job seekers should not be able to see pro features.
        """
        self.headers[
            "User_Agent"
        ] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:52.0) Gecko/20100101 Firefox/52.0 Pila/1.0"

        self.assert_pro_version_is_not_enabled()

    def test_ip_range(self):
        """
        IP specified in settings can be a range of addresses.
        Check that our program whitelists IP addresses in this range.
        """

        ips = pro.ips_from_ip_ranges(settings.VERSION_PRO_ALLOWED_IPS)

        for ip in ips:
            self.headers["X-Forwarded-For"] = ip
            self.assert_pro_version_is_enabled()

        blacklisted_ips = ["173.192.6.0", "173.192.2.0"]
        for ip in blacklisted_ips:
            self.headers["X-Forwarded-For"] = ip
            self.assert_pro_version_is_not_enabled()

    def test_ips_from_ip_ranges(self):
        """
        Unit test for pro.ips_from_ip_ranges method.
        It should return a list of ip addresses.
        """
        whitelisted_ips = pro.ips_from_ip_ranges(settings.VERSION_PRO_ALLOWED_IPS)
        self.assertIsInstance(whitelisted_ips, list)
        self.assertIsInstance(whitelisted_ips[0], ipaddress.IPv4Address)

        # Check that our method accepts single IP addresses.
        test_ip = "129.132.2.1"
        ips = pro.ips_from_ip_ranges([test_ip])
        self.assertIn(ipaddress.ip_address(test_ip), ips)
        self.assertEqual(len(ips), 1)

        # Check that our method accepts IP ranges.
        test_ip_range = "198.49.0.0/30"
        ips = pro.ips_from_ip_ranges([test_ip_range])
        self.assertIn(ipaddress.ip_address("198.49.0.1"), ips)
        self.assertEqual(len(ips), 4)

        # Check that our method accepts many addresses.
        self.assertIn(ipaddress.ip_address(test_ip), pro.ips_from_ip_ranges([test_ip, test_ip_range]))

    ##################################
    ######### Utility methods ########
    ##################################

    def assert_pro_version_is_enabled(self):
        """
        Utility method to assert pro version is visible.
        """
        with self.test_request_context(headers=self.headers):
            self.assertTrue(pro.user_is_pro())

    def assert_pro_version_is_not_enabled(self):
        """
        Utility method to assert pro version is not visible.
        """
        with self.test_request_context(headers=self.headers):
            self.assertFalse(pro.user_is_pro())
            self.assertFalse(pro.pro_version_enabled())
