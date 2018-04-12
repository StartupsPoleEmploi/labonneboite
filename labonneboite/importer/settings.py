"""
Importer default settings.

This file gathers default value and documentation about each importer setting.

Environment-specific values of these parameters are overriden in files:

conf/development.py
conf/test.py
conf/lbbdev.py
"""
import os
from datetime import datetime
from labonneboite.common.env import get_current_env, ENV_LBBDEV, ENV_DEVELOPMENT, ENV_TEST
from labonneboite.common import departements as dpt

# Folder that contains the repo
LBB_ROOT_FOLDER = os.path.join(os.path.dirname(__file__), '..', '..', '..')
IMPORTER_ROOT_FOLDER = os.path.dirname(__file__)

# --- importer tables (names and schema)
BACKOFFICE_ETABLISSEMENT_TABLE = 'etablissements_backoffice'
RAW_OFFICE_TABLE = 'etablissements_raw'
DPAE_TABLE = 'dpae'
SCORE_REDUCING_TARGET_TABLE = 'etablissements_exportable'
SCORE_REDUCING_TARGET_TABLE_CREATE_FILE = "importer/db/etablissements_exportable.sql"
BACKOFFICE_ETABLISSEMENT_TABLE_CREATE_FILE = "importer/db/etablissements_backoffice.sql"

# --- importer table backuping process
BACKUP_FIRST = False
BACKUP_INPUT_FOLDER = os.path.join(LBB_ROOT_FOLDER, 'backups', 'inputs')

# --- importer input directory of DPAE and ETABLISSEMENT exports
INPUT_SOURCE_FOLDER = os.path.join(IMPORTER_ROOT_FOLDER, 'data')

# --- job 1/8 & 2/8 : check_etablissements & extract_etablissements
dirname = os.path.dirname(os.path.realpath(__file__))
JENKINS_ETAB_PROPERTIES_FILENAME = os.path.join(dirname, "jenkins/properties.jenkins")
DISTINCT_DEPARTEMENTS_HAVING_OFFICES = 96
MINIMUM_OFFICES_TO_BE_EXTRACTED_PER_DEPARTEMENT = 1

# --- job 3/8 & 4/8 : check_dpae & extract_dpae
JENKINS_DPAE_PROPERTIES_FILENAME = os.path.join(dirname, "jenkins/properties_dpae.jenkins")
DPAE_ERROR_RATE_MAX = 0.1
MOST_RECENT_DPAE_DATE = datetime(2012, 1, 1)
MAXIMUM_ZIPCODE_ERRORS = 0
MAXIMUM_INVALID_ROWS = 0

# --- job 5/8 : compute_scores
SCORE_COMPUTING_MAX_DIFF_MEAN = 30
HIGH_SCORE_COMPANIES_DIFF_MAX = 30
FIRST_DAY_DPAE = datetime(2012, 1, 1)
SCORE_COEFFICIENT_OF_VARIATION_MAX = 3.0
MINIMUM_OFFICES_REQUIRED_TO_TRAIN_MODEL = 50
RMSE_MAX = 300
MAXIMUM_COMPUTE_SCORE_JOB_FAILURES = 0
HIGH_SCORE_COMPANIES_COUNT_MIN = 100

# --- job 6/8 : validate_scores
SCORE_REDUCING_MINIMUM_THRESHOLD = 50
MINIMUM_OFFICES_PER_DEPARTEMENT = 1
DEPARTEMENTS_TO_BE_SANITY_CHECKED = dpt.DEPARTEMENTS

# --- job 7/8 : geocode
MINIMUM_GEOCODING_RATIO = 0.75

# --- job 8/8 : populate_flags
BACKUP_OUTPUT_FOLDER = os.path.join(IMPORTER_ROOT_FOLDER, 'output')
BACKUP_FOLDER = os.path.join(IMPORTER_ROOT_FOLDER, 'output')

if get_current_env() == ENV_LBBDEV:
    # pylint: disable=wildcard-import,unused-wildcard-import
    from .conf.lbbdev import *
elif get_current_env() == ENV_DEVELOPMENT:
    # pylint: disable=wildcard-import,unused-wildcard-import
    from .conf.development import *
elif get_current_env() == ENV_TEST:
    # pylint: disable=wildcard-import,unused-wildcard-import
    from .conf.test import *
else:
    raise Exception("unknown environment for importer")
