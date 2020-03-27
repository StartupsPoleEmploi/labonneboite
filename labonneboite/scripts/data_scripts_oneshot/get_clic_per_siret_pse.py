import os
import json
import pandas as pd

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

class NoDataException(Exception):
    pass


class ActivityLogParser:

    def __init__(self):
        self.json_logs_folder_path = '/srv/lbb/data'
        #self.json_logs_folder_path = '../labonneboite/labonneboite/importer/data'

    def get_json_logs_activity(self):
        '''Function which will return a list with all file names of activity logs that need to be parsed
        '''
        # Now we have a cron task which will copy json activity logs to /srv/lbb/data

        # list of all the json activities files
        json_logs_files_names_to_parse = [i for i in os.listdir(self.json_logs_folder_path) if (not i.startswith('activity-lbb-2018') and i.startswith('activity') )]

        print(json_logs_files_names_to_parse)
        self.json_logs_files_names_to_parse = json_logs_files_names_to_parse

    def save_logs_activity(self):
        '''
           Main function which will take the list of all json files,
           create a dataframe from it,
           and which, from the dataframe, save data in the 3 tables created above
        '''
        for file_name in self.json_logs_files_names_to_parse:

            # Create dataframe from json file
            print(f'activity dataframe for file {file_name}: start')
            activity_df = self.get_activity_log_dataframe(file_name)
            print(f'activity dataframe for file {file_name}: end')

            # Insert into logs_activity
            print(f'Insert into logs_activity for file {file_name}: start')
            df = self.insert_logs_activity(activity_df)
            self.insert_in_csv(df)
            print(f'Insert into logs_activity for file {file_name}: end')

            print(f'Insert into logs_activity_recherche for file {file_name}: end')

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

    def insert_logs_activity(self, activity_df):
        '''
        details = consulter une page entreprise
        afficher-details = déplier fiche entreprise
        '''

        clics_of_interest = ['details', 'afficher-details', 'ajout-favori']

        df = activity_df[activity_df['nom'].isin(clics_of_interest)]

        df['siret'] = df.apply(lambda row: siret(row), axis=1)

        df = df.groupby(['siret', 'date'])['nom'].apply(lambda x: list(x)).reset_index()
        
        df['nb-clics-afficher-details'] = df['nom'].apply(lambda x: len([_ for _ in x if _ == 'afficher-details']))
        df['nb-clics-details'] = df['nom'].apply(lambda x: len([_ for _ in x if _ == 'details']))
        df['nb-clics-ajout-favori'] = df['nom'].apply(lambda x: len([_ for _ in x if _ == 'ajout-favori']))

        cols_of_interest = [
            "date",
            "siret",
            "nb-clics-details",
            "nb-clics-afficher-details",
            "nb-clics-ajout-favori"
        ]

        df = df[cols_of_interest]

        nb_lines = df.shape[0]
        print(f'Number of lines to insert into logs_activity : {nb_lines}')

        return df

    def insert_in_csv(self, df):
        # save file after each chunk of the dpae file used
        csv = f'{self.json_logs_folder_path}/clics_per_siret_pse.csv'
        file_exists = os.path.isfile(csv)

        if file_exists:
            with open(csv, 'a') as f:
                df.to_csv(f, header=False, sep='|')
        else:
            df.to_csv(csv, encoding='utf-8', sep='|')

def run_main():
    activity_log = ActivityLogParser()
    activity_log.get_json_logs_activity()
    activity_log.save_logs_activity()


if __name__ == '__main__':
    run_main()
