# coding: utf-8
"""
Launches all compute_score jobs in parallel if possible.

We use multiprocessing library for parallelization, which launches Python functions in a new process,
bypassing the Global Interpreter Lock limits.

Each compute_score job is launched on a given departement.
"""

import sys
import traceback
from collections import deque

import multiprocessing as mp
from multiprocessing.dummy import Pool as ThreadPool
from functools import partial
import logging

from labonneboite.importer import settings
from labonneboite.importer import compute_score
from labonneboite.importer import util as import_util
from labonneboite.importer.models.computing import DpaeStatistics
from labonneboite.importer.jobs.base import Job


logger = logging.getLogger('main')
formatter = logging.Formatter("%(levelname)s - IMPORTER - %(message)s")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

COMPUTE_SCORE_TIMEOUT = 3600 * 8  # computing scores for 75 might take 4h+

# Only enable if you know what you are doing - this will compute only selected departements then fail on purpose
COMPUTE_SCORES_DEBUG_MODE = False
# compute scores only for those departements, or all if empty list
# examples: ["90"] ["51", "10"] []
# departement 90 has the least offices - thus is it most suitable for a quick debugging
COMPUTE_SCORES_DEBUG_DEPARTEMENTS = ["90"]


def abortable_worker(func, etab_table, dpae_table, departement, dpae_date, **kwargs):
    timeout = kwargs.get('timeout', None)
    p = ThreadPool(1)
    res = p.apply_async(func, args=(etab_table, dpae_table, departement, dpae_date))
    try:
        out = res.get(timeout)  # Wait timeout seconds for func to complete.
        logger.info("got result before timeout(%s)", departement)
        return out
    except mp.TimeoutError:
        logger.warning("timeout error for departement (%s)", departement)
        p.terminate()
        return None
    except:
        logger.error("abortable_worker traceback: %s", traceback.format_exc())
        return None


def compute(etab, dpae, departement, dpae_date):
    try:
        result = compute_score.run(etab, dpae, departement, dpae_date)
        logger.info("finished compute_score.run (%s)", departement)
    except:
        logger.error("error in departement %s : %s", departement, sys.exc_info()[1])
        logger.error("compute_score traceback: %s", traceback.format_exc())
        result = None
    return result


class ScoreComputingJob(Job):

    def run(self):
        """
        Tricky parallelization.
        In some cases the jobs take a long time to run, so there's COMPUTE_SCORE_TIMEOUT for that.
        If a job was not finished before the timeout, it will be added to a list to be processed sequentially.
        """
        results = []
        # Use parallel computing on all available CPU cores.
        # maxtasksperchild default is infinite, which means memory is never freed up, and grows up to 200G :-/
        # maxtasksperchild=1 ensures memory is freed up after every departement computation.
        pool = mp.Pool(processes=mp.cpu_count(), maxtasksperchild=1)
        async_results = {}
        most_recent_data_date = DpaeStatistics.get_most_recent_data_date()

        if '75' in settings.DEPARTEMENTS:
            departements = deque(settings.DEPARTEMENTS)
            departements.remove('75')
            departements.appendleft('75')
        else:
            departements = list(settings.DEPARTEMENTS)

        if COMPUTE_SCORES_DEBUG_MODE:
            if len(COMPUTE_SCORES_DEBUG_DEPARTEMENTS) >= 1:
                departements = COMPUTE_SCORES_DEBUG_DEPARTEMENTS

        for departement in departements:
            abortable_func = partial(abortable_worker, compute, timeout=COMPUTE_SCORE_TIMEOUT)
            async_result = pool.apply_async(
                abortable_func,
                args=(settings.OFFICE_TABLE, settings.DPAE_TABLE, departement, most_recent_data_date)
            )
            async_results[departement] = async_result

        logger.info("going to close process pool...")
        pool.close()
        logger.info("going to join pool")
        pool.join()
        logger.info("all compute_score done, analyzing results...")

        for departement, async_result in async_results.iteritems():
            try:
                result = async_result.get()
                if not bool(result):
                    logger.info("departement with error : %s", departement)
                results.append([departement, bool(result)])
            except:
                logger.error("traceback for unprocessed_departement: %s", traceback.format_exc())

        logger.info("compute_scores FINISHED")
        return results


if __name__ == "__main__":
    import_util.clean_tables()
    task = ScoreComputingJob()
    results = task.run()
    no_results = []
    departements = []
    for departement, result in results:
        departements.append(departement)
        if not result:
            no_results.append(departement)
    if len(no_results) > 0:
        logger.warning(
            "compute_scores did not return results for following departement (%i failures), aborting...\n%s",
            len(no_results),
            ",".join(no_results))
        sys.exit(-1)

    import_util.reduce_scores_for_backoffice(departements)
    if COMPUTE_SCORES_DEBUG_MODE:
        logger.warning("debug mode enabled, failing on purpose for debugging of temporary tables")
        sys.exit(-1)
    import_util.reduce_scores_for_main_db(departements)
    import_util.clean_tables()
    logger.info("compute_scores task: FINISHED")
