# coding: utf8
import logging
import datetime
import requests
from requests.exceptions import ConnectionError, ReadTimeout
from labonneboite.conf import settings

logger = logging.getLogger('main')

ESD_TOKEN_ENDPOINT_URL = "https://entreprise.pole-emploi.fr/connexion/oauth2/access_token"
ESD_TIMEOUT = 5


class TokenFailure(Exception):
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
        data = "realm=%%2Fpartenaire&grant_type=client_credentials&client_id=%s&client_secret=%s&scope=application_%s%%20api_offresdemploiv1 o2dsoffre" % (
            settings.PEAM_CLIENT_ID,
            settings.PEAM_CLIENT_SECRET,
            settings.PEAM_CLIENT_ID,
        )
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
    return _get_response(url, data, headers)


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
        return []

    if response.status_code >= 400:
        error = '{} responded with a {} error: {}'.format(
            url,
            response.status_code,
            response.content,
        )
        log_level = logging.WARNING if response.status_code >= 500 else logging.ERROR
        logger.log(log_level, error)
        return []

    return response.json()
