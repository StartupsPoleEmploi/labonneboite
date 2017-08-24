import time

from labonneboite.importer.jobs import compute_scores
from labonneboite.importer.settings import DPAE_TABLE, OFFICE_TABLE
from labonneboite.importer.tests.test_base import DatabaseTest


class TestComputeScores(DatabaseTest):

    def test_timeout_error_finishes(self):
        """
        Even if there is a timeout error, the error should be tracked and the job should finish.
        No exception should be raised uncaught.
        """

        def mock_run(a, b, c):
            time.sleep(1)

        compute_scores.ScoreComputingJob.run = mock_run
        job = compute_scores.ScoreComputingJob()
        compute_scores.COMPUTE_SCORE_TIMEOUT = 0.01
        job.run(DPAE_TABLE, OFFICE_TABLE)
