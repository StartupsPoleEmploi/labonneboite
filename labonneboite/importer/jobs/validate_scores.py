# coding: utf-8
"""
Validates scoring data produced by compute_scores.
"""
import os
from labonneboite.importer import sanity
from labonneboite.importer.jobs.common import logger
from labonneboite.importer.util import history_importer_job_decorator


@history_importer_job_decorator(os.path.basename(__file__))
def run():
    errors = sanity.check_scores()
    if errors:
        msg = "departements with errors: %s" % ",".join(errors)
        logger.error(msg)
        raise ValueError(msg)
    logger.info("validate_scores task: FINISHED")


if __name__ == "__main__":
    run()
