import logging
import os

TESTING = True

ES_INDEX = 'labonneboite_unit_test'

DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')
DB_PORT = int(os.environ.get('DB_PORT', 3307))
DB_NAME = os.environ.get('DB_NAME', 'lbb_test')
DB_USER = os.environ.get('DB_USER', 'lbb_test')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
REDIS_HOST = 'incorrecthost'

LOG_LEVEL_USER_ACTIVITY = logging.ERROR

ENABLE_TIMEIT_TIMERS = False
API_KEYS = {
    'labonneboite': 'dummykey',
    'emploi_store_dev': 'anotherdummykey',
}

API_ADRESSE_BASE_URL = 'http://urlintrouvablepourlbb.fr'

SENTRY_ENVIRONMENT = "test"
WTF_CSRF_ENABLED = False

TRAVEL_VENDOR_BACKENDS = {
    'isochrone': {
        'car': 'dummy',
        'public': 'dummy',
    },
    'durations': {
        'car': 'dummy',
        'public': 'dummy',
    },
}
