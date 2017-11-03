# coding: utf-8
"""
Validates scoring data produced by compute_scores.
"""
from labonneboite.importer import sanity
from labonneboite.importer.jobs.common import logger

COMPUTE_SCORE_TIMEOUT = 3600 * 4  # four hours should be largely enough to compute scores for an entire departement


if __name__ == "__main__":
    errors = sanity.check_scores()
    if errors:
        logger.error("departements with errors: %s", " ".join(errors))
        raise Exception
    logger.info("validate_scores task: FINISHED")
