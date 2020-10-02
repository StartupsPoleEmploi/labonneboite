import logging
import os

from labonneboite.common.constants import Scope, SCOPES_SAFE, SCOPES_TRUSTED

TESTING = True

ES_INDEX = 'labonneboite_unit_test'
ES_TIMEOUT = int(os.environ.get('ES_TIMEOUT', 60)) or None

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
    'trusteduser': 'trusteduserkey',
    'supertrusteduser': 'supertrusteduserkey',
    'untrusteduser': 'untrusteduserkey',
}

API_USERS = {
    'labonneboite': {
        'scopes': SCOPES_SAFE,
    },
    'trusteduser': {
        'scopes': SCOPES_TRUSTED,
    },
    'supertrusteduser': {
        'scopes': SCOPES_TRUSTED + [Scope.COMPANY_PMSMP, Scope.COMPANY_BOE],
    },
    'untrusteduser': {
        'scopes': [],
    },
    'empty_user': {
        # no scope here
    },
}

API_ADRESSE_BASE_URL = 'http://urlintrouvablepourlbb.fr'
API_DEPARTMENTS_URL = 'http://urlintrouvablepourlbb.fr'

SENTRY_ENVIRONMENT = "test"
WTF_CSRF_ENABLED = False

TRAVEL_VENDOR_BACKENDS = {
    'isochrone': {
        'car': 'ign_mock',
        'public': 'navitia_mock',
    },
    'durations': {
        'car': 'ign_mock',
        'public': 'navitia_mock',
    },
}

PROCESS_ASYNC_TASKS = False

# Dummy IP addresses for test only
VERSION_PRO_ALLOWED_IPS = [
    '198.49.0.0/30',
    '198.49.23.144'
]

VERSION_PRO_ALLOWED_EMAIL_SUFFIXES = ['@pole-emploi.fr']
