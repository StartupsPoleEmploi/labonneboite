import os

BACKUP_FIRST = True

INPUT_SOURCE_FOLDER = '/srv/lbb/data'

JENKINS_ETAB_PROPERTIES_FILENAME = os.path.join(os.environ["WORKSPACE"], "properties.jenkins")
JENKINS_DPAE_PROPERTIES_FILENAME = os.path.join(os.environ["WORKSPACE"], "properties_dpae.jenkins")

MINIMUM_OFFICES_TO_BE_EXTRACTED_PER_DEPARTEMENT = 10000

SCORE_COEFFICIENT_OF_VARIATION_MAX = 0.35

MINIMUM_OFFICES_PER_DEPARTEMENT = 100

BACKUP_OUTPUT_FOLDER = '/srv/lbb/backups/outputs'

BACKUP_FOLDER = '/srv/lbb/backups'
