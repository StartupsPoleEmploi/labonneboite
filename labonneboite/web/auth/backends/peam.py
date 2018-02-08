# coding: utf8
"""
Provides user registration and login using PEAM (Pôle Emploi Access Management).
"""

from social_core.exceptions import AuthUnreachableProvider
from social_core.backends.oauth import BaseOAuth2
from social_core.backends.open_id_connect import OpenIdConnectAuth

from labonneboite.conf import settings


# We don't need to override some abstract methods in parent classes.
# pylint:disable=abstract-method

class PEAMOAuth2(BaseOAuth2):
    """
    Pôle Emploi Access Management OAuth2 backend.
    """
    name = 'peam-oauth2'

    AUTHORIZATION_URL = '%s/connexion/oauth2/authorize' % settings.PEAM_AUTH_BASE_URL
    ACCESS_TOKEN_URL = '%s/connexion/oauth2/access_token' % settings.PEAM_AUTH_BASE_URL
    REFRESH_TOKEN_URL = '%s/connexion/oauth2/access_token' % settings.PEAM_AUTH_BASE_URL

    def request_access_token(self, *args, **kwargs):
        kwargs['params'] = {'realm': '/individu'}
        return self.get_json(*args, **kwargs)


class PEAMOpenIdConnect(PEAMOAuth2, OpenIdConnectAuth):
    """
    Pôle Emploi Access Management OpenId Connect backend.
    """
    name = 'peam-openidconnect'

    USERINFO_URL = settings.PEAM_USERINFO_URL

    def user_data(self, access_token, *args, **kwargs):
        url = self.userinfo_url()
        response = self.get_json(
            url,
            params={'realm': '/individu'},
            headers={'Authorization': 'Bearer {0}'.format(access_token)}
        )
        if response.status_code == 502: # Bad Gateway
            # 502 errors are not properly handled by social_core (see
            # handle_http_errors decorator in social_core.utils)
            # If we don't raise an exception, the user sees a spinning wheel.
            # This exception must be caught by an error handler of the app.
            raise AuthUnreachableProvider(url)
        return response

    def get_user_details(self, response):
        return {
            # Optional fields.
            'email': response.get('email', ''),  # Explicitly fallback to an empty string when there is no email.
            # Mandatory fields.
            'external_id': response['sub'],
            'gender': response['gender'],
            'first_name': response['given_name'],
            'last_name': response['family_name'],
        }

# pylint:enable=abstract-method
