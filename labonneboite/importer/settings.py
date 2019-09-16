"""
Importer default settings.

This file gathers default value and documentation about each importer setting.

Environment-specific values of these parameters are overriden in files:

conf/development.py
conf/test.py
conf/bonaparte.py
"""
import os
from datetime import datetime
from labonneboite.common.env import get_current_env, ENV_BONAPARTE, ENV_DEVELOPMENT, ENV_TEST
from labonneboite.common import departements as dpt

# Folder that contains the repo
LBB_ROOT_FOLDER = os.path.join(os.path.dirname(__file__), '..', '..', '..')
IMPORTER_ROOT_FOLDER = os.path.dirname(__file__)

# --- importer tables (names and schema)
BACKOFFICE_ETABLISSEMENT_TABLE = 'etablissements_backoffice'
RAW_OFFICE_TABLE = 'etablissements_raw'
HIRING_TABLE = 'hirings'
SCORE_REDUCING_TARGET_TABLE = 'etablissements_exportable'

# --- importer input directory of DPAE and ETABLISSEMENT exports
INPUT_SOURCE_FOLDER = os.path.join(IMPORTER_ROOT_FOLDER, 'data')

# --- job 1/8 & 2/8 : check_etablissements & extract_etablissements
dirname = os.path.dirname(os.path.realpath(__file__))
DISTINCT_DEPARTEMENTS_HAVING_OFFICES = 96
MINIMUM_OFFICES_TO_BE_EXTRACTED_PER_DEPARTEMENT = 1

# --- job 3/8 & 4/8 : check_dpae & extract_dpae
DPAE_ERROR_RATE_MAX = 0.1
OLDEST_POSSIBLE_DPAE_DATE = datetime(2011, 12, 31)
MAXIMUM_ZIPCODE_ERRORS = 0
MAXIMUM_INVALID_ROWS = 0

# --- job 5/8 : compute_scores
SCORE_COMPUTING_MAX_DIFF_MEAN = 30
HIGH_SCORE_COMPANIES_DIFF_MAX = 30
SCORE_COEFFICIENT_OF_VARIATION_MAX = 3.0
MINIMUM_OFFICES_REQUIRED_TO_TRAIN_MODEL = 50
RMSE_MAX = 300
MAXIMUM_COMPUTE_SCORE_JOB_FAILURES = 0
HIGH_SCORE_COMPANIES_COUNT_MIN = 100
ALTERNANCE_LAST_HISTORICAL_DATA_DATE = datetime(2017, 12, 31)

# --- job 6/8 : validate_scores
SCORE_REDUCING_MINIMUM_THRESHOLD = 50
SCORE_ALTERNANCE_REDUCING_MINIMUM_THRESHOLD = 50
MINIMUM_OFFICES_PER_DEPARTEMENT_FOR_DPAE = 1
MINIMUM_OFFICES_PER_DEPARTEMENT_FOR_ALTERNANCE = 0
DEPARTEMENTS_TO_BE_SANITY_CHECKED = dpt.DEPARTEMENTS

# --- job 7/8 : geocode
MINIMUM_GEOCODING_RATIO = 0.75

# --- job 8/8 : populate_flags
BACKUP_OUTPUT_FOLDER = os.path.join(IMPORTER_ROOT_FOLDER, 'output')
BACKUP_FOLDER = os.path.join(IMPORTER_ROOT_FOLDER, 'output')

if get_current_env() == ENV_BONAPARTE:
    # pylint: disable=wildcard-import,unused-wildcard-import
    from .conf.bonaparte import *
elif get_current_env() == ENV_DEVELOPMENT:
    # pylint: disable=wildcard-import,unused-wildcard-import
    from .conf.development import *
elif get_current_env() == ENV_TEST:
    # pylint: disable=wildcard-import,unused-wildcard-import
    from .conf.test import *
