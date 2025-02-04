import os
import io
import json

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload


load_dotenv()

GCLOUD_CLIENT_ID = os.getenv('GCLOUD_CLIENT_ID', '')
GCLOUD_CLIENT_SECRET = os.getenv('GCLOUD_CLIENT_SECRET', '')
GCLOUD_PROJECT_ID = os.getenv('GCLOUD_PROJECT_ID', '')
GCLOUD_AUTH_URI = os.getenv('GCLOUD_AUTH_URI', '')
GCLOUD_TOKEN_URI = os.getenv('GCLOUD_TOKEN_URI', '')
GCLOUD_AUTH_PROVIDER_X509_CERT_URL = os.getenv('GCLOUD_AUTH_PROVIDER_X509_CERT_URL', '')
GDRIVE_FOLDER_ID = os.getenv('GDRIVE_FOLDER_ID', '')

MIME_TYPE_GSLIDES = 'application/vnd.google-apps.presentation'
MIME_TYPE_PPTX = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'

SCOPES = ['https://www.googleapis.com/auth/drive']

CREDENTIALS_JSON = {
    'installed': {
        'client_id': GCLOUD_CLIENT_ID,
        'project_id': GCLOUD_PROJECT_ID,
        'auth_uri': GCLOUD_AUTH_URI,
        'token_uri': GCLOUD_TOKEN_URI,
        'auth_provider_x509_cert_url': GCLOUD_AUTH_PROVIDER_X509_CERT_URL,
        'client_secret': GCLOUD_CLIENT_SECRET,
        'redirect_uris': [
            'http://localhost'
        ]
    }
}

with open('credentials.json', 'w') as f:
    json.dump(CREDENTIALS_JSON, f, indent=4)

def main():
    '''
        Shows basic usage of the Drive v3 API.
        Prints the names and ids of the first 10 files the user has access to.
    '''
    credentials = None

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        credentials = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES
            )
            credentials = flow.run_local_server(port=0)
        
        #Save the credentials for the next run.
        with open('token.json', 'w') as f:
            f.write(credentials.to_json())
    
    try:
        service = build('drive', 'v3', credentials=credentials)

        query = f'"{GDRIVE_FOLDER_ID}" in parents and trashed = false'

        # Call the Drive v3 API
        response = service.files().list(
            q=query,
            orderBy='modifiedTime desc',
            fields='files(id, mimeType)',
        ).execute()

        if not response['files']:
            print('No folder found.')
            return

        # Retrieve most recently modified Google Slides file ID
        GDRIVE_FILE_ID = response['files'][0]['id']
        GDRIVE_FILE_MIME_TYPE = response['files'][0].get('mimeType')

        if GDRIVE_FILE_MIME_TYPE == MIME_TYPE_GSLIDES:
            # Export Google Slides as a PowerPoint format (.pptx)
            response = service.files().export_media(
                fileId=GDRIVE_FILE_ID,
                mimeType=MIME_TYPE_PPTX,
            )
        elif GDRIVE_FILE_MIME_TYPE == MIME_TYPE_PPTX:
            # Export PowerPoint
            response = service.files().get_media(
                fileId=GDRIVE_FILE_ID,
            )
        else:
            # TODO(developer) - Throw error: invalid file format in drive
            print('Invalid file format in drive.')
            return

        # Stream download
        file_stream = io.BytesIO()
        downloader = MediaIoBaseDownload(file_stream, response)

        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f'Download Progress: {int(status.progress() * 100)}%')

        # Save file as a PowerPoint (.pptx) after download is complete
        with open('bulletin.pptx', 'wb') as f:
            f.write(file_stream.getvalue())

    except HttpError as error:
        # TODO(developer) - Handle errors from drive API
        print(f'An error has occurred: {error}')

if __name__ == '__main__':
    main()
