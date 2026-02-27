import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Scopes to access Google Calendar and Gmail
SCOPES = [
    "https://mail.google.com/",
    "https://www.googleapis.com/auth/calendar",
    
]

# Token storage file
token_file = 't.pickle'

def authenticate_google_account():
    creds = None

    # Check if token.pickle exists (stored credentials after user logs in)
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)

    # If no valid credentials, initiate the login flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)

    return creds


