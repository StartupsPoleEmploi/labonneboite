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
from labonneboite.scripts.impact_retour_emploi.settings import SPREADSHEET_ID, ORDERING_COLUMN
import numpy
from utils_make_report import generate_google_sheet_service

TABLE_NAME = 'logs_activity_dpae_clean'

# PI 
'''
        details = consulter une page entreprise 
        afficher-details = déplier fiche entreprise 
        premiere étape JP --> Récup datas ailleurs
'''

class MakeGoogleSheetsReport:

    def __init__(self):
        # First column : Nb IDPE unique ayant accédé à LBB
        self.df_evol_idpe_connect = self.get_df_evol_idpe_connect()
        
        # Second column : Nb d'IDPE unique ayant déplié une fiche entreprise 
        self.df_evol_idpe_connect_sign_afficher_details = self.get_df_evol_idpe_connect_sign(did_specific_activity='afficher-details')
        
        #Third column : Nb d'IDPE unique ayant consulté une page entreprise
        self.df_evol_idpe_connect_sign_details = self.get_df_evol_idpe_connect_sign(did_specific_activity='details')

        #Fourth column : Not data yet but : Nb d'IDPE unique ayant accédé à la première étape de "Je postule"

        #Fifth column : Nb IDPE unique ayant déplié une fiche entreprise, consulté une page entreprise, mis en Favoris une entreprise ou accédé à la première étape de JP
        #               + Fourth column
        self.df_evol_idpe_connect_sign = self.get_df_evol_idpe_connect_sign()

        # Sixth column : Nb d'embauche par mois ayant pour origine une activité d'usager connecté LBB (date de début/fin = date d'embauche)
        self.df_evol_dpae = self.get_df_evol_dpae()

        print('Getting infos and datas from SQL done !')

        self.df_month = self.prepare_google_sheet_data() 


    def get_df_evol_dpae(self):
        # GET the evolution of the number of dpae with LBB activity
        engine = import_util.create_sqlalchemy_engine()
        query = 'SELECT count(idutilisateur_peconnect) as count_dpae_lbb, concat(MONTH(date_embauche),"-",YEAR(date_embauche)) as date_month \
                FROM logs_activity_dpae_clean\
                GROUP BY MONTH(date_embauche), YEAR(date_embauche)\
                ORDER BY YEAR(date_embauche), MONTH(date_embauche);'
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

    def get_df_evol_idpe_connect_sign(self, did_specific_activity = None):
        # Get the evolution of the number of significative activities about a company
        engine = import_util.create_sqlalchemy_engine()

        if did_specific_activity is not None:
            specific_column_name = did_specific_activity.replace('-','_')
            column_name = f'count_distinct_activity_{specific_column_name}'
        else:
            column_name = 'count_distinct_activity'

        query = f'SELECT count(DISTINCT idutilisateur_peconnect) as {column_name},\
                        concat(MONTH(dateheure),"-",YEAR(dateheure)) as date_month\
                 FROM logs_activity '

        if did_specific_activity is not None:
            query += f'WHERE nom="{did_specific_activity}"'

        query += ' GROUP BY MONTH(dateheure), YEAR(dateheure)\
                   ORDER BY YEAR(dateheure), MONTH(dateheure);'
        df_evol_idpe_connect_sign = pd.read_sql_query(query, engine)
        engine.close()
        return df_evol_idpe_connect_sign


    def prepare_google_sheet_data(self):

        # Prepare main df needed by other df
        df_by_month = self.prepare_main_data_frame()

        # Clean df by month
        df_by_month = self.clean_main_data_frame(df_by_month)

        return df_by_month

    def prepare_main_data_frame(self):
        
        #Merge all datas requested before on the field 'date_month'
        df_by_month = self.df_evol_idpe_connect.merge(
            self.df_evol_idpe_connect_sign_afficher_details).merge(
            self.df_evol_idpe_connect_sign_details).merge(
            self.df_evol_idpe_connect_sign).merge(
            self.df_evol_dpae)

        df_by_month.reset_index(inplace=True)

        #Deal with different types of wanted dates
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

        df_by_month['count_postule'] = 0

        df_by_month['count_distinct_activity'] = df_by_month['count_distinct_activity'] + df_by_month['count_postule'] 

        return df_by_month

    # Clean and format df_by_month
    def clean_main_data_frame(self, df_by_month):

        df_ = self.create_columns('month', df_by_month, df_by_month['date_month'])

        # Clean unecessary column
        df_ = df_[ORDERING_COLUMN]

        # Ordering column
        df_ = df_.loc[:, ORDERING_COLUMN]

        return df_

    # Create the colum needed for any sheet (date_begin, date_end, tre_max, and 'count_postule for the moment )
    def create_columns(self, type_, df_initial, df_date):

        df_ = df_initial

        date_begin = []
        date_end = []

        i = 0
        while i < len(df_date):
            j = i if type_ != 'cumulative_month' else 0
            date_begin.append(self.calculate_date_begin(type_, df_date[j]))
            date_end.append(self.calculate_date_end(type_, df_date[i]))
            i += 1
            gline = str(i+1)

        df_['date_begin'] = date_begin
        df_['date_end'] = date_end

        return df_

    # Switch to calculat the date of begin depends of type of df
    def calculate_date_begin(self, type_, date_):

        switcher = {
            'semester': self.switch_semester_begin,
            'year': self.switch_year_begin,
            'cumulative_month': self.switch_month_begin,
            'month': self.switch_month_begin
        }

        return switcher.get(type_)(type_, date_)

    # Rule for calulate the first date of semester


    def switch_semester_begin(self, type_, date_):
        sem, year = date_.split('-')
        if sem == '1':  # first semester
            return '01/01/'+year
        else:
            return '01/07/'+year

    # Rule for calulate the first date of month


    def switch_month_begin(self, type_, date_):
        month, year = date_.split('-')
        return '01/'+month+'/'+year

    # Rule for calulate the first date of year


    def switch_year_begin(self, type_, date_):
        return '01/01/'+str(date_)

    # Switch to calculat the date of end depends of type of df
    def calculate_date_end(self, type_, date_):

        switcher = {
            'semester': self.switch_semester_end,
            'year': self.switch_year_end,
            'cumulative_month': self.switch_month_end,
            'month': self.switch_month_end
        }

        return switcher.get(type_)(type_, date_)

    # Rule for calulate the last date of semester
    def switch_semester_end(self, type_, date_):
        sem, year = date_.split('-')
        if sem == '1':  # first semester
            return '30/06/'+year
        else:
            return '31/12/'+year

    # Rule for calulate the last date of month
    def switch_month_end(self, type_, date_):
        month, year = date_.split('-')
        return str(calendar.monthrange(int(year), int(month))[1])+'/'+month+'/'+year

    # Rule for calulate the last date of year
    def switch_year_end(self, type_, date_):
        return '31/12/'+str(date_)

    def make_google_sheet_report(self):

        google_service = generate_google_sheet_service()

        # Get the list of our sheets properties (title)
        list_sheets = google_service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID,
                                                        fields="sheets/properties").execute()['sheets']

        # Writing the 1st sheet (by month)
        sheet_name = list_sheets[0]['properties']
        self.write_data_into_sheet(google_service, sheet_name, self.df_month)

    def write_data_into_sheet(self, google_service, sheet, df_data):

        # clean NaN data
        df_data = df_data.replace(numpy.nan, '', regex=True)

        # Clear sheet
        range_all = '{0}!A2:H'.format(sheet['title'])
        google_service.spreadsheets().values().clear(
            spreadsheetId=SPREADSHEET_ID,
            range=range_all, 
            body={}).execute()

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

def run_main():

    make_google_sheet_report = MakeGoogleSheetsReport()
    make_google_sheet_report.make_google_sheet_report()


if __name__ == '__main__':
    run_main()
