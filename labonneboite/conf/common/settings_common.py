# coding: utf8
"""
Main app default settings.

This file gathers default value and documentation about each setting.

Environment-specific values of these parameters are overriden in files:

overrides/development.py
overrides/test.py
overrides/lbbdev.py
overrides/staging.py
overrides/production.py
"""
from labonneboite.common.env import get_current_env, ENV_LBBDEV, ENV_DEVELOPMENT, ENV_TEST, ENV_STAGING, ENV_PRODUCTION
from labonneboite.common.load_data import load_rome_labels, load_naf_labels

DEBUG = True

GLOBAL_STATIC_PATH = '/tmp'

ROME_DESCRIPTIONS = load_rome_labels()

NAF_CODES = load_naf_labels()

LOCALE = 'fr_FR.utf8'

SEARCHING_TIME = 10000

HOST = 'labonneboite.pole-emploi.fr'

DISTANCE_FILTER_DEFAULT = 10

ENABLE_TIMEIT_TIMERS = True


######### TODO Settings added to make tests work without local_settings.py
# Maybe we should remove some entirely, or set default values in the code?
ADMIN_EMAIL = 'no-reply@labonneboite.pole-emploi.fr'
FLASK_SECRET_KEY = '<set it>'
# Settings that need to be overwritten
# FIXME there should be a default value for these settings in the code whenever the setting is not defined.
PEAM_CLIENT_ID = '<set it>'
PEAM_CLIENT_SECRET = '<set it>'
PEAM_AUTH_BASE_URL = '<set it>'
PEAM_API_BASE_URL = '<set it>'
PEAM_USERINFO_URL = '<set it>'
MANDRILL_API_KEY = '<set it>'
FORM_EMAIL = '<set it>'
LOG_LEVEL = 'DEBUG'
STAGING_SERVER_URL = 'http://localhost:5000'
# Values below are *fake* and should be used in development and test environments only.
# The real values are confidential, stored outside of github repository
# and are only used in production+staging.
# Note that tests don't pass for all values..
SCORE_50_HIRINGS = 10.0
SCORE_60_HIRINGS = 50.0
SCORE_80_HIRINGS = 100.0
SCORE_100_HIRINGS = 500.0
API_KEYS = {}
API_INTERNAL_CONSUMERS = []
VERSION_PRO_ALLOWED_IPS = []
VERSION_PRO_ALLOWED_EMAILS = []
VERSION_PRO_ALLOWED_EMAIL_SUFFIXES = []
VERSION_PRO_ALLOWED_EMAIL_REGEXPS = []

# Headcount
HEADCOUNT_INSEE = {
    u'00': u'0 salarié',
    u'01': u'1 ou 2 salariés',
    u'02': u'3 à 5 salariés',
    u'03': u'6 à 9 salariés',
    u'11': u'10 à 19 salariés',
    u'12': u'20 à 49 salariés',
    u'21': u'50 à 99 salariés',
    u'22': u'100 à 199 salariés',
    u'31': u'200 à 249 salariés',
    u'32': u'250 à 499 salariés',
    u'41': u'500 à 999 salariés',
    u'42': u'1 000 à 1 999 salariés',
    u'51': u'2 000 à 4 999 salariés',
    u'52': u'5 000 à 9 999 salariés',
    u'53': u'10 000 salariés et plus',
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

# Contract Value
CONTRACT_VALUES = {'all': 0, 'alternance': 1}

# Databases
ES_INDEX = 'labonneboite'
DB_USER = 'labonneboite'
DB_PASSWORD = 'labonneboite'
DB_NAME = 'labonneboite'
OFFICE_TABLE = 'etablissements'

TILE_SERVER_URL = "http://openmapsurfer.uni-hd.de/tiles/roads/x={x}&y={y}&z={z}"

ROME_NAF_PROBABILITY_CUTOFF = 0.05

FLASK_SECRET_KEY = '<set it>'

# Settings that need to be overwritten
# FIXME there should be a default value for these settings in the code whenever the setting is not defined.
PEAM_CLIENT_ID = '<set it>'
PEAM_CLIENT_SECRET = '<set it>'
PEAM_AUTH_BASE_URL = '<set it>'
PEAM_API_BASE_URL = '<set it>'
PEAM_USERINFO_URL = '<set it>'
MANDRILL_API_KEY = '<set it>'
FORM_EMAIL = '<set it>'

# GA/GO snippets are only useful in production and staging,
# we use dummy values everywhere else
GOOGLE_ANALYTICS_ID = 'UA-00000000-0'
GOOGLE_OPTIMIZE_ID = 'GTM-AAAA00A'
GOOGLE_TAG_MANAGER_ID = 'AAA-AAAAAAA'
ENABLE_ADBLOCK_TRACKING = False
ENABLE_GOOGLE_OPTIMIZE = False

MEMO_JS_URL = 'https://memo.pole-emploi.fr/js/importButton/memoButton-min.js'

if get_current_env() == ENV_LBBDEV:
    # pylint: disable=wildcard-import,unused-wildcard-import
    from .overrides.lbbdev import *
elif get_current_env() == ENV_DEVELOPMENT:
    # pylint: disable=wildcard-import,unused-wildcard-import
    from .overrides.development import *
elif get_current_env() == ENV_TEST:
    # pylint: disable=wildcard-import,unused-wildcard-import
    from .overrides.test import *
elif get_current_env() == ENV_STAGING:
    # pylint: disable=wildcard-import,unused-wildcard-import
    from .overrides.staging import *
elif get_current_env() == ENV_PRODUCTION:
    # pylint: disable=wildcard-import,unused-wildcard-import
    from .overrides.production import *
else:
    raise Exception("unknown environment")
