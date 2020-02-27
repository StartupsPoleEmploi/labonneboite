import os
from unittest import TestCase

from labonneboite.common import mailjet
from labonneboite.tests.test_base import DatabaseTest

MAILJET_API_KEY = os.environ.get('MAILJET_API_KEY')
MAILJET_API_SECRET = os.environ.get('MAILJET_API_SECRET')
FORM_EMAIL = 'no-reply@lexoyo.me'
FROM_EMAIL = 'unit-tests@jepostule.labonneboite.pole-emploi.fr'

class MailjetTest(TestCase):
    """
    Test sending mail.
    """
    def setUp(self):
        """
        Init mailjet.
        """
        self.assertIsNotNone(MAILJET_API_KEY, 'you need to provide mailjet api keys as env vars')
        self.assertIsNotNone(MAILJET_API_SECRET, 'you need to provide mailjet api keys as env vars')
        mailjet.init_mail(MAILJET_API_KEY, MAILJET_API_SECRET, FORM_EMAIL, FROM_EMAIL)

    def test_send_mail(self):
        """
        Test basic send mail.
        """
        response = mailjet.send('test email from unit tests', 'test email from <b>unit tests</b>')
        print(response)
        self.assertIsNotNone(response)

    def test_send_mail_error(self):
        with self.assertRaises(mailjet.MailjetAPIError):
            mailjet.init_mail(MAILJET_API_KEY, 'MAILJET_API_SECRET', 'wrongemail', FROM_EMAIL)
            mailjet.send('test email from unit tests', 'test email from <b>unit tests</b>')
