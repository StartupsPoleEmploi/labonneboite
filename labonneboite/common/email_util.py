# coding: utf8

import json
import logging

from labonneboite.conf import settings


logger = logging.getLogger('main')


class EmailClient(object):
    to = settings.FORM_EMAIL
    from_email = settings.ADMIN_EMAIL
    subject = 'nouveau message entreprise LBB'


class MandrillClient(EmailClient):

    def __init__(self, mandrill):
        self.mandrill = mandrill

    def send(self, html):
        from_email = self.from_email
        to_email = self.to
        response = self.mandrill.send_email(
            subject=self.subject,
            to=[{'email': to_email}],
            html=html,
            from_email=from_email)
        content = json.loads(response.content.decode())
        if content[0]["status"] != "sent":
            raise Exception("email was not sent from %s to %s" % (from_email, to_email))
        return response
