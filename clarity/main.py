import os
import io
import json
import subprocess
import time

from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload


MIME_TYPES = {
    'gslides': 'application/vnd.google-apps.presentation',
    'pptx':'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'mp4': 'video/mp4',
}


def generate_credentials() -> None:
    '''
        Generate the credentials.json file using the GCLOUD* environment variable values.
    '''
    load_dotenv()

    CREDENTIALS_JSON = {
        'type': os.getenv('GCLOUD_TYPE', ''),
        'project_id': os.getenv('GCLOUD_PROJECT_ID', ''),
        'private_key_id': os.getenv('GCLOUD_PRIVATE_KEY_ID', ''),
        'private_key': os.getenv('GCLOUD_PRIVATE_KEY', ''),
        'client_email': os.getenv('GCLOUD_CLIENT_EMAIL', ''),
        'client_id': os.getenv('GCLOUD_CLIENT_ID', ''),
        'auth_uri': os.getenv('GCLOUD_AUTH_URI', ''),
        'token_uri': os.getenv('GCLOUD_TOKEN_URI', ''),
        'auth_provider_x509_cert_url': os.getenv('GCLOUD_AUTH_PROVIDER_X509_CERT_URL', ''),
        'client_x509_cert_url': os.getenv('GCLOUD_CLIENT_X509_CERT_URL', ''),
        'universe_domain': os.getenv('GCLOUD_UNIVERSE_DOMAIN', ''),
    }

    with open('credentials.json', 'w') as f:
        json.dump(CREDENTIALS_JSON, f, indent=4)

    return


def get_gdrive_folder_id() -> str:
    '''
        Get the GDRIVE_FOLDER_ID environment variable value.
    '''
    load_dotenv()

    folder_id = os.getenv('GDRIVE_FOLDER_ID')

    if not folder_id:
        raise Exception('No Google Drive folder ID provided.')

    return folder_id


def retrieve_file():
    '''
        Retrieve most recent file in Google Drive folder.
    '''
    SCOPES = ['https://www.googleapis.com/auth/drive']

    generate_credentials()

    credentials = service_account.Credentials.from_service_account_file('credentials.json', scopes=SCOPES)

    try:
        service = build('drive', 'v3', credentials=credentials)

        query = f'"{get_gdrive_folder_id()}" in parents and trashed = false'

        # Call the Drive v3 API
        response = service.files().list(
            q=query,
            orderBy='modifiedTime desc',
            fields='files(id, mimeType)',
        ).execute()

        if not response['files']:
            raise Exception(f'No Google Drive folder found with the folder id {get_gdrive_folder_id()}.')

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
            raise Exception('Invalid file format in Google Drive folder.')

    except HttpError as error:
        # TODO(developer) - Handle errors from drive API
        print(f'An error has occurred: {error}')
    except Exception as error:
        print(f'Error: {error}')
    else:
        return response, GDRIVE_FILE_MIME_TYPE


def download_file(data, file_type) -> None:
    '''
        Download file retrieved.
    '''
    # Stream download
    file_stream = io.BytesIO()

    try:
        downloader = MediaIoBaseDownload(file_stream, data)

        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f'Download Progress: {int(status.progress() * 100)}%')
    except Exception as error:
        print(f'Error: {error}')
    else:
        # Save file as a PowerPoint (.pptx) or MP4 (.mp4) after download is complete
        with open('bulletin' + ('.mp4' if file_type == MIME_TYPES['mp4'] else '.pptx'), 'wb') as f:
            f.write(file_stream.getvalue())

    return


def play_pptx(file):
    '''
        Play PowerPoint in full-screen mode.
    '''
    print(f"Opening PowerPoint: {file}")
    subprocess.run(["libreoffice", "--show", file])  # LibreOffice Impress full-screen


def play_mp4(file):
    '''
        Play video in full-screen & loop mode.
    '''
    print(f"Playing Video: {file}")
    subprocess.run(["vlc", "--fullscreen", "--loop", file])  # VLC in full-screen loop


def has_new_gdrive_file() -> bool:
    '''
        Checks if there's a more recent file in the Google Drive folder than the file that is downloaded.
    '''
    # TODO(developer): 
    return True


def main():
    '''
        The main entry point of the script.

        This function initializes the program, processes inputs, 
        and calls other functions as needed.
    '''
    while True:
        if has_new_gdrive_file():
            try:
                data, file_type = retrieve_file()

                download_file(data, file_type)
            except Exception as error:
                continue

            # Close any running LibreOffice or VLC instances
            subprocess.run(["pkill", "soffice"])  # Kill LibreOffice Impress
            subprocess.run(["pkill", "vlc"])      # Kill VLC

            time.sleep(5)  # Small delay before restarting

            # Play based on file type
            try:
                if file_type == MIME_TYPES['pptx']:
                    play_pptx('bulletin.pptx')
                elif file_type == MIME_TYPES['mp4']:
                    play_mp4('bulletin.mp4')
            except Exception as error:
                continue

        time.sleep(10)  # Check for new files every 10 seconds


if __name__ == '__main__':
    main()
