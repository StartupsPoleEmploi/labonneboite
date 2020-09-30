from labonneboite.importer import util as import_util
from labonneboite.importer import settings
from labonneboite.importer.models.computing import PerfImporterCycleInfos
from labonneboite.common.database import db_session

import os 
import gzip
import logging
from datetime import datetime, timedelta
from dateutil.relativedelta import *

import pandas as pd

logger = logging.getLogger(__name__)

def get_date_from_file_name(file_name):
    date_splitted = file_name.split("backup")[1].split(".sql.gz")[0].split('_')
    # date_splitted looks like : ['', '2020', '08', '25', '1636']
    date_str = '-'.join(date_splitted[1:5])
    # date_str looks like : '2020-08-25-1636'
    date_time_object = datetime. strptime(date_str, '%Y-%m-%d-%H%M')
    return date_time_object

def get_available_files_list():
    logger.info("\nStart : Get all the backup .gz files")
    backup_files_list = import_util.get_backup_files_list(
        settings.BACKUP_OUTPUT_FOLDER, 
        "export_etablissement"
    )
    file_list_not_parsed_yet = []
    for file in backup_files_list:
        file_name = os.path.basename(file)
        logger.info(f"file to check : {file_name}")
        if PerfImporterCycleInfos.query.filter(PerfImporterCycleInfos.file_name == file_name).count() == 0:
            file_list_not_parsed_yet.append(file)
            logger.info(f"file {file_name} not parsed yet")
        else:
            logger.info(f"file {file_name} already parsed")

    return file_list_not_parsed_yet

headers_name= [
    "siret",
    "raisonsociale",
    "enseigne",
    "codenaf",
    "trancheeffectif",
    "numerorue",
    "libellerue",
    "codepostal",
    "tel",
    "email",
    "website",
    "flag_alternance",
    "flag_junior",
    "flag_senior",
    "flag_handicap",
    "has_multi_geolocations",
    "codecommune",
    "coordinates_x",
    "coordinates_y",
    "departement",
    "score",
    "email_alternance",
    "score_alternance",
    "social_network",
    "phone_alternance",
    "website_alternance",
    "contact_mode",
    "flag_poe_afpr",
    "flag_pmsmp"
]

headers_we_want_to_keep = [
    "siret",
    "raisonsociale",
    "enseigne",
    "codenaf",
    "codepostal",
    "codecommune",
    "departement",
    "score",
    "score_alternance",
]

def clean_etab_data_from_output_importer(data):
    """
    data = list of 28 items
    """
    new_data = []
    for header in headers_we_want_to_keep:
        index_to_keep = headers_name.index(header)
        clean_data = data[index_to_keep].replace('\'','').replace('(','').replace(')','').strip()
        if 'score' in header:
            clean_data = int(clean_data)
        new_data.append(clean_data)

    return new_data

def parse_backup_file_importer_output(file):
    #FIXME : Very ugly way to retrieve old data from importer
    file_name = os.path.basename(file)
    logger.info(f"\nStart : Parse all data in file {file_name}")
    f = gzip.open(file, 'rt', encoding='utf8')
    file_content = f.read()
    f.close()
    values_to_insert = str(file_content).split("INSERT INTO `etablissements_new` VALUES")[1].split(';')[0]
    # values_to_insert is a string which looks like :
    #" ('03880702000011','MUTUALITE FRANCAISE NORMANDE SSAM','EHPAD - R\\xc3\\xa9sidence les coquelicots','8710A','03','2','RUE DE LA TETE NOIRE','14700','','','',0,0,0,0,0,'14258',-0.186361,48.8906,'14',0,'',5,'','','','',1,1),('51146379600017','L.B.C ASSOCIES','','6622Z','03','30','RUE AUGUSTE FRESNEL','69800','0123456789','','http://www.lbcassocies.fr',0,0,0,0,0,'69290',4.96598,45.7181,'69',0,'',25,'','','','',1,0)"
    values_to_insert = values_to_insert.split(',')
    etab_list = []
    LENGTH_LINE_TO_INSERT = 29
    start_index = 0
    end_index = start_index + LENGTH_LINE_TO_INSERT

    while end_index <= len(values_to_insert):
        etab_list.append(clean_etab_data_from_output_importer(values_to_insert[start_index:end_index]))
        start_index = end_index
        end_index = start_index + LENGTH_LINE_TO_INSERT

    logger.info(f"End : Parse all data in file {file_name}")
    logger.info(f"Number of offices in the file {len(etab_list)}")

    return etab_list

def insert_into_importer_cycle_infos(file, file_name):
    logger.info(f"\n Start : Insert data into importer_cycle_infos from file {file_name}")

    #Insert into importer cycle infos

    #TODO : Check that the prediction start date and end date match these ones
    execution_date = get_date_from_file_name(file_name)
    prediction_start_date = execution_date+relativedelta(months=+1)+relativedelta(day=1) # First day of next month 
    prediction_end_date = prediction_start_date + relativedelta(months=+6)
    importer_cycle_infos = PerfImporterCycleInfos(
        execution_date = execution_date,
        prediction_start_date = prediction_start_date,
        prediction_end_date = prediction_end_date,
        file_name = file_name
    )
    db_session.add(importer_cycle_infos)
    db_session.commit()
    importer_cycle_infos = PerfImporterCycleInfos.query.filter(PerfImporterCycleInfos.file_name == file_name).first()
    importer_cycle_infos_id = importer_cycle_infos._id

    logger.info(f"id = {importer_cycle_infos_id}")
    logger.info(f"execution_date = {execution_date}")
    logger.info(f"prediction_start_date = {prediction_start_date}")
    logger.info(f"prediction_end_date = {prediction_end_date}")
    logger.info(f"file_name = {file_name}")
    logger.info("insertion into importer_cycle_infos OK")

    return importer_cycle_infos_id

def insert_into_etablissements_predicted_and_effective_hirings(importer_cycle_infos_id, file_name, etab_list):
    logger.info(f"\n Start : Insert data into perf_prediction_and_effective_hirings from file {file_name}")
    table_columns_name = headers_we_want_to_keep
    table_columns_name[table_columns_name.index("score")] = "lbb_nb_predicted_hirings_score"
    table_columns_name[table_columns_name.index("score_alternance")] = "lba_nb_predicted_hirings_score"
    df = pd.DataFrame(etab_list, columns=table_columns_name)

    df['importer_cycle_infos_id'] = importer_cycle_infos_id

    df.reset_index(drop=True, inplace=True)
    engine = import_util.create_sqlalchemy_engine()
    df.to_sql(
        con=engine,
        name="perf_prediction_and_effective_hirings",
        if_exists='append',
        index=False,
        chunksize=10000
    )
    engine.close()

    logger.info("Insertion into perf_prediction_and_effective_hirings OK")
    logger.info(f"Insertion of {len(df.index)} rows ")

def insert_data(file,etab_list):
    file_name = os.path.basename(file)
    logger.info(f"\n Start : Insert data into database from file {file_name}")
    importer_cycle_infos_id = insert_into_importer_cycle_infos(file, file_name)
    insert_into_etablissements_predicted_and_effective_hirings(importer_cycle_infos_id, file_name, etab_list)

def main():
    # First part of insertion : Get data from the file exported after each importer cycle
    files_list = get_available_files_list()
    for file in files_list:
        etab_list = parse_backup_file_importer_output(file)
        insert_data(file, etab_list)

    # Second part : Compute nb of effective hirings
    # TODO

if __name__ == '__main__':
    main()