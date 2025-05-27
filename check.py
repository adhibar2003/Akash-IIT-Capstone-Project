import json
import logging
import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Load the Google Drive API credentials
def load_credentials():
    # Path to your service account key file
    SERVICE_ACCOUNT_FILE = 'credentials.json'

    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=['https://www.googleapis.com/auth/drive.readonly']
    )
    return credentials

# Function to load recommendations from Google Drive
def load_recommendations():
    credentials = load_credentials()
    service = build('drive', 'v3', credentials=credentials)

    file_id = '10L5PdVIsx5E8Y6XMc5KwH1gFZJWrl9ME'
    request = service.files().get_media(fileId=file_id)

    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()
        logging.debug("Download %d%%.", int(status.progress() * 100))

    fh.seek(0)
    recommendations = json.load(fh)

    logging.debug("Loaded recommendations: %s", recommendations)
    return recommendations

if __name__ == '__main__':
    try:
        recommendations = load_recommendations()
        print("Recommendations fetched from Google Drive:")
        print(json.dumps(recommendations, indent=4))
    except Exception as e:
        logging.error("An error occurred: %s", e)
