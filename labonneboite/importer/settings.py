from datetime import datetime
from collections import deque
from backports.functools_lru_cache import lru_cache

SCORE_COMPUTING_MAX_DIFF_MEAN = 30
HIGH_SCORE_COMPANIES_DIFF_MAX = 30
HIGH_SCORE_COMPANIES_COUNT_MIN = 100
SCORE_COEFFICIENT_OF_VARIATION_MAX = 0.35
RMSE_MAX = 300

FIRST_DAY_DPAE = datetime(2012, 1, 1)
LAST_DAY_DPAE = datetime(2015, 6, 30)

NOW = datetime.now()


BACKOFFICE_ETABLISSEMENT_TABLE = 'etablissements_backoffice'
EXPORT_ETABLISSEMENT_TABLE = 'etablissements'
OFFICE_TABLE = 'etablissements_prod'
DPAE_TABLE = 'dpae'

INPUT_SOURCE_FOLDER = '/srv/lbb/data'
BACKUP_FOLDER = '/srv/lbb/backups'
BACKUP_INPUT_FOLDER = '/srv/lbb/backups/inputs'
BACKUP_OUTPUT_FOLDER = '/srv/lbb/backups/outputs'

MOST_RECENT_DPAE_DATE = datetime(2012, 1, 1)

DPAE_ERROR_RATE_MAX = 0.1

MYSQL_NO_PASSWORD = False


@lru_cache(maxsize=None)
def get_departements(largest_ones_first=False):
    departements = []
    raw_departements = range(1, 96) + [97]  # 97 is DOM-TOM
    for d in raw_departements:
        if d < 10:
            dep = "0%s" % d
        else:
            dep = str(d)
        departements.append(dep)
    if largest_ones_first:
        departements = deque(departements)
        departements.remove('75')
        departements.appendleft('75')        
        departements = list(departements)
    return departements

DEPARTEMENTS = get_departements()
DEPARTEMENTS_WITH_LARGEST_ONES_FIRST = get_departements(largest_ones_first=True)


