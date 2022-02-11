"""
Main app default settings.

This file gathers default value and documentation about each setting.

Environment-specific values of these parameters are overriden in files:

overrides/development.py
overrides/test.py
overrides/bonaparte.py
"""
import logging
import os

from labonneboite.common.env import get_current_env, ENV_BONAPARTE, ENV_DEVELOPMENT, ENV_TEST
from labonneboite.common.load_data import load_rome_labels, load_naf_labels

DEBUG = False
TESTING = False

LOG_LEVEL = logging.INFO
LOG_LEVEL_DB_ENGINE = logging.WARNING
LOG_API_ID = 'labonneboite.pole-emploi.fr'

LOG_LEVEL_USER_ACTIVITY = logging.INFO
LOGGING_HANDLER_USER_ACTIVITY = logging.StreamHandler()
LOGGING_HANDLER_API_ACTIVITY = logging.StreamHandler()
LOG_FORMAT_USER_ACTIVITY = '%(message)s'

GLOBAL_STATIC_PATH = '/tmp'

# Related ROMEs suggestions
ENABLE_RELATED_ROMES = True # set this to False to deactivate the related romes mechanism
MAX_RELATED_ROMES = 5

ROME_DESCRIPTIONS = load_rome_labels()
NAF_CODES = load_naf_labels()

SEARCHING_TIME = 10000

DISTANCE_FILTER_DEFAULT = 10

ENABLE_TIMEIT_TIMERS = True

SENTRY_DSN = None
SENTRY_ENVIRONMENT = ""
SENTRY_SAMPLE_RATE = 0.1 # set to 0 to disable sentry performance monitoring, @see https://docs.sentry.io/platforms/python/guides/flask/performance/#configure-the-sample-rate

ADMIN_EMAIL = 'no-reply@labonneboite.pole-emploi.fr'
LBB_EMAIL = 'labonneboite@pole-emploi.fr'
LBA_EMAIL = 'labonnealternance@pole-emploi.fr'

SERVER_NAME = 'labonneboite.pole-emploi.fr'
PREFERRED_URL_SCHEME = 'http'
COOKIE_SECURE = False

WTF_CSRF_ENABLED = True

# Setting for LBA search API
# 'ONLY_ALTERNANCE_COMPANIES' or 'INCLUDE_DPAE_COMPANIES'
# ALTERNANCE_SEARCH_MODE = 'INCLUDE_DPAE_COMPANIES'
ALTERNANCE_SEARCH_MODE = 'ONLY_ALTERNANCE_COMPANIES'

# Values below are *fake* and should be used in development and test environments only.
# The real values are confidential, stored outside of github repository
# and are only used in production+staging.
# Note that tests don't pass for all values..
SCORE_50_HIRINGS = 10.0
SCORE_60_HIRINGS = 50.0
SCORE_80_HIRINGS = 100.0
SCORE_100_HIRINGS = 500.0

# API keys used to sign requests and check that a user is authorised to use the API
# Note for API proxies such as ESD: they have api keys and need to sign the requests with it
# So an api key is chosen according to the GET param `user` **not** `origin_user`
API_KEYS = {}

# Per user config
# Note for API proxies such as ESD: `API_USERS` are "real" users, the name can be either in the GET param `user` or `origin_user`
API_USERS = {}

VERSION_PRO_ALLOWED_IPS = []
VERSION_PRO_ALLOWED_EMAILS = []
VERSION_PRO_ALLOWED_EMAIL_SUFFIXES = []
VERSION_PRO_ALLOWED_EMAIL_REGEXPS = []

# Headcount
HEADCOUNT_INSEE = {
    '00': '0 salarié',
    '01': '1 ou 2 salariés',
    '02': '3 à 5 salariés',
    '03': '6 à 9 salariés',
    '11': '10 à 19 salariés',
    '12': '20 à 49 salariés',
    '21': '50 à 99 salariés',
    '22': '100 à 199 salariés',
    '31': '200 à 249 salariés',
    '32': '250 à 499 salariés',
    '41': '500 à 999 salariés',
    '42': '1 000 à 1 999 salariés',
    '51': '2 000 à 4 999 salariés',
    '52': '5 000 à 9 999 salariés',
    '53': '10 000 salariés et plus',
}

HEADCOUNT_INSEE_CHOICES = [(key, value) for key, value in sorted(HEADCOUNT_INSEE.items())]

HEADCOUNT_WHATEVER = 1
HEADCOUNT_SMALL_ONLY = 2
HEADCOUNT_BIG_ONLY = 3

HEADCOUNT_SMALL_ONLY_MAXIMUM = 12
HEADCOUNT_BIG_ONLY_MINIMUM = 21
HEADCOUNT_FILTER_DEFAULT = 1

HEADCOUNT_VALUES = {
    'all': HEADCOUNT_WHATEVER,
    'big': HEADCOUNT_BIG_ONLY,
    'small': HEADCOUNT_SMALL_ONLY
}

# Databases
ES_INDEX = 'labonneboite'
# Set ES_TIMEOUT environment variable to 0 to remove ES timeouts entirely
ES_TIMEOUT = int(os.environ.get('ES_TIMEOUT', 10)) or None
ES_HOST = 'localhost:9200'
DB_HOST = 'localhost'
DB_PORT = 3306
DB_NAME = 'labonneboite'
DB_USER = 'labonneboite'
DB_PASSWORD = 'labonneboite'
OFFICE_TABLE = 'etablissements'

# 2020-05-13: The tile API of OpenRouteService (api.openrouteservice.org) will be discontinued in June 2020.
TILE_SERVER_URL = "http://openmapsurfer.uni-hd.de/tiles/roads/x={x}&y={y}&z={z}"

ROME_NAF_PROBABILITY_CUTOFF = 0.05

FLASK_SECRET_KEY = '<set it>'

PEAM_AUTH_BASE_URL = 'https://authentification-candidat.pole-emploi.fr'
PEAM_AUTH_RECRUITER_BASE_URL = 'https://entreprise.pole-emploi.fr/'
PEAM_API_BASE_URL = 'https://api.emploi-store.fr'
PEAM_TOKEN_BASE_URL = 'https://entreprise.pole-emploi.fr'
PEAM_VERIFY_SSL = True
REMEMBER_ME_ARG_NAME = 'keep'

# Settings that need to be overwritten
PEAM_CLIENT_ID = '<set it>'
PEAM_CLIENT_SECRET = '<set it>'

MAILJET_API_KEY = '<set it>'
MAILJET_API_SECRET = '<set it>'
TO_EMAILS = ['<set it>'] # this was named `FORM_EMAIL`, but it is confusing
FROM_EMAIL = '<set it>'

# URL of a script to load for tag management
# Leave blank to disable
TAG_MANAGER_URL = ''

MEMO_URL = 'https://memo.pole-emploi.fr' # staging url is https://memo.beta.pole-emploi.fr
API_ADRESSE_BASE_URL = 'https://api-adresse.data.gouv.fr'
API_DEPARTMENTS_URL = 'https://geo.api.gouv.fr/departements'

# Je postule
JEPOSTULE_BASE_URL = 'http://127.0.0.1:8000'
JEPOSTULE_CLIENT_ID = '<set it>'
JEPOSTULE_CLIENT_SECRET = '<set it>'
JEPOSTULE_BETA_EMAILS = []
JEPOSTULE_QUOTA = 0

# Google site verification code - for linking with Google Search Console
GOOGLE_SITE_VERIFICATION_CODE = None

SCAM_EMAILS_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'scripts', 'scam_emails')

# Ids of spreadsheets for local dev
# SPREADSHEET_IDS = [
#     '197iFVyuCHiNNuA0ns99TCTS-v2CmBITg-e0ztEcwPMA',#Impact retour à l'emploi
#     '1Gl_rWicSmLwpXAPJLR3eRbs5nWJ1ROf6GSmUGmL2DEk',#Impact retour à l'emploi
#     '1HFkQVLxzjT0zIACCCp8c6fJII1VieKDtdvdEkLLO16M',#Indicateurs de perf LBB
#     '1hPq1X_VXM7-l38jhLFrxQaDdpoB4s5W1Ok612SVTHts'# Indicateurs de perf LBA
# ]

SPREADSHEET_IDS = {
    "stats_ire": '197iFVyuCHiNNuA0ns99TCTS-v2CmBITg-e0ztEcwPMA',
    "delay_activity_ire": '1Gl_rWicSmLwpXAPJLR3eRbs5nWJ1ROf6GSmUGmL2DEk',
    "perf_indicators_lba": '1hPq1X_VXM7-l38jhLFrxQaDdpoB4s5W1Ok612SVTHts',
    "perf_indicators_lbb": '1HFkQVLxzjT0zIACCCp8c6fJII1VieKDtdvdEkLLO16M'
}

# Encryption of user PEAM-U token between LBB and JePostule.
# Dummy key used everywhere but in production.
CRYPTOGRAPHY_SECRET_KEY = b'gj6ouKvodK6PCAz4mt5tdTMUnVPHFFYWjh_P-O-IMqU='

# The only case where you don't want this is when using
# PE Connect on the staging ESD, where we do not have this
# QOS privilege.
ENABLE_PEAM_HIGHER_QOS = True

REFRESH_PEAM_TOKEN_NO_MORE_THAN_ONCE_EVERY_SECONDS = 2 * 3600

FORWARD_PEAM_TOKEN_TO_JP_FOR_AMI = False

if get_current_env() == ENV_BONAPARTE:
    # pylint: disable=wildcard-import,unused-wildcard-import
    from .overrides.bonaparte import *
elif get_current_env() == ENV_DEVELOPMENT:
    # pylint: disable=wildcard-import,unused-wildcard-import
    from .overrides.development import *
elif get_current_env() == ENV_TEST:
    # pylint: disable=wildcard-import,unused-wildcard-import
    from .overrides.test import *

ALLOW_INDEXING = False

# Mobiville
MOBIVILLE_MAX_COMPANY_COUNT = 5