import unittest

from labonneboite.common.search import AudienceFilter, HiddenMarketFetcher, hiring_type_util, settings, sorting


class TestHiddenMarketFetcher(unittest.TestCase):

    def test_clone(self):
        init = HiddenMarketFetcher(
            longitude=1,
            latitude=2,
            departments=[3],
            romes=['4'],
            distance=5,
            travel_mode='unused',
            sort=sorting.SORT_FILTER_SCORE,
            hiring_type=hiring_type_util.ALTERNANCE,
            from_number=10,
            to_number=20,
            audience=AudienceFilter.ALL,
            headcount=settings.HEADCOUNT_WHATEVER,
            naf=['NAF'],
            naf_codes=['NAF01'],
            aggregate_by=['naf'],
            flag_pmsmp=1,
        )
        clone = init.clone()
        self.assertIn('office_count', init.__dict__, 'The test case is incorrect, all fields aren\'t in __dict__...')
        self.assertEqual(init.__dict__, clone.__dict__,
                         'Missing field after clonning the object. Did you forget to clone it ?')
