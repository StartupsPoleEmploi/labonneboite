"""
Provides user registration and login using PEAM (Pôle Emploi Access Management).

Useful documentation of social-auth-core:
https://python-social-auth.readthedocs.io/en/latest/
"""
from typing import Dict, List, Mapping, Union

import requests
from social_core.backends.open_id_connect import OpenIdConnectAuth
from social_core.exceptions import AuthUnreachableProvider

from labonneboite.common import activity
from labonneboite.common.constants import GENDER_OTHER
from labonneboite.common.models import User
from labonneboite.conf import settings

from .exceptions import AuthFailedMissingReturnValues

Indemnisations = Dict[str, bool]  # TODO: use TypedDict

# class Indemnisations(TypedDict):
#     beneficiairePrestationSolidarite: bool
#     beneficiaireAssuranceChomage: bool


# pylint:disable=abstract-method
class PEAMOpenIdConnect(OpenIdConnectAuth):
    """
    Pôle Emploi Access Management OpenId Connect backend.
    """
    name = 'peam-openidconnect'

    AUTHORIZATION_URL = f"{settings.PEAM_AUTH_BASE_URL}/connexion/oauth2/authorize"
    ACCESS_TOKEN_URL = f"{settings.PEAM_AUTH_BASE_URL}/connexion/oauth2/access_token"
    REFRESH_TOKEN_URL = f"{settings.PEAM_AUTH_BASE_URL}/connexion/oauth2/access_token?realm=%2Findividu"
    USERINFO_URL = f"{settings.PEAM_API_BASE_URL}/partenaire/peconnect-individu/v1/userinfo"
    INDEMNISATIONS_URL = f"{settings.PEAM_API_BASE_URL}/partenaire/peconnect-indemnisations/v1/indemnisation"

    # as documented in https://python-social-auth.readthedocs.io/en/latest/use_cases.html#multiple-scopes-per-provider
    def get_scope(self) -> List[str]:
        scope = super(PEAMOpenIdConnect, self).get_scope()
        if settings.ENABLE_PEAM_HIGHER_QOS:
            # enable higher quota of req/s to avoid 429 HTTP errors
            scope += ['qos_silver_peconnect-individuv1']
        scope += ['api_candidaturespontaneev1', 'ami', 'amiW']
        return scope

    def request_access_token(self, *args, **kwargs):
        kwargs['params'] = {'realm': '/individu'}
        result = self.get_json(*args, **kwargs)
        return result

    @classmethod
    def get_indemnisations_url(cls) -> str:
        return cls.INDEMNISATIONS_URL

    # TODO: refacto [POC] --> migrer dans un service dedié ou dans une fonction
    def get_user_indemnisations(self, access_token) -> Indemnisations:
        # user_indemnisations = self.get_json(
        #     self.get_indemnisations_url(),
        #     params={'realm': '/individu'},
        #     headers={'Authorization': f'Bearer {access_token}'}
        # )
        user_indemnisations = {
            'beneficiairePrestationSolidarite': True,
        }
        return user_indemnisations

    # TODO: refacto [POC] --> migrer dans un service dedié ou dans une fonction
    def get_user_is_long_duration_job_seekers(self, access_token) -> bool:
        user_indemnisations = self.get_user_indemnisations(access_token)
        return user_indemnisations['beneficiairePrestationSolidarite']

    def user_data(self, access_token, *args, **kwargs):
        url = self.userinfo_url()
        try:
            return self.get_json(
                url, params={'realm': '/individu'}, headers={'Authorization': 'Bearer {0}'.format(access_token)}
            )
        except requests.HTTPError as e:
            if e.response.status_code == 502:  # Bad Gateway
                # 502 errors are not properly handled by social_core (see
                # handle_http_errors decorator in social_core.utils)
                # If we don't raise an exception, the user sees a spinning wheel.
                # This exception must be caught by an error handler of the app.
                raise AuthUnreachableProvider(url)
            raise

    def get_user_details(self, response):
        user_details = {
            'gender': response.get('gender', GENDER_OTHER),
            'email': response.get('email'),
            'external_id': response.get('sub'),
            'first_name': response.get('given_name'),
            'last_name': response.get('family_name'),
            # TODO: refacto [POC] --> migrer dans un backend dedié ou dans une fonction
            'is_long_duration_job_seekers': self.get_user_is_long_duration_job_seekers(response['access_token'])
        }
        # Sometimes PEAM responds without the user details. For instance, the
        # email address is empty when a user has not validated its account.
        required_fields = ('email', 'external_id', 'first_name', 'last_name')
        for field in required_fields:
            if not user_details[field]:
                raise AuthFailedMissingReturnValues(self, field)
        # Sometimes users have updated their PEAM email and we need to reflect
        # the change in our db on the fly.
        existing_user_query = User.query.filter_by(external_id=user_details['external_id'])
        if existing_user_query.count():
            existing_user = existing_user_query.first()
            existing_user.email = user_details['email']
            existing_user.is_long_duration_job_seekers = user_details['is_long_duration_job_seekers']
            existing_user.save()
        return user_details

    def complete(self, *args, **kwargs):
        user = super().complete(*args, **kwargs)
        activity.log('connexion', user=user)
        return user


# pylint:disable=abstract-method
class PEAMOpenIdConnectNoPrompt(PEAMOpenIdConnect):
    name = 'peam-openidconnect-no-prompt'
    # For some reason, the 'state' session parameter is not set by PE.fr, so we
    # need to ignore it.
    STATE_PARAMETER = False
