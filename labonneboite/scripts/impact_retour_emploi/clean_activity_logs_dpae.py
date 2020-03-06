from datetime import date
import time
import pandas as pd
import os
import math
from labonneboite.importer import util as import_util
from labonneboite.importer import settings as importer_settings
from labonneboite.importer.jobs.common import logger
from labonneboite.scripts.impact_retour_emploi.settings import DEBUG

TABLE_NAME = 'logs_activity_dpae_clean'

#Pandas utils functions
#----------------------
## Functions used for pandas dataframe, which take a row dataframe in param, and will return a specific value based on the row
def get_type_contrat(row):
    if row['dc_typecontrat_id'] == 1:
        return 'CDD'
    elif row['dc_typecontrat_id'] == 2:
        return 'CDI'
    return 'CTT'

def get_nb_mois(row):
    try:
        nb_mois = math.ceil(row['duree_activite_cdd_jours'] // 30)
    except:
        nb_mois = None

    return nb_mois

def get_nbr_jours_act_emb(row):
    de = row['date_embauche'][:10].split('-')
    da = row['date_activite'][:10].split('-')
    f_date = date(int(da[0]), int(da[1]), int(da[2]))
    l_date = date(int(de[0]), int(de[1]), int(de[2]))
    delta = l_date - f_date
    return delta.days

def get_priv_pub(row):
    if row['dc_privepublic'] == 0:
        secteur = 'Public'
    elif row['dc_privepublic'] == 1:
        secteur = 'Prive'

    return secteur

def good_format(row):
    return row['date_embauche'][:-2]

def del_interrogation(row):
    tranche_age = 'entre 26 et 50 ans' if row['tranche_age'] == 'de 26 ans ? 50 ans' else row['tranche_age']
    return tranche_age

def del_cdd_incoherent(row):
    duree = row['duree_activite_cdd_jours']
    status = 'OK'
    if duree is not None: 
        if duree > 1200:
            status = 'KO'
    
    return status

class CleanActivityLogsDPAE:

    def __init__(self):
        self.csv_folder_path = importer_settings.INPUT_SOURCE_FOLDER+'/'
        self.df_dpae_act = pd.read_csv(
            self.csv_folder_path + self.get_most_recent_csv_file(), 
            sep='|', 
            header=0
        )

    def get_most_recent_csv_file(self):
        csv_paths = os.listdir(self.csv_folder_path)
        csv_paths = [i for i in csv_paths if i.startswith('act_dpae-')]
        csv_paths.sort()
        most_recent_csv_file = csv_paths[-1]

        logger.info(f"the DPAE file which will be used is : {most_recent_csv_file}")

        return most_recent_csv_file
    
    def check_existing_act_dpae_table(self):
        engine = import_util.create_sqlalchemy_engine()

        query = f"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '{TABLE_NAME}'"

        existing_sql_table = False
        if engine.execute(query).fetchone()[0] == 1:  # Table existe
            existing_sql_table = True

        engine.close()

        return existing_sql_table

    def get_old_activities_logs_saved(self):
        engine = import_util.create_sqlalchemy_engine()

        query = f"select * from {TABLE_NAME}"
        df_dpae_act_existing = pd.read_sql_query(query, engine)
        df_dpae_act_existing['siret'] = df_dpae_act_existing.siret.astype(str)
        engine.close()

        return df_dpae_act_existing

    def save_activity_logs(self):

        engine = import_util.create_sqlalchemy_engine()
        self.df_dpae_act.to_sql(
            con=engine, 
            name=TABLE_NAME, 
            if_exists='replace', 
            index=False, 
            chunksize=10000
        )
        engine.close()

    def clean_csv_act_dpae_file(self):
        
        logger.info("The .csv file generated to clean has {} rows".format(self.df_dpae_act.shape[0]))

        # rename some columns
        self.df_dpae_act.rename(
            columns={
                'dateheure': 'date_activite',
                'kd_dateembauche': 'date_embauche',
                'nbrjourtravaille': 'duree_activite_cdd_jours',
                'kn_trancheage': 'tranche_age',
                'duree_pec': 'duree_prise_en_charge',
                'dc_commune_id': 'code_postal'
            },
            inplace=True
        )

        #convert to string the siret column
        self.df_dpae_act.siret = self.df_dpae_act.siret.astype(str)
        
        #remove rows where the field premiere embauche is not equal to "Embauche"
        self.df_dpae_act = self.df_dpae_act[self.df_dpae_act.premiere_embauche == 'Embauche']
        nb_rows = self.df_dpae_act.shape[0]
        logger.info(f"The .csv file - rows with not 'premiere embauche' has {nb_rows} rows")

        # remove duplicates when multiple activities for the same dpae
        self.df_dpae_act = self.df_dpae_act.sort_values('date_activite')
        self.df_dpae_act = self.df_dpae_act.drop_duplicates(subset=['idutilisateur-peconnect', 'siret'], keep='first')
        nb_rows = self.df_dpae_act.shape[0]
        logger.info(f"The .csv file - duplicates has {nb_rows} rows")

        #make readable the contract types
        self.df_dpae_act['type_contrat'] = self.df_dpae_act.apply(lambda row: get_type_contrat(row), axis=1)
        
        #we want the number of month a contract will last
        self.df_dpae_act['duree_activite_cdd_mois'] = self.df_dpae_act.apply(lambda row: get_nb_mois(row), axis=1)
        
        #we want to know how long there is between the activity log and the hiring
        self.df_dpae_act['diff_activite_embauche_jrs'] = self.df_dpae_act.apply(lambda row: get_nbr_jours_act_emb(row), axis=1)
        
        #make readable the private/public field
        self.df_dpae_act['dc_privepublic'] = self.df_dpae_act.apply(lambda row: get_priv_pub(row), axis=1)
        
        #make readable the hiring date
        self.df_dpae_act['date_embauche'] = self.df_dpae_act.apply(lambda row: good_format(row), axis=1)
        
        #make readable the age of the employee
        self.df_dpae_act['tranche_age'] = self.df_dpae_act.apply(lambda row: del_interrogation(row), axis=1)
        
        #create a field that will delete wrong functionnaly rows that contain CDD which last longer than 1200 days
        self.df_dpae_act['status_duree'] = self.df_dpae_act.apply(lambda row: del_cdd_incoherent(row), axis=1)
        self.df_dpae_act = self.df_dpae_act[self.df_dpae_act.status_duree == 'OK']
        nb_rows = self.df_dpae_act.shape[0]
        logger.info(f"The .csv file - contrats which last too long to be legal has {nb_rows} rows")

        # We only have activities in august for 31/08/2018 --> ugly charts, we want to start from the 1st september
        self.df_dpae_act = self.df_dpae_act[self.df_dpae_act.date_activite > "2018-08-31"]
        
        #We keep only the interesting columns
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

        self.df_dpae_act = self.df_dpae_act[cols_of_interest]

        #We check if the table which stores the clean data about dpae and activities exist
        existing_sql_table = self.check_existing_act_dpae_table()

        #If it exists, we have to get the whole old datas, to delete rows which are duplicates for a couple idpeconnect/siret
        if existing_sql_table:

            df_dpae_act_existing = self.get_old_activities_logs_saved()

            # In case a problem appear in the script, we save old datas under .csv extension
            # because we will rewrite the whole table after each execution, we have to remove duplicates
            df_dpae_act_existing.to_csv(
                f"{self.csv_folder_path}backup_sql_{TABLE_NAME}", 
                encoding='utf-8', 
                sep='|'
            )

            nb_rows_old = df_dpae_act_existing.shape[0]
            logger.info(f"There were already act/dpae : {nb_rows} rows")

            nb_rows = self.df_dpae_act.shape[0]
            logger.info(f"There are {nb_rows} new rows to concat with the old one")

            #We concatenate all the old rows with the new ones
            self.df_dpae_act = pd.concat([self.df_dpae_act, df_dpae_act_existing])
            nb_rows = self.df_dpae_act.shape[0]
            logger.info(f"Concatenation of both has {nb_rows} rows")

            
            #Remove the duplicates
            self.df_dpae_act = self.df_dpae_act.sort_values('date_activite')
            self.df_dpae_act = self.df_dpae_act.drop_duplicates(subset=['idutilisateur_peconnect', 'siret'], keep='first')
            nb_rows = self.df_dpae_act.shape[0]
            logger.info(f"Concatenation of both minus duplicates has {nb_rows} rows")

        self.save_activity_logs()

def run_main():
    clean_act_log_dpae = CleanActivityLogsDPAE()
    clean_act_log_dpae.clean_csv_act_dpae_file()

if __name__ == '__main__':
    run_main()
