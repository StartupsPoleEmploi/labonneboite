# -*- coding: utf-8 -*-

import os
import time
import datetime as datetime
import pandas as pd

from labonneboite.importer import util as import_util
from labonneboite.importer import settings as importer_settings
from labonneboite.importer.jobs.common import logger
from labonneboite.scripts.impact_retour_emploi.settings import DEBUG
from labonneboite.importer.models.computing import LogsActivityDPAEClean
from labonneboite.common.env import get_current_env, ENV_DEVELOPMENT

# Pandas utils functions
# ----------------------
# function used to create a new column from dateheure column in dpae


def get_date(row):
    return row['kd_dateembauche'][:10]


class JoinActivityLogsDPAE:

    def __init__(self):
        self.dpae_folder_path = importer_settings.INPUT_SOURCE_FOLDER+'/'

    def set_df_activity(self):
        self.df_activity = self.get_activity_logs()

    def get_activity_logs(self):
        engine = import_util.create_sqlalchemy_engine()

        query = "select * from logs_activity"
        if DEBUG:
            query += " ORDER BY RAND() LIMIT 10000"
        df_activity = pd.read_sql_query(query, engine)

        engine.close()

        # TODO : Define how long we should use logs
        # https://valodata.slack.com/archives/C0QR8RYL8/p1562319224015200

        # TODO : Uncomment these lines after the first initialization of the project
        # one_year_date = datetime.date.today() - datetime.timedelta(365)
        # df_activity['dateheure'] = pd.to_datetime(df_activity['dateheure'])
        # df_activity = df_activity[df_activity.dateheure > one_year_date]

        logger.info('Activities logs are loaded')

        return df_activity.astype(str)

    def set_most_recent_dpae_file(self):
        self.most_recent_dpae_file = self.get_most_recent_dpae_file()
        # FIXME : Remove this line to pass a specific dpae file for initialisation, we'll have to parse older DPAE files
        # self.most_recent_dpae_file = "lbb_xdpdpae_delta_201908102200.bz2"

    def get_most_recent_dpae_file(self):
        dpae_paths = os.listdir(self.dpae_folder_path)
        # IMPORTANT : Need to copy the DPAE file from /mnt/datalakepe/ to /srv/lbb/data
        # It is certainly ok, because of the importer which also needs this file
        dpae_paths = [i for i in dpae_paths if i.startswith('lbb_xdpdpae_delta')]

        dpae_paths.sort()
        most_recent_dpae_file = dpae_paths[-1]
        if get_current_env() == ENV_DEVELOPMENT:
            most_recent_dpae_file = 'lbb_xdpdpae_delta_201511102200.csv'

        logger.info(f"the DPAE file which will be used is : {most_recent_dpae_file}")

        return most_recent_dpae_file

    def set_last_recorded_hiring_date(self):
        self.date_last_recorded_hiring = self.get_last_recorded_hiring_date()

    def get_last_recorded_hiring_date(self):

        # We want to check if there are already data  in the final table
        table_name_act_dpae = LogsActivityDPAEClean.__tablename__
        query = f"SELECT COUNT(*) FROM {table_name_act_dpae}"
        engine = import_util.create_sqlalchemy_engine()

        # If data in table
        if engine.execute(query).fetchone()[0] > 0:
            query = f"select date_embauche from {table_name_act_dpae} order by date_embauche DESC LIMIT 1"
            row = engine.execute(query).fetchone()
            date_last_recorded_hiring = row[0].split()[0]
        # Else no data
        else:
            # We set the date to the first activity log that has ever been created on LBB
            date_last_recorded_hiring = "2018-08-31"

        engine.close()
        logger.info(f"the most recent date found is {date_last_recorded_hiring}")

        return date_last_recorded_hiring

    def get_compression_to_use_by_pandas_according_to_file(self):
        dpae_file_extension = self.most_recent_dpae_file.split('.')[-1]
        if dpae_file_extension == 'csv':
            compression = 'infer'
        else:
            compression = 'bz2'

        return compression

    def get_path_to_saved_csv(self):
        timestr = time.strftime("%Y-%m-%d")
        path_to_csv = f"{self.dpae_folder_path}act_dpae-{timestr}.csv"

        return path_to_csv

    def save_csv_file(self, df_dpae_act, iteration):
        # save file after each chunk of the dpae file used
        file_exists = os.path.isfile(self.path_to_csv)

        # We want to rewrite the CSV file after each new execution of Join activity Logs DPAE extraction
        if iteration == 0:  # First iteration
            if file_exists:
                os.remove(self.path_to_csv)
            df_dpae_act.to_csv(self.path_to_csv, encoding='utf-8', sep='|')
        else:
            with open(self.path_to_csv, 'a') as f:
                df_dpae_act.to_csv(f, header=False, sep='|')

    def join_dpae_activity_logs(self):

        # We use the datas in csv using smaller chunks
        if DEBUG:
            chunksize = 10 ** 2
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

        total_dpae_rows_used = 0

        self.path_to_csv = self.get_path_to_saved_csv()

        for df_dpae in pd.read_csv(self.dpae_folder_path + self.most_recent_dpae_file,
                                   header=None,
                                   compression=self.get_compression_to_use_by_pandas_according_to_file(),
                                   names=column_names,
                                   sep='|',
                                   index_col=False,
                                   chunksize=chunksize):

            nb_rows = df_dpae.shape[0]
            logger.info(f"Sample of DPAE has : {nb_rows} rows")

            # We keep rows in the DPAE file that has a date > to the date_last_recorded_hiring
            # The dpae used must be after the last recorded emabuche date
            df_dpae['kd_dateembauche_bis'] = df_dpae.apply(lambda row: get_date(row), axis=1)
            df_dpae = df_dpae[df_dpae.kd_dateembauche_bis > self.date_last_recorded_hiring]
            nb_rows = df_dpae.shape[0]
            logger.info(f"Sample of DPAE minus old dates has : {nb_rows} rows")

            # convert df dpae columns to 'object'
            df_dpae = df_dpae.astype(str)

            # We join the dpae and activity logs dataframe
            df_dpae_act = pd.merge(
                df_dpae,
                self.df_activity,
                how='left',
                left_on=['dc_ididentiteexterne', 'kc_siret'],
                right_on=['idutilisateur_peconnect', 'siret']
            )

            nb_rows = df_dpae_act.shape[0]
            logger.info(f"Sample of merged activity/DPAE has : {nb_rows} rows")

            # filter on the fact that dateheure activity must be inferior to kd_dateembauche
            df_dpae_act = df_dpae_act[df_dpae_act.kd_dateembauche_bis > df_dpae_act.dateheure]
            df_dpae_act = df_dpae_act.drop(['kd_dateembauche_bis'], axis=1)
            nb_rows = df_dpae_act.shape[0]
            logger.info(f"Sample of merged activity/DPAE with the good dates has : {nb_rows} rows")

            df_dpae_act = df_dpae_act.astype(str)

            # We save the lines of the join we want to keep
            self.save_csv_file(df_dpae_act, i)

            nb_rows = df_dpae_act.shape[0]
            logger.info(f" ==> Nb rows we keep in this sample : {nb_rows} rows")

            total_dpae_rows_used += df_dpae_act.shape[0]
            logger.info(f" ==> Nb total rows that have been kept : {total_dpae_rows_used} rows")

            nb_total_rows_dpae_used = (i+1) * chunksize
            logger.info(f" ==> Nb total rows of DPAE that have been used : {nb_total_rows_dpae_used} rows")
            logger.info("\n-------------------------")

            i += 1

        return self.path_to_csv, df_dpae_act


def run_main():
    join_act_log = JoinActivityLogsDPAE()

    join_act_log.set_most_recent_dpae_file()
    join_act_log.set_df_activity()
    join_act_log.set_last_recorded_hiring_date()

    join_act_log.join_dpae_activity_logs()


if __name__ == '__main__':
    run_main()
