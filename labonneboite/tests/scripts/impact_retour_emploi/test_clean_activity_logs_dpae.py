import unittest
import math
import pandas as pd

from labonneboite.scripts.impact_retour_emploi.join_activity_logs_dpae import JoinActivityLogsDPAE
from labonneboite.scripts.impact_retour_emploi.daily_json_activity_parser import ActivityLogParser
from labonneboite.scripts.impact_retour_emploi.clean_activity_logs_dpae import CleanActivityLogsDPAE, get_type_contrat, get_nb_mois, get_nbr_jours_act_emb, get_priv_pub, clean_date, get_tranche_age, delete_cdd_too_long


class TestCleanActivityLogsDPAE(unittest.TestCase):

    def setUp(self):
        alp = ActivityLogParser()
        alp.json_logs_folder_path = f'labonneboite/tests/scripts/impact_retour_emploi/data'
        alp.json_logs_files_names_to_parse = ['activity-test.json']
        activity_df = alp.get_activity_log_dataframe(alp.json_logs_files_names_to_parse[0])

        jald = JoinActivityLogsDPAE()
        jald.dpae_folder_path = f'labonneboite/tests/scripts/impact_retour_emploi/data/'
        jald.most_recent_dpae_file = jald.get_most_recent_dpae_file()
        jald.df_activity = alp.insert_logs_activity(activity_df)
        jald.date_last_recorded_hiring = '2010-08-31'
        jald.join_dpae_activity_logs()

        self.clean_act_log_dpae = CleanActivityLogsDPAE()
        self.clean_act_log_dpae.csv_folder_path = f'labonneboite/tests/scripts/impact_retour_emploi/data/'
        self.clean_act_log_dpae.set_most_recent_csv_file()
        self.clean_act_log_dpae.set_df_dpae_act()

    def test_get_most_recent_csv_file(self):
        csv_file = self.clean_act_log_dpae.get_most_recent_csv_file()
        self.assertIn('act_dpae-', csv_file)

    def test_clean_csv_act_dpae_file(self):
        df = self.clean_act_log_dpae.clean_csv_act_dpae_file()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(df.shape[0], 7)  # 7 rows
        self.assertEqual(df.shape[1], 14)  # 14 columns
        idpeconnect_list = [
            "perandomid1",
            "perandomid2",
            "perandomid3",
            "perandomid4",
            "perandomid5",
            "perandomid6",
        ]

        id_list = df.idutilisateur_peconnect.unique()
        id_list.sort()
        self.assertListEqual(list(id_list), idpeconnect_list)

        siret_list = [
            "00000000000001",
            "00000000000000"
        ]
        self.assertListEqual(list(df.siret.unique()), siret_list)

    def test_get_type_contrat(self):
        data = [[0], [1], [2]]
        df = pd.DataFrame(data, columns=['dc_typecontrat_id'])
        df['type_contrat'] = df.apply(lambda row: get_type_contrat(row), axis=1)

        self.assertEqual(df.loc[0, 'type_contrat'], 'CTT')
        self.assertEqual(df.loc[1, 'type_contrat'], 'CDD')
        self.assertEqual(df.loc[2, 'type_contrat'], 'CDI')

    def test_get_nb_mois(self):
        data = [[0], [15], [30], [70], [None], ['']]
        df = pd.DataFrame(data, columns=['duree_activite_cdd_jours'])
        df['duree_activite_cdd_mois'] = df.apply(lambda row: get_nb_mois(row), axis=1)
        self.assertEqual(df.loc[0, 'duree_activite_cdd_mois'], 0)
        self.assertEqual(df.loc[1, 'duree_activite_cdd_mois'], 0)
        self.assertEqual(df.loc[2, 'duree_activite_cdd_mois'], 1)
        self.assertEqual(df.loc[3, 'duree_activite_cdd_mois'], 2)
        self.assertTrue(math.isnan(df.loc[4, 'duree_activite_cdd_mois']))
        self.assertTrue(math.isnan(df.loc[5, 'duree_activite_cdd_mois']))

    def test_get_nbr_jours_act_emb(self):
        data = [
            ['2018-12-29 04:07:00', '2018-12-31 04:07:00'],
            ['2018-12-29 04:07:00', '2019-12-29 04:07:00'],
            ['2018-12-29 04:07:00', '2019-01-04 04:07:00']
        ]
        df = pd.DataFrame(data, columns=['date_activite', 'date_embauche'])
        df['nb_jours_diff'] = df.apply(lambda row: get_nbr_jours_act_emb(row), axis=1)
        self.assertEqual(df.loc[0, 'nb_jours_diff'], 2)
        self.assertEqual(df.loc[1, 'nb_jours_diff'], 365)
        self.assertEqual(df.loc[2, 'nb_jours_diff'], 6)

    def test_get_priv_pub(self):
        data = [[0], [1], [2], ['random']]
        df = pd.DataFrame(data, columns=['dc_privepublic'])
        df['secteur'] = df.apply(lambda row: get_priv_pub(row), axis=1)

        self.assertEqual(df.loc[0, 'secteur'], 'Public')
        self.assertEqual(df.loc[1, 'secteur'], 'Prive')
        self.assertEqual(df.loc[2, 'secteur'], None)
        self.assertEqual(df.loc[3, 'secteur'], None)

    def test_clean_date(self):
        data = [["2019-10-28 00:00:00.0"]]
        df = pd.DataFrame(data, columns=['date_embauche'])
        df['date_embauche'] = df.apply(lambda row: clean_date(row), axis=1)
        self.assertEqual(df.loc[0, 'date_embauche'], '2019-10-28 00:00:00')

    def test_get_tranche_age(self):
        data = [["- de 26 ans"], ["+ de 20 ans"], ['de 26 ans ? 50 ans']]
        df = pd.DataFrame(data, columns=['tranche_age'])
        df['tranche_age'] = df.apply(lambda row: get_tranche_age(row), axis=1)

        self.assertEqual(df.loc[0, 'tranche_age'], '- de 26 ans')
        self.assertEqual(df.loc[1, 'tranche_age'], '+ de 20 ans')
        self.assertEqual(df.loc[2, 'tranche_age'], 'entre 26 et 50 ans')

    def test_delete_cdd_too_long(self):
        data = [[None], [10000], [1300], [36]]
        df = pd.DataFrame(data, columns=['duree_activite_cdd_jours'])
        df['status_cdd'] = df.apply(lambda row: delete_cdd_too_long(row), axis=1)

        self.assertEqual(df.loc[0, 'status_cdd'], 'OK')
        self.assertEqual(df.loc[1, 'status_cdd'], 'KO')
        self.assertEqual(df.loc[2, 'status_cdd'], 'KO')
        self.assertEqual(df.loc[3, 'status_cdd'], 'OK')
