from datetime import datetime

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


def get_departements():
    departements_str = []
    departements = range(1, 96)
    departements.append(97)  # DOM-TOM
    for d in departements:
        if d < 10:
            dep = "0%s" % d
        else:
            dep = str(d)
        departements_str.append(dep)
    return departements_str

DEPARTEMENTS = get_departements()
