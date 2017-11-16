# --- importer input directory of DPAE and ETABLISSEMENT exports
INPUT_SOURCE_FOLDER = '/srv/lbb/labonneboite/importer/tests/data'

# --- job 1/8 & 2/8 : check_etablissements & extract_etablissements
DISTINCT_DEPARTEMENTS_HAVING_OFFICES = 15

# --- job 5/8 : compute_scores
SCORE_COEFFICIENT_OF_VARIATION_MAX = 1.0
HIGH_SCORE_COMPANIES_COUNT_MIN = 0

# --- job 6/8 : validate_scores
DEPARTEMENTS_TO_BE_SANITY_CHECKED = []
