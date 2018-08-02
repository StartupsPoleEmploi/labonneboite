# coding: utf8
"""
Flask app configuration settings.
"""
from labonneboite.conf import settings


class Config(object):
    DEBUG = settings.DEBUG
    ASSETS_DEBUG = settings.DEBUG
    TESTING = settings.TESTING

    SERVER_NAME = settings.SERVER_NAME
    PREFERRED_URL_SCHEME = settings.PREFERRED_URL_SCHEME

    SECRET_KEY = settings.FLASK_SECRET_KEY

    VERSIONS = 'timestamp'
    URL_EXPIRE = True
    JSON_AS_ASCII = False

    MANDRILL_API_KEY = settings.MANDRILL_API_KEY
    MANDRILL_DEFAULT_FROM = 'pole-emploi@noreply-pole-emploi.fr'

    SENTRY_ENVIRONMENT = settings.SENTRY_ENVIRONMENT
    WTF_CSRF_ENABLED = settings.WTF_CSRF_ENABLED

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
    SOCIAL_AUTH_PEAM_OPENIDCONNECT_VERIFY_SSL = settings.PEAM_VERIFY_SSL
    SOCIAL_AUTH_PEAM_OPENIDCONNECT_KEY = settings.PEAM_CLIENT_ID
    SOCIAL_AUTH_PEAM_OPENIDCONNECT_SECRET = settings.PEAM_CLIENT_SECRET
    # Extra scope.
    SOCIAL_AUTH_PEAM_OPENIDCONNECT_SCOPE = [
        'application_%s' % settings.PEAM_CLIENT_ID,
        'api_peconnect-individuv1',
    ]
    SOCIAL_AUTH_PEAM_OPENIDCONNECT_AUTH_EXTRA_ARGUMENTS = {'realm': '/individu'}
    SOCIAL_AUTH_PEAM_OPENIDCONNECT_USER_FIELDS = ['external_id', 'email', 'gender', 'first_name', 'last_name']


CONFIG = Config()
