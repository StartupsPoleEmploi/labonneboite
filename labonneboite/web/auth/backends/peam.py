# coding: utf8
"""
Provides user registration and login using PEAM (Pôle Emploi Access Management).
"""
import requests

from social_core.exceptions import AuthUnreachableProvider
from social_core.backends.open_id_connect import OpenIdConnectAuth

from labonneboite.conf import settings
from labonneboite.common import user_util
from .exceptions import AuthFailedMissingReturnValues


# pylint:disable=abstract-method
class PEAMOpenIdConnect(OpenIdConnectAuth):
    """
    Pôle Emploi Access Management OpenId Connect backend.
    """
    name = 'peam-openidconnect'

    AUTHORIZATION_URL = '%s/connexion/oauth2/authorize' % settings.PEAM_AUTH_BASE_URL
    ACCESS_TOKEN_URL = '%s/connexion/oauth2/access_token' % settings.PEAM_AUTH_BASE_URL
    REFRESH_TOKEN_URL = '%s/connexion/oauth2/access_token' % settings.PEAM_AUTH_BASE_URL
    USERINFO_URL = '%s/partenaire/peconnect-individu/v1/userinfo' % settings.PEAM_API_BASE_URL

    def request_access_token(self, *args, **kwargs):
        kwargs['params'] = {'realm': '/individu'}
        result = self.get_json(*args, **kwargs)
        return result

    def user_data(self, access_token, *args, **kwargs):
        url = self.userinfo_url()
        try:
            return self.get_json(
                url, params={'realm': '/individu'},
                headers={'Authorization': 'Bearer {0}'.format(access_token)}
            )
        except requests.HTTPError as e:
            if e.response.status_code == 502: # Bad Gateway
                # 502 errors are not properly handled by social_core (see
                # handle_http_errors decorator in social_core.utils)
                # If we don't raise an exception, the user sees a spinning wheel.
                # This exception must be caught by an error handler of the app.
                raise AuthUnreachableProvider(url)
            raise

    def get_user_details(self, response):
        try:
            return {
                # Optional fields.
                'email': response.get('email', ''),  # Explicitly fallback to an empty string when there is no email.
                # Mandatory fields.
                'external_id': response['sub'],
                'gender': response.get('gender', user_util.GENDER_OTHER),
                'first_name': response['given_name'],
                'last_name': response.get('family_name'),
            }
        except KeyError as e:
            # Sometimes PEAM responds without the user details.
            raise AuthFailedMissingReturnValues(*e.args)


# pylint:disable=abstract-method
class PEAMOpenIdConnectNoPrompt(PEAMOpenIdConnect):
    name = 'peam-openidconnect-no-prompt'
    # For some reason, the 'state' session parameter is not set by PE.fr, so we
    # need to ignore it.
    STATE_PARAMETER = False
