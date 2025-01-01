from flask import Flask, request, jsonify
from google.cloud import storage
import requests
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

storage_client = storage.Client()
bucket = storage_client.bucket('uniquebuket')

@app.route('/store-weather-data', methods=['POST'])
def store_weather_data():
    data = request.json

    # Input validation
    required_fields = ['latitude', 'longitude', 'start_date', 'end_date']
    for field in required_fields:
        if data.get(field) is None:
            return jsonify({'error': f"Invalid input: {field} is required"}), 400
    try:
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        
        if end_date < start_date:
            return jsonify({'error': 'end_date cannot be before start_date'}), 400
            
        start_date = start_date.strftime('%Y-%m-%d')
        end_date = end_date.strftime('%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Dates must be in YYYY-MM-DD format'}), 400
    

    latitude = data['latitude']
    longitude = data['longitude']
    timezone = data.get('timezone', 'auto')  

    response = requests.get(
        'https://archive-api.open-meteo.com/v1/archive',
        params={
            'latitude': latitude,
            'longitude': longitude,
            'start_date': start_date,
            'end_date': end_date,
            'daily': 'temperature_2m_max,temperature_2m_min,temperature_2m_mean,apparent_temperature_max,apparent_temperature_min,apparent_temperature_mean',
            'timezone': timezone
        }
    )
    if response.status_code != 200:
        return jsonify({'error': 'Failed to fetch data from Open-Meteo API'}), 500

    weather_data = response.json()

    file_name = f"weather_{latitude}_{longitude}_{start_date}_{end_date}.json"
    blob = bucket.blob(file_name)
    blob.upload_from_string(json.dumps(weather_data), content_type='application/json')

    return jsonify({'message': 'Data stored successfully', 'file_name': file_name})

@app.route('/list-weather-files', methods=['GET'])
def list_weather_files():
    blobs = bucket.list_blobs()
    file_names = [blob.name for blob in blobs]
    return jsonify(file_names)

@app.route('/weather-file-content/<file_name>', methods=['GET'])
def weather_file_content(file_name):
    blob = bucket.blob(file_name)
    if not blob.exists():
        return jsonify({'error': 'File not found'}), 404

    content = blob.download_as_text()
    return jsonify(json.loads(content))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=True)