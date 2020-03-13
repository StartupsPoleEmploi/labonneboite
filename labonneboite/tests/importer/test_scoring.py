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
    def test_high_scoring_company_has_at_least_one_dpae(self):

        # Test a bunch of departements - not all because some do break.
        departements = ["10", "20", "30", "40", "50", "57", "60", "70", "75", "80", "90", "92"]

        for departement in departements:
            offices = Office.query.filter(and_(Office.departement == departement, Office.score > 50)).limit(1000)

            last_year = datetime.now() - timedelta(days=FIFTEEN_MONTHS)

            for office in offices:
                dpae = Hiring.query.filter(and_(Hiring.siret == office.siret, Hiring.hiring_date > last_year)).all()
                dpae_all = Hiring.query.filter(Hiring.siret == office.siret).all()
                try:
                    self.assertTrue(len(dpae) > 0)
                except:
                    print(office)
                    for dpae in dpae_all:
                        print(dpae)
                    raise

    def test_converting_hirings_into_scores_back_and_forth(self):
        for score in range(101):  # [0, 1, 2, 3.. 100]
            self.assertEqual(
                score,
                scoring_util.get_score_from_hirings(scoring_util.get_hirings_from_score(score), skip_bucketing=True),
            )

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
