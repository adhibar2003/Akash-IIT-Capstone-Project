import os
import io
import json
import pandas as pd
import joblib
from flask import Flask, request, jsonify, render_template
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

# Load the trained model
try:
    model = joblib.load('crop_recommendation_model.pkl')
    logging.info("Model loaded successfully")
except Exception as e:
    logging.error(f"Error loading model: {e}")


# Load credentials from file
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
SERVICE_ACCOUNT_FILE = 'credentials.json'  # Update this path


creds = None
if os.path.exists(SERVICE_ACCOUNT_FILE):
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

drive_service = build('drive', 'v3', credentials=creds)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/aboutus')
def aboutus():
    return render_template('aboutus.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/fertilizer')
def fertilizer():
    return render_template('fertilizer.html')


@app.route('/crop')
def crop():
    return render_template('crop.html')


@app.route('/disease')
def disease():
    diseases = list_diseases()
    return render_template('disease.html', diseases=diseases)


@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    image = request.files['image']

    if image.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Save the uploaded image locally
    image_path = os.path.join('static/uploads', image.filename)
    os.makedirs(os.path.dirname(image_path), exist_ok=True)
    image.save(image_path)

    # Extract disease name from the image filename
    disease_name = os.path.splitext(image.filename)[0]

    # Fetch the disease details from Google Drive
    disease_details = get_disease_details_by_name(disease_name)
    if disease_details:
        result = {
            'name': disease_details['name'],
            'description': disease_details['description'],
            'spread_data': disease_details.get('spread_data', {}),
            'image_path': image_path
        }
    else:
        result = {'error': 'Disease not found'}

    return jsonify(result)


@app.route('/crop-recommend', methods=['POST'])
def crop_recommend():
    try:
        # Get form data
        nitrogen = int(request.form['nitrogen'])
        phosphorus = int(request.form['phosphorus'])
        potassium = int(request.form['potassium'])
        temperature = float(request.form['temperature'])
        humidity = float(request.form['humidity'])
        ph = float(request.form['ph'])
        rainfall = float(request.form['rainfall'])

        logging.debug(
            f"Received input - Nitrogen: {nitrogen}, Phosphorus: {phosphorus}, Potassium: {potassium}, "
            f"Temperature: {temperature}, Humidity: {humidity}, pH: {ph}, Rainfall: {rainfall}"
        )

        # Create a dataframe for the input features
        input_features = pd.DataFrame([[
            nitrogen, phosphorus, potassium, temperature, humidity, ph,
            rainfall
        ]],
                                      columns=[
                                          'N', 'P', 'K', 'temperature',
                                          'humidity', 'ph', 'rainfall'
                                      ])

        # Predict the crop using the trained model
        prediction = model.predict(input_features)
        recommended_crop = prediction[0]

        logging.info(f"Recommended Crop: {recommended_crop}")

        return jsonify({'crop': recommended_crop})

    except Exception as e:
        logging.error(f"Error during crop recommendation: {e}")
        return jsonify(
            {'error': 'An error occurred while processing your request.'}), 500


def list_diseases():
    try:
        # Folder ID for the PlantDiseases folder in Google Drive
        folder_id = '1E7pwvCIvIaNh07ZFXNn-x3XS5raet9jD'  # Replace with your folder ID
        query = f"'{folder_id}' in parents and mimeType='application/json'"
        results = drive_service.files().list(
            q=query, fields="files(id, name)").execute()
        items = results.get('files', [])

        return [{
            'id': item['id'],
            'name': item['name'].replace('.json', '')
        } for item in items]
    except Exception as e:
        print(f"An error occurred: {e}")
        return []


def get_disease_details(file_id):
    try:
        request = drive_service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        fh.seek(0)
        return json.loads(fh.read().decode('utf-8'))
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def get_disease_details_by_name(disease_name):
    try:
        folder_id = '1E7pwvCIvIaNh07ZFXNn-x3XS5raet9jD'  # Replace with your folder ID
        query = f"'{folder_id}' in parents and name='{disease_name}.json'"
        results = drive_service.files().list(
            q=query, fields="files(id, name)").execute()
        items = results.get('files', [])
        if not items:
            return None

        file_id = items[0]['id']
        return get_disease_details(file_id)
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5500)
