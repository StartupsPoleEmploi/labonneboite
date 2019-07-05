import urllib.parse
import os
import json
import pandas as pd

from labonneboite.importer import util as import_util
from labonneboite.importer import settings as importer_settings

def sql_queries():
    create_table_query1 = 'CREATE TABLE IF NOT EXISTS `idpe_connect` ( \
                                `idutilisateur_peconnect` text, \
                                `dateheure` text \
                            ) ENGINE=InnoDB DEFAULT CHARSET=utf8;'

    create_table_query2 = 'CREATE TABLE IF NOT EXISTS `activity_logs` ( \
                            `dateheure` text,\
                            `nom` text,\
                            `idutilisateur_peconnect` text,\
                            `siret` text\
                            ) ENGINE=InnoDB DEFAULT CHARSET=utf8;'

    last_date_query = 'SELECT dateheure \
                    FROM idpe_connect \
                    ORDER BY dateheure DESC \
                    LIMIT 1'
    
    # If a problem occurs during insertion of idpe_connect rows, just drop rows after the last recorded activity : 
    #    DELETE 
    #    FROM idpe_connect
    #    WHERE dateheure > '2019-05-28 01:59:40'

    engine = import_util.create_sqlalchemy_engine()
    engine.execute(create_table_query1)
    engine.execute(create_table_query2)
    row = engine.execute(last_date_query).fetchone()
    date_last_recorded_activity = row[0].split()[0]
    print('The last recorded activity in database is on : {}'.format(date_last_recorded_activity))
    engine.close()
    return date_last_recorded_activity

def parse_activity_logs(date_last_recorded_activity):
    def format_dateheure(row):
        return row['dateheure'].replace('T',' ').split('.')[0]

    def get_dateheure(row):
        return row['dateheure'].split()[0]

    data = []

    # FIXME : Later, we'll be able to get datas, directly from PE datalake
    # Now we have a cron task which will copy json activity logs to /srv/lbb/data
    json_logs_folder_path = importer_settings.INPUT_SOURCE_FOLDER
    json_logs_paths = os.listdir(json_logs_folder_path)
    json_logs_paths = [i for i in json_logs_paths if i.startswith('activity')]

    for json_logs_path in json_logs_paths:
        date = json_logs_path.replace('activity-lbb-','').replace('.json','').replace('.','-')
        if date >= date_last_recorded_activity:
            with open(json_logs_folder_path+'/'+json_logs_path, 'r') as json_file:
                for line in json_file:
                    data.append(line)

    activities = {}
    i = 1
    for activity in data:
        activities[str(i)] = json.loads(activity)
        i += 1
    
    activity_df = pd.DataFrame.from_dict(activities).transpose()

    #FIXME : Change the names of mysql column instead of renaming here
    activity_df.rename(columns = {'idutilisateur-peconnect':'idutilisateur_peconnect'}, inplace = True)

    activity_df = activity_df.dropna(axis=0, subset=['idutilisateur_peconnect'])

    activity_df['dateheure'] = activity_df.apply(
        lambda row: format_dateheure(row), axis=1)

    activity_df['date'] = activity_df.apply(
        lambda row: get_dateheure(row), axis=1)

    return activity_df

def insert_id_peconnect(activity_df):

    activity_idpec = activity_df.drop_duplicates(
        subset=['idutilisateur_peconnect','date'], keep='first')

    activity_idpec = activity_idpec[[
        'dateheure', 'idutilisateur_peconnect']]

    engine = import_util.create_sqlalchemy_engine()

    activity_idpec.to_sql(
        con=engine, name='idpe_connect', if_exists='append', index=False)

    engine.close()

def insert_activity_logs(activity_df):

    def siret(row):
        return row['proprietes']['siret']

    clics_of_interest = ['details', 'afficher-details',
                        'telecharger-pdf', 'ajout-favori']

    activity_logs_df = activity_df[activity_df['nom'].isin(clics_of_interest)]

    activity_logs_df['siret'] = activity_logs_df.apply(
        lambda row: siret(row), axis=1)

    cols_of_interest = ["dateheure", "nom", "idutilisateur_peconnect", "siret"]

    activity_logs_df = activity_logs_df[cols_of_interest]

    engine = import_util.create_sqlalchemy_engine()

    activity_logs_df.to_sql(con=engine, name='activity_logs',
                        if_exists='append', index=False)

    engine.close()

def main():
    date_last_recorded_activity = sql_queries()
    activity_df = parse_activity_logs(date_last_recorded_activity)
    insert_id_peconnect(activity_df)
    insert_activity_logs(activity_df)

if __name__ == '__main__':
    main()