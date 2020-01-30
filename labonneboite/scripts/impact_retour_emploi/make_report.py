import urllib
import shutil
import calendar
from os import makedirs, remove, listdir
import os.path
from datetime import date
import pandas as pd
import openpyxl
import openpyxl.styles
from sqlalchemy import create_engine
from labonneboite.scripts.impact_retour_emploi.scripts_charts import charts as charts
from labonneboite.scripts.impact_retour_emploi.scripts_charts import fr_charts as fr
from labonneboite.scripts.impact_retour_emploi.scripts_charts import grand_public as gd
from labonneboite.importer import util as import_util
from labonneboite.importer.jobs.common import logger
from labonneboite.scripts.impact_retour_emploi.settings_path_charts import JOIN_ON_SIREN, SPREADSHEET_ID, ORDERING_COLUMN, TITLE_GOOGLE_SHEET
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import numpy

ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

# FIXME : Refacto all files about the creation of charts and pasting on sheets (<3 Joris)
table_name_act_dpae = 'act_dpae_clean_siren' if JOIN_ON_SIREN is True else 'act_dpae_clean'


def get_infos_from_sql():
    # Get all joined activity logs and dpae CLEAN and NO DUPLICATES
    engine = import_util.create_sqlalchemy_engine()

    # GET the evolution of the number of dpae with LBB activity
    query = f'SELECT count(idutilisateur_peconnect) as count_dpae_lbb, concat(MONTH(date_activite),"-",YEAR(date_activite)) as date_month \
    FROM {table_name_act_dpae}\
    GROUP BY MONTH(date_activite), YEAR(date_activite)\
    ORDER BY YEAR(date_activite), MONTH(date_activite);'

    df_evol_dpae = pd.read_sql_query(query, engine)

    # Get the evolution of number of IDPEC which log into LBB
    query = '''
    SELECT count(DISTINCT idutilisateur_peconnect) as count_distinct_idpe, concat(MONTH(dateheure),"-",YEAR(dateheure)) as date_month
    FROM idpe_connect
    GROUP BY MONTH(dateheure), YEAR(dateheure)
    ORDER BY YEAR(dateheure), MONTH(dateheure);
    '''

    df_evol_idpe_connect = pd.read_sql_query(query, engine)

    # Get the evolution of the number of significative activities about a company
    query_ter = '''
    SELECT count(DISTINCT idutilisateur_peconnect) as count_distinct_activity ,concat(MONTH(dateheure),"-",YEAR(dateheure)) as date_month
    FROM activity_logs
    GROUP BY MONTH(dateheure), YEAR(dateheure)
    ORDER BY YEAR(dateheure), MONTH(dateheure);
    '''
    df_evol_idpe_connect_sign = pd.read_sql_query(query_ter, engine)

    print('Getting infos and datas from SQL done !')

    return df_evol_dpae, df_evol_idpe_connect,  df_evol_idpe_connect_sign


def make_google_sheet_data(df_evol_dpae, df_evol_idpe_connect, df_evol_idpe_connect_sign):

    # Join all the data we need
    df_by_month_x1 = df_evol_dpae.set_index('date_month').join(
        df_evol_idpe_connect.set_index('date_month'), how='outer')

    df_by_month = df_by_month_x1.join(
        df_evol_idpe_connect_sign.set_index('date_month'), how='outer')
    df_by_month.reset_index(inplace=True)

    df_date_month = df_by_month['date_month']

    semester_year = []  # Formatting
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
    # Get count by semester
    df_by_semester = df_by_month.set_index('semester').sum(level='semester')

    # Add additionnal column
    df_by_semester.reset_index(inplace=True)
    date_begin = []
    date_end = []
    tre_min = []
    tre_max = []
    date_semester = df_by_semester['semester']
    i = 0
    while i < len(date_semester):
        sem, year = date_semester[i].split('-')
        if sem == '1':  # first semester
            date_begin.append('01/01/'+year)
            date_end.append('30/06/'+year)
        else:
            date_begin.append('01/07/'+year)
            date_end.append('31/12/'+year)
        i += 1
        gline = str(i+1)
        tre_min.append('=F'+gline+'/D'+gline)  # Calulating TRE
        tre_max.append('=F'+gline+'/E'+gline)

    df_by_semester['date_begin'] = date_begin
    df_by_semester['date_end'] = date_end
    df_by_semester['tre_min'] = tre_min
    df_by_semester['tre_max'] = tre_max
    df_by_semester['count_postule'] = ""  # TODO find a way to get the value

    # Clean unecessary column
    df_by_semester = df_by_semester.drop(columns=['month', 'year', 'semester'])

    # Ordering column
    df_by_semester = df_by_semester.loc[:, ORDERING_COLUMN]

    # Get count by year
    df_by_year = df_by_month.set_index('year').sum(level='year')

    df_by_year.reset_index(inplace=True)
    date_begin = []
    date_end = []
    tre_min = []
    tre_max = []
    date_year = df_by_year['year']
    i = 0

    while i < len(date_year):
        year = str(date_year[i])
        i += 1
        gline = str(i+1)
        date_begin.append('01/01/'+year)
        date_end.append('31/12/'+year)
        tre_min.append('=F'+gline+'/D'+gline)  # Calulating TRE
        tre_max.append('=F'+gline+'/E'+gline)

    df_by_year['date_begin'] = date_begin
    df_by_year['date_end'] = date_end
    df_by_year['tre_min'] = tre_min
    df_by_year['tre_max'] = tre_max
    df_by_year['count_postule'] = ""  # TODO find a way to get the value

    # Clean unecessary column
    df_by_year = df_by_year.drop(columns=['year', 'month'])

    # Ordering column
    df_by_year = df_by_year.loc[:, ORDERING_COLUMN]

    # Get cumulative sum by month
    df_cumulative_by_month = df_by_month.set_index('date_month').cumsum()

    df_cumulative_by_month.reset_index(inplace=True)
    date_begin = []
    date_end = []
    tre_min = []
    tre_max = []
    date_month = df_cumulative_by_month['date_month']
    i = 0
    first_month, firt_year = date_month[0].split('-')
    first_date = '01/'+first_month+'/'+firt_year
    while i < len(date_month):
        month, year = date_month[i].split('-')
        i += 1
        gline = str(i+1)
        date_begin.append(first_date)
        date_end.append(str(calendar.monthrange(
            int(year), int(month))[1])+'/'+month+'/'+year)
        tre_min.append('=F'+gline+'/D'+gline)  # Calulating TRE
        tre_max.append('=F'+gline+'/E'+gline)

    df_cumulative_by_month['date_begin'] = date_begin
    df_cumulative_by_month['date_end'] = date_end
    df_cumulative_by_month['tre_min'] = tre_min
    df_cumulative_by_month['tre_max'] = tre_max
    # TODO find a way to get the value
    df_cumulative_by_month['count_postule'] = ""

    # Clean unecessary column
    df_cumulative_by_month = df_cumulative_by_month.drop(
        columns=['month', 'year', 'semester'])

    # Ordering column
    df_cumulative_by_month = df_cumulative_by_month.loc[:, ORDERING_COLUMN]

    date_begin = []
    date_end = []
    tre_min = []
    tre_max = []
    date_month = df_by_month['date_month']
    i = 0
    while i < len(date_month):
        month, year = date_month[i].split('-')
        i += 1
        gline = str(i+1)
        date_begin.append('01/'+month+'/'+year)
        date_end.append(str(calendar.monthrange(
            int(year), int(month))[1])+'/'+month+'/'+year)
        tre_min.append('=F'+gline+'/D'+gline)  # Calulating TRE
        tre_max.append('=F'+gline+'/E'+gline)

    df_by_month['date_begin'] = date_begin
    df_by_month['date_end'] = date_end
    df_by_month['tre_min'] = tre_min
    df_by_month['tre_max'] = tre_max
    df_by_month['count_postule'] = ""  # TODO find a way to get the value

    # Clean unecessary column
    df_by_month = df_by_month.drop(
        columns=['semester', 'date_month', 'month', 'year'])
    # Ordering column
    df_by_month = df_by_month.loc[:, ORDERING_COLUMN]

    return df_by_month, df_by_semester, df_by_year, df_cumulative_by_month


def generate_google_sheet_service():

    # https://developers.google.com/sheets/api/guides/authorizing
    # Delete the file token.pickle if the scopes changes
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    TOKEN_FILE = 'token.pickle'

    # Put the credentials file on the root of the labonneboite project
    CREDENTIAL_FILE = 'credentials.json'

    # Check the validity of the token
    credentials = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            credentials = pickle.load(token)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIAL_FILE, SCOPES)
            credentials = flow.run_local_server(port=10800)
    # Save the credentials for the next run
    with open(TOKEN_FILE, 'wb') as token:
        pickle.dump(credentials, token)

    # Connexion to the Google Sheet
    return build('sheets', 'v4', credentials=credentials, cache_discovery=False)


def write_data_into_sheet(google_service, sheet, df_data):

    # clean NaN data
    df_data = df_data.replace(numpy.nan, '', regex=True)

    # Clear sheet
    range_all = '{0}!A1:Z'.format(sheet['title'])
    google_service.spreadsheets().values().clear(
        spreadsheetId=SPREADSHEET_ID, range=range_all, body={}).execute()

    # Generate title
    # Calculate range data
    range_ = sheet['title'] + '!'+'A1:H1'
    # Define ValueJSON body
    value_range_body = {'values': TITLE_GOOGLE_SHEET}
    # Execute update
    request = google_service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID, range=range_, valueInputOption='USER_ENTERED', body=value_range_body)
    request.execute()

    # Insert Data
    # Calculate range data
    range_ = sheet['title'] + '!'+'A2:H'+str(len(df_data)+2)
    # Define ValueJSON body
    value_range_body = {'values': df_data.values.tolist()}
    # Execute update
    request = google_service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID, range=range_, valueInputOption='USER_ENTERED', body=value_range_body)
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

    # Writing the 2nd sheet (by semester)
    sheet_name = list_sheets[1]['properties']
    write_data_into_sheet(google_service, sheet_name, df_by_semester)

    # Writing the 3rd sheet (by year)
    sheet_name = list_sheets[2]['properties']
    write_data_into_sheet(google_service, sheet_name, df_by_year)

    # Writing the 4th sheet (cumulative by month)
    sheet_name = list_sheets[3]['properties']
    write_data_into_sheet(google_service, sheet_name, df_cumulative_by_month)


def run_main():

    df_evol_dpae, df_evol_idpe_connect,  df_evol_idpe_connect_sign = get_infos_from_sql()
    df_by_month, df_by_semester, df_by_year, df_cumulative_by_month = make_google_sheet_data(
        df_evol_dpae, df_evol_idpe_connect,  df_evol_idpe_connect_sign)
    make_google_sheet_report(df_by_month, df_by_semester,
                             df_by_year, df_cumulative_by_month)


if __name__ == '__main__':
    run_main()
