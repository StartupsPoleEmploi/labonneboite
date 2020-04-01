import os
import json
import pandas as pd

from labonneboite.importer import util as import_util
from labonneboite.importer import settings as importer_settings
from labonneboite.importer.jobs.common import logger

# Pandas utils functions
# ----------------------
# Functions used by pandas to create new fields based on other fields, in the dataframe


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

# Specific function to clean the emploi field in the logs activity recherche dataframe


def clean_emploi(row):
    def hasNumbers(inputString):
        return any(char.isdigit() for char in inputString)

    emploi = row['emploi']
    try:
        # example : "soins-d-hygiene-de-confort-du-patient99999' union select unhex(hex(version
        if ' ' in emploi:
            emploi = emploi.split(' ')[0]
        #example : securite-et-surveillance-privees/static/images/logo-lbb.svg
        if '/' in emploi:
            emploi = emploi.split('/')[0]
        # example : tel:0590482468
        if emploi.startswith('tel:'):
            emploi = ''
        # example :vente-en-habillement-et-accessoires-de-la-personne?to=82&from=81&sa=U&ved=2ahUKEwiLqI6mi43mAhVD6aQKHVxyAP4QFjAOegQIRxAB&usg=AOvVaw1hYvyYvxE3CPZnYly-CKci"
        if '?' in emploi:
            emploi = emploi.split('?')[0]
        # example : vente-en-habillement-et-accessoires-de-la-personne%Fto=&from=&d=
        if '%' in emploi:
            emploi = emploi.split('%')[0]
        # example : 'conduite-de-transport-en-commun-sur-route&sa=U&ved=ahUKEwjhlZvHv_kAhUKqlkKHRJyCNQFjAWegQIDBAB&usg=AOvVawWAKqGLFCkVOTiWqLfJXF"'
        if '&' in emploi:
            emploi = emploi.split('&')[0]
        # example : soins-d-hygiene-de-confort-du-patient99999
        if hasNumbers(emploi):
            emploi = ''.join([i for i in emploi if not i.isdigit()])
        # example : soins-d-hygiene-de-confort-du-patient\'"
        if '\'' in emploi:
            emploi = emploi.split('\'')[0]
        #example : www.orecrute.fr
        if emploi.startswith('www'):
            emploi = ''
        #example : '...'
        if emploi.endswith('..'):
            emploi = ''
        #example : '�'
        if len(emploi) == 1:
            emploi = ''
        # example '||UTL_INADDR.get_host_address(',
        if emploi.startswith('||'):
            emploi = ''
        # example {{__field_friYEMKBPT}}']
        if emploi.startswith('{'):
            emploi = ''
        # exampleS :
        # '"><javascript:alert(String.fromCharCode(,,));">', '"><script',
        # '(SELECT', '-"', '-)', '-);select', '..', ';copy', '@@AMfqT',
        #'@@Ddywc', '@@EnFdC', '@@JOQK', '@@LAdgd', '@@MlSoU', '@@QKchw',
        #'@@Rido', '@@WiWWC', '@@XFdfe', '@@ZIdkt', '@@bLTT', '@@gZP',
        #'@@lMTz', '@@nc', '@@ozw', '@@uusYI', '@@zRlWc', '@@ziuX',
        if ('<' or '>') in emploi:
            emploi = ''
        if emploi.startswith('>'):
            emploi = ''
        if ';' in emploi:
            emploi = ''
        if emploi.startswith('('):
            emploi = ''
        if emploi.startswith('-'):
            emploi = ''
        if emploi.startswith('('):
            emploi = ''
        if emploi.startswith('@'):
            emploi = ''
        if '\"' in emploi:
            emploi.replace('\"', '')
        if '.' in emploi:
            emploi.replace('.', '')
        if 'test' in emploi:
            emploi = ''

    except TypeError:  # If emploi is NoneType
        emploi = ''

    return emploi


class NoDataException(Exception):
    pass


class ActivityLogParser:

    def __init__(self):
        self.json_logs_folder_path = importer_settings.INPUT_SOURCE_FOLDER

    def get_json_logs_activity(self, need_all_files = False):
        '''Function which will return a list with all file names of activity logs that need to be parsed
        '''
        # Now we have a cron task which will copy json activity logs to /srv/lbb/data

        # list of all the json activities files
        json_logs_files_names = [i for i in os.listdir(self.json_logs_folder_path) if i.startswith('activity')]

        # list of all the json activities that need to be parsed (which aren't stored in database)
        if need_all_files is False:
            json_logs_files_names_to_parse = [
                file_name for file_name in json_logs_files_names if self.needs_parse_json_activity_log(file_name)]
        else:
            json_logs_files_names_to_parse = json_logs_files_names
            
        if not json_logs_files_names_to_parse: #if empty list
            logger.info("Did not find/need any data to parse")
            raise NoDataException

        logger.info(f'.json files to parse : {json_logs_files_names_to_parse}')

        self.json_logs_files_names_to_parse = json_logs_files_names_to_parse

    def needs_parse_json_activity_log(self, json_file_name):
        '''Function which takes one json file name and check if it needs to be parsed and saved in database
        '''

        # json_file_name is format : activity-lbb-2019.09.13.json
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
            # we check the last hour of the activity logs in database
            hour_recorded_activity = row[0].hour
            # if the most recent hour in the database for the logs is before 3am, the file needs to be parsed
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

            # Create dataframe from json file
            logger.info(f'activity dataframe for file {file_name}: start')
            activity_df = self.get_activity_log_dataframe(file_name)
            logger.info(f'activity dataframe for file {file_name}: end')

            # Insert into idpeconnect
            logger.info(f'Insert into idepeconnect for file {file_name}: start')
            df = self.insert_id_peconnect(activity_df)
            self.insert_in_database(df, 'logs_idpe_connect')
            logger.info(f'Insert into idepeconnect for file {file_name}: end')

            # Insert into logs_activity
            logger.info(f'Insert into logs_activity for file {file_name}: start')
            df = self.insert_logs_activity(activity_df)
            self.insert_in_database(df, 'logs_activity')
            logger.info(f'Insert into logs_activity for file {file_name}: end')

            # Insert into logs_activity_recherche
            logger.info(f'Insert into logs_activity_recherche for file {file_name}: start')
            df = self.insert_logs_activity_recherche(activity_df)
            self.insert_in_database(df, 'logs_activity_recherche')

            logger.info(f'Insert into logs_activity_recherche for file {file_name}: end')

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

        return activity_idpec

    def insert_logs_activity(self, activity_df):
        '''
        details = consulter une page entreprise
        afficher-details = déplier fiche entreprise
        '''

        clics_of_interest = ['details', 'afficher-details', 'ajout-favori']

        logs_activity_df = activity_df[activity_df['nom'].isin(clics_of_interest)]

        logs_activity_df['siret'] = logs_activity_df.apply(lambda row: siret(row), axis=1)
        logs_activity_df['utm_medium'] = logs_activity_df.apply(lambda row: get_propriete(row, 'utm_medium'), axis=1)
        logs_activity_df['utm_source'] = logs_activity_df.apply(lambda row: get_propriete(row, 'utm_source'), axis=1)
        logs_activity_df['utm_campaign'] = logs_activity_df.apply(lambda row: get_propriete(row, 'utm_campaign'), axis=1)

        # We want to keep only the activity logs with IDPeconnect OR the ones that have the values we want in utm_medium
        # If we keep everything, there will be way too many lines in the database
        utm_medium_to_keep = ['mailing']
        logs_activity_df = logs_activity_df[
            (logs_activity_df.idutilisateur_peconnect.notnull()) |
            (logs_activity_df.utm_medium.isin(utm_medium_to_keep))
        ]

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

        return logs_activity_df

    def insert_logs_activity_recherche(self, activity_df):

        logs_activity_df = activity_df[activity_df['nom'] == 'recherche']

        logs_activity_df['ville'] = logs_activity_df.apply(lambda row: get_propriete(row, 'localisation', 'ville'), axis=1)
        logs_activity_df['code_postal'] = logs_activity_df.apply(
            lambda row: get_propriete(row, 'localisation', 'codepostal'), axis=1)
        logs_activity_df['emploi'] = logs_activity_df.apply(lambda row: get_propriete(row, 'emploi'), axis=1)
        logs_activity_df['emploi'] = logs_activity_df.apply(lambda row: clean_emploi(row), axis=1)

        # TODO : Find a way to concatenate logs, because too many
        logs_activity_df = logs_activity_df[(logs_activity_df.source == 'site')]

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

        return logs_activity_df

    def insert_in_database(self, dataframe, table_name):
        engine = import_util.create_sqlalchemy_engine()

        dataframe.to_sql(
            con=engine,
            name=table_name,
            if_exists='append',
            index=False,
            chunksize=10000
        )

        engine.close()


def run_main():
    activity_log = ActivityLogParser()
    activity_log.get_json_logs_activity()
    activity_log.save_logs_activity()


if __name__ == '__main__':
    run_main()
