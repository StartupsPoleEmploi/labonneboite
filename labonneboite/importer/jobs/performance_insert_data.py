from labonneboite.importer import util as import_util
from labonneboite.importer import settings
from labonneboite.importer.models.computing import PerfImporterCycleInfos, PerfPredictionAndEffectiveHirings, \
    PerfDivisionPerRome, Hiring
from labonneboite.common.database import db_session
from labonneboite.common import scoring as scoring_util
from labonneboite.common import load_data

import os
import gzip
import logging
from datetime import datetime, timedelta
from dateutil.relativedelta import *
import re

import pandas as pd

logger = logging.getLogger(__name__)


def get_date_from_file_name(file_name):
    req = re.search("(\d*_\d*_\d*_\d*).sql.gz", file_name)
    date_str = req.group(1)
    date_time_object = datetime.strptime(date_str, '%Y_%m_%d_%H%M')
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


def insert_into_sql_table_old_prediction_file(file):
    file_name = os.path.basename(file)
    logger.info(f"\n Start : Insert data into etablissements_new from file {file_name}")
    con, cur = import_util.create_cursor()
    sql_file = gzip.open(file, 'rt', encoding='utf8')
    sql_as_string = sql_file.read()

    # Cant load the whole table at once, the file is to large ( ~ 400mb)
    # So we have to split the sql file in multiple transactions
    drop_statement = "DROP TABLE IF EXISTS `etablissements_new`;"
    cur.execute(drop_statement)

    start_create_text = "CREATE TABLE "
    end_create_text = "ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;"
    start_create_statement_index = sql_as_string.find(start_create_text) + len(start_create_text)
    end_create_statement_index = sql_as_string.find(end_create_text, start_create_statement_index)
    create_statement = start_create_text + sql_as_string[
                                           start_create_statement_index:end_create_statement_index] + end_create_text
    cur.execute(create_statement)

    cur.execute("LOCK TABLES `etablissements_new` WRITE;")

    insert_statements = sql_as_string.split("INSERT INTO `etablissements_new` VALUES")[1:]
    for statement in insert_statements:
        if "/*!40000 ALTER TABLE `etablissements_new` ENABLE KEYS */;" in statement:
            clean_insert_statement = "INSERT INTO `etablissements_new` VALUES" + \
                                     statement.split("/*!40000 ALTER TABLE `etablissements_new` ENABLE KEYS */;")[0]
        else:
            clean_insert_statement = "INSERT INTO `etablissements_new` VALUES" + statement
        cur.execute(clean_insert_statement)

    cur.execute("UNLOCK TABLES;")

    con.commit()  # foo test resolution du TO
    cur.close()
    con.close()
    logger.info(f"\n End : Insert data into etablissements_new from file {file_name}")


def insert_into_importer_cycle_infos(file, file_name):
    logger.info(f"\n Start : Insert data into importer_cycle_infos from file {file_name}")

    # Insert into importer cycle infos

    # TODO : Check that the prediction start date and end date match these ones
    execution_date = get_date_from_file_name(file_name)
    prediction_start_date = execution_date + relativedelta(months=+1) + relativedelta(day=1)  # First day of next month
    prediction_end_date = prediction_start_date + relativedelta(months=+6)
    importer_cycle_infos = PerfImporterCycleInfos(
        execution_date=execution_date,
        prediction_start_date=prediction_start_date,
        prediction_end_date=prediction_end_date,
        file_name=file_name,
        computed=False,
        on_google_sheets=False
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


def insert_into_etablissements_predicted_and_effective_hirings(importer_cycle_infos_id, file_name):
    logger.info(f"\n Start : Insert data into perf_prediction_and_effective_hirings from file {file_name}")

    query = f'SELECT siret, \
                    raisonsociale, \
                    enseigne, \
                    codenaf, \
                    codepostal, \
                    codecommune, \
                    departement, \
                    score, \
                    score_alternance \
               FROM etablissements_new;'

    engine = import_util.create_sqlalchemy_engine()
    df = pd.read_sql_query(query, engine)
    engine.close()

    df['importer_cycle_infos_id'] = importer_cycle_infos_id
    df = df.rename(
        columns={"score": "lbb_nb_predicted_hirings_score", "score_alternance": "lba_nb_predicted_hirings_score"})

    df.reset_index(drop=True, inplace=True)
    engine = import_util.create_sqlalchemy_engine()
    df.to_sql(
        con=engine,
        name="perf_prediction_and_effective_hirings",
        if_exists='append',
        index=False,
        chunksize=1000
    )
    engine.close()

    logger.info("Insertion into perf_prediction_and_effective_hirings OK")
    logger.info(f"Insertion of {len(df.index)} rows ")


def insert_data(file):
    file_name = os.path.basename(file)
    logger.info(f"\n Start : Insert data into database from file {file_name}")
    importer_cycle_infos = insert_into_importer_cycle_infos(file, file_name)
    insert_into_etablissements_predicted_and_effective_hirings(importer_cycle_infos._id, file_name)
    return True


def load_perf_division_per_rome_dict():
    perf_division_per_rome_dict = {}

    rome_naf_mapping = load_data.load_rome_naf_mapping()

    # headers of this mapping : rome_id,rome_label,naf_id,naf_label,hirings
    for rome_naf_row in rome_naf_mapping:
        rome_code = rome_naf_row[0]
        naf_code = rome_naf_row[2]
        perf_division_per_rome_dict[naf_code] = perf_division_per_rome_dict.get(naf_code, {})
        perf_division_per_rome_dict[naf_code][rome_code] = {
            "threshold_lbb": scoring_util.get_score_minimum_for_rome(rome_code),
            "nb_bonne_boites_lbb": 0,
            "threshold_lba": scoring_util.get_score_minimum_for_rome(rome_code, alternance=True),
            "nb_bonne_boites_lba": 0
        }

    return perf_division_per_rome_dict


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

    logger.info(
        f"Importer cycles infos which have not been computed yet : {[i.file_name for i in importer_cycles_infos_to_compute]}")

    for ici in importer_cycles_infos_to_compute:
        perf_division_per_rome_dict = load_perf_division_per_rome_dict()

        naf_not_founds = set()
        nb_companies_with_naf_not_found = 0

        logger.info(f"Start computing for importer cycle infos : {ici._id} - {ici.file_name}")

        engine = import_util.create_sqlalchemy_engine()
        ppaeh = PerfPredictionAndEffectiveHirings.query.filter(PerfPredictionAndEffectiveHirings.importer_cycle_infos_id==ici._id)
        columns_companies = ["_id", "siret", "naf", "lbb_nb_predicted_hirings_score", "lba_nb_predicted_hirings_score"]
        dict_df_companies = {}
        dict_ppaeh = {}
        for col in columns_companies:
            dict_df_companies[col] = []
        for perf in ppaeh:
            dict_ppaeh[perf._id] = perf
            for col in columns_companies:
                dict_df_companies[col].append(getattr(perf, col))
        del ppaeh
        df_companies_list = pd.DataFrame(data=dict_df_companies)

        logger.info(f"Nb offices to compute : {len(df_companies_list)}")

        query_hirings_lbb = f"SELECT siret, count(*) as lbb_nb_effective_hirings \
                FROM hirings\
                WHERE hiring_date >= '{ici.prediction_start_date}'\
                and hiring_date <= '{ici.prediction_end_date}'\
                and (contract_type={Hiring.CONTRACT_TYPE_CDD} or contract_type={Hiring.CONTRACT_TYPE_CDI})\
                GROUP BY siret;"
        df_hirings_lbb = pd.read_sql_query(query_hirings_lbb, engine)
        logger.info(f"Nb offices found in hirings for lbb : {len(df_hirings_lbb)}")

        query_hirings_lba = f"SELECT siret, count(*) as lba_nb_effective_hirings \
                FROM hirings\
                WHERE hiring_date >= '{ici.prediction_start_date}'\
                and hiring_date <= '{ici.prediction_end_date}'\
                and (contract_type={Hiring.CONTRACT_TYPE_APR} or contract_type={Hiring.CONTRACT_TYPE_CP})\
                GROUP BY siret;"
        df_hirings_lba = pd.read_sql_query(query_hirings_lba, engine)
        logger.info(f"Nb offices found in hirings for lba: {len(df_hirings_lba)}")

        engine.close()

        df_merge_hirings_tmp = pd.merge(df_companies_list, df_hirings_lbb, how='left', on="siret")
        df_merged = pd.merge(df_merge_hirings_tmp, df_hirings_lba, how='left', on="siret")

        # Compute the predicted hirings from the score
        df_merged["lbb_nb_predicted_hirings"] = df_merged["lbb_nb_predicted_hirings_score"].apply(
            lambda x: scoring_util.get_hirings_from_score(x))
        df_merged["lba_nb_predicted_hirings"] = df_merged["lba_nb_predicted_hirings_score"].apply(
            lambda x: scoring_util.get_hirings_from_score(x))

        df_merged = df_merged.fillna(0)

        cols_we_want_to_keep = [
            "_id",
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
        count = 0

        for row in values_to_update:
            row_id = row[0]
            #import ipdb;ipdb.set_trace()
            siret = row[1]
            naf = row[2]
            params = dict(zip(["lbb_nb_effective_hirings", "lba_nb_effective_hirings", "lbb_nb_predicted_hirings",
                               "lba_nb_predicted_hirings"], row[3:7]))
            lbb_nb_predicted_hirings_score = row[7]
            lba_nb_predicted_hirings_score = row[8]
            # foo
            pred_effective_hirings = dict_ppaeh[row_id]
            for key, val in params.items():
                setattr(pred_effective_hirings, key, int(val))
            is_a_bonne_boite = False
            is_a_bonne_alternance = False

            naf_present_in_mapping_rome_naf = naf in perf_division_per_rome_dict

            if naf_present_in_mapping_rome_naf:
                for rome_code, values in perf_division_per_rome_dict[naf].items():
                    score_lbb = scoring_util.get_score_adjusted_to_rome_code_and_naf_code(
                        score=lbb_nb_predicted_hirings_score,
                        rome_code=rome_code,
                        naf_code=naf
                    )
                    if score_lbb >= values["threshold_lbb"]:
                        perf_division_per_rome_dict[naf][rome_code]["nb_bonne_boites_lbb"] += 1
                        is_a_bonne_boite = True

                    score_lba = scoring_util.get_score_adjusted_to_rome_code_and_naf_code(
                        score=lba_nb_predicted_hirings_score,
                        rome_code=rome_code,
                        naf_code=naf
                    )
                    if score_lba >= values["threshold_lba"]:
                        perf_division_per_rome_dict[naf][rome_code]["nb_bonne_boites_lba"] += 1
                        is_a_bonne_alternance = True
            else:
                naf_not_founds.add(naf)
                nb_companies_with_naf_not_found += 1
            pred_effective_hirings.is_a_bonne_boite = is_a_bonne_boite
            pred_effective_hirings.is_a_bonne_alternance = is_a_bonne_alternance

            db_session.add(pred_effective_hirings)

            # Commit all the 10 000 transactions
            if count % 1000 == 0:
                logger.info(f"{count} companies have been treated")
                db_session.commit()

            count += 1

        # Commit for the remaining rows
        db_session.commit()

        logger.info(f"Number of naf not found in the mapping rome naf for this importer cycle : {len(naf_not_founds)}")
        logger.info(f"List of naf not found in the mapping rome naf for this importer cycle : {naf_not_founds}")
        logger.info(
            f"Number of companies with naf not found in the mapping rome naf for this importer cycle : {nb_companies_with_naf_not_found}")
        logger.info(f"Number of total companies : {count}")

        for naf_code, romes_list in perf_division_per_rome_dict.items():
            for rome_code, values in romes_list.items():
                division_per_rome = PerfDivisionPerRome(
                    importer_cycle_infos_id=ici._id,
                    naf=naf_code,
                    rome=rome_code,
                    threshold_lbb=values["threshold_lbb"],
                    threshold_lba=values["threshold_lba"],
                    nb_bonne_boites_lbb=values["nb_bonne_boites_lbb"],
                    nb_bonne_boites_lba=values["nb_bonne_boites_lba"],
                )
                db_session.add(division_per_rome)

        db_session.commit()

        ici.computed = True
        db_session.add(ici)
        db_session.commit()


def run_main():
    # First part of insertion : Get data from the file exported after each importer cycle
    files_list = get_available_files_list()
    for file in files_list:
        insert_into_sql_table_old_prediction_file(file)
        insert_data(file)

    compute_effective_and_predicted_hirings()


if __name__ == '__main__':
    run_main()
