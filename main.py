from flask import Flask, request, jsonify, current_app
from google.cloud import storage
import requests
import os
import json
from datetime import datetime
from typing import Tuple, Dict, Any
from functools import lru_cache
from google.api_core import retry


app = Flask(__name__)

# Initialize storage client with explicit project ID
storage_client = storage.Client(project='assement-446515')
bucket = storage_client.bucket('uniquebuket')

def validate_coordinates(lat: float, lon: float) -> Tuple[bool, str]:
    if not (-90 <= lat <= 90):
        return False, "Latitude must be between -90 and 90"
    if not (-180 <= lon <= 180):
        return False, "Longitude must be between -180 and 180"
    return True, ""

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Weather API is running"}), 200

@app.route('/store-weather-data', methods=['POST'])
def store_weather_data():
    try:
        data = request.json
        
        # Input validation
        required_fields = ['latitude', 'longitude', 'start_date', 'end_date']
        for field in required_fields:
            if data.get(field) is None:
                return jsonify({'error': f"Invalid input: {field} is required"}), 400
        
        # Coordinate validation
        lat, lon = float(data['latitude']), float(data['longitude'])
        is_valid, error_message = validate_coordinates(lat, lon)
        if not is_valid:
            return jsonify({'error': error_message}), 400

        # Date validation
        try:
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
            
            if end_date < start_date:
                return jsonify({'error': 'end_date cannot be before start_date'}), 400
                
            start_date = start_date.strftime('%Y-%m-%d')
            end_date = end_date.strftime('%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Dates must be in YYYY-MM-DD format'}), 400

        # API request with timeout
        try:
            response = requests.get(
                'https://archive-api.open-meteo.com/v1/archive',
                params={
                    'latitude': lat,
                    'longitude': lon,
                    'start_date': start_date,
                    'end_date': end_date,
                    'daily': 'temperature_2m_max,temperature_2m_min,temperature_2m_mean,apparent_temperature_max,apparent_temperature_min,apparent_temperature_mean',
                    'timezone': data.get('timezone', 'auto')
                },
                timeout=10
            )
            response.raise_for_status()
        except requests.Timeout:
            return jsonify({'error': 'Request to weather API timed out'}), 504
        except requests.RequestException as e:
            current_app.logger.error(f"Weather API error: {str(e)}")
            return jsonify({'error': 'Failed to fetch data from Open-Meteo API'}), 500

        weather_data = response.json()
        
        # Store in GCS
        file_name = f"weather_{lat}_{lon}_{start_date}_{end_date}.json"
        blob = bucket.blob(file_name)
        blob.upload_from_string(
            json.dumps(weather_data), 
            content_type='application/json'
        )
        
        return jsonify({
            'message': 'Data stored successfully', 
            'file_name': file_name
        })
    
    except Exception as e:
        current_app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/list-weather-files', methods=['GET'])
def list_weather_files():
    blobs = bucket.list_blobs()
    file_names = [blob.name for blob in blobs]
    return jsonify(file_names)

@lru_cache(maxsize=100)
def get_weather_file_content(file_name: str) -> Dict[str, Any]:
    blob = bucket.blob(file_name)
    if not blob.exists():
        raise FileNotFoundError
    return json.loads(blob.download_as_text())

@app.route('/weather-file-content/<file_name>', methods=['GET'])
@retry.Retry()
def weather_file_content(file_name):
    try:
        content = get_weather_file_content(file_name)
        return jsonify(content)
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        current_app.logger.error(f"Error retrieving file: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=True)