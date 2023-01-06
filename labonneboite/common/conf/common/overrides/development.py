from labonneboite.common.constants import SCOPES_TRUSTED

DEBUG = True
SERVER_NAME = None

# DB_HOST = '127.0.0.1'
DB_PORT = 3306

LOG_FORMAT_USER_ACTIVITY = (
    "-" * 80
    + "\n"
    + "%(levelname)s in %(module)s [%(pathname)s:%(lineno)d]:\n"
    + "%(message)s\n"
    + "-" * 80
)

PEAM_VERIFY_SSL = False

SENTRY_ENVIRONMENT = "development"

API_KEYS = {

    'foo': '8a21c5b3cfc0293c0198888888f315e5b4afcf17a88593ab68394e',

}

API_USERS = {

    'foo': {
        'scopes': SCOPES_TRUSTED,
    }
}
