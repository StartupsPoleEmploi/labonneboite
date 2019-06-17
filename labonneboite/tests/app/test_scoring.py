import unittest

from labonneboite.common import scoring


class ScoringTest(unittest.TestCase):

    def test_round_half_up(self):
        self.assertEqual(0, scoring.round_half_up(0))
        self.assertEqual(-1, scoring.round_half_up(-1))

        self.assertEqual(0, scoring.round_half_up(0.4))
        self.assertEqual(0, scoring.round_half_up(-0.4))

        self.assertEqual(1, scoring.round_half_up(0.6))
        self.assertEqual(-1, scoring.round_half_up(-0.6))

        self.assertEqual(1, scoring.round_half_up(0.5))
        self.assertEqual(-1, scoring.round_half_up(-0.5))

    def test_stars_vs_score(self):
        # Match is not exact due to internal bucketing approximation.
        self.assertEqual(scoring.get_score_from_stars(scoring.get_stars_from_score(100)), 100)
        self.assertEqual(round(scoring.get_score_from_stars(scoring.get_stars_from_score(90))), 90)
        self.assertEqual(round(scoring.get_score_from_stars(scoring.get_stars_from_score(80))), 81)
        self.assertEqual(round(scoring.get_score_from_stars(scoring.get_stars_from_score(70))), 71)
        self.assertEqual(round(scoring.get_score_from_stars(scoring.get_stars_from_score(60))), 62)
        self.assertEqual(round(scoring.get_score_from_stars(scoring.get_stars_from_score(50))), 49)
        self.assertEqual(round(scoring.get_score_from_stars(scoring.get_stars_from_score(40))), 39)

        # stars can onlly vary between 2.5 and 5.0
        self.assertEqual(scoring.get_stars_from_score(scoring.get_score_from_stars(5)), 5)
        self.assertEqual(scoring.get_stars_from_score(scoring.get_score_from_stars(4)), 4)
        self.assertEqual(scoring.get_stars_from_score(scoring.get_score_from_stars(3)), 3)
        self.assertEqual(scoring.get_stars_from_score(scoring.get_score_from_stars(2.5)), 2.5)
        self.assertEqual(scoring.get_stars_from_score(scoring.get_score_from_stars(2)), 2.5)
        self.assertEqual(scoring.get_stars_from_score(scoring.get_score_from_stars(1)), 2.5)
