import os
import unittest
import pandas as pd
import math

from labonneboite.scripts.impact_retour_emploi.google_sheets_report import GoogleSheetReport

class TestMakeReport(unittest.TestCase):

    def test_get_nb_columns(self):
        values = {
            "values":[
                ['column0', 'column1', 'column2']
            ]
        }
        report = GoogleSheetReport(
            'fake_service',
            'fake_id',
            0,
            'A1',
            values
        )
        self.assertEqual(report.get_nb_columns(),3)

    def test_get_nb_rows(self):
        values = {
            "values":[
                ['column0', 'column1', 'column2'],
                ['value0', 'value1', 'value2'],
                ['value0', 'value1', 'value2'],
                ['value0', 'value1', 'value2'],
            ]
        }
        report = GoogleSheetReport(
            'fake_service',
            'fake_id',
            0,
            'A1',
            values
        )
        self.assertEqual(report.get_nb_rows(),4)
    
    def test_get_end_cell(self):
        values = {
            "values":[
                ['column0', 'column1', 'column2'],
                ['value0', 'value1', 'value2'],
                ['value0', 'value1', 'value2'],
                ['value0', 'value1', 'value2'],
            ]
        }
        report = GoogleSheetReport(
            'fake_service',
            'fake_id',
            0,
            'A1',
            values
        )
        self.assertEqual(report.get_end_cell(
                            report.start_cell,
                            report.get_nb_columns(),
                            report.get_nb_rows()
                        ),'C4')

        report = GoogleSheetReport(
            'fake_service',
            'fake_id',
            0,
            'B8',
            values
        )
        self.assertEqual(report.get_end_cell(
                            report.start_cell,
                            report.get_nb_columns(),
                            report.get_nb_rows()
                        ),'D11')
