# coding: utf-8
"""
Launches all compute_score jobs in parallel if possible.

We use multiprocessing library for parallelization, which launches Python functions in a new process,
bypassing the Global Interpreter Lock limits.

Each compute_score job is launched on a given departement.
"""
import sys
import multiprocessing as mp
from multiprocessing.dummy import Pool as ThreadPool
from functools import partial
import os

from labonneboite.common import departements as dpt
from labonneboite.importer import settings
from labonneboite.importer import compute_score
from labonneboite.importer import util as import_util
from labonneboite.importer.util import history_importer_job_decorator
from labonneboite.common.util import timeit
from labonneboite.importer.jobs.base import Job
from labonneboite.importer.jobs.common import logger

# Only enable if you know what you are doing - this will compute only selected departements then fail on purpose
COMPUTE_SCORES_DEBUG_MODE = False
# compute scores only for those departements, or all if empty list
# examples: ["90"] ["51", "10"] []
# departement 90 has the least offices - thus is it most suitable for a quick debugging
# departements ["14", "69"] are the only departements with actual data in local dev
COMPUTE_SCORES_DEBUG_DEPARTEMENTS = ["90"]

# If parallel computing is enabled, you cannot use debugger like ipdb from
# within a job.
DISABLE_PARALLEL_COMPUTING_FOR_DEBUGGING = False


def apply_async(pool, func, departement):
    # note: it is very important to use `(departement,)` which is a 1-tuple,
    # since `(departement)` is actually not a tuple, and apply_async
    # will parse the departement as two values e.g. 57 becomes (5, 7) o_O
    return pool.apply_async(func, args=(departement,))


def abortable_worker(func, departement):
    pool = ThreadPool(1)
    res = apply_async(pool, func, departement)
    result = res.get()
    logger.info("got result for departement %s", departement)
    return result


@timeit
def compute(departement):
    result = compute_score.run(departement)
    logger.info("finished compute_score.run (%s)", departement)
    return result


class ScoreComputingJob(Job):

    @timeit
    def run(self):
        """
        Tricky parallelization on all available CPU cores.
        """
        results = []
        # maxtasksperchild default is infinite, which means memory is never freed up, and grows up to 200G :-/
        # maxtasksperchild=1 ensures memory is freed up after every departement computation.
        pool = mp.Pool(processes=mp.cpu_count(), maxtasksperchild=1)
        compute_results = {}

        departements = dpt.DEPARTEMENTS_WITH_LARGEST_ONES_FIRST

        if COMPUTE_SCORES_DEBUG_MODE:
            if len(COMPUTE_SCORES_DEBUG_DEPARTEMENTS) >= 1:
                departements = COMPUTE_SCORES_DEBUG_DEPARTEMENTS

        if DISABLE_PARALLEL_COMPUTING_FOR_DEBUGGING:  # single thread computing
            logger.info("starting single thread computing pool...")
            for departement in departements:
                compute_result = compute(departement)
                compute_results[departement] = compute_result
        else:  # parallel computing
            logger.info("starting parallel computing pool (%s jobs in parallel)...", mp.cpu_count())
            for departement in departements:
                abortable_func = partial(abortable_worker, compute)
                # apply_async returns immediately
                compute_results[departement] = apply_async(pool, abortable_func, departement)

            logger.info("going to close process pool...")
            pool.close()
            logger.info("going to join pool")
            pool.join()
            logger.info("all compute_score done, analyzing results...")

            at_least_one_departement_failed = False

            for departement in departements:
                # get() blocks until job is completed, this is why we run it only after
                # all jobs have completed.
                try:
                    compute_results[departement] = compute_results[departement].get()
                except Exception as e:
                    logger.info("departement %s met exception : %s", departement, repr(e))
                    at_least_one_departement_failed = True

            if at_least_one_departement_failed:
                raise Exception('At least one departement failed. See above for details.')
                    
        for departement, compute_result in compute_results.items():
            if not compute_result:
                logger.info("departement with error : %s", departement)
            results.append([departement, compute_result])

        logger.info("compute_scores FINISHED")
        return results

@history_importer_job_decorator(os.path.basename(__file__))
@timeit
def run_main():
    import_util.clean_temporary_tables()
    task = ScoreComputingJob()
    results = task.run()
    no_results = []
    departements = []
    for departement, result in results:
        departements.append(departement)
        if not result:
            no_results.append(departement)
    if len(no_results) > settings.MAXIMUM_COMPUTE_SCORE_JOB_FAILURES:
        results = set(departements) - set(no_results)
        logger.warning(
            "compute_scores by departement : %i failures (%s) vs %i successes (%s), aborting...",
            len(no_results),
            ",".join(no_results),
            len(results),
            ",".join(results),
        )
        sys.exit(-1)

    import_util.reduce_scores_for_backoffice(departements)
    import_util.reduce_scores_for_main_db(departements)
    if COMPUTE_SCORES_DEBUG_MODE:
        logger.warning("debug mode enabled, failing on purpose for debugging of temporary tables")
        sys.exit(-1)
    import_util.clean_temporary_tables()
    logger.info("compute_scores task: FINISHED")


if __name__ == "__main__":
    run_main()
