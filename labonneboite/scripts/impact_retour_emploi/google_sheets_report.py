import os
import pickle
import string
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request


def generate_google_sheet_service():

    # https://developers.google.com/sheets/api/guides/authorizing
    # Delete the file token.pickle if the scopes changes
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    TOKEN_FILE = os.path.dirname(os.path.realpath(__file__))+'/token.pickle'
    CREDENTIAL_FILE = os.path.dirname(os.path.realpath(__file__))+'/credentials.json'

    # Check the validity of the token
    credentials = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            credentials = pickle.load(token)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIAL_FILE, SCOPES)
            credentials = flow.run_local_server(port=10800)
            
    # Save the credentials for the next run
    with open(TOKEN_FILE, 'wb') as token:
        pickle.dump(credentials, token)

    # Connexion to the Google Sheet
    return build('sheets', 'v4', credentials=credentials, cache_discovery=False)

class GoogleSheetReport:

    def __init__(self, service, spreadsheet_id, sheet_index, start_cell, values):
        self.google_service = service
        self.spreadsheet_id = spreadsheet_id
        self.values = values
        self.start_cell = start_cell
        self.sheet_index = sheet_index

    def set_sheet_range(self):
        nb_columns = self.get_nb_columns()
        nb_rows = self.get_nb_rows()
        end_cell = self.get_end_cell(self.start_cell, nb_columns, nb_rows)
        self.sheet_range = self.get_sheet_range(self.start_cell, end_cell)

    def get_nb_columns(self):
        return len(self.values['values'][0])

    def get_nb_rows(self):
        return len(self.values['values'])

    def get_end_cell(self, start_cell, nb_columns, nb_rows):
        # FIXME : Cant accept long cells like ZZ32 for now
        letter_first_column = start_cell[0]
        number_first_row = start_cell[1]
        
        letter_last_column = string.ascii_uppercase[string.ascii_uppercase.index(letter_first_column) + nb_columns - 1]
        number_last_row = str(int(number_first_row) + nb_rows - 1)

        end_cell = f'{letter_last_column}{number_last_row}'
        
        return end_cell

    def get_sheet_range(self, start_cell, end_cell):
        # Get the list of our sheets properties (title)
        list_sheets = self.google_service.spreadsheets().get(
                            spreadsheetId=self.spreadsheet_id,
                            fields="sheets/properties"
                        ).execute()['sheets']

        # Writing the 1st sheet
        sheet = list_sheets[self.sheet_index]['properties']

        return f"{sheet['title']}!{start_cell}:{end_cell}"

    def write_data_into_sheet(self):
        #Clear old data
        self.google_service.spreadsheets().values().clear(
                spreadsheetId=self.spreadsheet_id,
                range=self.sheet_range,
                body={}
            ).execute()
        
        # Write new data
        request = self.google_service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id, 
            range=self.sheet_range,
            valueInputOption='USER_ENTERED', 
            body=self.values
        )

        request.execute()