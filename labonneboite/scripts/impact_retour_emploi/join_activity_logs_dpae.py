# -*- coding: utf-8 -*-

import os
import urllib
import pandas as pd
from labonneboite.importer import util as import_util
from labonneboite.importer import settings as importer_settings
from labonneboite.importer.jobs.common import logger

# TODO : To improve datas about job sector, to have more informations : use code NAF --> Luc Caffier

DEBUG = False

def get_activity_logs():
    engine = import_util.create_sqlalchemy_engine()

    query = "select * from activity_logs"
    if DEBUG: 
        query += " ORDER BY RAND() LIMIT 1000000"
    df_activity = pd.read_sql_query(query, engine)

    engine.close()

    # TODO : Défninir une durée pour laquelle on considère qu'une activité sur LBB n'a pas d'impacts sur le retour à l'emploi
    # Cela permettra de ne pas recharger tous les logs d'activité à chaque fois, mais uniquement sur une certaine période
    # https://valodata.slack.com/archives/C0QR8RYL8/p1562319224015200 
    # df_activity = df_activity[df_activity.dateheure > duree_activity_not_prise_en_compte]

    logger.info('Activities logs are loaded')

    return df_activity

def join_dpae_activity_logs(df_activity):
    # function used to create a new column from dateheure column in dpae
    def get_date(row):
        return row['kd_dateembauche'][:10]

    dpae_folder_path = importer_settings.INPUT_SOURCE_FOLDER+'/'
    dpae_paths = os.listdir(dpae_folder_path)
    # IMPORTANT : Need to copy the DPAE file from /mnt/datalakepe/ to /srv/lbb/data
    # It is certainly ok, because of the importer which also needs this file
    dpae_paths = [i for i in dpae_paths if i.startswith('LBB_XDPDPAE')]

    dpae_paths.sort()
    most_recent_dpae_file = dpae_paths[-1]

    logger.info("the DPAE file which will be used is : {}".format(most_recent_dpae_file))

    #We select the last DPAE date that has been used in the last joined dpae
    engine = import_util.create_sqlalchemy_engine()

    query = "select date_embauche from act_dpae_clean order by date_embauche DESC LIMIT 1 "
    row = engine.execute(query).fetchone()
    date_last_recorded_activity = row[0].split()[0]

    logger.info("the most recent date found is {} ".format(date_last_recorded_activity))

    engine.close()

    # We use the datas in csv using smaller chunks
    if DEBUG:
        chunksize = 10 ** 5
    else:
        chunksize = 10 ** 6
    i = 0

    column_names = ['kc_siret', 'dc_naf_id', 'dc_adresse', 'dc_codepostal', '_',
                    'dn_tailleetablissement', 'dc_communenaissancepays', 'kd_dateembauche',
                    'dc_typecontrat_id', 'dd_datefincdd', 'dc_romev3_1_id', 'dc_romev3_2_id',
                    'kd_datecreation', 'dc_privepublic', 'dc_commune_id', 'dc_natureemploi_id',
                    'dc_qualitesalarie_id', 'dn_dureetravailhebdo', 'dn_dureetravailmensuelle',
                    'dn_dureetravailannuelle', 'nbrjourtravaille', 'iiann', 'dc_lblprioritede',
                    'kn_trancheage', 'duree_pec', 'dc_ididentiteexterne', 'premiere_embauche']

    total_rows_kept = 0

    for df_dpae in pd.read_csv(dpae_folder_path+most_recent_dpae_file,
                            header=None,
                            compression='bz2',
                            names=column_names,
                            sep='|',
                            index_col=False,
                            chunksize=chunksize):

        logger.info("Sample of DPAE has : {} rows".format(df_dpae.shape[0]))

        # remove rows where the data is > to the 11 10 2018 (dont have activity dates after this)
        df_dpae['kd_dateembauche_bis'] = df_dpae.apply(
            lambda row: get_date(row), axis=1)
        df_dpae = df_dpae[df_dpae.kd_dateembauche_bis > date_last_recorded_activity]
        logger.info("Sample of DPAE minus old dates has : {} rows".format(df_dpae.shape[0]))

        # convert df dpae columns to 'object'
        df_dpae = df_dpae.astype(str)

        df_dpae_act = pd.merge(df_dpae,
                        df_activity,
                        how='left', 
                        left_on=['dc_ididentiteexterne', 'kc_siret'],
                        right_on=['idutilisateur_peconnect', 'siret'])
        logger.info("Sample of merged activity/DPAE has : {} rows".format(df_dpae_act.shape[0]))

        # filter on the fact that dateheure activity must be inferior to kd_dateembauche
        df_dpae_act = df_dpae_act[df_dpae_act.kd_dateembauche_bis > df_dpae_act.dateheure]
        df_dpae_act = df_dpae_act.drop(['kd_dateembauche_bis'], axis=1)
        logger.info("Sample of merged activity/DPAE with the good dates has : {} rows".format(df_dpae_act.shape[0]))

        path_to_csv = dpae_folder_path+'act_dpae.csv'
        exists = os.path.isfile(path_to_csv)

        #We want to rewrite the CSV file after each new execution of DPAE extraction
        if exists and i == 0:
            os.remove(path_to_csv)
            df_dpae_act.to_csv(path_to_csv, encoding='utf-8', sep='|')
        else:
            with open(path_to_csv, 'a') as f:
                df_dpae_act.to_csv(f, header=False, sep='|')

        total_rows_kept += df_dpae_act.shape[0]
        logger.info(" --> Nb rows we keep in this sample : {} rows".format(df_dpae_act.shape[0]))
        logger.info(" --> Nb total rows that have been kept : {} rows".format(total_rows_kept))
        logger.info(" --> Nb total rows of DPAE that has been parsed : {} rows".format((i+1) * chunksize))
        logger.info("-------------------------")
        i += 1
        
        #In debug mode, we stop parsing the DPAE file when we reach (10 ** 5) * 20 = 2 000 000 lines
        if DEBUG and i == 20:
            break
    
    return path_to_csv

def run_main():
    df_activity = get_activity_logs()
    join_dpae_activity_logs(df_activity)

if __name__ == '__main__':
    run_main()
