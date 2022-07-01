"""
To be executed after a scoring (update_lbb_data) to make sure the well scored companies have no DPAE.
"""
from datetime import datetime, timedelta

from sqlalchemy import and_

from labonneboite.common import scoring as scoring_util
from labonneboite.common.models import Office
from labonneboite.conf import settings
from labonneboite.importer.models.computing import Hiring
from .test_base import DatabaseTest


FIFTEEN_MONTHS = 15 * 30


class ScoringTest(DatabaseTest):

    # ############### WARNING about matching scores vs hirings ################
    # Methods scoring_util.get_hirings_from_score
    # and scoring_util.get_score_from_hirings
    # rely on special coefficients SCORE_50_HIRINGS, SCORE_60_HIRINGS etc..
    # which values in github repository are *fake* and used for dev and test only.
    #
    # The real values are confidential, stored outside of github repo,
    # and only used in staging and production.
    #
    # This is designed so that you *CANNOT* guess the hirings based
    # on the score you see in production.
    # #########################################################################

    def test_key_values_of_conversion_between_score_and_hirings(self):
        self.assertEqual(0, scoring_util.get_score_from_hirings(0))
        self.assertEqual(50, scoring_util.get_score_from_hirings(settings.SCORE_50_HIRINGS))
        self.assertEqual(60, scoring_util.get_score_from_hirings(settings.SCORE_60_HIRINGS))
        self.assertEqual(80, scoring_util.get_score_from_hirings(settings.SCORE_80_HIRINGS))
        self.assertEqual(100, scoring_util.get_score_from_hirings(settings.SCORE_100_HIRINGS))
