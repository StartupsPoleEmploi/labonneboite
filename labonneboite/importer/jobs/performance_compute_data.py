import csv
import numpy
import pandas as pd
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

dict_df = {}

#import donnée#######################################################################""

def load_csv_perf_division_per_rome(filename, delimiter=';'):
    #date_time_obj = datetime.datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S.%f')
    for row in load_data.load_csv_file(filename,delimiter):
        perf_div_per_rome = PerfDivisionPerRome(
            _id = row[0],
            importer_cycle_infos_id = row[1],
            naf = row[2],
            rome = row[3],
            threshold =  row[4],
            nb_bonne_boites = row[5]
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
            file_name =  row[4]
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
            is_a_bonne_boite = (row[15] == "True")
        )
        db_session.add(perf_importer_cycle_info)
        db_session.commit()


#cycle + naf #######################################################################""



def get_nb_entreprise_par_cycle_et_naf():
    engine = import_util.create_sqlalchemy_engine()
    query = 'SELECT importer_cycle_infos_id as cycle , codenaf as naf ,count(*) as nbTotal \
            FROM perf_prediction_and_effective_hirings ppaeh \
            GROUP BY importer_cycle_infos_id , codenaf;'
    df_nb_entreprise = pd.read_sql_query(query, engine)
    engine.close()
    return df_nb_entreprise

def get_nb_entreprise_par_cycle_et_naf_isLBB():
    engine = import_util.create_sqlalchemy_engine()
    query = 'SELECT importer_cycle_infos_id as cycle , codenaf as naf ,count(*) as nbTotalLBB \
            FROM perf_prediction_and_effective_hirings ppaeh \
            WHERE is_a_bonne_boite is true \
            GROUP BY importer_cycle_infos_id , codenaf;'
    df_nb_entreprise_isLBB = pd.read_sql_query(query, engine)
    engine.close()
    return df_nb_entreprise_isLBB


def get_sum_predict_par_cycle_et_naf(cycle,naf):
    engine = import_util.create_sqlalchemy_engine()
    query = f'SELECT importer_cycle_infos_id as cycle , codenaf as naf ,sum(lbb_nb_predicted_hirings) as sommeTotal \
            FROM perf_prediction_and_effective_hirings ppaeh \
            WHERE importer_cycle_infos_id = {cycle} and codenaf = "{naf}"  \
            GROUP BY importer_cycle_infos_id , codenaf;'
    df_sum_predict = pd.read_sql_query(query, engine)
    engine.close()
    return df_sum_predict


def get_predict_par_cycle_et_naf(cycle,naf):
    engine = import_util.create_sqlalchemy_engine()
    query = f'SELECT lbb_nb_predicted_hirings as predict, lbb_nb_effective_hirings as effective \
            FROM perf_prediction_and_effective_hirings \
            WHERE importer_cycle_infos_id = {cycle} and codenaf = "{naf}"  \
            ORDER BY lbb_nb_predicted_hirings desc '
    df_predict = pd.read_sql_query(query, engine)
    engine.close()
    return df_predict

def get_cycle_infos():
    engine = import_util.create_sqlalchemy_engine()
    query = f'SELECT id as cycle, execution_date as dateExecution \
            FROM perf_importer_cycle_infos ;'
    df_predict = pd.read_sql_query(query, engine)
    engine.close()
    return df_predict




def get_sum_predict_naf(row,i):
    df_predict = get_predict_par_cycle_et_naf(row["cycle"],row["naf"])
    df_sum_predict = get_sum_predict_par_cycle_et_naf(row["cycle"],row["naf"])
    if i == 100:
        df_predict['RMSE'] = df_predict.apply(lambda row: calcul_rmse(row), axis=1)
        return math.sqrt(df_predict['RMSE'].sum() / row['nbTotal'])
    df_head_predict =  df_predict.head(int(row['nbTotal']*i/100))
    if df_sum_predict['sommeTotal'].sum() == 0 :
        return 0
    return  df_head_predict['predict'].sum() / df_sum_predict['sommeTotal'].sum()

def get_prop_recrut_non_lbb(row):
    return  (row['nbTotal'] - row['nbTotalLBB'])/ row['nbTotal']
     
def calcul_rmse(row):
    return  math.pow((row['effective'] - row['predict']),2)


def lancement_requete_naf():
    df_nb_entreprise = get_nb_entreprise_par_cycle_et_naf()

    for i in range(10,110,10):
        df_nb_entreprise[f'sum{i}'] = df_nb_entreprise.apply(lambda row: get_sum_predict_naf(row,i), axis=1)

    df_nb_entreprise = df_nb_entreprise.rename(columns={'sum100':'RMSE'})

    df_nb_entreprise_isLBB  = get_nb_entreprise_par_cycle_et_naf_isLBB()
    df_result = pd.merge(df_nb_entreprise , df_nb_entreprise_isLBB , on=['cycle','naf'])
    df_result['propRecrutNonLBB'] = df_result.apply(lambda row: get_prop_recrut_non_lbb(row), axis=1)
    return df_result

#cycle + dep #######################################################################""


 

def get_nb_entreprise_par_cycle_et_dep():
    engine = import_util.create_sqlalchemy_engine()
    query = 'SELECT importer_cycle_infos_id as cycle , departement as dep ,count(*) as nbTotal \
            FROM perf_prediction_and_effective_hirings ppaeh \
            GROUP BY importer_cycle_infos_id , departement;'
    df_nb_entreprise = pd.read_sql_query(query, engine)
    engine.close()
    return df_nb_entreprise

def get_nb_entreprise_par_cycle_et_dep_isLBB():
    engine = import_util.create_sqlalchemy_engine()
    query = 'SELECT importer_cycle_infos_id as cycle , departement as dep ,count(*) as nbTotalLBB \
            FROM perf_prediction_and_effective_hirings ppaeh \
            WHERE is_a_bonne_boite is true \
            GROUP BY importer_cycle_infos_id , departement;'
    df_nb_entreprise_isLBB = pd.read_sql_query(query, engine)
    engine.close()
    return df_nb_entreprise_isLBB


def get_sum_predict_par_cycle_et_dep(cycle,dep):
    engine = import_util.create_sqlalchemy_engine()
    query = f'SELECT importer_cycle_infos_id as cycle , departement as dep ,sum(lbb_nb_predicted_hirings) as sommeTotal \
            FROM perf_prediction_and_effective_hirings ppaeh \
            WHERE importer_cycle_infos_id = {cycle} and departement = "{dep}"  \
            GROUP BY importer_cycle_infos_id , departement;'
    df_sum_predict = pd.read_sql_query(query, engine)
    engine.close()
    return df_sum_predict


def get_predict_par_cycle_et_dep(cycle,dep):
    engine = import_util.create_sqlalchemy_engine()
    query = f'SELECT lbb_nb_predicted_hirings as predict, lbb_nb_effective_hirings as effective \
            FROM perf_prediction_and_effective_hirings \
            WHERE importer_cycle_infos_id = {cycle} and departement = "{dep}"  \
            ORDER BY lbb_nb_predicted_hirings desc '
    df_predict = pd.read_sql_query(query, engine)
    engine.close()
    return df_predict

def get_sum_predict_dep(row,i):
    df_predict = get_predict_par_cycle_et_dep(row["cycle"],row["dep"])
    df_sum_predict = get_sum_predict_par_cycle_et_dep(row["cycle"],row["dep"])
    if i == 100:
        df_predict['RMSE'] = df_predict.apply(lambda row: calcul_rmse(row), axis=1)
        return math.sqrt(df_predict['RMSE'].sum() / row['nbTotal'])
    df_head_predict =  df_predict.head(int(row['nbTotal']*i/100))
    if df_sum_predict['sommeTotal'].sum() == 0 :
        return 0
    return  df_head_predict['predict'].sum() / df_sum_predict['sommeTotal'].sum()


def lancement_requete_dep():
    df_nb_entreprise = get_nb_entreprise_par_cycle_et_dep()

    for i in range(10,110,10):
        df_nb_entreprise[f'sum{i}'] = df_nb_entreprise.apply(lambda row: get_sum_predict_dep(row,i), axis=1)

    df_nb_entreprise = df_nb_entreprise.rename(columns={'sum100':'RMSE'})

    df_nb_entreprise_isLBB  = get_nb_entreprise_par_cycle_et_dep_isLBB()
    df_result = pd.merge(df_nb_entreprise , df_nb_entreprise_isLBB , on=['cycle','dep'])
    df_result['propRecrutNonLBB'] = df_result.apply(lambda row: get_prop_recrut_non_lbb(row), axis=1)
    return df_result

def prepare_google_sheet_data():
    df_naf = lancement_requete_naf()
    df_dep = lancement_requete_dep()
    df_cycle_infos = get_cycle_infos()
    df_naf = pd.merge(df_naf , df_cycle_infos , on=['cycle'])
    df_dep = pd.merge(df_dep , df_cycle_infos , on=['cycle'])
    df_naf['dateExecutionImp'] = df_naf['dateExecution'].dt.strftime('%d/%m/%Y')
    df_dep['dateExecutionImp'] = df_dep['dateExecution'].dt.strftime('%d/%m/%Y')


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
        'propRecrutNonLBB',
        'RMSE',
        'nbTotal',
        'nbTotalLBB',
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
        'propRecrutNonLBB',
        'RMSE',
        'nbTotal',
        'nbTotalLBB',
    ]

    # Clean unecessary column
    df_naf = df_naf[ORDERING_COLUMN_NAF]
    df_dep = df_dep[ORDERING_COLUMN_DEP]

    # Ordering column
    df_naf = df_naf.loc[:, ORDERING_COLUMN_NAF]
    df_dep = df_dep.loc[:, ORDERING_COLUMN_DEP]

    # clean NaN data
    df_naf = df_naf.replace(numpy.nan, '', regex=True)
    df_dep = df_dep.replace(numpy.nan, '', regex=True)

    # Define ValueJSON body to insert in Google Sheets
    values_to_insert_naf = {'values': df_naf.values.tolist()}
    values_to_insert_dep = {'values': df_dep.values.tolist()}

    return values_to_insert_naf , values_to_insert_dep


def main():
    #load_csv_perf_importer_cycle_infos("../../importer/data/perf_importer_cycle_infos.csv")
    #load_csv_perf_division_per_rome("../../importer/data/perf_division_per_rome.csv")
    #load_csv_perf_prediction_and_effective_h("../../importer/data/perf_prediction_and_effective_h.csv")
    values_to_insert_first_sheet , values_to_insert_second_sheet = prepare_google_sheet_data()
    service = generate_google_sheet_service()

    first_sheet_report = GoogleSheetReport(
        service=service,
        spreadsheet_id=settings.SPREADSHEET_IDS[2],
        sheet_index=0,
        start_cell='A2',
        values=values_to_insert_first_sheet
    )
    first_sheet_report.set_sheet_range()
    first_sheet_report.write_data_into_sheet()

    second_sheet_report = GoogleSheetReport(
        service=service,
        spreadsheet_id=settings.SPREADSHEET_IDS[2],
        sheet_index=1,
        start_cell='A2',
        values=values_to_insert_second_sheet
    )
    second_sheet_report.set_sheet_range()
    second_sheet_report.write_data_into_sheet()


if __name__ == '__main__':
    main()