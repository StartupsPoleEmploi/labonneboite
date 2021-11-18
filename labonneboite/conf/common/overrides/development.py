import flask.logging

DEBUG = True
SERVER_NAME = None

DB_HOST = '127.0.0.1'
DB_PORT = 3307

LOG_FORMAT_USER_ACTIVITY = flask.logging.DEBUG_LOG_FORMAT

PEAM_VERIFY_SSL = False

SENTRY_ENVIRONMENT = "development"


PEAM_AUTH_BASE_URL = 'https://authentification-candidat-r.pe-qvr.fr'
PEAM_AUTH_RECRUITER_BASE_URL = 'https://entreprise.pe-qvr.fr/'
PEAM_API_BASE_URL = "https://api.peio.pe-qvr.fr"
PEAM_TOKEN_BASE_URL = 'https://entreprise.pe-qvr.fr'


# Isochrone data available to work locally but only for the Metz area
# and only for isochrones.
# Concerning commute time available in office details (in results search page),
# it is not possible to mock all the requests locally as there are too many
# offices in the local DB.

TRAVEL_VENDOR_BACKENDS = {
    'isochrone': {
        'car': 'ign_mock',
        'public': 'navitia_mock',
    },
    'durations': {
        'car': 'dummy',
        'public': 'dummy',
    },
}