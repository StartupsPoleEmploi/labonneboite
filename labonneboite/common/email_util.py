# coding: utf8

import json
import logging
from urllib.error import HTTPError
from requests.exceptions import ConnectionError

from labonneboite.conf import settings


logger = logging.getLogger('main')


class MailNoSendException(Exception):
    pass

class EmailClient(object):
    to = settings.FORM_EMAIL
    from_email = settings.ADMIN_EMAIL


class MandrillClient(EmailClient):

    def __init__(self, mandrill):
        self.mandrill = mandrill


    def send(self, html, subject):
        from_email = self.from_email
        to_email = self.to
        success = True

        try:
            response = self.mandrill.send_email(
                subject=subject,
                to=[{'email': to_email}],
                html=html,
                from_email=from_email)
        except (HTTPError, ConnectionError):
            success = False
        else:
            content = response.json()
            if content[0]["status"] != "sent":
                logger.error('Unexpected Mandrill status : {}'.format(content))
                success = False

        if not success:
            raise MailNoSendException("email was not sent from %s to %s" % (from_email, to_email))


        return response
