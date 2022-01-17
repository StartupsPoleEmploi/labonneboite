import flask.logging

DEBUG = True
SERVER_NAME = None

DB_HOST = '127.0.0.1'
DB_PORT = 3307

LOG_FORMAT_USER_ACTIVITY = (
    '-' * 80 + '\n' +
    '%(levelname)s in %(module)s [%(pathname)s:%(lineno)d]:\n' +
    '%(message)s\n' +
    '-' * 80
)

PEAM_VERIFY_SSL = False

SENTRY_ENVIRONMENT = "development"

