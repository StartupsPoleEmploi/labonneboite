import os
import json
import pandas as pd
from datetime import date

from labonneboite.scripts.impact_retour_emploi.daily_json_activity_parser import ActivityLogParser, siret


class NoDataException(Exception):
    pass


def get_clics_per_siret_main(activity_log_parser, file_path):
    '''
        Main function which will take the list of all json files,
        create a dataframe from it,
        and which, from the dataframe, save data in the 3 tables created above
    '''
    for file_name in activity_log_parser.json_logs_files_names_to_parse:

        # Create dataframe from json file
        print(f'activity dataframe for file {file_name}: start')
        activity_df = activity_log_parser.get_activity_log_dataframe(file_name)
        print(f'activity dataframe for file {file_name}: end')

        # Insert into logs_activity
        print(f'Get clic per siret per day for file {file_name}: start')
        df = get_clics_per_siret(activity_df)
        insert_in_csv(df, file_path)
        print(f'Get clic per siret per day for file for file {file_name}: end')

# PSE school wanted to know how many 'clics' on companies have been made
# We consider a "clic on a company" to be an event in : details, afficher-details, ajout-favory
# So for these 3 categories, we group by siret and date the number of each event
def get_clics_per_siret(activity_df):
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


def insert_in_csv(df, file_path):
    # save file after each chunk of the dpae file used
    file_exists = os.path.isfile(file_path)

    if file_exists:
        with open(file_path, 'a') as f:
            df.to_csv(f, header=False, sep='|')
    else:
        df.to_csv(file_path, encoding='utf-8', sep='|')


def get_filepath(activity_log_parser):
    today = date.today()
    clean_date = today.strftime("%Y-%m-%d")
    file_path = f'{activity_log_parser.json_logs_folder_path}/clics_per_siret_pse-{clean_date}.csv'

    if os.path.isfile(file_path):
        os.remove(file_path)

    return file_path


def run_main():
    activity_log = ActivityLogParser()
    activity_log.get_json_logs_activity(need_all_files=True)
    filepath = get_filepath(activity_log)
    get_clics_per_siret_main(activity_log, filepath)


if __name__ == '__main__':
    run_main()
