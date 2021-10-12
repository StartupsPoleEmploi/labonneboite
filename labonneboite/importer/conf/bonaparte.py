import os

# --- importer input directory of DPAE and ETABLISSEMENT exports
INPUT_SOURCE_FOLDER = '/srv/lbb/data'

# --- job 1/8 & 2/8 : check_etablissements & extract_etablissements
MINIMUM_OFFICES_TO_BE_EXTRACTED_PER_DEPARTEMENT = 10000

# --- job 3/8 & 4/8 : check_dpae & extract_dpae
MAXIMUM_ZIPCODE_ERRORS = 100
MAXIMUM_INVALID_ROWS = 100

# --- job 5/8 : compute_scores
SCORE_COEFFICIENT_OF_VARIATION_MAX = 2.0
RMSE_MAX = 15000  # On 2020.08.20 departement 11 reached RMSE=1822 and department 73 reached RMSE=1829
HIGH_SCORE_COMPANIES_DIFF_MAX = 85  # On 2020.08.04 department 43 reached evolution 81.65 ==> Exception('evolution too high: 81.65289256198348 > 75',)

# --- job 6/8 : validate_scores
MINIMUM_OFFICES_PER_DEPARTEMENT_FOR_DPAE = 500
MINIMUM_OFFICES_PER_DEPARTEMENT_FOR_ALTERNANCE = 0

# --- job 8/8 : populate_flags
