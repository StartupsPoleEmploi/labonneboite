from datetime import date
import time
import pandas as pd
from labonneboite.importer import util as import_util
from labonneboite.importer import settings as importer_settings
from labonneboite.importer.jobs.common import logger
from labonneboite.scripts.impact_retour_emploi.settings_path_charts import DEBUG, JOIN_ON_SIREN


def clean_csv_act_dpae_file():

    dpae_folder_path = importer_settings.INPUT_SOURCE_FOLDER + '/'

    timestr = time.strftime("%Y-%m-%d")
    csv_path = f"{dpae_folder_path}act_dpae-{timestr}.csv"

    df_dpae_act = pd.read_csv(csv_path,
                              sep='|',
                              header=0)

    logger.info("The .csv file generated to clean has {} rows".format(
        df_dpae_act.shape[0]))

    df_dpae_act = df_dpae_act[df_dpae_act.premiere_embauche == 'Embauche']
    logger.info(
        "The .csv file - rows with not 'premiere embauche' has {} rows".format(df_dpae_act.shape[0]))

    # remove duplicates when multiple activities for the same dpae
    df_dpae_act = df_dpae_act.sort_values('dateheure')

    if JOIN_ON_SIREN:
        column_join_etab = 'siren'
    else:
        column_join_etab = 'siret'

    df_dpae_act = df_dpae_act.drop_duplicates(
        subset=['idutilisateur-peconnect', column_join_etab], keep='first')
    logger.info(
        "The .csv file - duplicates has {} rows ".format(df_dpae_act.shape[0]))

    # rename some columns
    df_dpae_act.rename(columns={'dateheure': 'date_activite',
                                'kd_dateembauche': 'date_embauche',
                                'nbrjourtravaille': 'duree_activite_cdd_jours',
                                'kn_trancheage': 'tranche_age',
                                'duree_pec': 'duree_prise_en_charge',
                                'dc_commune_id': 'code_postal'
                                },
                       inplace=True)

    def get_type_contrat(row):
        if row['dc_typecontrat_id'] == 1:
            return 'CDD'
        elif row['dc_typecontrat_id'] == 2:
            return 'CDI'
        return 'CTT'
    df_dpae_act['type_contrat'] = df_dpae_act.apply(
        lambda row: get_type_contrat(row), axis=1)

    def get_nb_mois(row):
        return row['duree_activite_cdd_jours'] // 30
    df_dpae_act['duree_activite_cdd_mois'] = df_dpae_act.apply(
        lambda row: get_nb_mois(row), axis=1)

    def get_nbr_jours_act_emb(row):
        de = row['date_embauche'][:10].split('-')
        da = row['date_activite'][:10].split('-')
        f_date = date(int(da[0]), int(da[1]), int(da[2]))
        l_date = date(int(de[0]), int(de[1]), int(de[2]))
        delta = l_date - f_date
        return delta.days
    df_dpae_act['diff_activite_embauche_jrs'] = df_dpae_act.apply(
        lambda row: get_nbr_jours_act_emb(row), axis=1)

    def get_priv_pub(row):
        if row['dc_privepublic'] == 0:
            return 'Public'
        return 'Prive'
    df_dpae_act['dc_privepublic'] = df_dpae_act.apply(
        lambda row: get_priv_pub(row), axis=1)

    def good_format(row):
        return row['date_embauche'][:-2]
    df_dpae_act['date_embauche'] = df_dpae_act.apply(
        lambda row: good_format(row), axis=1)

    def del_interrogation(row):
        if row['tranche_age'] == 'de 26 ans ? 50 ans':
            return 'entre 26 et 50 ans'
        return row['tranche_age']
    df_dpae_act['tranche_age'] = df_dpae_act.apply(
        lambda row: del_interrogation(row), axis=1)

    def del_cdd_incoherent(row):
        try:
            if int(row['duree_activite_cdd_jours']) > 1200:
                return 1
            return 0
        except:
            return 0
    df_dpae_act['temporaire'] = df_dpae_act.apply(
        lambda row: del_cdd_incoherent(row), axis=1)
    df_dpae_act = df_dpae_act[df_dpae_act.temporaire == 0]
    logger.info(
        "The .csv file - contrats which last too long to be legal has {} rows".format(df_dpae_act.shape[0]))

    # We only have activities in august for 31/08/2018 --> ugly charts, we want to start from the 1st september
    df_dpae_act = df_dpae_act[df_dpae_act.date_activite > "2018-08-31"]
    logger.info(
        "The .csv file - activity with date = 31/08/2018 has {} rows".format(df_dpae_act.shape[0]))

    cols_of_interest = ['idutilisateur_peconnect',
                        'siret',
                        'date_activite',
                        'date_embauche',
                        'type_contrat',
                        'duree_activite_cdd_mois',
                        'duree_activite_cdd_jours',
                        'diff_activite_embauche_jrs',
                        'dc_lblprioritede',
                        'tranche_age',
                        'dc_privepublic',
                        'duree_prise_en_charge',
                        'dn_tailleetablissement',
                        'code_postal']

    if JOIN_ON_SIREN:
        cols_of_interest.append('siren')

    df_dpae_act = df_dpae_act[cols_of_interest]

    engine = import_util.create_sqlalchemy_engine()

    table_name_act_dpae = 'act_dpae_clean_siren' if JOIN_ON_SIREN is True else 'act_dpae_clean'
    query = f"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '{table_name_act_dpae}'"

    if engine.execute(query).fetchone()[0] == 1:  # Table existe
        existing_sql_table = True
    else:
        existing_sql_table = False

    if existing_sql_table:

        query = f"select * from {table_name_act_dpae}"
        df_dpae_act_existing = pd.read_sql_query(query, engine)

        # In case a problem appear in the script, we save old datas under .csv extension
        # because we will rewrite the whole table after each execution, we have to remove duplicates
        df_dpae_act_existing.to_csv(
            f"{dpae_folder_path}backup_sql_{table_name_act_dpae}", encoding='utf-8', sep='|')
        logger.info(
            "There were already act/dpae : {} rows".format(df_dpae_act_existing.shape[0]))
        df_dpae_act = pd.concat([df_dpae_act, df_dpae_act_existing])
        logger.info("Concatenation of both has {} rows".format(
            df_dpae_act.shape[0]))

    df_dpae_act = df_dpae_act.drop_duplicates(
        subset=['idutilisateur_peconnect', column_join_etab], keep='first')
    logger.info(
        "Concatenation of both - duplicates has {} rows".format(df_dpae_act.shape[0]))

    df_dpae_act.to_sql(con=engine, name=table_name_act_dpae,
                       if_exists='replace', index=False, chunksize=10000)

    engine.close()


def run_main():
    clean_csv_act_dpae_file()


if __name__ == '__main__':
    run_main()
