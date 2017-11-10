import os
from datetime import datetime
from backports.functools_lru_cache import lru_cache
from labonneboite.conf import get_current_env, ENV_LBBDEV, ENV_DEVELOPMENT, ENV_TEST

SCORE_COMPUTING_MAX_DIFF_MEAN = 30
HIGH_SCORE_COMPANIES_DIFF_MAX = 30

FIRST_DAY_DPAE = datetime(2012, 1, 1)
LAST_DAY_DPAE = datetime(2015, 6, 30)

NOW = datetime.now()

# FIXME rename all those
BACKOFFICE_ETABLISSEMENT_TABLE = 'etablissements_backoffice'
BACKOFFICE_ETABLISSEMENT_TABLE_CREATE_FILE = "importer/db/etablissements_backoffice.sql"
EXPORT_ETABLISSEMENT_TABLE = 'etablissements'  # FIXME DNRY
OFFICE_TABLE = 'etablissements_importer'

DPAE_TABLE = 'dpae'
SCORE_REDUCING_TARGET_TABLE = 'etablissements_reduced'

BACKUP_INPUT_FOLDER = '/srv/lbb/backups/inputs'

MOST_RECENT_DPAE_DATE = datetime(2012, 1, 1)

DPAE_ERROR_RATE_MAX = 0.1
MINIMUM_GEOCODING_RATIO = 0.75

MYSQL_NO_PASSWORD = False


@lru_cache(maxsize=None)
def get_departements(largest_ones_first=False):
    departements = ["{:02d}".format(d) for d in range(1, 96)] + ['97']
    if largest_ones_first:
        departements.remove('75')
        departements[:0] = ['75']
    return departements

DEPARTEMENTS = get_departements()
DEPARTEMENTS_WITH_LARGEST_ONES_FIRST = get_departements(largest_ones_first=True)

if get_current_env() == ENV_LBBDEV:
    BACKUP_FIRST = True
    INPUT_SOURCE_FOLDER = '/srv/lbb/data'
    DISTINCT_DEPARTEMENTS_HAVING_OFFICES = 96
    DISTINCT_DEPARTEMENTS_HAVING_OFFICES_FROM_FILE = 96
    JENKINS_ETAB_PROPERTIES_FILENAME = os.path.join(os.environ["WORKSPACE"], "properties.jenkins")
    JENKINS_DPAE_PROPERTIES_FILENAME = os.path.join(os.environ["WORKSPACE"], "properties_dpae.jenkins")
    MINIMUM_OFFICES_TO_BE_EXTRACTED_PER_DEPARTEMENT = 10000
    SCORE_COEFFICIENT_OF_VARIATION_MAX = 0.35
    MINIMUM_OFFICES_REQUIRED_TO_TRAIN_MODEL = 50
    RMSE_MAX = 300
    MAXIMUM_COMPUTE_SCORE_JOB_FAILURES = 0
    SCORE_REDUCING_TARGET_TABLE_CREATE_FILE = "importer/db/etablissements.sql"
    SCORE_REDUCING_MINIMUM_THRESHOLD = 50
    HIGH_SCORE_COMPANIES_COUNT_MIN = 100
    MINIMUM_OFFICES_PER_DEPARTEMENT = 100
    DEPARTEMENTS_TO_BE_SANITY_CHECKED = DEPARTEMENTS
    BACKUP_OUTPUT_FOLDER = '/srv/lbb/backups/outputs'
    BACKUP_FOLDER = '/srv/lbb/backups'
elif get_current_env() == ENV_DEVELOPMENT:
    BACKUP_FIRST = False
    INPUT_SOURCE_FOLDER = '/srv/lbb/labonneboite/importer/data'
    DISTINCT_DEPARTEMENTS_HAVING_OFFICES = 1
    DISTINCT_DEPARTEMENTS_HAVING_OFFICES_FROM_FILE = 15
    dirname = os.path.dirname(os.path.realpath(__file__))
    JENKINS_ETAB_PROPERTIES_FILENAME = os.path.join(dirname, "jenkins/properties.jenkins")
    JENKINS_DPAE_PROPERTIES_FILENAME = os.path.join(dirname, "jenkins/properties_dpae.jenkins")
    MINIMUM_OFFICES_TO_BE_EXTRACTED_PER_DEPARTEMENT = 1
    SCORE_COEFFICIENT_OF_VARIATION_MAX = 3.0
    MINIMUM_OFFICES_REQUIRED_TO_TRAIN_MODEL = 0
    RMSE_MAX = 5000
    MAXIMUM_COMPUTE_SCORE_JOB_FAILURES = 94  # 96 = 2 successes + 94 failures
    SCORE_REDUCING_TARGET_TABLE_CREATE_FILE = "importer/db/etablissements_reduced.sql"
    SCORE_REDUCING_MINIMUM_THRESHOLD = 0
    HIGH_SCORE_COMPANIES_COUNT_MIN = 100
    MINIMUM_OFFICES_PER_DEPARTEMENT = 1
    DEPARTEMENTS_TO_BE_SANITY_CHECKED = ['14', '69']
    BACKUP_OUTPUT_FOLDER = '/srv/lbb/labonneboite/importer/output'
    BACKUP_FOLDER = '/srv/lbb/labonneboite/importer/output'
elif get_current_env() == ENV_TEST:
    BACKUP_FIRST = False
    INPUT_SOURCE_FOLDER = '/srv/lbb/labonneboite/importer/tests/data'
    DISTINCT_DEPARTEMENTS_HAVING_OFFICES = 15
    DISTINCT_DEPARTEMENTS_HAVING_OFFICES_FROM_FILE = 15
    MINIMUM_OFFICES_TO_BE_EXTRACTED_PER_DEPARTEMENT = 1
    SCORE_COEFFICIENT_OF_VARIATION_MAX = 1.0
    SCORE_REDUCING_MINIMUM_THRESHOLD = 50
    HIGH_SCORE_COMPANIES_COUNT_MIN = 0
    MINIMUM_OFFICES_PER_DEPARTEMENT = 1
    DEPARTEMENTS_TO_BE_SANITY_CHECKED = []
else:
    raise Exception("unknown environment for importer")

