import numpy
import pandas as pd

from labonneboite.conf import settings
from labonneboite.importer import util as import_util
from labonneboite.importer.jobs.common import logger
from labonneboite.importer import settings as importer_settings
from labonneboite.scripts.impact_retour_emploi.google_sheets_report import GoogleSheetReport, generate_google_sheet_service
from labonneboite.importer.models.computing import LogsActivityDPAEClean

TABLE_NAME = LogsActivityDPAEClean.__tablename__


class PrepareDataForGoogleSheetReport:

    def __init__(self):
        self.csv_jp_folder_path = importer_settings.INPUT_SOURCE_FOLDER

    def get_data_first_sheet(self):

        # FIRST SHEET : https://docs.google.com/spreadsheets/d/1kx-mxCaXIkys3hU4El4K7a6JBwzrdF75X4U8igqLB4I/edit?folder=1QFm0t2weoUjTsl-FPYUj94__zq_mZq0h#gid=0
        # 1st column : Nb IDPE unique ayant accédé à LBB
        self.df_evol_idpe_connect = self.get_df_evol_idpe_connect()

        # 2nd column : Nb d'IDPE unique ayant déplié une fiche entreprise
        self.df_evol_idpe_connect_sign_afficher_details = self.get_df_evol_idpe_connect_sign(
            did_specific_activity='afficher-details')

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
        self.df_nb_candidatures_jp = pd.read_csv(f'{self.csv_jp_folder_path}/dump_nb_candidatures_jp.csv', delimiter=';')

        # 9th column : Nb email unique ayant candidaté via Je postule
        self.df_nb_distinct_email_jp = pd.read_csv(f'{self.csv_jp_folder_path}/dump_nb_distinct_email_jp.csv', delimiter=';')

        # 10th column : Nb candidats ayant reçus une réponse via JP
        self.df_nb_candidates_with_answer_jp = pd.read_csv(
            f'{self.csv_jp_folder_path}/dump_nb_candidates_with_answer_jp.csv', delimiter=';')

        # 11th column : Délai moyen de réponse des recruteurs via JP (en jours)
        self.df_medium_delay_answer_jp = pd.read_csv(f'{self.csv_jp_folder_path}/dump_medium_delay_answer_jp.csv', delimiter=';')

        logger.info("Data for first sheet ready")

    def get_data_second_sheet(self):

        # SECOND SHEET : https://docs.google.com/spreadsheets/d/1gbvFvFEEugCmPhsAdoRZEdjfEl579uUnmf5MIryaVB8/edit#gid=0
        self.df_evol_nb_dpae_hiring_and_activity_date = self.get_df_evol_nb_dpae_hiring_and_activity_date()

        logger.info("Data for second sheet ready")

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

    def get_df_evol_idpe_connect_sign(self, did_specific_activity=None):
        # Get the evolution of the number of significative activities about a company
        engine = import_util.create_sqlalchemy_engine()

        if did_specific_activity is not None:
            specific_column_name = did_specific_activity.replace('-', '_')
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
        def clean_date(row):
            date = row['date_month']
            stripped_index = date.split('-')
            if len(date) != 7:
                date = f"{stripped_index[1]}-0{stripped_index[0]}"
            else:
                date = f"{stripped_index[1]}-{stripped_index[0]}"
            return date

        # Merge all datas requested before on the field 'date_month'
        df = self.df_evol_idpe_connect.merge(
            self.df_evol_idpe_connect_sign_afficher_details, how='outer').merge(
            self.df_evol_idpe_connect_sign_details, how='outer').merge(
            self.df_evol_idpe_connect_sign, how='outer').merge(
            self.df_evol_dpae, how='outer').merge(
            self.df_nb_candidatures_jp, how='outer').merge(
            self.df_nb_distinct_email_jp, how='outer').merge(
            self.df_nb_candidates_with_answer_jp, how='outer').merge(
            self.df_medium_delay_answer_jp, how='outer')

        df.reset_index(inplace=True)

        df['date_month'] = df.apply(lambda row: clean_date(row), axis=1)
        df = df.sort_values('date_month')

        # FIXME : When datas will be available
        df['count_id_pe_firststep_jp'] = 0

        df['empty_column'] = None

        df['count_distinct_activity'] = df['count_distinct_activity'] + df['count_id_pe_firststep_jp']

        #df = self.create_columns('month', df, df['date_month'])

        ORDERING_COLUMN = [
            'date_month',
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
        values_to_insert = {'values': df.values.tolist()}

        logger.info("Data preparation for first sheet ready")

        return values_to_insert, df

    def prepare_2nd_google_sheet_data(self):

        # Rename the date of the month by adding a '0' when needed
        # The dates in columns and indexes look like :
        # ['2018-10', '2018-8', '2018-9', '2018-11', '2018-12', '2019-1',
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

        # Prepare columns for dataframe
        columns = self.df_evol_nb_dpae_hiring_and_activity_date.date_month_embauche.unique()

        df = pd.DataFrame(columns=columns, index=rows)
        for _, row in self.df_evol_nb_dpae_hiring_and_activity_date.iterrows():
            df.loc[row['date_month_activite'], row['date_month_embauche']] = row['count_dpae_lbb']

        # Rename columns dates names
        df.index = clean_dates_list(df.index)
        df.columns = clean_dates_list(df.columns)

        # Sort dataframe by column name and row index for the date to be in the right order
        df = df.reindex(sorted(df.columns), axis=1)
        df = df.sort_index()

        df = df.fillna(0)

        # For the values to insert, we also need the columns names and index name to insert into google sheets
        values_to_insert = []

        # columns
        columns = df.columns.tolist()
        columns.insert(0, '')
        values_to_insert.append(columns)

        # indexes + values of dataframe
        i = 0
        for row in df.values.tolist():
            row.insert(0, df.index[i])
            values_to_insert.append(row)
            i += 1

        values_to_insert = {'values': values_to_insert}

        logger.info("Data preparation for second sheet ready")

        return values_to_insert, df


def run_main():

    data_preparation_for_google_sheets = PrepareDataForGoogleSheetReport()

    service = generate_google_sheet_service()
    logger.info("google sheets service generated")

    # First sheet
    data_preparation_for_google_sheets.get_data_first_sheet()
    values_to_insert_first_sheet, _ = data_preparation_for_google_sheets.prepare_google_sheet_data()

    first_sheet_report = GoogleSheetReport(
        service=service,
        spreadsheet_id=settings.SPREADSHEET_IDS[0],
        sheet_index=0,
        start_cell='A2',
        values=values_to_insert_first_sheet
    )
    first_sheet_report.set_sheet_range()
    first_sheet_report.write_data_into_sheet()

    logger.info('Data written on first google sheet report')

    # Second sheet
    data_preparation_for_google_sheets.get_data_second_sheet()
    values_to_insert_second_sheet, _ = data_preparation_for_google_sheets.prepare_2nd_google_sheet_data()

    second_sheet_report = GoogleSheetReport(
        service=service,
        spreadsheet_id=settings.SPREADSHEET_IDS[1],
        sheet_index=0,
        start_cell='B5',
        values=values_to_insert_second_sheet
    )
    second_sheet_report.set_sheet_range()
    second_sheet_report.write_data_into_sheet()

    logger.info('Data written on second google sheet report')



if __name__ == '__main__':
    run_main()
