# --- job 1/8 & 2/8 : check_etablissements & extract_etablissements
DISTINCT_DEPARTEMENTS_HAVING_OFFICES = 15

# --- job 5/8 : compute_scores
MINIMUM_OFFICES_REQUIRED_TO_TRAIN_MODEL = 0
RMSE_MAX = 20000
MAXIMUM_COMPUTE_SCORE_JOB_FAILURES = 94  # 96 departements == 2 successes + 94 failures

# --- job 6/8 : validate_scores
SCORE_REDUCING_MINIMUM_THRESHOLD = 0
DEPARTEMENTS_TO_BE_SANITY_CHECKED = ['14', '69']
