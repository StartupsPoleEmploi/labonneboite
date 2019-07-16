# coding: utf-8
"""
Validates scoring data produced by compute_scores.
"""
from labonneboite.importer import sanity
from labonneboite.importer.jobs.common import logger


def run():
    errors = sanity.check_scores()
    if errors:
        msg = "departements with errors: %s" % ",".join(errors)
        logger.error(msg)
        raise ValueError(msg)
    logger.info("validate_scores task: FINISHED")


if __name__ == "__main__":
    run()
