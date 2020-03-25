import os
import unittest
import pandas as pd
import math

from labonneboite.scripts.impact_retour_emploi.join_activity_logs_dpae import JoinActivityLogsDPAE
from labonneboite.scripts.impact_retour_emploi.daily_json_activity_parser import ActivityLogParser
from labonneboite.scripts.impact_retour_emploi.clean_activity_logs_dpae import CleanActivityLogsDPAE
from labonneboite.scripts.impact_retour_emploi.make_report import PrepareDataForGoogleSheetReport

class TestMakeReport(unittest.TestCase):

    def setUp(self):
        self.pdfgsr = PrepareDataForGoogleSheetReport()
        self.pdfgsr.csv_jp_folder_path = f'labonneboite/tests/scripts/impact_retour_emploi/data'

    def test_prepare_google_sheet_data(self):
        
        #DATA INITIALIZATION
        data = [[6,"12-2018"]]
        self.pdfgsr.df_evol_idpe_connect = pd.DataFrame(data, columns = ['count_distinct_idpe','date_month'])
        
        data = [[6,"12-2018"]]
        self.pdfgsr.df_evol_idpe_connect_sign_afficher_details = pd.DataFrame(data, columns = ['count_distinct_activity_afficher_details','date_month'])

        data = [[6,"12-2018"]]
        self.pdfgsr.df_evol_idpe_connect_sign_details = pd.DataFrame(data, columns = ['count_distinct_activity_details','date_month'])

        data = [[6,"12-2018"]]
        self.pdfgsr.df_evol_idpe_connect_sign = pd.DataFrame(data, columns = ['count_distinct_activity','date_month'])

        data = [[1,"1-2019"],[1,"2-2019"],[1,"3-2019"],[1,"5-2019"],[1,"6-2019"],[2,"10-2019"]]
        self.pdfgsr.df_evol_dpae = pd.DataFrame(data, columns = ['count_dpae_lbb','date_month'])

        self.pdfgsr.df_nb_candidatures_jp = pd.read_csv(f'{self.pdfgsr.csv_jp_folder_path}/dump_nb_candidatures_jp.csv',delimiter=';')
        self.pdfgsr.df_nb_distinct_email_jp = pd.read_csv(f'{self.pdfgsr.csv_jp_folder_path}/dump_nb_distinct_email_jp.csv',delimiter=';')
        self.pdfgsr.df_nb_candidates_with_answer_jp = pd.read_csv(f'{self.pdfgsr.csv_jp_folder_path}/dump_nb_candidates_with_answer_jp.csv',delimiter=';')
        self.pdfgsr.df_medium_delay_answer_jp = pd.read_csv(f'{self.pdfgsr.csv_jp_folder_path}/dump_medium_delay_answer_jp.csv',delimiter=';')

        #Function to test : 
        values, df = self.pdfgsr.prepare_google_sheet_data()

        #Check the validity of data sent to google sheets
        self.assertIn('values',values)
        self.assertEqual(len(values['values']),17)
        self.assertEqual(len(values['values'][0]),12)

        #Check the validity of data prepared in the dataframe
        self.assertIsInstance(df,pd.DataFrame)
        self.assertEqual(df.shape[0],17) #17 rows
        self.assertEqual(df.shape[1],12) #12 columns

        years_good_format_sorted = ['2018-11', '2018-12', '2019-01', '2019-02', '2019-03', '2019-04', '2019-05', '2019-06', '2019-07', '2019-08', '2019-09', '2019-10', '2019-11', '2019-12', '2020-01', '2020-02', '2020-03']
        self.assertEqual(df.date_month.tolist(),years_good_format_sorted)

    
    def test_prepare_2nd_google_sheet_data(self):
        data = [
            [1, "2018-12", "2019-1"],
            [2, "2018-12", "2019-10"],
            [1, "2018-12", "2019-2"],
            [1, "2018-12", "2019-3"],
            [1, "2018-12", "2019-5"],
            [1, "2018-12", "2019-6"],
        ]
        self.pdfgsr.df_evol_nb_dpae_hiring_and_activity_date = pd.DataFrame(data, columns = ['count_dpae_lbb','date_month_activite','date_month_embauche'])

        #Function to test : 
        values, df = self.pdfgsr.prepare_2nd_google_sheet_data()

        #Check the validity of data sent to google sheets
        self.assertIn('values',values)
        self.assertEqual(len(values['values']),2)
        self.assertEqual(len(values['values'][0]),7)

        #Check the validity of data prepared in the dataframe
        self.assertIsInstance(df,pd.DataFrame)
        self.assertEqual(df.shape[0],1) #1 rows
        self.assertEqual(df.shape[1],6) #6 columns

        self.assertListEqual(df.index.tolist(),['2018-12'])
        self.assertListEqual(df.columns.tolist(),['2019-01', '2019-02', '2019-03', '2019-05', '2019-06', '2019-10'])