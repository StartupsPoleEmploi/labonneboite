import urllib
import shutil
import calendar
from os import makedirs, remove, listdir
import os.path
from datetime import date
import pandas as pd
from sqlalchemy import create_engine
from labonneboite.importer import util as import_util
from labonneboite.importer.jobs.common import logger
from labonneboite.scripts.impact_retour_emploi.settings SPREADSHEET_ID, ORDERING_COLUMN
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import numpy
from utils_make_report import generate_google_sheet_service


# FIXME : Refacto all files about the creation of charts and pasting on sheets (<3 Joris)
TABLE_NAME = 'logs_activity_dpae_clean'

class MakeGoogleSheetsReport:

    def __init__(self):
        # Get all joined activity logs and dpae CLEAN and NO DUPLICATES
        self.df_evol_dpae = self.get_df_evol_dpae()
        self.df_evol_idpe_connect = self.get_df_evol_idpe_connect()
        self.df_evol_idpe_connect_sign = self.get_df_evol_idpe_connect_sign()

        print('Getting infos and datas from SQL done !')

        self.df_month = self.prepare_google_sheet_data() 

    def get_df_evol_dpae(self):
        # GET the evolution of the number of dpae with LBB activity
        engine = import_util.create_sqlalchemy_engine()
        query = 'SELECT count(idutilisateur_peconnect) as count_dpae_lbb, concat(MONTH(date_activite),"-",YEAR(date_activite)) as date_month \
                FROM logs_activity_dpae_clean\
                GROUP BY MONTH(date_activite), YEAR(date_activite)\
                ORDER BY YEAR(date_activite), MONTH(date_activite);'
        df_evol_dpae = pd.read_sql_query(query, engine)
        engine.close()
        return df_evol_dpae

    def get_df_evol_idpe_connect(self):
        # Get the evolution of number of IDPEC which log into LBB
        engine = import_util.create_sqlalchemy_engine()
        query = 'SELECT count(DISTINCT idutilisateur_peconnect) as count_distinct_idpe, concat(MONTH(dateheure),"-",YEAR(dateheure)) as date_month\
                FROM logs_idpe_connect\
                GROUP BY MONTH(dateheure), YEAR(dateheure)\
                ORDER BY YEAR(dateheure), MONTH(dateheure);'
        df_evol_idpe_connect = pd.read_sql_query(query, engine)
        engine.close()
        return df_evol_idpe_connect

    def get_df_evol_idpe_connect_sign(self):
        # Get the evolution of the number of significative activities about a company
        engine = import_util.create_sqlalchemy_engine()
        query = 'SELECT count(DISTINCT idutilisateur_peconnect) as count_distinct_activity, concat(MONTH(dateheure),"-",YEAR(dateheure)) as date_month\
                    FROM logs_activity\
                    GROUP BY MONTH(dateheure), YEAR(dateheure)\
                    ORDER BY YEAR(dateheure), MONTH(dateheure);'
        df_evol_idpe_connect_sign = pd.read_sql_query(query, engine)
        engine.close()
        return df_evol_idpe_connect_sign


    def prepare_google_sheet_data(self):

        # Prepare main df needed by other df
        df_by_month = prepare_main_data_frame()

        # Clean df by month
        df_by_month = clean_main_data_frame(df_by_month)

        return df_by_month

    def prepare_main_data_frame(self):

        # Join all the data we need
        df_by_month_x1 = self.df_evol_dpae.set_index('date_month').join(
            self.df_evol_idpe_connect.set_index('date_month'), how='outer')

        df_by_month = df_by_month_x1.join(
            self.df_evol_idpe_connect_sign.set_index('date_month'), how='outer')
        df_by_month.reset_index(inplace=True)

        df_date_month = df_by_month['date_month']

        semester_year = [] #Formatting
        list_month = []
        list_year = []
        i = 0

        while i < len(df_date_month):
            month, year = df_date_month[i].split('-')
            semester_year.append(str((int(month)-1)//6 + 1)+'-'+year)
            list_month.append(int(month))
            list_year.append(int(year))
            i += 1

        df_by_month['semester'] = semester_year
        df_by_month['month'] = list_month
        df_by_month['year'] = list_year

        df_by_month = df_by_month.sort_values(by=['year', 'month'])
        df_by_month = df_by_month.reset_index(drop=True)

        return df_by_month
    # Create the colum needed for any sheet (date_begin, date_end, tre_max, and 'count_postule for the moment )

    # Clean and format df_by_month
    def clean_main_data_frame(df_by_month):

        df_ = create_columns('month', df_by_month, df_by_month['date_month'])

        # Clean unecessary column
        df_ = df_.drop(
            columns=['semester', 'date_month', 'month', 'year'])
        # Ordering column
        df_ = df_.loc[:, ORDERING_COLUMN]

        return df_


def create_columns(type_, df_initial, df_date):

    df_ = df_initial

    date_begin = []
    date_end = []
    tre_min = []
    tre_max = []

    i = 0
    while i < len(df_date):
        j = i if type_ != 'cumulative_month' else 0
        date_begin.append(calculate_date_begin(type_, df_date[j]))
        date_end.append(calculate_date_end(type_, df_date[i]))
        i += 1
        gline = str(i+1)
        tre_min.append('=F'+gline+'/D'+gline)  # Calulating TRE
        tre_max.append('=F'+gline+'/E'+gline)

    df_['date_begin'] = date_begin
    df_['date_end'] = date_end
    # TODO find a way to get the value
    df_['count_postule'] = ""

    return df_

# Switch to calculat the date of begin depends of type of df


def calculate_date_begin(type_, date_):

    switcher = {
        'semester': switch_semester_begin,
        'year': swich_year_begin,
        'cumulative_month': swich_month_begin,
        'month': swich_month_begin
    }

    return switcher.get(type_)(type_, date_)

# Rule for calulate the first date of semester


def switch_semester_begin(type_, date_):
    sem, year = date_.split('-')
    if sem == '1':  # first semester
        return '01/01/'+year
    else:
        return '01/07/'+year

# Rule for calulate the first date of month


def swich_month_begin(type_, date_):
    month, year = date_.split('-')
    return '01/'+month+'/'+year

# Rule for calulate the first date of year


def swich_year_begin(type_, date_):
    return '01/01/'+str(date_)

# Switch to calculat the date of end depends of type of df


def calculate_date_end(type_, date_):

    switcher = {
        'semester': switch_semester_end,
        'year': swich_year_end,
        'cumulative_month': swich_month_end,
        'month': swich_month_end
    }

    return switcher.get(type_)(type_, date_)

# Rule for calulate the last date of semester


def switch_semester_end(type_, date_):
    sem, year = date_.split('-')
    if sem == '1':  # first semester
        return '30/06/'+year
    else:
        return '31/12/'+year

# Rule for calulate the last date of month


def swich_month_end(type_, date_):
    month, year = date_.split('-')
    return str(calendar.monthrange(int(year), int(month))[1])+'/'+month+'/'+year

# Rule for calulate the last date of year


def swich_year_end(type_, date_):
    return '31/12/'+str(date_)


def write_data_into_sheet(google_service, sheet, df_data):

    # clean NaN data
    df_data = df_data.replace(numpy.nan, '', regex=True)

    # Clear sheet
    range_all = '{0}!A2:Z'.format(sheet['title'])
    google_service.spreadsheets().values().clear(
        spreadsheetId=SPREADSHEET_ID,
        range=range_all, 
        body={}).execute()

    # Generate title
    # # Calculate range data
    # range_ = sheet['title'] + '!'+'A1:H1'
    # # Define ValueJSON body
    # value_range_body = {'values': TITLE_GOOGLE_SHEET}
    # # Execute update
    # request = google_service.spreadsheets().values().update(
    #     spreadsheetId=SPREADSHEET_ID, range=range_, valueInputOption='USER_ENTERED', body=value_range_body)
    # request.execute()

    # Insert Data

    # Calculate range data
    range_ = sheet['title'] + '!'+'A2:H'+str(len(df_data)+2)

    # Define ValueJSON body
    value_range_body = {'values': df_data.values.tolist()}

    # Execute update
    request = google_service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID, 
        range=range_, 
        valueInputOption='USER_ENTERED', 
        body=value_range_body
    )

    request.execute()


def make_google_sheet_report(df_by_month, df_by_semester, df_by_year, df_cumulative_by_month):
    # def make_google_sheet_report():

    google_service = generate_google_sheet_service()

    # Get the list of our sheets properties (title)
    list_sheets = google_service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID,
                                                    fields="sheets/properties").execute()['sheets']

    # Writing the 1st sheet (by month)
    sheet_name = list_sheets[0]['properties']
    write_data_into_sheet(google_service, sheet_name, df_by_month)

def run_main():

    make_google_sheet_report = MakeGoogleSheetsReport()
    df_by_month, df_by_semester, df_by_year, df_cumulative_by_month = make_google_sheet_data(
        df_evol_dpae, df_evol_idpe_connect,  df_evol_idpe_connect_sign)
    make_google_sheet_report(df_by_month, df_by_semester,
                             df_by_year, df_cumulative_by_month)


if __name__ == '__main__':
    run_main()
