# Weather API

This project is a Flask-based API that fetches weather data from the Open-Meteo API and stores it in Google Cloud Storage (GCS). It also provides endpoints to list and retrieve stored weather data files.

## Setup and Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/anshulgoyal43/assement
   cd assement
   ```

2. **Create a virtual environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**

   ```bash
   python3 main.py
   ```

## Deployment on Google Cloud Run

1. **Build the Docker image:**

   ```bash
   docker build --platform=linux/amd64 -t weather-api .
   ```

2. **Tag the Docker image:**
   ```bash
   docker tag weather-api gcr.io/<your-project-id>/weather-api
   ```
   
3. **Push the Docker image to Google Container Registry:**

   ```bash
   docker push gcr.io/<your-project-id>/weather-api
   ```

4. **Deploy to Google Cloud Run:**

   ```bash
   gcloud run deploy weather-api \
     --image gcr.io/<your-project-id>/weather-api \
     --platform managed \
     --region <your-region> \
     --allow-unauthenticated
   ```

   Replace `<your-project-id>` and `<your-region>` with your Google Cloud project ID and desired region.

## API Endpoints

Below are the details of the implemented API endpoints:

### `GET /`

- **URL:** `https://weather-api-869245302809.asia-south1.run.app/`
- **Method:** GET
- **Description:** Check if the API is running.
- **Response:** JSON message confirming the API is running.

### `POST /store-weather-data`

- **URL:** `https://weather-api-869245302809.asia-south1.run.app/store-weather-data`
- **Method:** POST
- **Description:** Fetches weather data for a given location and date range, then stores it in Google Cloud Storage (GCS).
- **Request Body:**
  - `latitude` (float): Latitude of the location.
  - `longitude` (float): Longitude of the location.
  - `start_date` (string): Start date in `YYYY-MM-DD` format.
  - `end_date` (string): End date in `YYYY-MM-DD` format.
  - `timezone` (string, optional): Timezone for the data.
- **Response:** JSON message with the status and file name of the stored data.

### `GET /list-weather-files`

- **URL:** `https://weather-api-869245302809.asia-south1.run.app/list-weather-files`
- **Method:** GET
- **Description:** Lists all weather data files stored in GCS.
- **Response:** JSON array of file names.

### `GET /weather-file-content/<file_name>`

- **URL:** `https://weather-api-869245302809.asia-south1.run.app/weather-file-content/<file_name>`
- **Method:** GET
- **Description:** Retrieves the content of a specific weather data file from GCS.
- **Response:** JSON content of the specified file.

## Live Demo

The backend application is hosted on Google Cloud Run. You can access the live demo using the following URL:

[Live Demo URL](https://weather-api-869245302809.asia-south1.run.app)

Ensure that you replace `<file_name>` in the `GET /weather-file-content/<file_name>` endpoint with the actual file name you wish to retrieve.

## Additional Information

- Ensure that your Google Cloud credentials are correctly set up and that the service account has the necessary permissions to access GCS.

