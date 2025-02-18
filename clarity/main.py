import os
import io
import json
import subprocess
import time

from datetime import datetime, timezone
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


def init_gdrive_service():
    '''
        Initialize service request to the Google Drive API.
    '''
    SCOPES = ['https://www.googleapis.com/auth/drive']

    generate_credentials()

    credentials = service_account.Credentials.from_service_account_file('credentials.json', scopes=SCOPES)

    service = build('drive', 'v3', credentials=credentials)

    return service


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
    try:
        service = init_gdrive_service()

        query = f'"{get_gdrive_folder_id()}" in parents and trashed = false'

        # Call the Drive v3 API
        response = service.files().list(
            q=query,
            fields='files(id, mimeType)',
            orderBy='modifiedTime desc',
        ).execute()

        if not response['files']:
            raise Exception(f'No Google Drive folder found with the folder id {get_gdrive_folder_id()}.')

        # Retrieve most recently modified Google Slides file ID
        GDRIVE_FILE_ID = response.get('files', [])[0]['id']
        GDRIVE_FILE_MIME_TYPE = response.get('files', [])[0].get('mimeType')

        # Export Google Slides as a PowerPoint format (.pptx)
        if GDRIVE_FILE_MIME_TYPE == MIME_TYPES['gslides']:
            response = service.files().export_media(
                fileId=GDRIVE_FILE_ID,
                mimeType=MIME_TYPES['pptx'],
            )
        # Export PowerPoint or MP4
        elif GDRIVE_FILE_MIME_TYPE == MIME_TYPES['pptx'] or GDRIVE_FILE_MIME_TYPE == MIME_TYPES['mp4']:
            response = service.files().get_media(
                fileId=GDRIVE_FILE_ID,
            )
        else:
            # TODO(developer) - Throw error: invalid file format in drive
            raise Exception('Invalid file format in Google Drive folder.')

    except HttpError as error:
        # TODO(developer) - Handle errors from drive API
        print(f'Error: {error}')
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
    subprocess.Popen(['libreoffice', '--norestore', '--invisible', '--show', file])

    return


def play_mp4(file):
    '''
        Play video in full-screen & loop mode.
    '''
    subprocess.Popen(['vlc', '--aout', 'dummy', '--fullscreen', '--loop', '--no-video-title-show', '--no-qt-privacy-ask', '--qt-start-minimized', file])

    return


def has_new_gdrive_file() -> bool:
    '''
        Checks if there's a more recent file in the Google Drive folder than the file that is downloaded.
    '''
    # Retrieve Google drive's most recently updated file's datetime
    service = init_gdrive_service()

    query = f'"{get_gdrive_folder_id()}" in parents and trashed = false'

    response = service.files().list(
        q=query, 
        fields='files(modifiedTime)', 
        orderBy='modifiedTime desc'
    ).execute()

    gdrive_file_modified_time = response.get('files', [])[0]['modifiedTime']

    # Convert modified time to Python datetime object
    gdrive_file_dt_object = datetime.strptime(gdrive_file_modified_time,'%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)

    # Retrieve bulletin file's datetime
    directory = os.getcwd()

    # Get files that start with "bulletin"
    matching_files = [f for f in os.listdir(directory) if f.startswith('bulletin')]

    # Get the most recently downloaded bulletin modified time
    if matching_files:
        latest_bulletin_file = max(matching_files, key=lambda f: os.path.getmtime(os.path.join(directory, f)))
        bulletin_file_modified_time = os.path.getmtime(os.path.join(directory, latest_bulletin_file))
        bulletin_file_dt_object = datetime.fromtimestamp(bulletin_file_modified_time).replace(tzinfo=datetime.now().astimezone().tzinfo)

        # Check if the Google Drive file is more recently updated than the bulletin file
        if gdrive_file_dt_object > bulletin_file_dt_object:
            return True
        else:
            return False

    return True


def clean_up() -> None:
    '''
        Kill LibreOffice or VLC processes and remove old files.
    '''
    # Close any running LibreOffice or VLC instances
    subprocess.Popen(['pkill', 'soffice'])
    subprocess.Popen(['pkill', 'vlc'])

    time.sleep(5)

    directory = os.getcwd()

    matching_files = [f for f in os.listdir(directory) if f.startswith('bulletin')]

    for f in matching_files:
        file_path = os.path.join(directory, f)

        # Check if it is a file (not a directory) and remove it
        if os.path.isfile(file_path):
            os.remove(file_path)

    return


def main() -> None:
    '''
        The main entry point of the script.

        This function initializes the program, processes inputs, 
        and calls other functions as needed.
    '''
    while True:
        # Check if Google Drive has a new file
        if has_new_gdrive_file():
            try:
                # Retrieve file from Google Drive
                data, file_type = retrieve_file()

                # Clean up processes and directory
                clean_up()

                # Download file
                download_file(data, file_type)
            except Exception as error:
                print(f'Error: {error}')
                continue

            # Play file based on file type
            try:
                if file_type == MIME_TYPES['pptx']:
                    play_pptx('bulletin.pptx')
                elif file_type == MIME_TYPES['mp4']:
                    play_mp4('bulletin.mp4')
            except Exception as error:
                print(f'Error: {error}')
                continue

        time.sleep(10)

    return


if __name__ == '__main__':
    main()
