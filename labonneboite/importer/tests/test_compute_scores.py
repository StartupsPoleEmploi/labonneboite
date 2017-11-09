import time

from labonneboite.importer.jobs import compute_scores
from labonneboite.importer.settings import DPAE_TABLE, OFFICE_TABLE
from labonneboite.importer.tests.test_base import DatabaseTest


class TestComputeScores(DatabaseTest):

    def test_minimalistic_mock_run_finishes(self):

        def mock_run(a, b, c):
            time.sleep(1)

        compute_scores.ScoreComputingJob.run = mock_run
        job = compute_scores.ScoreComputingJob()
        job.run(DPAE_TABLE, OFFICE_TABLE)
