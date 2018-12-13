# coding: utf8
import logging
import datetime
import time
import requests
from urllib.parse import urlencode
from requests.exceptions import ConnectionError, ReadTimeout
from labonneboite.conf import settings

logger = logging.getLogger('main')

ESD_TOKEN_ENDPOINT_URL = "%s/connexion/oauth2/access_token" % settings.PEAM_TOKEN_BASE_URL
ESD_TIMEOUT = 5

ESD_OFFERS_MAX_ATTEMPTS = 3
ESD_OFFERS_THROTTLE_IN_SECONDS = 1


class TokenFailure(Exception):
    pass


class TooManyRequests(Exception):
    pass


class RequestFailed(Exception):
    pass


class EsdToken(object):
    VALUE = None
    EXPIRATION_DATE = None

    @classmethod
    def get_token(cls):
        if not cls.is_token_valid():
            cls.prepare_token()
        return cls.VALUE


    @classmethod
    def is_token_valid(cls):
        if not cls.EXPIRATION_DATE:
            return False
        return cls.EXPIRATION_DATE > datetime.datetime.now()


    @classmethod
    def prepare_token(cls):
        data = urlencode([
            ('realm', '/partenaire'),
            ('grant_type', 'client_credentials'),
            ('client_id', settings.PEAM_CLIENT_ID),
            ('client_secret', settings.PEAM_CLIENT_SECRET),
            ('scope', "application_%s" % settings.PEAM_CLIENT_ID)
        ])
        data += "%20api_offresdemploiv1 o2dsoffre"
        # FIXME enable again when JT will have updated the recette app
        # data += " qos_silver_offresdemploiv1 qos_silver_offresdemploiv2"

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        response = _get_response(
            url=ESD_TOKEN_ENDPOINT_URL,
            data=data,
            headers=headers,
        )
        if 'access_token' in response:
            cls.VALUE = response['access_token']
            expires_in = response['expires_in']
            cls.EXPIRATION_DATE = datetime.datetime.now() + datetime.timedelta(seconds=expires_in)
        else:
            raise TokenFailure


def get_response(url, data):
    """
    Get a response for a request to one of the ESD APIs.
    """
    headers = {
        'Authorization': 'Bearer {}'.format(EsdToken.get_token()),
        'Content-Type': 'application/json',
    }
    attempts = 1

    response = {'results': []}
    while attempts <= ESD_OFFERS_MAX_ATTEMPTS:
        try:
            return _get_response(url, data, headers)
        except TooManyRequests:
            time.sleep(ESD_OFFERS_THROTTLE_IN_SECONDS)
            attempts += 1
    return response


def _get_response(url, data, headers):
    """
    Generic method fetching the response for a POST request to a given
    url with a given data object.
    """
    try:
        response = requests.post(
            url=url,
            data=data,
            headers=headers,
            timeout=ESD_TIMEOUT,
        )
    except (ConnectionError, ReadTimeout) as e:
        logger.exception(e)
        raise e

    http_too_many_requests = 429
    if response.status_code == http_too_many_requests:
        raise TooManyRequests
    elif response.status_code >= 400:
        error = '{} responded with a {} error: {}'.format(
            url,
            response.status_code,
            response.content,
        )
        log_level = logging.WARNING if response.status_code >= 500 else logging.ERROR
        logger.log(log_level, error)
        raise RequestFailed

    return response.json()
