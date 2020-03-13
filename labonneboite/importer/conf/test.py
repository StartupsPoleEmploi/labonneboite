import os
from datetime import datetime


# --- importer input directory of DPAE and ETABLISSEMENT exports
INPUT_SOURCE_FOLDER = os.path.join(os.path.dirname(__file__), "..", "..", "tests", "importer", "data")

# --- job 1/8 & 2/8 : check_etablissements & extract_etablissements
DISTINCT_DEPARTEMENTS_HAVING_OFFICES = 15

# --- job 3/8 & 4/8 : check_dpae & extract_dpae

# --- job 5/8 : compute_scores
SCORE_COEFFICIENT_OF_VARIATION_MAX = 1.0
HIGH_SCORE_COMPANIES_COUNT_MIN = 0
MINIMUM_OFFICES_REQUIRED_TO_TRAIN_MODEL = 10
ALTERNANCE_LAST_HISTORICAL_DATA_DATE = datetime(2011, 8, 31)

# --- job 6/8 : validate_scores
DEPARTEMENTS_TO_BE_SANITY_CHECKED = []
