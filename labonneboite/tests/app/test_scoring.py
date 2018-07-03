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
