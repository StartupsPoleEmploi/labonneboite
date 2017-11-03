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

from labonneboite.importer import settings
from labonneboite.importer import compute_score
from labonneboite.importer import util as import_util
from labonneboite.importer.util import timeit
from labonneboite.importer.models.computing import DpaeStatistics
from labonneboite.importer.jobs.base import Job
from labonneboite.importer.jobs.common import logger

# Only enable if you know what you are doing - this will compute only selected departements then fail on purpose
COMPUTE_SCORES_DEBUG_MODE = False
# compute scores only for those departements, or all if empty list
# examples: ["90"] ["51", "10"] []
# departement 90 has the least offices - thus is it most suitable for a quick debugging
COMPUTE_SCORES_DEBUG_DEPARTEMENTS = ["90"]

# If parallel computing is enabled, you cannot use debugger like ipdb from
# within a job.
DISABLE_PARALLEL_COMPUTING_FOR_DEBUGGING = False


def abortable_worker(func, etab_table, dpae_table, departement, dpae_date):
    p = ThreadPool(1)
    res = p.apply_async(func, args=(etab_table, dpae_table, departement, dpae_date))
    result = res.get()
    logger.info("got result for departement %s", departement)
    return result


@timeit
def compute(etab, dpae, departement, dpae_date):
    result = compute_score.run(etab, dpae, departement, dpae_date)
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
        most_recent_data_date = DpaeStatistics.get_most_recent_data_date()

        departements = settings.DEPARTEMENTS_WITH_LARGEST_ONES_FIRST

        if COMPUTE_SCORES_DEBUG_MODE:
            if len(COMPUTE_SCORES_DEBUG_DEPARTEMENTS) >= 1:
                departements = COMPUTE_SCORES_DEBUG_DEPARTEMENTS

        if DISABLE_PARALLEL_COMPUTING_FOR_DEBUGGING:  # single thread computing
            for departement in departements:
                compute_result = compute(settings.OFFICE_TABLE,
                    settings.DPAE_TABLE, departement, most_recent_data_date)
                compute_results[departement] = compute_result
        else:  # parallel computing
            for departement in departements:
                abortable_func = partial(abortable_worker, compute)
                compute_result = pool.apply_async(
                    abortable_func,
                    args=(settings.OFFICE_TABLE, settings.DPAE_TABLE, departement, most_recent_data_date)
                )
                compute_results[departement] = compute_result.get()

            logger.info("going to close process pool...")
            pool.close()
            logger.info("going to join pool")
            pool.join()
            logger.info("all compute_score done, analyzing results...")

        for departement, compute_result in compute_results.iteritems():
            if not bool(compute_result):
                logger.info("departement with error : %s", departement)
            results.append([departement, bool(compute_result)])

        logger.info("compute_scores FINISHED")
        return results


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
    if COMPUTE_SCORES_DEBUG_MODE:
        logger.warning("debug mode enabled, failing on purpose for debugging of temporary tables")
        sys.exit(-1)
    import_util.reduce_scores_for_main_db(departements)
    import_util.clean_temporary_tables()
    logger.info("compute_scores task: FINISHED")


if __name__ == "__main__":
    run_main()
    