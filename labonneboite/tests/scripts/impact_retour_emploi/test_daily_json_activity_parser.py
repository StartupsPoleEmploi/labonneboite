import os
import unittest
import pandas as pd
import json

from labonneboite.scripts.impact_retour_emploi.daily_json_activity_parser import ActivityLogParser, siret, format_dateheure, get_date, get_propriete, clean_emploi

class TestDailyJsonActivityParser(unittest.TestCase):

    def setUp(self):
        
        self.alp = ActivityLogParser()
        self.alp.json_logs_folder_path = f'labonneboite/tests/scripts/impact_retour_emploi/data'
        self.alp.json_logs_files_names_to_parse = ['activity-test.json']

    def test_get_activity_log_dataframe(self):
        activity_df = self.alp.get_activity_log_dataframe(self.alp.json_logs_files_names_to_parse[0])
        self.assertIsInstance(activity_df,pd.DataFrame)
        self.assertEqual(activity_df.shape[0],21) #1000 rows in the test log activity
        self.assertEqual(activity_df.shape[1],9) #9 columns in the test log activity
        self.activity_df = activity_df

    def test_insert_id_peconnect(self):
        activity_df = self.alp.get_activity_log_dataframe(self.alp.json_logs_files_names_to_parse[0])
        df = self.alp.insert_id_peconnect(activity_df)
        self.assertIsInstance(df,pd.DataFrame)
        self.assertEqual(df.shape[0],6)
        self.assertEqual(df.shape[1],2)

    def test_insert_logs_activity(self):
        activity_df = self.alp.get_activity_log_dataframe(self.alp.json_logs_files_names_to_parse[0])
        df = self.alp.insert_logs_activity(activity_df)
        self.assertIsInstance(df,pd.DataFrame)
        self.assertEqual(df.shape[0],19) 
        self.assertEqual(df.shape[1],7)
        self.assertListEqual(list(df.nom.unique()),['afficher-details', 'details', 'ajout-favori'])
        self.assertEqual(df.nom[df.nom == 'details'].count(),6)
        self.assertEqual(df.nom[df.nom == 'ajout-favori'].count(),6)
        self.assertEqual(df.nom[df.nom == 'afficher-details'].count(),7)
        self.assertListEqual(list(df.siret.unique()),['00000000000000','00000000000001'])

    def test_insert_logs_activity_recherche(self):
        activity_df = self.alp.get_activity_log_dataframe(self.alp.json_logs_files_names_to_parse[0])
        df = self.alp.insert_logs_activity_recherche(activity_df)
        self.assertIsInstance(df,pd.DataFrame)
        self.assertEqual(df.shape[0],1)
        self.assertEqual(df.shape[1],5)
        emplois = ['coiffure']
        self.assertListEqual(list(df.emploi.unique()),emplois)

    def test_siret(self):
        data = [[{"siret":"48243589800507"}]]
        df = pd.DataFrame(data, columns = ['proprietes'])
        df['siret'] = df.apply(lambda row: siret(row), axis=1)

        self.assertEqual(df.loc[0,'siret'],'48243589800507')

    def test_format_dateheure(self):
        data = [['2020-01-20T01:00:22.099817']]
        df = pd.DataFrame(data, columns = ['dateheure'])
        df['dateheure'] = df.apply(lambda row: format_dateheure(row), axis=1)

        self.assertEqual(df.loc[0,'dateheure'],'2020-01-20 01:00:22')

    def test_get_date(self):
        data = [['2020-01-20 01:00:22']]
        df = pd.DataFrame(data, columns = ['dateheure'])
        df['date'] = df.apply(lambda row: get_date(row), axis=1)

        self.assertEqual(df.loc[0,'date'],'2020-01-20')

    def test_get_propriete(self):
        data = [[{
            "emploi":"pilotage-d-unite-elementaire-de-production-mecanique",
            "localisation":{
                "nom":"La Rochelle (17000)",
                "ville":"La Rochelle",
                "codepostal":"17000",
                "latitude":46.159478185419076,
                "longitude":-1.1726734305862612
                }
            }]
        ]
        df = pd.DataFrame(data, columns = ['proprietes'])
        df['ville'] = df.apply(lambda row: get_propriete(row, 'localisation','ville'), axis=1)
        df['code_postal'] = df.apply(lambda row: get_propriete(row, 'localisation','codepostal'), axis=1)
        df['emploi'] = df.apply(lambda row: get_propriete(row, 'emploi'), axis=1)

        self.assertEqual(df.loc[0,'ville'],'La Rochelle')
        self.assertEqual(df.loc[0,'code_postal'],'17000')
        self.assertEqual(df.loc[0,'emploi'],'pilotage-d-unite-elementaire-de-production-mecanique')

    def test_clean_emploi(self):
        data = [
            ["soins-d-hygiene-de-confort-du-patient99999' union select unhex(hex(version"],
            ["securite-et-surveillance-privees/static/images/logo-lbb.svg"],
            ["tel:0590482468"],
            ["vente-en-habillement-et-accessoires-de-la-personne?to=82&from=81&sa=U&ved=2ahUKEwiLqI6mi43mAhVD6aQKHVxyAP4QFjAOegQIRxAB&usg=AOvVaw1hYvyYvxE3CPZnYly-CKci"],
            ["vente-en-habillement-et-accessoires-de-la-personne%Fto=&from=&d="],
            ["conduite-de-transport-en-commun-sur-route&sa=U&ved=ahUKE"],
            ["soins-d-hygiene-de-confort-du-patient99999"],
            ["soins-d-hygiene-de-confort-du-patient\'"],
            ["www.orecrute.fr"],
            ["..."],
            ["�"],
            ["||UTL_INADDR.get_host_address("],
            ["{{__field_friYEMKBPT}}"],
            ['"><javascript:alert(String.fromCharCode(,,));">'], 
            ['"><script'],
            ['(SELECT'], 
            ['-"'],
            ['-)'], 
            ['-);select'], 
            ['..'], 
            [';copy'], 
            ['@@AMfqT'],
        ]
        df = pd.DataFrame(data, columns = ['emploi'])
        df['emploi'] = df.apply(lambda row: clean_emploi(row), axis=1)
        self.assertEqual(df.loc[0,'emploi'],'soins-d-hygiene-de-confort-du-patient')
        self.assertEqual(df.loc[1,'emploi'],'securite-et-surveillance-privees')
        self.assertEqual(df.loc[2,'emploi'],'')
        self.assertEqual(df.loc[3,'emploi'],'vente-en-habillement-et-accessoires-de-la-personne')
        self.assertEqual(df.loc[4,'emploi'],'vente-en-habillement-et-accessoires-de-la-personne')
        self.assertEqual(df.loc[5,'emploi'],'conduite-de-transport-en-commun-sur-route')
        self.assertEqual(df.loc[6,'emploi'],'soins-d-hygiene-de-confort-du-patient')
        self.assertEqual(df.loc[7,'emploi'],'soins-d-hygiene-de-confort-du-patient')
        self.assertEqual(df.loc[8,'emploi'],'')
        self.assertEqual(df.loc[9,'emploi'],'')
        self.assertEqual(df.loc[10,'emploi'],'')
        self.assertEqual(df.loc[11,'emploi'],'')
        self.assertEqual(df.loc[12,'emploi'],'')
        self.assertEqual(df.loc[13,'emploi'],'')
        self.assertEqual(df.loc[14,'emploi'],'')
        self.assertEqual(df.loc[15,'emploi'],'')
        self.assertEqual(df.loc[16,'emploi'],'')
        self.assertEqual(df.loc[17,'emploi'],'')
        self.assertEqual(df.loc[18,'emploi'],'')
        self.assertEqual(df.loc[19,'emploi'],'')
        self.assertEqual(df.loc[20,'emploi'],'')



