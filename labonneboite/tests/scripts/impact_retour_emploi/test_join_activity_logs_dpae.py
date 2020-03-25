import os
import unittest
from labonneboite.scripts.impact_retour_emploi.join_activity_logs_dpae import JoinActivityLogsDPAE, get_date
from labonneboite.scripts.impact_retour_emploi.daily_json_activity_parser import ActivityLogParser
import pandas as pd

class TestJoinActivityLogsDPAE(unittest.TestCase):

    def setUp(self):
        alp = ActivityLogParser()
        alp.json_logs_folder_path = f'labonneboite/tests/scripts/impact_retour_emploi/data'
        alp.json_logs_files_names_to_parse = ['activity-test.json']
        activity_df = alp.get_activity_log_dataframe(alp.json_logs_files_names_to_parse[0])
        
        self.jald = JoinActivityLogsDPAE()
        self.jald.dpae_folder_path = f'labonneboite/tests/scripts/impact_retour_emploi/data/'
        self.jald.most_recent_dpae_file = self.jald.get_most_recent_dpae_file()
        self.jald.df_activity = alp.insert_logs_activity(activity_df)
        self.jald.date_last_recorded_hiring = '2010-08-31'

    def test_get_most_recent_dpae_file(self):
        dpae_file = self.jald.get_most_recent_dpae_file()
        self.assertEqual(dpae_file,'lbb_xdpdpae_delta_201511102200.csv')

    def test_get_compression_to_use_by_pandas_according_to_file(self):
        compression = self.jald.get_compression_to_use_by_pandas_according_to_file()
        self.assertEqual(compression,'infer')

    def test_join_dpae_activity_logs(self):
        path_to_csv, df_dpae_act = self.jald.join_dpae_activity_logs()
        file_exists = os.path.isfile(path_to_csv)
        self.assertTrue(file_exists)
        self.assertIsInstance(df_dpae_act,pd.DataFrame)
        self.assertEqual(df_dpae_act.shape[0],28) #28 rows
        self.assertEqual(df_dpae_act.shape[1],34) #34 columns
        idpeconnect_list = [
            "perandomid1",
            "perandomid2",
            "perandomid3",
            "perandomid4",
            "perandomid5",
            "perandomid6",
        ]
        self.assertListEqual(list(df_dpae_act.idutilisateur_peconnect.unique()),idpeconnect_list)
        self.assertListEqual(list(df_dpae_act.dc_ididentiteexterne.unique()),idpeconnect_list)

        siret_list = [
            "00000000000000",
            "00000000000001"
        ]
        self.assertListEqual(list(df_dpae_act.siret.unique()),siret_list)
        self.assertListEqual(list(df_dpae_act.kc_siret.unique()),siret_list)

    def test_get_date(self):
        data = [['2019-10-28 00:00:00.0']]
        df = pd.DataFrame(data, columns = ['kd_dateembauche'])
        df['date'] = df.apply(lambda row: get_date(row), axis=1)

        self.assertEqual(df.loc[0,'date'],'2019-10-28')