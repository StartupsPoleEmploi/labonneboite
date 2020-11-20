import csv
import numpy
import pandas as pd
import logging
import math
from labonneboite.common.database import db_session
from labonneboite.importer import util as import_util
from labonneboite.common import load_data
from labonneboite.conf import settings
from labonneboite.importer import settings as importer_settings
from labonneboite.scripts.impact_retour_emploi.google_sheets_report import GoogleSheetReport, generate_google_sheet_service
from labonneboite.importer.models.computing import PerfImporterCycleInfos
from labonneboite.importer.models.computing import PerfDivisionPerRome
from labonneboite.importer.models.computing import PerfPredictionAndEffectiveHirings
from datetime import datetime

logger = logging.getLogger(__name__)

class PayloadDataframe:

    def __init__(self):
        self.dict_df_predict = {}
        self.dict_df_sum_predict = {}
        self.dict_df_predict_global = {}
        self.dict_df_sum_predict_global = {}
        self.head_predict = {}
        self.head_predict_global = {}

    def reset(self):
        self.dict_df_predict = {}
        self.dict_df_sum_predict = {}
        self.dict_df_predict_global = {}
        self.dict_df_sum_predict_global = {}
        self.head_predict = {}
        self.head_predict_global = {}

#import donnée#######################################################################""
#TODO : Remove from here to use during unit tests (not written yet)
def load_csv_perf_division_per_rome(filename, delimiter=';'):
    #date_time_obj = datetime.datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S.%f')
    for row in load_data.load_csv_file(filename,delimiter):
        perf_div_per_rome = PerfDivisionPerRome(
            _id = row[0],
            importer_cycle_infos_id = row[1],
            naf = row[3],
            rome = row[2],
            threshold_lbb = row[4],
            nb_bonne_boites_lbb = row[5],
            threshold_lba = row[6],
            nb_bonne_boites_lba = row[7]
        )
        db_session.add(perf_div_per_rome)
        db_session.commit()

def load_csv_perf_importer_cycle_infos(filename, delimiter=';'):
    #date_time_obj = datetime.datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S.%f')
    for row in load_data.load_csv_file(filename,delimiter):
        perf_importer_cycle_info = PerfImporterCycleInfos(
            _id = row[0],
            execution_date = datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S.%f'),
            prediction_start_date = datetime.strptime(row[2], '%Y-%m-%d %H:%M:%S.%f'),
            prediction_end_date = datetime.strptime(row[3], '%Y-%m-%d %H:%M:%S.%f'),
            file_name =  row[4],
            computed = (row[5] == 'True'),
            on_google_sheets = (row[6] == 'True')
        )
        db_session.add(perf_importer_cycle_info)
        db_session.commit()

def load_csv_perf_prediction_and_effective_h(filename, delimiter=';'):
    #date_time_obj = datetime.datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S.%f')
    for row in load_data.load_csv_file(filename,delimiter):
        perf_importer_cycle_info = PerfPredictionAndEffectiveHirings(
            _id = row[0],
            importer_cycle_infos_id = row[1],
            siret = row[2],
            naf = row[3],
            city_code =  row[4],
            zipcode = row[5],
            departement = row[6],
            company_name = row[7],
            office_name = row[8],
            lbb_nb_predicted_hirings_score = row[9],
            lba_nb_predicted_hirings_score = row[10],
            lbb_nb_predicted_hirings = row[11],
            lba_nb_predicted_hirings = row[12],
            lbb_nb_effective_hirings = row[13],
            lba_nb_effective_hirings = row[14],
            is_a_bonne_boite = (row[15] == "True"),
            is_a_bonne_alternance = (row[16] == "True")
        )
        db_session.add(perf_importer_cycle_info)
        db_session.commit()



def get_nb_entreprise_par_cycle_et_naf_ou_dep(colonne, nom, is_lbb=True):
    engine = import_util.create_sqlalchemy_engine()
    prefix_columns = "lbb" if is_lbb else "lba"
    if colonne == "global":
        query = f"""SELECT importer_cycle_infos_id as cycle, sum({prefix_columns}_nb_effective_hirings) as nbTotalHirings, count(*) as nbTotal \
                FROM perf_prediction_and_effective_hirings ppaeh \
                INNER JOIN perf_importer_cycle_infos pici on pici.id = ppaeh.importer_cycle_infos_id
                WHERE pici.computed is true
                AND pici.on_google_sheets is false
                GROUP BY importer_cycle_infos_id;"""
    else: #colonne == Naf OR departement
        query = f'SELECT importer_cycle_infos_id as cycle , {colonne} as {nom} ,sum({prefix_columns}_nb_effective_hirings) as nbTotalHirings, count(*) as nbTotal \
                FROM perf_prediction_and_effective_hirings ppaeh \
        INNER JOIN perf_importer_cycle_infos pici on pici.id = ppaeh.importer_cycle_infos_id \
        WHERE pici.computed is true \
        AND pici.on_google_sheets is false \
                GROUP BY importer_cycle_infos_id , {colonne};'
    df_nb_entreprise = pd.read_sql_query(query, engine)
    engine.close()
    return df_nb_entreprise

def get_nb_entreprise_par_cycle_et_naf_ou_dep_isLBX(colonne, nom, is_lbb):
    filter_lbx = "is_a_bonne_boite" if is_lbb else "is_a_bonne_alternance"
    prefix_columns = "lbb" if is_lbb else "lba"
    engine = import_util.create_sqlalchemy_engine()
    if colonne == "global":
        query = f'SELECT importer_cycle_infos_id as cycle,sum({prefix_columns}_nb_effective_hirings) as nbTotalLBXHirings, count(*) as nbTotalLBX \
                FROM perf_prediction_and_effective_hirings ppaeh \
        INNER JOIN perf_importer_cycle_infos pici on pici.id = ppaeh.importer_cycle_infos_id \
        WHERE pici.computed is true \
        AND pici.on_google_sheets is false \
                AND {filter_lbx} is true \
                GROUP BY importer_cycle_infos_id;'
    else: #colonne == Naf OR departement
        query = f'SELECT importer_cycle_infos_id as cycle , {colonne} as {nom} ,sum({prefix_columns}_nb_effective_hirings) as nbTotalLBXHirings, count(*) as nbTotalLBX \
                FROM perf_prediction_and_effective_hirings ppaeh \
        INNER JOIN perf_importer_cycle_infos pici on pici.id = ppaeh.importer_cycle_infos_id \
        WHERE pici.computed is true \
        AND pici.on_google_sheets is false \
                AND {filter_lbx} is true \
                GROUP BY importer_cycle_infos_id , {colonne};'
    df_nb_entreprise_isLBX = pd.read_sql_query(query, engine)
    engine.close()
    return df_nb_entreprise_isLBX

def get_sum_predict_par_cycle_et_naf_ou_dep(cycle, colonne, nom=None, value=None, is_lbb=True):
    prefix_columns = "lbb" if is_lbb else "lba"
    engine = import_util.create_sqlalchemy_engine()
    if colonne == "global":
        query = f'SELECT importer_cycle_infos_id as cycle, sum({prefix_columns}_nb_predicted_hirings) as sommeTotal \
                FROM perf_prediction_and_effective_hirings ppaeh \
                WHERE importer_cycle_infos_id = {cycle} \
                GROUP BY importer_cycle_infos_id;'
    else: #colonne == Naf OR departement
        query = f'SELECT importer_cycle_infos_id as cycle , {colonne} as {nom},sum({prefix_columns}_nb_predicted_hirings) as sommeTotal \
                FROM perf_prediction_and_effective_hirings ppaeh \
                WHERE importer_cycle_infos_id = {cycle} and {colonne} = "{value}"  \
                GROUP BY importer_cycle_infos_id , {colonne};'
    df_sum_predict = pd.read_sql_query(query, engine)
    engine.close()
    return df_sum_predict

def get_predict_par_cycle_et_naf_ou_dep(cycle, colonne, value=None, is_lbb=True):
    prefix_columns = "lbb" if is_lbb else "lba"
    engine = import_util.create_sqlalchemy_engine()
    if colonne == "global":
        query = f'SELECT {prefix_columns}_nb_predicted_hirings as predict, {prefix_columns}_nb_effective_hirings as effective, codenaf, departement \
                FROM perf_prediction_and_effective_hirings \
                WHERE importer_cycle_infos_id = {cycle}\
                ORDER BY {prefix_columns}_nb_predicted_hirings desc '
    else:
        query = f'SELECT {prefix_columns}_nb_predicted_hirings as predict, {prefix_columns}_nb_effective_hirings as effective, codenaf, departement \
                FROM perf_prediction_and_effective_hirings \
                WHERE importer_cycle_infos_id = {cycle} and {colonne} = "{value}"  \
                ORDER BY {prefix_columns}_nb_predicted_hirings desc'
    df_predict = pd.read_sql_query(query, engine)
    engine.close()
    return df_predict

def get_cycle_infos():
    engine = import_util.create_sqlalchemy_engine()
    query = f'SELECT id as cycle, execution_date as dateExecution \
            FROM perf_importer_cycle_infos \
            WHERE on_google_sheets = 0 \
            and computed is true;'
    df_predict = pd.read_sql_query(query, engine)
    engine.close()
    return df_predict

#cycle + naf #######################################################################""

def get_sum_predict(pdf, row,i,colonne,nom=None, is_lbb=True):
    logger.info(f"START - {str(datetime.now())}- is_lbb : {is_lbb} - computing sum predict by {colonne} for cycle importer {row['cycle']} and sum {i}")
    if nom is not None:
        row_nom = row[nom]
    else:
        row_nom = None

    if i == 10:
        head_sum = 0
        head_len = 0
        if colonne != "global":
            df_predict = pdf.dict_df_predict_global[row["cycle"]].query(f"{colonne} == '{row_nom}'")
            df_sum_predict = df_predict["effective"].values.sum()
            if row["cycle"] not in pdf.dict_df_predict:
                pdf.dict_df_predict[row["cycle"]] = {}
            pdf.dict_df_predict[row["cycle"]][row[nom]] = df_predict
            if row["cycle"] not in pdf.dict_df_sum_predict:
                pdf.dict_df_sum_predict[row["cycle"]] = {}
            pdf.dict_df_sum_predict[row["cycle"]][row[nom]] = df_sum_predict
            df_sum_predict = pdf.dict_df_sum_predict[row["cycle"]][row[nom]]
            if row["cycle"] not in pdf.head_predict:
                pdf.head_predict[row["cycle"]] = {}
            pdf.head_predict[row["cycle"]][row[nom]] = {
                "len": head_len,
                "sum": head_sum
            }
        else:
            df_predict = get_predict_par_cycle_et_naf_ou_dep(row["cycle"], colonne, row_nom, is_lbb=is_lbb)
            df_sum_predict = df_predict["effective"].values.sum()
            if row["cycle"] not in pdf.dict_df_predict_global:
                pdf.dict_df_predict_global[row["cycle"]] = {}
            pdf.dict_df_predict_global[row["cycle"]] = df_predict
            if row["cycle"] not in pdf.dict_df_sum_predict_global:
                pdf.dict_df_sum_predict_global[row["cycle"]] = {}
            pdf.dict_df_sum_predict_global[row["cycle"]] = df_sum_predict
            df_sum_predict = pdf.dict_df_sum_predict_global[row["cycle"]]
            if row["cycle"] not in pdf.head_predict_global:
                pdf.head_predict_global[row["cycle"]] = {
                    "len": head_len,
                    "sum": head_sum
                }

    else:
        if colonne != "global":
            df_predict = pdf.dict_df_predict[row["cycle"]][row[nom]]
            df_sum_predict = pdf.dict_df_sum_predict[row["cycle"]][row[nom]]
            head_sum = pdf.head_predict[row["cycle"]][row[nom]]["sum"]
            head_len = pdf.head_predict[row["cycle"]][row[nom]]["len"]
        else:
            df_predict = pdf.dict_df_predict_global[row["cycle"]]
            df_sum_predict = pdf.dict_df_sum_predict_global[row["cycle"]]
            head_sum = pdf.head_predict_global[row["cycle"]]["sum"]
            head_len = pdf.head_predict_global[row["cycle"]]["len"]
    if i == 100:
        rmse_list = numpy.array([calcul_rmse(eff, pred) for eff, pred in zip(numpy.array(df_predict["effective"]),
                                                                             numpy.array(df_predict["predict"]))])
        logger.info(
            f"END - {str(datetime.now())}- computing sum predict by {colonne} for cycle importer {row['cycle']} and sum {i}")
        return math.sqrt(rmse_list.sum() / row['nbTotal'])


    # calculate top sum
    new_len_head = int(row['nbTotal']*i/100)
    diff_sum = df_predict["effective"].values[head_len:new_len_head].sum()
    head_sum += diff_sum
    head_len = new_len_head
    # update dict head with new values
    if colonne != "global":
        pdf.head_predict[row["cycle"]][row[nom]]["sum"] = head_sum
        pdf.head_predict[row["cycle"]][row[nom]]["len"] = head_len
    else:
        pdf.head_predict_global[row["cycle"]]["sum"] = head_sum
        pdf.head_predict_global[row["cycle"]]["len"] = head_len
    if df_sum_predict == 0:
        return 0
    logger.info(f"END - {str(datetime.now())}- computing sum predict by {colonne} for cycle importer {row['cycle']} and sum {i}")
    return head_sum / df_sum_predict


def get_prop_recrut_non_lbx(total, total_lbx):
    res = (total - total_lbx)/ total if total > 0 else 1
    return res


def calcul_rmse(effective, predict):
    return math.pow((effective - predict), 2)


def lancement_requete(pdf, colonne,nom=None, is_lbb=True):
    df_nb_entreprise = get_nb_entreprise_par_cycle_et_naf_ou_dep(colonne,nom, is_lbb)
    if len(df_nb_entreprise) > 0:
        for i in range(10,110,10):
            df_nb_entreprise[f'sum{i}'] = df_nb_entreprise.apply(lambda row: get_sum_predict(pdf, row,i,colonne,nom,is_lbb), axis=1)

        df_nb_entreprise = df_nb_entreprise.rename(columns={'sum100':'RMSE'})
        df_nb_entreprise_isLBX  = get_nb_entreprise_par_cycle_et_naf_ou_dep_isLBX(colonne, nom, is_lbb)
        df_result = pd.merge(df_nb_entreprise , df_nb_entreprise_isLBX , on=['cycle',nom])
        df_result['propRecrutNonLBX'] = numpy.array([get_prop_recrut_non_lbx(total, total_lbx) for total, total_lbx in zip(numpy.array(df_result["nbTotalHirings"]),
                                                                                                       numpy.array(df_result["nbTotalLBXHirings"]))])
        return df_result
    else:
        raise Exception(f"Nothing to compute. (params: [colonne={colonne}, nom={nom}, is_lbb={is_lbb}])")



def prepare_google_sheet_data(pdf, is_lbb=True):
    #TODO : Refacto this function
    df_cycle_infos = get_cycle_infos()
    df_global = lancement_requete(pdf, "global", is_lbb=is_lbb)
    df_naf = lancement_requete(pdf, "codenaf", "naf", is_lbb)
    df_dep = lancement_requete(pdf, "departement","dep", is_lbb)
    df_naf = pd.merge(df_naf , df_cycle_infos , on=['cycle'])
    df_dep = pd.merge(df_dep , df_cycle_infos , on=['cycle'])
    df_global = pd.merge(df_global , df_cycle_infos , on=['cycle'])
    df_naf['dateExecutionImp'] = df_naf['dateExecution'].dt.strftime('%d/%m/%Y')
    df_dep['dateExecutionImp'] = df_dep['dateExecution'].dt.strftime('%d/%m/%Y')
    df_global['dateExecutionImp'] = df_global['dateExecution'].dt.strftime('%d/%m/%Y')

    ORDERING_COLUMN_NAF = [
        'cycle',
        'dateExecutionImp',
        'naf',
        'sum10',
        'sum20',
        'sum30',
        'sum40',
        'sum50',
        'sum60',
        'sum70',
        'sum80',
        'sum90',
        'propRecrutNonLBX',
        'RMSE',
        'nbTotal',
        'nbTotalLBX',
    ]
    ORDERING_COLUMN_DEP = [
        'cycle',
        'dateExecutionImp',
        'dep',
        'sum10',
        'sum20',
        'sum30',
        'sum40',
        'sum50',
        'sum60',
        'sum70',
        'sum80',
        'sum90',
        'propRecrutNonLBX',
        'RMSE',
        'nbTotal',
        'nbTotalLBX',
    ]
    ORDERING_COLUMN_GLOBAL = [
        'cycle',
        'dateExecutionImp',
        'sum10',
        'sum20',
        'sum30',
        'sum40',
        'sum50',
        'sum60',
        'sum70',
        'sum80',
        'sum90',
        'propRecrutNonLBX',
        'RMSE',
        'nbTotal',
        'nbTotalLBX',
    ]

    # Clean unecessary column
    df_naf = df_naf[ORDERING_COLUMN_NAF]
    df_dep = df_dep[ORDERING_COLUMN_DEP]
    df_global = df_global[ORDERING_COLUMN_GLOBAL]

    # Ordering column
    df_naf = df_naf.loc[:, ORDERING_COLUMN_NAF]
    df_dep = df_dep.loc[:, ORDERING_COLUMN_DEP]
    df_global = df_global.loc[:, ORDERING_COLUMN_GLOBAL]

    # clean NaN data
    df_naf = df_naf.replace(numpy.nan, '', regex=True)
    df_dep = df_dep.replace(numpy.nan, '', regex=True)
    df_global = df_global.replace(numpy.nan, '', regex=True)

    # Define ValueJSON body to insert in Google Sheets
    values_to_insert_naf = {'values': df_naf.values.tolist()}
    values_to_insert_dep = {'values': df_dep.values.tolist()}
    values_to_insert_global = {'values': df_global.values.tolist()}

    importer_cycle_infos_ids = df_cycle_infos["cycle"].values.tolist()

    return values_to_insert_naf , values_to_insert_dep, values_to_insert_global, importer_cycle_infos_ids

def set_importer_cycle_infos_google_sheets_boolean(importer_cycle_infos_id):
    for ici_id in importer_cycle_infos_id:
        ici = PerfImporterCycleInfos.query.filter(PerfImporterCycleInfos._id == ici_id).first()
        ici.on_google_sheets = True
        db_session.add(ici)
        db_session.commit()

def clear_useless_data(importer_cycle_infos_id):
    con, cur = import_util.create_cursor()
    for ici_id in importer_cycle_infos_id:
        cur.execute("DELETE FROM perf_prediction_and_effective_hirings WHERE importer_cycle_infos_id = %s", [ici_id])


def fill_indicators_sheet(pdf, is_lbb):
    # If it's not LBB we're seeking for, then we seeking LBA
    spreadsheet_id = settings.SPREADSHEET_IDS["perf_indicators_lbb"] if is_lbb else settings.SPREADSHEET_IDS["perf_indicators_lba"]
    logger.info("START - PREPARE DATA SHEET")
    values_to_insert_naf_sheet, values_to_insert_departement_sheet, values_to_insert_global_sheet, importer_cycle_infos_ids = prepare_google_sheet_data(pdf, is_lbb)
    logger.info("END - PREPARE DATA SHEET")
    service = generate_google_sheet_service()

    naf_sheet_report = GoogleSheetReport(
        service=service,
        spreadsheet_id=spreadsheet_id,
        sheet_index=0,
        start_cell=None,
        values=values_to_insert_naf_sheet
    )
    naf_sheet_report.set_sheet_range()
    naf_sheet_report.write_data_into_sheet()

    departement_sheet_report = GoogleSheetReport(
        service=service,
        spreadsheet_id=spreadsheet_id,
        sheet_index=1,
        start_cell=None,
        values=values_to_insert_departement_sheet
    )
    departement_sheet_report.set_sheet_range()
    departement_sheet_report.write_data_into_sheet()

    global_sheet_report = GoogleSheetReport(
        service=service,
        spreadsheet_id=spreadsheet_id,
        sheet_index=2,
        start_cell=None,
        values=values_to_insert_global_sheet
    )
    global_sheet_report.set_sheet_range()
    global_sheet_report.write_data_into_sheet()

    return importer_cycle_infos_ids


def run_main():
    logger.info(f"START - {str(datetime.now())}- Generate indicators for LBB")
    pdf = PayloadDataframe()
    fill_indicators_sheet(pdf, is_lbb=True)  # Perf indicators for LBB
    logger.info(f"END - {str(datetime.now())}- Generate indicators for LBB")
    pdf.reset()
    logger.info(f"START - {str(datetime.now())}- Generate indicators for LBA")
    ici = fill_indicators_sheet(pdf, is_lbb=False)  # Perf indicators for LBA
    set_importer_cycle_infos_google_sheets_boolean(ici)
    logger.info(f"END - {str(datetime.now())}- Generate indicators for LBA")



if __name__ == '__main__':
    # load_csv_perf_importer_cycle_infos("../../importer/data/perf_importer_cycle_infos.csv")
    # load_csv_perf_division_per_rome("../../importer/data/perf_division_per_rome.csv")
    # load_csv_perf_prediction_and_effective_h("../../importer/data/perf_prediction_and_effective_h.csv")
    run_main()