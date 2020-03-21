import urllib
import shutil
import calendar
import pandas as pd
import os.path
import numpy
from os import makedirs, remove, listdir
from datetime import date
import string

from labonneboite.importer import util as import_util
from labonneboite.importer.jobs.common import logger
from labonneboite.importer import settings as importer_settings
from labonneboite.scripts.impact_retour_emploi.google_sheets_report import GoogleSheetReport, generate_google_sheet_service

TABLE_NAME = 'logs_activity_dpae_clean'

#https://docs.google.com/spreadsheets/d/1kx-mxCaXIkys3hU4El4K7a6JBwzrdF75X4U8igqLB4I/edit?folder=1QFm0t2weoUjTsl-FPYUj94__zq_mZq0h#gid=0
FIRST_SPREADSHEET_ID = '1kx-mxCaXIkys3hU4El4K7a6JBwzrdF75X4U8igqLB4I'

#https://docs.google.com/spreadsheets/d/1gbvFvFEEugCmPhsAdoRZEdjfEl579uUnmf5MIryaVB8/edit#gid=0
SECOND_SPREADSHEET_ID = '1gbvFvFEEugCmPhsAdoRZEdjfEl579uUnmf5MIryaVB8'

class PrepareDataForGoogleSheetReport:

    def __init__(self):
        self.dpae_folder_path = importer_settings.INPUT_SOURCE_FOLDER

    def get_data_first_sheet(self):
        
        ### FIRST SHEET : https://docs.google.com/spreadsheets/d/1kx-mxCaXIkys3hU4El4K7a6JBwzrdF75X4U8igqLB4I/edit?folder=1QFm0t2weoUjTsl-FPYUj94__zq_mZq0h#gid=0
        # 1st column : Nb IDPE unique ayant accédé à LBB
        self.df_evol_idpe_connect = self.get_df_evol_idpe_connect()
        
        # 2nd column : Nb d'IDPE unique ayant déplié une fiche entreprise 
        self.df_evol_idpe_connect_sign_afficher_details = self.get_df_evol_idpe_connect_sign(did_specific_activity='afficher-details')
        
        # 3rd column : Nb d'IDPE unique ayant consulté une page entreprise
        self.df_evol_idpe_connect_sign_details = self.get_df_evol_idpe_connect_sign(did_specific_activity='details')

        # 4th column : Not data yet but : Nb d'IDPE unique ayant accédé à la première étape de "Je postule"

        # 5th column : Nb IDPE unique ayant déplié une fiche entreprise, consulté une page entreprise, mis en Favoris une entreprise
        #               + Fourth column ( accédé à la première étape de JP)
        self.df_evol_idpe_connect_sign = self.get_df_evol_idpe_connect_sign()

        # 6th column : Nb d'embauche par mois ayant pour origine une activité d'usager connecté LBB (date de début/fin = date d'embauche)
        self.df_evol_dpae = self.get_df_evol_dpae()

        # 7th column is an empty column

        # 8th column : Nb candidatures JP
        self.df_nb_candidatures_jp = pd.read_csv(f'{self.dpae_folder_path}/dump_nb_candidatures_jp.csv',delimiter=';')
        
        # 9th column : Nb email unique ayant candidaté via Je postule
        self.df_nb_distinct_email_jp = pd.read_csv(f'{self.dpae_folder_path}/dump_nb_distinct_email_jp.csv',delimiter=';')

        # 10th column : Nb candidats ayant reçus une réponse via JP
        self.df_nb_candidates_with_answer_jp = pd.read_csv(f'{self.dpae_folder_path}/dump_nb_candidates_with_answer_jp.csv',delimiter=';')

        # 11th column : Délai moyen de réponse des recruteurs via JP (en jours)
        self.df_medium_delay_answer_jp = pd.read_csv(f'{self.dpae_folder_path}/dump_medium_delay_answer_jp.csv',delimiter=';')

    def get_data_second_sheet(self):

        ### SECOND SHEET : https://docs.google.com/spreadsheets/d/1gbvFvFEEugCmPhsAdoRZEdjfEl579uUnmf5MIryaVB8/edit#gid=0
        self.df_evol_nb_dpae_hiring_and_activity_date = self.get_df_evol_nb_dpae_hiring_and_activity_date()

        print('Getting infos and datas from SQL done !')

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

    def get_df_evol_nb_dpae_hiring_and_activity_date(self):
        # GET the evolution of the number of dpae with LBB activity
        engine = import_util.create_sqlalchemy_engine()
        query = 'SELECT count(idutilisateur_peconnect) as count_dpae_lbb, concat(YEAR(date_activite),"-",MONTH(date_activite)) as date_month_activite,concat(YEAR(date_embauche),"-",MONTH(date_embauche)) as date_month_embauche \
                 FROM logs_activity_dpae_clean \
                 GROUP BY date_month_embauche, date_month_activite \
                 ORDER BY date_month_embauche;'
        df_evol_nb_dpae_hiring_and_activity_date = pd.read_sql_query(query, engine)
        engine.close()
        return df_evol_nb_dpae_hiring_and_activity_date

    def prepare_google_sheet_data(self):
        
        #Merge all datas requested before on the field 'date_month'
        df_by_month = self.df_evol_idpe_connect.merge(
            self.df_evol_idpe_connect_sign_afficher_details, how='outer').merge(
            self.df_evol_idpe_connect_sign_details, how='outer').merge(
            self.df_evol_idpe_connect_sign, how='outer').merge(
            self.df_evol_dpae, how='outer').merge(
            self.df_nb_candidatures_jp, how='outer').merge(
            self.df_nb_distinct_email_jp, how='outer').merge(
            self.df_nb_candidates_with_answer_jp, how='outer').merge(
            self.df_medium_delay_answer_jp, how='outer')

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

        #FIXME : When datas will be available
        df_by_month['count_id_pe_firststep_jp'] = 0

        df_by_month['empty_column'] = None

        df_by_month['count_distinct_activity'] = df_by_month['count_distinct_activity'] + df_by_month['count_id_pe_firststep_jp']

        df = self.create_columns('month', df_by_month, df_by_month['date_month'])

        ORDERING_COLUMN = [
            'date_begin',
            'date_end',
            'count_distinct_idpe',
            'count_distinct_activity_afficher_details',
            'count_distinct_activity_details',
            'count_id_pe_firststep_jp',
            'count_distinct_activity',
            'count_dpae_lbb',
            'empty_column',
            'count_jp_applications',
            'count_distint_email',
            'count_distinct_candidates_with_answer',
            'delay_answer_average',
        ]

        # Clean unecessary column
        df = df[ORDERING_COLUMN]

        # Ordering column
        df = df.loc[:, ORDERING_COLUMN]

        # clean NaN data
        df = df.replace(numpy.nan, '', regex=True)

        # Define ValueJSON body to insert in Google Sheets
        df_values_to_insert = {'values': df.values.tolist()}

        return df_values_to_insert

    def prepare_2nd_google_sheet_data(self):

        
        #Rename the date of the month by adding a '0' when needed
        #The dates in columns and indexes look like : 
        #['2018-10', '2018-8', '2018-9', '2018-11', '2018-12', '2019-1',
        # '2019-10', '2019-2', '2019-3', '2019-4', '2019-5', '2019-6', '2019-7',
        # '2019-8', '2019-9', '2019-11', '2019-12', '2020-1', '2020-2', '2020-3']
        #
        # ==> It needs to be turned into 'YYYY-MM' FROM 'YYYY-M' (2019-1 for example)
        def clean_dates_list(date_list):
            clean_list = []
            for row in date_list:
                if len(row) != 7:
                    stripped_index = row.split('-')
                    clean_list.append(f"{stripped_index[0]}-0{stripped_index[1]}")
                else:
                    clean_list.append(row)

            return clean_list

        # Prepare rows for dataframe
        rows = self.df_evol_nb_dpae_hiring_and_activity_date.date_month_activite.unique()

        #Prepare columns for dataframe
        columns = self.df_evol_nb_dpae_hiring_and_activity_date.date_month_embauche.unique()
        
        df = pd.DataFrame(columns=columns, index=rows)
        for index, row in self.df_evol_nb_dpae_hiring_and_activity_date.iterrows():
            df.loc[row['date_month_activite'], row['date_month_embauche']] = row['count_dpae_lbb']

        #Rename columns dates names
        df.index = clean_dates_list(df.index)
        df.columns = clean_dates_list(df.columns)

        #Sort dataframe by column name and row index for the date to be in the right order
        df = df.reindex(sorted(df.columns), axis=1)
        df = df.sort_index()

        df = df.fillna(0)

        #For the values to insert, we also need the columns names and index name to insert into google sheets
        values_to_insert = []

        #columns        
        columns = df.columns.tolist()
        columns.insert(0,'')
        values_to_insert.append(columns)

        #indexes + values of dataframe
        i = 0
        for row in df.values.tolist():
            row.insert(0,df.index[i])
            values_to_insert.append(row)
            i += 1

        df_values_to_insert = {'values': values_to_insert}
        return df_values_to_insert

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

def run_main():

    data_preparation_for_google_sheets = PrepareDataForGoogleSheetReport()

    service = generate_google_sheet_service()

    #First sheet 

    #data_preparation_for_google_sheets.get_data_first_sheet()
    #values_to_insert_first_sheet = data_preparation_for_google_sheets.prepare_google_sheet_data()

    #first_sheet_report = GoogleSheetReport(
    #    service=service,
    #    spreadsheet_id= FIRST_SPREADSHEET_ID,
    #    start_cell= 'A2',
    #    values= values_to_insert_first_sheet        
    #)
    #first_sheet_report.write_data_into_sheet()

    #Second sheet 

    data_preparation_for_google_sheets.get_data_second_sheet()
    values_to_insert_second_sheet = data_preparation_for_google_sheets.prepare_2nd_google_sheet_data()

    second_sheet_report = GoogleSheetReport(
        service=service,
        spreadsheet_id= SECOND_SPREADSHEET_ID,
        start_cell= 'B5',
        values= values_to_insert_second_sheet        
    )
    second_sheet_report.write_data_into_sheet()


if __name__ == '__main__':
    run_main()