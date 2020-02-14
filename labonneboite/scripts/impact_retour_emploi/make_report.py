import urllib
import shutil
import calendar
from os import makedirs, remove, listdir
import os.path
from datetime import date
import pandas as pd
from sqlalchemy import create_engine
from labonneboite.scripts.impact_retour_emploi.scripts_charts import charts as charts
from labonneboite.scripts.impact_retour_emploi.scripts_charts import fr_charts as fr
from labonneboite.scripts.impact_retour_emploi.scripts_charts import grand_public as gd
from labonneboite.importer import util as import_util
from labonneboite.importer.jobs.common import logger
from labonneboite.scripts.impact_retour_emploi.settings_path_charts import JOIN_ON_SIREN, SPREADSHEET_ID, ORDERING_COLUMN
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

    # Brepare main df needed by other df
    df_by_month = prepare_main_data_frame(
        df_evol_dpae, df_evol_idpe_connect, df_evol_idpe_connect_sign)

    # Get count by semester
    df_by_semester = make_google_sheet_data_by_semester(df_by_month)

    # Get count by year
    df_by_year = make_google_sheet_data_by_year(df_by_month)

    # Get cumulative sum by month
    df_cumulative_by_month = make_google_sheet_data_cumulative_by_month(
        df_by_month)

    # Clean df by month
    df_by_month = clean_main_data_frame(df_by_month)

    return df_by_month, df_by_semester, df_by_year, df_cumulative_by_month

# Build  the main dataframe by month need by the other dataframes


def prepare_main_data_frame(df_evol_dpae, df_evol_idpe_connect, df_evol_idpe_connect_sign):

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

    return df_by_month

# build and format the dataframe for the google sheet by semester


def make_google_sheet_data_by_semester(df_by_month):
    # Get count by semester
    df_by_semester = df_by_month.set_index('semester').sum(level='semester')

    # Add additionnal column
    df_by_semester.reset_index(inplace=True)
    df_by_semester = create_columns(
        'semester', df_by_semester, df_by_semester['semester'])

    # Clean unecessary column
    df_by_semester = df_by_semester.drop(columns=['month', 'year', 'semester'])

    # Ordering column
    df_by_semester = df_by_semester.loc[:, ORDERING_COLUMN]

    return df_by_semester

# build and format the dataframe for the google sheet by year


def make_google_sheet_data_by_year(df_by_month):

    # Get count by year
    df_by_year = df_by_month.set_index('year').sum(level='year')

    # Add additionnal column
    df_by_year.reset_index(inplace=True)
    df_by_year = create_columns('year', df_by_year, df_by_year['year'])

    # Clean unecessary column
    df_by_year = df_by_year.drop(columns=['year', 'month'])

    # Ordering column
    df_by_year = df_by_year.loc[:, ORDERING_COLUMN]

    return df_by_year

# build and format the dataframe for the google sheet cumulative count by month


def make_google_sheet_data_cumulative_by_month(df_by_month):
    # Get cumulative sum by month
    df_cumulative_by_month = df_by_month.set_index('date_month').cumsum()

    df_cumulative_by_month.reset_index(inplace=True)
    df_cumulative_by_month = create_columns(
        'cumulative_month', df_cumulative_by_month, df_cumulative_by_month['date_month'])

    # Clean unecessary column
    df_cumulative_by_month = df_cumulative_by_month.drop(
        columns=['month', 'year', 'semester'])

    # Ordering column
    df_cumulative_by_month = df_cumulative_by_month.loc[:, ORDERING_COLUMN]

    return df_cumulative_by_month

# Create the colum needed for any sheet (date_begin, date_end, tre_max, and 'count_postule for the moment )


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
    df_['tre_min'] = tre_min
    df_['tre_max'] = tre_max
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


# Clean and format df_by_month
def clean_main_data_frame(df_by_month):

    df_ = create_columns('month', df_by_month, df_by_month['date_month'])

    # Clean unecessary column
    df_ = df_.drop(
        columns=['semester', 'date_month', 'month', 'year'])
    # Ordering column
    df_ = df_.loc[:, ORDERING_COLUMN]

    return df_


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
    range_all = '{0}!A2:Z'.format(sheet['title'])
    google_service.spreadsheets().values().clear(
        spreadsheetId=SPREADSHEET_ID, range=range_all, body={}).execute()

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
