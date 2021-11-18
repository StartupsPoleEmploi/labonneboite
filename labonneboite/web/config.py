"""
Flask app configuration settings.
"""
from datetime import timedelta

from labonneboite.conf import settings


class Config(object):
    DEBUG = settings.DEBUG
    ASSETS_DEBUG = settings.DEBUG
    TESTING = settings.TESTING

    SERVER_NAME = settings.SERVER_NAME
    PREFERRED_URL_SCHEME = settings.PREFERRED_URL_SCHEME

    SECRET_KEY = settings.FLASK_SECRET_KEY

    # Set 'secure' attribute on cookies on https
    SESSION_COOKIE_SECURE = settings.COOKIE_SECURE
    REMEMBER_COOKIE_SECURE = settings.COOKIE_SECURE

    VERSIONS = 'timestamp'
    URL_EXPIRE = True
    JSON_AS_ASCII = False

    SENTRY_ENVIRONMENT = settings.SENTRY_ENVIRONMENT
    WTF_CSRF_ENABLED = settings.WTF_CSRF_ENABLED

    # Babel is currently only used with Flask-Admin.
    # http://flask-admin.readthedocs.io/en/latest/advanced/#localization-with-flask-babelex
    BABEL_DEFAULT_LOCALE = 'fr'

    SOCIAL_AUTH_USER_MODEL = 'labonneboite.common.models.auth.User'
    SOCIAL_AUTH_LOGIN_URL = '/'
    SOCIAL_AUTH_INACTIVE_USER_URL = '/'

    # Persist user authentication in cookie, and not just in session
    SOCIAL_AUTH_FIELDS_STORED_IN_SESSION = [settings.REMEMBER_ME_ARG_NAME]  # used by social_core
    REMEMBER_COOKIE_NAME = 'auth'  # used by social_flask and flask_login
    REMEMBER_COOKIE_DURATION = timedelta(days=365)

    # List of supported third party authentication providers.
    SOCIAL_AUTH_AUTHENTICATION_BACKENDS = (
        'labonneboite.web.auth.backends.peam.PEAMOpenIdConnect',
        'labonneboite.web.auth.backends.peam.PEAMOpenIdConnectNoPrompt',
    )

    SOCIAL_AUTH_PIPELINE = (
        'social_core.pipeline.social_auth.social_details',
        'social_core.pipeline.social_auth.social_uid',
        'social_core.pipeline.social_auth.auth_allowed',
        'social_core.pipeline.social_auth.social_user',
        'social_core.pipeline.user.get_username',
        # We use the default pipeline (social_core.pipeline.DEFAULT_AUTH_PIPELINE)
        # with just the additional find_user function.
        'labonneboite.common.models.auth.find_user',
        'social_core.pipeline.user.create_user',
        'social_core.pipeline.social_auth.associate_user',
        'social_core.pipeline.social_auth.load_extra_data',
        'social_core.pipeline.user.user_details'
    )

    # PEAM backends config.
    SOCIAL_AUTH_VERIFY_SSL = settings.PEAM_VERIFY_SSL
    SOCIAL_AUTH_KEY = settings.PEAM_CLIENT_ID
    SOCIAL_AUTH_SECRET = settings.PEAM_CLIENT_SECRET
    # Extra scope.
    SOCIAL_AUTH_SCOPE = [
        'application_%s' % settings.PEAM_CLIENT_ID,
        'api_peconnect-individuv1',
    ]
    SOCIAL_AUTH_USER_FIELDS = ['external_id', 'email', 'gender', 'first_name', 'last_name', 'is_long_duration_job_seekers']
    SOCIAL_AUTH_PEAM_OPENIDCONNECT_AUTH_EXTRA_ARGUMENTS = {'realm': '/individu'}
    SOCIAL_AUTH_PEAM_OPENIDCONNECT_NO_PROMPT_AUTH_EXTRA_ARGUMENTS = {'realm': '/individu', 'prompt': 'none'}
    # For some reason, the redirect passed to "next=..." is not sent back by
    # PE.fr, so we need to define a redirect url manually
    SOCIAL_AUTH_PEAM_OPENIDCONNECT_NO_PROMPT_LOGIN_REDIRECT_URL = '/authentication/iframe'

    # Define connection timeouts to make sure LBB is not going to timeout before PEAM
    SOCIAL_AUTH_PEAM_OPENIDCONNECT_URLOPEN_TIMEOUT = 8
    SOCIAL_AUTH_PEAM_OPENIDCONNECT_NO_PROMPT_URLOPEN_TIMEOUT = 5


CONFIG = Config()
