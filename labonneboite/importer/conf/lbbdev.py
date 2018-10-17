import os

# --- importer table backuping process (DPAE + ETABLISSEMENTS)
# As of Jan 2018 we no longer make backups in order to accelerate the process, and for the following reasons:
# Exports are files on lbbbackup server, mounted via NFS to lbbdev. Thus, as original files
# are stored on lbbbackup and as db tables are stored on lbbdev, data is already physically on two different
# servers, which we can consider as a rough backup good enough for now.
BACKUP_FIRST = False

# --- importer input directory of DPAE and ETABLISSEMENT exports
INPUT_SOURCE_FOLDER = '/srv/lbb/data'

# --- job 1/8 & 2/8 : check_etablissements & extract_etablissements
JENKINS_ETAB_PROPERTIES_FILENAME = os.path.join(os.environ["WORKSPACE"], "properties.jenkins")
MINIMUM_OFFICES_TO_BE_EXTRACTED_PER_DEPARTEMENT = 10000

# --- job 3/8 & 4/8 : check_dpae & extract_dpae
JENKINS_DPAE_PROPERTIES_FILENAME = os.path.join(os.environ["WORKSPACE"], "properties_dpae.jenkins")
MAXIMUM_ZIPCODE_ERRORS = 100
MAXIMUM_INVALID_ROWS = 100

# --- job 5/8 : compute_scores
SCORE_COEFFICIENT_OF_VARIATION_MAX = 2.0
RMSE_MAX = 1500  # On 2017.03.15 departement 52 reached RMSE=1141
HIGH_SCORE_COMPANIES_DIFF_MAX = 70

# --- job 6/8 : validate_scores
MINIMUM_OFFICES_PER_DEPARTEMENT_FOR_DPAE = 500
MINIMUM_OFFICES_PER_DEPARTEMENT_FOR_ALTERNANCE = 2

# --- job 8/8 : populate_flags
BACKUP_OUTPUT_FOLDER = '/srv/lbb/backups/outputs'
BACKUP_FOLDER = '/srv/lbb/backups'
