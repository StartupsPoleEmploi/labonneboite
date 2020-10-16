from labonneboite.importer import util as import_util
from labonneboite.importer import settings
from labonneboite.importer.models.computing import PerfImporterCycleInfos, PerfPredictionAndEffectiveHirings, PerfDivisionPerRome
from labonneboite.common.database import db_session
from labonneboite.common import scoring as scoring_util
from labonneboite.common import load_data

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
        file_name = file_name,
        computed = False
    )
    db_session.add(importer_cycle_infos)
    db_session.commit()
    importer_cycle_infos = PerfImporterCycleInfos.query.filter(PerfImporterCycleInfos.file_name == file_name).first()

    logger.info(f"id = {importer_cycle_infos._id}")
    logger.info(f"execution_date = {execution_date}")
    logger.info(f"prediction_start_date = {prediction_start_date}")
    logger.info(f"prediction_end_date = {prediction_end_date}")
    logger.info(f"file_name = {file_name}")
    logger.info("insertion into importer_cycle_infos OK")

    return importer_cycle_infos

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
    importer_cycle_infos = insert_into_importer_cycle_infos(file, file_name)
    insert_into_etablissements_predicted_and_effective_hirings(importer_cycle_infos._id, file_name, etab_list)
    return True

def compute_effective_and_predicted_hirings():
    logger.info(f"\n Start : Computing effective hirings")

    importer_cycles_infos = PerfImporterCycleInfos.query.filter(PerfImporterCycleInfos.computed == False).all()
    importer_cycles_infos_to_compute = []
    for ici in importer_cycles_infos:
        if os.environ["LBB_ENV"] == "development":
            importer_cycles_infos_to_compute.append(ici)
            continue
        if ici.prediction_end_date < datetime.now():
            importer_cycles_infos_to_compute.append(ici)

    logger.info(f"Importer cycles infos which have not been computed yet : {[ i.file_name for i in importer_cycles_infos_to_compute]}")

    perf_division_per_rome_dict = {}

    rome_naf_mapping = load_data.load_rome_naf_mapping()
    #headers of this mapping : rome_id,rome_label,naf_id,naf_label,hirings
    for rome_naf_row in rome_naf_mapping:
        rome_code = rome_naf_row[0]
        naf_code = rome_naf_row[2]
        perf_division_per_rome_dict[naf_code] = []
        perf_division_per_rome_dict[naf_code].append(
            {
                rome_code: {
                    "threshold_lbb": scoring_util.get_score_minimum_for_rome(rome_code), #FIXME
                    "nb_bonne_boites_lbb":0,
                    "threshold_lba": scoring_util.get_score_minimum_for_rome(rome_code, alternance=True),
                    "nb_bonne_boites_lba":0
                }
            }
        )

    for ici in importer_cycles_infos_to_compute:
        logger.info(f"Start computing for importer cycle infos : {ici._id} - {ici.file_name}")

        engine = import_util.create_sqlalchemy_engine()
        query = f'SELECT id, siret, codenaf as naf, lbb_nb_predicted_hirings_score, lba_nb_predicted_hirings_score \
                FROM perf_prediction_and_effective_hirings\
                WHERE importer_cycle_infos_id={ici._id};'
        df_companies_list = pd.read_sql_query(query, engine)
        logger.info(f"Nb offices to compute : {len(df_companies_list)}")

        query_hirings_lbb = f"SELECT siret, count(*) as lbb_nb_effective_hirings \
                FROM hirings\
                WHERE hiring_date >= '{ici.prediction_start_date}'\
                and hiring_date <= '{ici.prediction_end_date}'\
                and (contract_type=1 or contract_type=2)\
                GROUP BY siret;"
        df_hirings_lbb = pd.read_sql_query(query_hirings_lbb,engine)
        logger.info(f"Nb offices found in hirings for lbb : {len(df_hirings_lbb)}")

        query_hirings_lba = f"SELECT siret, count(*) as lba_nb_effective_hirings \
                FROM hirings\
                WHERE hiring_date >= '{ici.prediction_start_date}'\
                and hiring_date <= '{ici.prediction_end_date}'\
                and (contract_type=11 or contract_type=12)\
                GROUP BY siret;"
        df_hirings_lba = pd.read_sql_query(query_hirings_lba,engine)
        logger.info(f"Nb offices found in hirings for lba: {len(df_hirings_lba)}")

        engine.close()

        df_merge_hirings_tmp = pd.merge(df_companies_list, df_hirings_lbb, how='left', on="siret")
        df_merged = pd.merge(df_merge_hirings_tmp, df_hirings_lba, how='left', on="siret")


        #Compute the predicted hirings from the score
        df_merged["lbb_nb_predicted_hirings"] = df_merged["lbb_nb_predicted_hirings_score"].apply(lambda x: scoring_util.get_hirings_from_score(x))
        df_merged["lba_nb_predicted_hirings"] = df_merged["lba_nb_predicted_hirings_score"].apply(lambda x: scoring_util.get_hirings_from_score(x))

        df_merged = df_merged.fillna(0)

        cols_we_want_to_keep = [
            "id", 
            "siret", 
            "naf",
            "lbb_nb_effective_hirings", 
            "lba_nb_effective_hirings", 
            "lbb_nb_predicted_hirings", 
            "lba_nb_predicted_hirings",
            "lbb_nb_predicted_hirings_score",
            "lba_nb_predicted_hirings_score",
        ]

        df_merged = df_merged[cols_we_want_to_keep]

        values_to_update = df_merged.values.tolist()
        count=0

        for row in values_to_update:
            row_id=row[0]
            siret=row[1]
            naf=row[2]
            lbb_nb_effective_hirings=row[3]
            lba_nb_effective_hirings=row[4]
            lbb_nb_predicted_hirings=row[5]
            lba_nb_predicted_hirings=row[6]
            lbb_nb_predicted_hirings_score=row[7]
            lba_nb_predicted_hirings_score=row[8]
            
            pred_effective_hirings = PerfPredictionAndEffectiveHirings.query.filter(PerfPredictionAndEffectiveHirings._id == row_id).first()
            #FIXME : For the first run it does not work, then it works
            pred_effective_hirings.lbb_nb_effective_hirings = lbb_nb_effective_hirings
            pred_effective_hirings.lba_nb_effective_hirings = lba_nb_effective_hirings
            pred_effective_hirings.lbb_nb_predicted_hirings = int(lbb_nb_predicted_hirings)
            pred_effective_hirings.lba_nb_predicted_hirings = int(lba_nb_predicted_hirings)

            is_a_bonne_boite = False
            is_a_bonne_alternance = False


            # Dico { "codenaf" : [{"coderome" : {"threshold","nb_companies"}},]}

            for rome_code_infos in perf_division_per_rome_dict[naf]:
                rome_code = list(rome_code_infos.keys())[0]
                score_lbb = scoring_util.get_score_adjusted_to_rome_code_and_naf_code(
                        score=lbb_nb_predicted_hirings_score,
                        rome_code=rome_code,
                        naf_code=naf
                    )
                if score_lbb >= rome_code_infos[rome_code]["threshold_lbb"]:
                    perf_division_per_rome_dict[naf][rome_code]["nb_bonne_boites_lbb"] += 1
                    is_a_bonne_boite = True

                score_lba = scoring_util.get_score_adjusted_to_rome_code_and_naf_code(
                        score=lba_nb_predicted_hirings_score,
                        rome_code=rome_code,
                        naf_code=naf
                    )
                if score_lbb >= rome_code_infos[rome_code]["threshold_lba"]:
                    perf_division_per_rome_dict[naf][rome_code]["nb_bonne_boites_lba"] += 1
                    is_a_bonne_alternance = True

            pred_effective_hirings.is_a_bonne_boite = is_a_bonne_boite
            pred_effective_hirings.is_a_bonne_alternance = is_a_bonne_alternance

            db_session.add(pred_effective_hirings)

            #Commit all the 10 000 transactions
            if count % 10000 == 0:
                db_session.commit()

            count += 1

        # Commit for the remaining rows
        db_session.commit()
        
        for naf_code, romes_list in perf_division_per_rome_dict.items():
            for rome_infos in romes_list:
                rome_code = list(rome_infos.keys())[0]
                division_per_rome = PerfDivisionPerRome(
                    importer_cycle_infos_id = ici._id,
                    naf = naf_code,
                    rome = rome_code,
                    threshold_lbb = rome_infos[rome_code]["threshold_lbb"],
                    threshold_lba = rome_infos[rome_code]["threshold_lba"],
                    nb_bonne_boites_lbb = rome_infos[rome_code]["nb_bonne_boites_lbb"],
                    nb_bonne_boites_lba = rome_infos[rome_code]["nb_bonne_boites_lba"],
                )
                db_session.add(division_per_rome)

        db_session.commit()

        ici.computed = True
        db_session.add(ici)
        db_session.commit()

def main():
    # First part of insertion : Get data from the file exported after each importer cycle
    files_list = get_available_files_list()
    for file in files_list:
        etab_list = parse_backup_file_importer_output(file)
        insert_data(file, etab_list)

    compute_effective_and_predicted_hirings()
    
if __name__ == '__main__':
    main()