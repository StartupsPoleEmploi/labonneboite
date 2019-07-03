import urllib.parse
import os
import json
import pandas as pd

from labonneboite.importer import util as import_util
from labonneboite.importer import settings as importer_settings

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

con, cur = import_util.create_cursor()
cur.execute(create_table_query1)
cur.execute(create_table_query2)
cur.execute(last_date_query)
row = cur.fetch()
cur.close()
con.close()

data = []

# FIXME : Later, we'll be able to get datas, directly from PE datalake
# Now we have a cron task which will cpy json activity logs to /srv/lbb/data
json_logs_folder_path = importer_settings.INPUT_SOURCE_FOLDER
json_logs_paths = os.listdir(json_logs_folder_path)
json_logs_paths = [i for i in json_logs_paths if i.startswith('activity')]

for json_logs_path in json_logs_paths:
        

with open(json_path+last_json, 'r') as json_file:
    for line in json_file:
        data.append(line)
activities = {}
i = 1
for activity in data:
    activities[str(i)] = json.loads(activity)
    i += 1

activity_df = pd.DataFrame.from_dict(activities).transpose()


def idpe_only(row):
    if row['idutilisateur-peconnect'] is None:
        return 0
    return 1


activity_df['tri_idpec'] = activity_df.apply(
    lambda row: idpe_only(row), axis=1)
activity_df = activity_df[activity_df.tri_idpec != 0]
activity_idpec = activity_df.drop_duplicates(
    subset=['idutilisateur-peconnect'], keep='first')

activity_idpec = activity_idpec[[
    'dateheure', 'idutilisateur-peconnect']]
activity_idpec.to_sql(
    con=engine, name='idpe_connect', if_exists='append', index=False)

cliks_of_interest = ['details', 'afficher-details',
                     'telecharger-pdf', 'ajout-favori']


def tri_names(row):
    if row['nom'] in cliks_of_interest:
        return True
    return False


activity_df['tri_names'] = activity_df.apply(
    lambda row: tri_names(row), axis=1)
activity_logs = activity_df[activity_df.tri_names is True]


def siret(row):
    return row['proprietes']['siret']


activity_logs['siret'] = activity_logs.apply(
    lambda row: siret(row), axis=1)
cols_of_interest = ["dateheure", "nom", "idutilisateur-peconnect", "siret"]
act_logs_good = activity_logs[cols_of_interest]
act_logs_good.to_sql(con=engine, name='activity_logs',
                        if_exists='append', index=False)
