import os
import json
import pandas as pd

from labonneboite.importer import util as import_util
from labonneboite.importer import settings as importer_settings
from labonneboite.importer.jobs.common import logger


class NoDataException(Exception):
    pass


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

    create_table_query3 = 'CREATE TABLE IF NOT EXISTS `activity_logs_pse` ( \
                            `dateheure` text,\
                            `idutilisateur_peconnect` text,\
                            `siret` text,\
                            `utm_medium` text,\
                            `utm_source` text,\
                            `utm_campaign` text\
                            ) ENGINE=InnoDB DEFAULT CHARSET=utf8;'

    # If a problem occurs during insertion of idpe_connect rows, just drop rows after the last recorded activity :
    #    DELETE
    #    FROM idpe_connect
    #    WHERE dateheure > '2019-05-28 01:59:40'

    engine = import_util.create_sqlalchemy_engine()
    engine.execute(create_table_query1)
    engine.execute(create_table_query2)
    engine.execute(create_table_query3)
    engine.close()


def parse_activity_logs():
    def format_dateheure(row):
        return row['dateheure'].replace('T', ' ').split('.')[0]

    def get_dateheure(row):
        return row['dateheure'].split()[0]

    data = []

    # FIXME : Later, we'll be able to get datas, directly from PE datalake
    # Now we have a cron task which will copy json activity logs to /srv/lbb/data
    json_logs_folder_path = importer_settings.INPUT_SOURCE_FOLDER
    json_logs_paths = os.listdir(json_logs_folder_path)
    json_logs_paths = [i for i in json_logs_paths if i.startswith('activity')]

    logger.info('.json files found : {}'.format(json_logs_paths))

    file_used = False

    engine = import_util.create_sqlalchemy_engine()

    for json_logs_path in json_logs_paths:
        date = json_logs_path.replace(
            'activity-lbb-', '').replace('.json', '').replace('.', '-')

        date_in_db_query = 'select dateheure\
                        from activity_logs\
                        where date(dateheure) = "{}"\
                        ORDER BY dateheure desc\
                        LIMIT 1'.format(date)

        row = engine.execute(date_in_db_query).fetchone()
        
        logs_in_db = True
        if row is None:
            logs_in_db = False
        else:
            hour_recorded_activity = int(row[0].split()[1].split(':')[0])
            if hour_recorded_activity <= 3: #Complètement arbitraire, mais si les logs les plus récents de la journée sont avant 3h du matin, on estime que les logs n'ont pas été parsés 
                logs_in_db = False

        if not logs_in_db:
            file_used = True
            logger.info('.json file used : {}'.format(json_logs_path))
            with open(json_logs_folder_path+'/'+json_logs_path, 'r') as json_file:
                for line in json_file:
                    data.append(line)

    engine.close()

    if not file_used:
        logger.info("Did not find/need any data to parse")
        raise NoDataException

    activities = {}
    i = 1
    for activity in data:
        activities[str(i)] = json.loads(activity)
        i += 1

    activity_df = pd.DataFrame.from_dict(activities).transpose()

    # FIXME : Change the names of mysql column instead of renaming here
    activity_df.rename(
        columns={'idutilisateur-peconnect': 'idutilisateur_peconnect'}, inplace=True)

    activity_df['dateheure'] = activity_df.apply(
        lambda row: format_dateheure(row), axis=1)

    activity_df['date'] = activity_df.apply(
        lambda row: get_dateheure(row), axis=1)

    logger.info('activity dataframe OK')

    return activity_df


def insert_id_peconnect(activity_df):

    activity_df = activity_df.dropna(
        axis=0, subset=['idutilisateur_peconnect'])

    activity_idpec = activity_df.drop_duplicates(
        subset=['idutilisateur_peconnect', 'date'], keep='first')

    activity_idpec = activity_idpec[[
        'dateheure', 'idutilisateur_peconnect']]

    engine = import_util.create_sqlalchemy_engine()

    nb_lines = activity_idpec.shape[0]
    logger.info('Number of lines to insert into idpec : {}'.format(nb_lines))

    activity_idpec.to_sql(
        con=engine, name='idpe_connect', if_exists='append', index=False, chunksize=10000)

    engine.close()

    logger.info('insert into idpe_connect OK')


def siret(row):
    return row['proprietes']['siret']


def insert_activity_logs(activity_df):
    activity_df = activity_df.dropna(
        axis=0, subset=['idutilisateur_peconnect'])

    clics_of_interest = ['details', 'afficher-details',
                         'telecharger-pdf', 'ajout-favori']

    activity_logs_df = activity_df[activity_df['nom'].isin(clics_of_interest)]

    activity_logs_df['siret'] = activity_logs_df.apply(
        lambda row: siret(row), axis=1)

    cols_of_interest = ["dateheure", "nom", "idutilisateur_peconnect", "siret"]

    activity_logs_df = activity_logs_df[cols_of_interest]

    engine = import_util.create_sqlalchemy_engine()

    nb_lines = activity_logs_df.shape[0]
    logger.info(
        'Number of lines to insert into activity logs : {}'.format(nb_lines))

    activity_logs_df.to_sql(con=engine, name='activity_logs',
                            if_exists='append', index=False, chunksize=10000)

    engine.close()

    logger.info('insert into activity_logs OK')


def insert_activity_logs_pse(activity_df):

    activity_df = activity_df[activity_df['nom'].isin(['details'])]

    activity_df['siret'] = activity_df.apply(
        lambda row: siret(row), axis=1)

    def utm(row, key):
        value = None
        if key in row['proprietes']:
            value = row['proprietes'][key]

        return value

    activity_df['utm_medium'] = activity_df.apply(
        lambda row: utm(row, 'utm_medium'), axis=1)

    activity_df['utm_source'] = activity_df.apply(
        lambda row: utm(row, 'utm_source'), axis=1)

    activity_df['utm_campaign'] = activity_df.apply(
        lambda row: utm(row, 'utm_campaign'), axis=1)

    activity_df = activity_df[activity_df.utm_medium == "mailing"]

    cols_of_interest = ["dateheure", "idutilisateur_peconnect",
                        "siret", "utm_medium", "utm_source", "utm_campaign"]

    activity_df = activity_df[cols_of_interest]

    engine = import_util.create_sqlalchemy_engine()

    nb_lines = activity_df.shape[0]
    logger.info(
        'Number of lines to insert into activity logs PSE : {}'.format(nb_lines))

    activity_df.to_sql(con=engine, name='activity_logs_pse',
                       if_exists='append', index=False, chunksize=10000)

    engine.close()

    logger.info('insert into activity_logs PSE OK')


def run_main():
    sql_queries()
    activity_df = parse_activity_logs()
    insert_activity_logs_pse(activity_df)
    insert_id_peconnect(activity_df)
    insert_activity_logs(activity_df)


if __name__ == '__main__':
    run_main()
