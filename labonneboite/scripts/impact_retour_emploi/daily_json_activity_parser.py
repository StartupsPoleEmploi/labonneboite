import os
import json
import pandas as pd

from labonneboite.importer import util as import_util
from labonneboite.importer import settings as importer_settings
from labonneboite.importer.jobs.common import logger


def create_table_queries():
    '''Init function which will create tables in the database if they don't exist
    '''

    #Create the table that will store into database the idpeconnect
    create_table_query1 = 'CREATE TABLE IF NOT EXISTS `logs_idpe_connect` ( \
                                `idutilisateur_peconnect` text, \
                                `dateheure` text \
                            ) ENGINE=InnoDB DEFAULT CHARSET=utf8;'

    #Create the table that will store into database the activity logs
    create_table_query2 = 'CREATE TABLE IF NOT EXISTS `logs_activity` ( \
                            `dateheure` text,\
                            `nom` text,\
                            `idutilisateur_peconnect` text,\
                            `siret` text,\
                            `utm_medium` text,\
                            `utm_source` text,\
                            `utm_campaign` text\
                            ) ENGINE=InnoDB DEFAULT CHARSET=utf8;'

    #Create the table that will store into database the search queries (too many search queries)
    create_table_query3 = 'CREATE TABLE IF NOT EXISTS `logs_activity_recherche` ( \
                            `date` text,\
                            `idutilisateur_peconnect` text,\
                            `ville` text,\
                            `code_postal` text,\
                            `emploi` text,\
                            `count` int \
                            ) ENGINE=InnoDB DEFAULT CHARSET=utf8;'

    engine = import_util.create_sqlalchemy_engine()
    engine.execute(create_table_query1)
    engine.execute(create_table_query2)
    engine.execute(create_table_query3)
    engine.close()

## Functions used by pandas to create new fields based on other fields, in the dataframe
def siret(row):
    return row['proprietes']['siret']

def format_dateheure(row):
    return row['dateheure'].replace('T', ' ').split('.')[0]

def get_date(row):
    return row['dateheure'].split()[0]

def get_propriete(row, key, key2=None):
    value = None
    if key in row['proprietes']:
        if key2 is not None:
            if key2 in row['proprietes'][key]:
                value = row['proprietes'][key][key2]
        else:
            value = row['proprietes'][key]

    return value

class NoDataException(Exception):
    pass

class ActivityLog:

    def __init__(self):
        self.json_logs_folder_path = importer_settings.INPUT_SOURCE_FOLDER
        self.json_logs_files_names_to_parse = self.get_json_logs_activity()

    def get_json_logs_activity(self):
        '''Function which will return a list with all file names of activity logs that need to be parsed
        '''
        # FIXME : Later, we'll be able to get datas, directly from PE datalake
        # Now we have a cron task which will copy json activity logs to /srv/lbb/data
        
        data = []

        #path of folder which stores all the activityXXX.json
        
        #list of all the json activities files
        json_logs_files_names = [i for i in os.listdir(self.json_logs_folder_path) if i.startswith('activity')]

        #list of all the json activities that need to be parsed (which aren't stored in database)
        json_logs_files_names_to_parse = [file_name for file_name in json_logs_files_names if self.needs_parse_json_activity_log(file_name)]

        if len(json_logs_files_names_to_parse) == 0:
            logger.info("Did not find/need any data to parse")
            raise NoDataException

        logger.info('.json files to parse : {}'.format(json_logs_files_names_to_parse))

        return json_logs_files_names_to_parse

    def needs_parse_json_activity_log(self, json_file_name):
        '''Function which takes one json file name and check if it needs to be parsed and saved in database
        '''

        #json_file_name is format : activity-lbb-2019.09.13.json
        date = json_file_name.replace(
            'activity-lbb-', '').replace('.json', '').replace('.', '-')

        date_in_db_query = 'select dateheure\
                        from logs_activity\
                        where date(dateheure) = "{}"\
                        ORDER BY dateheure desc\
                        LIMIT 1'.format(date)

        engine = import_util.create_sqlalchemy_engine()         
        row = engine.execute(date_in_db_query).fetchone()
        engine.close()
        
        file_needs_to_be_parsed = False
        if row is None:
            file_needs_to_be_parsed = True
        else:
            #we check the last hour of the activity logs in database
            hour_recorded_activity = int(row[0].split()[1].split(':')[0])
            #if the most recent hour in the database for the logs is before 3am, the file needs to be parsed
            if hour_recorded_activity <= 3:
                file_needs_to_be_parsed = True

        return file_needs_to_be_parsed

    def save_logs_activity(self):
        '''
           Main function which will take the list of all json files,
           create a dataframe from it,
           and which, from the dataframe, save data in the 3 tables created above
        '''
        for file_name in self.json_logs_files_names_to_parse:

            #Create dataframe from json file
            logger.info(f'activity dataframe for file {file_name}: start')
            activity_df = self.get_activity_log_dataframe(file_name)
            logger.info(f'activity dataframe for file {file_name}: end')
            
            #Insert into idpeconnect
            logger.info(f'Insert into idepeconnect for file {file_name}: start')
            #self.insert_id_peconnect(activity_df)
            logger.info(f'Insert into idepeconnect for file {file_name}: end')
            
            #Insert into logs_activity
            logger.info(f'Insert into logs_activity for file {file_name}: start')
            self.insert_logs_activity(activity_df)
            logger.info(f'Insert into logs_activity for file {file_name}: end')

            #Insert into logs_activity_recherche
            logger.info(f'Insert into logs_activity for file {file_name}: start')
            self.insert_logs_activity_recherche(activity_df)
            logger.info(f'Insert into logs_activity for file {file_name}: end')

    def get_activity_log_dataframe(self, json_file_name):
        '''Function which will transform a json file, into a pandas dataframe
        '''
        data = []

        # Chargement des logs json dans une liste
        with open(f'{self.json_logs_folder_path}/{json_file_name}', 'r') as json_file:
            for line in json_file:
                data.append(line)
        
        activities_logs_lines = {}
        i = 1
        for activity_log_line in data:
            activities_logs_lines[str(i)] = json.loads(activity_log_line)
            i += 1
        
        activity_df = pd.DataFrame.from_dict(activities_logs_lines).transpose()
        activity_df['dateheure'] = activity_df.apply(lambda row: format_dateheure(row), axis=1)
        activity_df['date'] = activity_df.apply(lambda row: get_date(row), axis=1)
        activity_df.rename(columns={'idutilisateur-peconnect': 'idutilisateur_peconnect'}, inplace=True)

        return activity_df


    def insert_id_peconnect(self, activity_df):
        
        activity_df = activity_df.dropna(axis=0, subset=['idutilisateur_peconnect'])
        activity_idpec = activity_df.drop_duplicates(subset=['idutilisateur_peconnect', 'date'], keep='first')
        activity_idpec = activity_idpec[['dateheure', 'idutilisateur_peconnect']]

        nb_lines = activity_idpec.shape[0]
        logger.info(f'Number of lines to insert into idpec : {nb_lines}')

        engine = import_util.create_sqlalchemy_engine()
        activity_idpec.to_sql(
            con=engine, 
            name='logs_idpe_connect', 
            if_exists='append', 
            index=False, 
            chunksize=10000
        )
        engine.close()

    def insert_logs_activity(self, activity_df):
        
        '''
        details = consulter une page entreprise 
        afficher-details = déplier fiche entreprise 
        premiere étape JP --> Récup datas ailleurs

        '''

        clics_of_interest = ['details', 'afficher-details', 'ajout-favori']

        logs_activity_df = activity_df[activity_df['nom'].isin(clics_of_interest)]
        
        import ipdb;ipdb.set_trace()
        logs_activity_df['siret'] = logs_activity_df.apply(lambda row: siret(row), axis=1)
        logs_activity_df['utm_medium'] = logs_activity_df.apply(lambda row: get_propriete(row, 'utm_medium'), axis=1)
        logs_activity_df['utm_source'] = logs_activity_df.apply(lambda row: get_propriete(row, 'utm_source'), axis=1)
        logs_activity_df['utm_campaign'] = logs_activity_df.apply(lambda row: get_propriete(row, 'utm_campaign'), axis=1)
        
        # We want to keep only the activity logs with IDPeconnect OR the ones that have the values we want in utm_medium
        # If we keep everything, there will be way too many lines in the database
        utm_medium_to_keep = ['mailing']
        logs_activity_df = logs_activity_df[(logs_activity_df.idutilisateur_peconnect.notnull()) | (logs_activity_df.utm_medium.isin(utm_medium_to_keep))]

        cols_of_interest = [
            "dateheure", 
            "nom", 
            "idutilisateur_peconnect", 
            "siret",
            "utm_medium",
            "utm_source",
            "utm_campaign",
        ]

        logs_activity_df = logs_activity_df[cols_of_interest]

        nb_lines = logs_activity_df.shape[0]
        logger.info(f'Number of lines to insert into logs_activity : {nb_lines}')

        engine = import_util.create_sqlalchemy_engine()
        
        logs_activity_df.to_sql(
            con=engine, 
            name='logs_activity',
            if_exists='append', 
            index=False, 
            chunksize=10000
        )

        engine.close()

    def insert_logs_activity_recherche(self, activity_df):

        logs_activity_df = activity_df[activity_df['nom'] == 'recherche']

        logs_activity_df['ville'] = logs_activity_df.apply(lambda row: get_propriete(row, 'localisation','ville'), axis=1)
        logs_activity_df['code_postal'] = logs_activity_df.apply(lambda row: get_propriete(row, 'localisation','codepostal'), axis=1)
        logs_activity_df['emploi'] = logs_activity_df.apply(lambda row: get_propriete(row, 'emploi'), axis=1)
        
        #TODO : Find a way to concatenate logs, because too many
        import ipdb;ipdb.set_trace()

        cols_of_interest = [
            "dateheure", 
            "idutilisateur_peconnect", 
            "ville",
            "code_postal",
            "emploi",
        ]

        logs_activity_df = logs_activity_df[cols_of_interest]

        nb_lines = logs_activity_df.shape[0]
        logger.info(f'Number of lines to insert into logs_activity_recherche : {nb_lines}')


        engine = import_util.create_sqlalchemy_engine()
        
        logs_activity_df.to_sql(
            con=engine, 
            name='logs_activity_recherche',
            if_exists='append', 
            index=False, 
            chunksize=10000
        )

        engine.close()

def run_main():
    create_table_queries()
    activity_log = ActivityLog()
    activity_log.save_logs_activity()

if __name__ == '__main__':
    run_main()
