import json, urllib
import requests

from enum import Enum
from flask import session, url_for
from labonneboite.conf import settings

class PeamRecruiterError(Exception):
    pass

# Recruiter session value keys
class SessionKeys(Enum):
    EMAIL = 'SESSION_EMAIL'
    EMAIL_VERIFIED = 'SESSION_EMAIL_VERIFIED'
    GENDER = 'SESSION_GENDER'
    FIRSTNAME = 'SESSION_FIRSTNAME'
    LASTNAME = 'SESSION_LASTNAME'
    HABILITATION = 'SESSION_HABILITATION'
    UID = 'SESSION_UID'


def is_recruiter():
    recruiter_values = [
        session.get(SessionKeys.EMAIL.value, ''),
        session.get(SessionKeys.EMAIL_VERIFIED.value, ''),
        session.get(SessionKeys.FIRSTNAME.value, ''),
        session.get(SessionKeys.LASTNAME.value, ''),
        session.get(SessionKeys.HABILITATION.value, ''),
        session.get(SessionKeys.HABILITATION.value, ''),
        session.get(SessionKeys.UID.value, ''),
    ]
    return all(recruiter_values)

def get_recruiter_uid():
    return session.get(SessionKeys.UID.value, '')

def is_certified_recruiter():
    uid = session.get(SessionKeys.UID.value, '')
    habilitation = session.get(SessionKeys.HABILITATION.value, '')
    email_verified = session.get(SessionKeys.EMAIL_VERIFIED.value, False)
    return habilitation == 'recruteurcertifie' and uid and email_verified

def clear_pe_connect_recruiter_session():
    for key in SessionKeys:
        if key.value in session:
            del session[key.value]

def get_token_data(code):
    token_url = settings.PEAM_AUTH_RECRUITER_BASE_URL + 'connexion/oauth2/access_token?' + urllib.parse.urlencode({
        'realm': '/employeur',
    })

    return peam_recruiter_request(
        token_url,
        method='POST',
        headers={'Content-Type':'application/x-www-form-urlencoded'},
        body={
            'grant_type':'authorization_code',
            'code': code,
            'client_id': settings.PEAM_CLIENT_ID,
            'client_secret': settings.PEAM_CLIENT_SECRET,
            'redirect_uri': url_for('auth.peam_recruiter_token_callback', _external=True)
        }
    )


def get_recruiter_data(access_token):
    return peam_recruiter_request(
        "{}/partenaire/peconnect-entreprise/v1/userinfo".format(settings.PEAM_API_BASE_URL),
        headers={'Authorization': 'Bearer {}'.format(access_token)}
    )

def peam_recruiter_request(url, method='GET', headers=None, body=None):
    user_request = urllib.request.Request(
        url,
        method=method,
        headers=headers,
        data=urllib.parse.urlencode(body).encode('utf-8') if body else None
    )

    try:
        response = urllib.request.urlopen(user_request)
    except urllib.error.HTTPError:
        message = 'HTTP error url={} method={}'.format(url, method)
        raise PeamRecruiterError(message)

    if response.status >= 400:
        message = 'HTTP error url={} method={} status={} content="{}"'.format(
            url,
            method,
            response.status,
            response.content,
        )
        raise PeamRecruiterError(message)

    return json.loads(response.read().decode('utf-8'))
