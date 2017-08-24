# coding: utf-8
"""
Validates scoring data produced by compute_scores.
"""

import logging

logger = logging.getLogger('main')
formatter = logging.Formatter("%(levelname)s - IMPORTER - %(message)s")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

from labonneboite.importer import sanity

COMPUTE_SCORE_TIMEOUT = 3600 * 4  # four hours should be largely enough to compute scores for an entire departement


if __name__ == "__main__":
    errors = sanity.check_scores()
    if errors:
        logger.error("departements with errors: %s", " ".join(errors))
        raise Exception
    logger.info("validate_scores task: FINISHED")
