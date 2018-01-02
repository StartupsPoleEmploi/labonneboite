# coding: utf8
"""
Flask app configuration settings.
"""
from labonneboite.conf import settings
from labonneboite.common.env import get_current_env, ENV_DEVELOPMENT, ENV_PRODUCTION, ENV_STAGING, ENV_TEST


class BaseConfig(object):
    DEBUG = False

    SECRET_KEY = settings.FLASK_SECRET_KEY

    SERVER_NAME = settings.SERVER_NAME
    PREFERRED_URL_SCHEME = settings.PREFERRED_URL_SCHEME

    VERSIONS = 'timestamp'
    URL_EXPIRE = True
    JSON_AS_ASCII = False

    MANDRILL_API_KEY = settings.MANDRILL_API_KEY
    MANDRILL_DEFAULT_FROM = 'pole-emploi@noreply-pole-emploi.fr'

    WTF_CSRF_ENABLED = True

    # Babel is currently only used with Flask-Admin.
    # http://flask-admin.readthedocs.io/en/latest/advanced/#localization-with-flask-babelex
    BABEL_DEFAULT_LOCALE = 'fr'

    SOCIAL_AUTH_USER_MODEL = 'labonneboite.common.models.auth.User'
    SOCIAL_AUTH_LOGIN_URL = '/'
    SOCIAL_AUTH_INACTIVE_USER_URL = '/'

    # List of supported third party authentication providers.
    SOCIAL_AUTH_AUTHENTICATION_BACKENDS = (
        'labonneboite.web.auth.backends.peam.PEAMOpenIdConnect',
    )

    # PEAM backend config.
    SOCIAL_AUTH_PEAM_OPENIDCONNECT_KEY = settings.PEAM_CLIENT_ID
    SOCIAL_AUTH_PEAM_OPENIDCONNECT_SECRET = settings.PEAM_CLIENT_SECRET
    # Extra scope.
    SOCIAL_AUTH_PEAM_OPENIDCONNECT_SCOPE = [
        'application_%s' % settings.PEAM_CLIENT_ID,
        'api_peconnect-individuv1',
    ]
    SOCIAL_AUTH_PEAM_OPENIDCONNECT_AUTH_EXTRA_ARGUMENTS = {'realm': '/individu'}
    SOCIAL_AUTH_PEAM_OPENIDCONNECT_USER_FIELDS = ['external_id', 'email', 'gender', 'first_name', 'last_name']


class ProdConfig(BaseConfig):
    pass


class StagingConfig(BaseConfig):
    pass


class DevConfig(BaseConfig):
    DEBUG = True


class TestConfig(BaseConfig):
    TESTING = True


configs = {
    ENV_DEVELOPMENT: DevConfig,
    ENV_PRODUCTION: ProdConfig,
    ENV_STAGING: StagingConfig,
    ENV_TEST: TestConfig,
}

def get_config():
    return configs[get_current_env()]
