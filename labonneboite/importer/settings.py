from datetime import datetime
from backports.functools_lru_cache import lru_cache
from labonneboite.conf import get_current_env, ENV_LBBDEV, ENV_DEVELOPMENT, ENV_TEST

SCORE_COMPUTING_MAX_DIFF_MEAN = 30
HIGH_SCORE_COMPANIES_DIFF_MAX = 30
HIGH_SCORE_COMPANIES_COUNT_MIN = 100

FIRST_DAY_DPAE = datetime(2012, 1, 1)
LAST_DAY_DPAE = datetime(2015, 6, 30)

NOW = datetime.now()

# FIXME rename all those
BACKOFFICE_ETABLISSEMENT_TABLE = 'etablissements_backoffice'
BACKOFFICE_ETABLISSEMENT_TABLE_CREATE_FILE = "importer/db/etablissements_backoffice.sql"
EXPORT_ETABLISSEMENT_TABLE = 'etablissements'  # FIXME DNRY
OFFICE_TABLE = 'etablissements_importer'
DPAE_TABLE = 'dpae'

if get_current_env() == ENV_LBBDEV:
    INPUT_SOURCE_FOLDER = '/srv/lbb/data'
    SCORE_COEFFICIENT_OF_VARIATION_MAX = 0.35
    MINIMUM_OFFICES_REQUIRED_TO_TRAIN_MODEL = 50
    RMSE_MAX = 300
    MAXIMUM_COMPUTE_SCORE_JOB_FAILURES = 0
    SCORE_REDUCING_TARGET_TABLE = EXPORT_ETABLISSEMENT_TABLE
    SCORE_REDUCING_TARGET_TABLE_CREATE_FILE = "importer/db/etablissements.sql"
elif get_current_env() == ENV_DEVELOPMENT:
    INPUT_SOURCE_FOLDER = '/srv/lbb/labonneboite/importer/data'
    SCORE_COEFFICIENT_OF_VARIATION_MAX = 3.0
    MINIMUM_OFFICES_REQUIRED_TO_TRAIN_MODEL = 0
    RMSE_MAX = 5000
    MAXIMUM_COMPUTE_SCORE_JOB_FAILURES = 94
    SCORE_REDUCING_TARGET_TABLE = 'etablissements_reduced'
    SCORE_REDUCING_TARGET_TABLE_CREATE_FILE = "importer/db/etablissements_reduced.sql"
elif get_current_env() == ENV_TEST:
    pass
else:
    raise Exception("unknown environment for importer")

BACKUP_FOLDER = '/srv/lbb/backups'
BACKUP_INPUT_FOLDER = '/srv/lbb/backups/inputs'
BACKUP_OUTPUT_FOLDER = '/srv/lbb/backups/outputs'

MOST_RECENT_DPAE_DATE = datetime(2012, 1, 1)

DPAE_ERROR_RATE_MAX = 0.1

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
