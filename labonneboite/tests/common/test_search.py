import unittest
from unittest.mock import patch, Mock
import os
import json
from typing import Sequence

from labonneboite.common.search import AudienceFilter, HiddenMarketFetcher, hiring_type_util, settings, sorting, datetime as search_datetime
from labonneboite.common import search

PROPS_SUFFIX = '.props.json'
RESULT_SUFFIX = '.result.json'


class TestHiddenMarketFetcher(unittest.TestCase):
    test_dir: str = os.path.join(os.path.dirname(__file__), 'data', 'test_search')

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
        init.office_count = 10
        clone = init.clone()
        init_dict = init.__dict__
        clone_dict = clone.__dict__
        self.assertEqual(10, init_dict.pop('office_count', 'unset'))
        self.assertIsNone(clone_dict.pop('office_count', 'unset'),
                          'Clone office count should be reset, props may have change')
        self.assertEqual(init.__dict__, clone.__dict__,
                         'Missing field after clonning the object. Did you forget to clone it ?')

    @classmethod
    def _get_data_files(cls, suffix: str) -> Sequence[str]:
        filename: str
        filesnames = [filename for filename in os.listdir(cls.test_dir) if filename.endswith(suffix)]
        return filesnames

    def _get_expected_results(self):
        props_filenames = self._get_data_files(PROPS_SUFFIX)
        for props_filename in props_filenames:
            name = props_filename[:-len(PROPS_SUFFIX)]
            props_path = os.path.join(self.test_dir, props_filename)
            result_path = os.path.join(self.test_dir, f'{name}{RESULT_SUFFIX}')
            self.assertTrue(os.path.exists(result_path), f'{result_path} doesn\'t exists')
            yield (
                name,
                json.load(open(props_path, 'r')),
                json.load(open(result_path, 'r')),
            )

    @patch.object(search, 'datetime', Mock(today=Mock(return_value=Mock(strftime=Mock(return_value='2022-02-17')))))
    def test_build_json_body_elastic_search(self):
        self.assertEqual(len(self._get_data_files(PROPS_SUFFIX)), len(self._get_data_files(RESULT_SUFFIX)))
        for name, props, expected_result in self._get_expected_results():
            with self.subTest(name, **props):
                try:
                    fetcher = HiddenMarketFetcher(**props)
                except TypeError as e:
                    self.fail(f'Invalid props in {self.test_dir}/{name}{PROPS_SUFFIX} : {e}')
                result = fetcher._build_elastic_search_query()
                self.maxDiff = None
                self.assertDictEqual(expected_result, result, f"in subTest({name})")
