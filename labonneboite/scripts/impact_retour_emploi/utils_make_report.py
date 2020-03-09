import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

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
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIAL_FILE, SCOPES)
            credentials = flow.run_local_server(port=10800)
            
    # Save the credentials for the next run
    with open(TOKEN_FILE, 'wb') as token:
        pickle.dump(credentials, token)

    # Connexion to the Google Sheet
    return build('sheets', 'v4', credentials=credentials, cache_discovery=False)