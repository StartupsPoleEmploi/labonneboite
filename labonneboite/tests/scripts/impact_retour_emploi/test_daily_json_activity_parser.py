import os
import unittest
from labonneboite.scripts.impact_retour_emploi.daily_json_activity_parser import ActivityLogParser
import pandas as pd


class DailyJsonActivityParser(unittest.TestCase):

    def setUp(self):
        
        self.alp = ActivityLogParser()
        self.alp.json_logs_folder_path = f'labonneboite/tests/scripts/impact_retour_emploi/data'
        self.alp.json_logs_files_names_to_parse = ['activity-test.json']

    def test_get_activity_log_dataframe(self):
        activity_df = self.alp.get_activity_log_dataframe(self.alp.json_logs_files_names_to_parse[0])
        self.assertIsInstance(activity_df,pd.DataFrame)
        self.assertEqual(activity_df.shape[0],1000) #1000 rows in the test log activity
        self.assertEqual(activity_df.shape[1],9) #9 columns in the test log activity
        self.activity_df = activity_df

    def test_insert_id_peconnect(self):
        activity_df = self.alp.get_activity_log_dataframe(self.alp.json_logs_files_names_to_parse[0])
        df = self.alp.insert_id_peconnect(activity_df)
        self.assertIsInstance(df,pd.DataFrame)
        self.assertEqual(df.shape[0],82) 
        self.assertEqual(df.shape[1],2)

    def test_insert_logs_activity(self):
        activity_df = self.alp.get_activity_log_dataframe(self.alp.json_logs_files_names_to_parse[0])
        df = self.alp.insert_logs_activity(activity_df)
        self.assertIsInstance(df,pd.DataFrame)
        self.assertEqual(df.shape[0],133) 
        self.assertEqual(df.shape[1],7)
        self.assertListEqual(list(df.nom.unique()),['ajout-favori', 'afficher-details', 'details'])
        self.assertEqual(df.nom[df.nom == 'details'].count(),105)
        self.assertEqual(df.nom[df.nom == 'ajout-favori'].count(),3)
        self.assertEqual(df.nom[df.nom == 'afficher-details'].count(),25)
        self.assertListEqual(list(df.utm_medium.unique()),[None, 'mailing', 'web', ''])

    def test_insert_logs_activity_recherche(self):
        activity_df = self.alp.get_activity_log_dataframe(self.alp.json_logs_files_names_to_parse[0])
        df = self.alp.insert_logs_activity_recherche(activity_df)
        self.assertIsInstance(df,pd.DataFrame)
        self.assertEqual(df.shape[0],10)
        self.assertEqual(df.shape[1],5)
        emplois = [
            'secretariat', 
            'coiffure', 
            'developpement-des-ressources-humaines',
            'salubrite-et-traitement-de-nuisibles',
            'defense-et-conseil-juridique', 
            'personnel-d-etage',
            'personnel-polyvalent-des-services-hospitaliers',
            'services-domestiques', 'plonge-en-restauration',
            'soins-esthetiques-et-corporels'
        ]
        self.assertListEqual(list(df.emploi.unique()),emplois)