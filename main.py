import os

from dotenv import load_dotenv


load_dotenv()

GCLOUD_CLIENT_ID = os.getenv('GCLOUD_CLIENT_ID', '')
GCLOUD_CLIENT_SECRET = os.getenv('GCLOUD_CLIENT_SECRET', '')
GCLOUD_PROJECT_ID = os.getenv('GCLOUD_PROJECT_ID', '')
GCLOUD_AUTH_URI = os.getenv('GCLOUD_AUTH_URI', '')
GCLOUD_TOKEN_URI = os.getenv('GCLOUD_TOKEN_URI', '')
GCLOUD_AUTH_PROVIDER_X509_CERT_URL = os.getenv('GCLOUD_AUTH_PROVIDER_X509_CERT_URL', '')

credentials = {
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

print(credentials)