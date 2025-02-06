import os
import io
import json

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload


load_dotenv()

GCLOUD_TYPE = os.getenv('GCLOUD_TYPE', '')
GCLOUD_PROJECT_ID = os.getenv('GCLOUD_PROJECT_ID', '')
GCLOUD_PRIVATE_KEY_ID = os.getenv('GCLOUD_PRIVATE_KEY_ID', '')
GCLOUD_PRIVATE_KEY = os.getenv('GCLOUD_PRIVATE_KEY', '')
GCLOUD_CLIENT_EMAIL = os.getenv('GCLOUD_CLIENT_EMAIL', '')
GCLOUD_CLIENT_ID = os.getenv('GCLOUD_CLIENT_ID', '')
GCLOUD_AUTH_URI = os.getenv('GCLOUD_AUTH_URI', '')
GCLOUD_TOKEN_URI = os.getenv('GCLOUD_TOKEN_URI', '')
GCLOUD_AUTH_PROVIDER_X509_CERT_URL = os.getenv('GCLOUD_AUTH_PROVIDER_X509_CERT_URL', '')
GCLOUD_CLIENT_X509_CERT_URL = os.getenv('GCLOUD_CLIENT_X509_CERT_URL', '')
GCLOUD_UNIVERSE_DOMAIN = os.getenv('GCLOUD_UNIVERSE_DOMAIN', '')

GDRIVE_FOLDER_ID = os.getenv('GDRIVE_FOLDER_ID', '')

MIME_TYPES = {
    'gslides': 'application/vnd.google-apps.presentation',
    'pptx':'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'mp4': 'video/mp4',
}

SCOPES = ['https://www.googleapis.com/auth/drive']

CREDENTIALS_JSON = {
    'type': GCLOUD_TYPE,
    'project_id': GCLOUD_PROJECT_ID,
    'private_key_id': GCLOUD_PRIVATE_KEY_ID,
    'private_key': GCLOUD_PRIVATE_KEY,
    'client_email': GCLOUD_CLIENT_EMAIL,
    'client_id': GCLOUD_CLIENT_ID,
    'auth_uri': GCLOUD_AUTH_URI,
    'token_uri': GCLOUD_TOKEN_URI,
    'auth_provider_x509_cert_url': GCLOUD_AUTH_PROVIDER_X509_CERT_URL,
    'client_x509_cert_url': GCLOUD_CLIENT_X509_CERT_URL,
    'universe_domain': GCLOUD_UNIVERSE_DOMAIN,
}

with open('credentials.json', 'w') as f:
    json.dump(CREDENTIALS_JSON, f, indent=4)


def main():
    '''
        Shows basic usage of the Drive v3 API.
        Prints the names and ids of the first 10 files the user has access to.
    '''
    credentials = service_account.Credentials.from_service_account_file('credentials.json', scopes=SCOPES)

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

        if GDRIVE_FILE_MIME_TYPE == MIME_TYPES['gslides']:
            # Export Google Slides as a PowerPoint format (.pptx)
            response = service.files().export_media(
                fileId=GDRIVE_FILE_ID,
                mimeType=MIME_TYPES['pptx'],
            )
        elif GDRIVE_FILE_MIME_TYPE == MIME_TYPES['pptx'] or GDRIVE_FILE_MIME_TYPE == MIME_TYPES['mp4']:
            # Export PowerPoint or MP4
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

        # Save file as a PowerPoint (.pptx) or MP4 (.mp4) after download is complete
        with open('bulletin' + ('.mp4' if GDRIVE_FILE_MIME_TYPE == MIME_TYPES['mp4'] else '.pptx'), 'wb') as f:
            f.write(file_stream.getvalue())

    except HttpError as error:
        # TODO(developer) - Handle errors from drive API
        print(f'An error has occurred: {error}')

if __name__ == '__main__':
    main()
