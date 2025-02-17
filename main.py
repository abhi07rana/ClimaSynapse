from flask import Flask, request, jsonify
from flask_cors import CORS  
import pandas as pd
import requests
import os
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64
from sklearn.linear_model import LinearRegression
import numpy as np
from datetime import datetime
from sklearn.preprocessing import StandardScaler

API_KEY = "06da29eebb4f45c595e45001251002"
WEATHER_API_URL = "http://api.weatherapi.com/v1/current.json"

app = Flask(__name__)
CORS(app)  

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return "Welcome to ClimaSynapse™ - AI Climate Forecasting System"

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)
    return jsonify({"message": "File uploaded successfully", "file_path": file_path})

@app.route('/data', methods=['GET'])
def get_data():
    files = os.listdir(UPLOAD_FOLDER)
    if not files:
        return jsonify({"error": "No files uploaded"}), 400
    
    file_path = os.path.join(UPLOAD_FOLDER, files[0])
    try:
        df = pd.read_csv(file_path)
        return df.to_json(orient='records')
    except Exception as e:
        return jsonify({"error": f"Failed to process CSV file: {str(e)}"}), 500

@app.route('/weather', methods=['GET'])
def get_weather():
    files = os.listdir(UPLOAD_FOLDER)
    if not files:
        return jsonify({"error": "No CSV file uploaded"}), 400
    
    file_path = os.path.join(UPLOAD_FOLDER, files[0])
    df = pd.read_csv(file_path)
    
    if "City" not in df.columns:
        return jsonify({"error": "CSV file must have a 'City' column"}), 400
    
    city_list = df["City"].unique().tolist()
    weather_data = []

    for city in city_list:
        params = {"key": API_KEY, "q": city}
        try:
            response = requests.get(WEATHER_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            return jsonify({"error": f"Failed to fetch weather data for {city}: {str(e)}"}), 400

        weather_info = {
            "city": city,
            "temperature_c": data["current"]["temp_c"],
            "humidity": data["current"]["humidity"],
            "wind_speed_kph": data["current"]["wind_kph"],
            "condition": data["current"]["condition"]["text"]
        }
        weather_data.append(weather_info)
    
    return jsonify(weather_data)

@app.route('/predict', methods=['GET'])
def predict_future_climate():
    files = os.listdir(UPLOAD_FOLDER)
    if not files:
        return jsonify({"error": "No CSV file uploaded"}), 400
    
    file_path = os.path.join(UPLOAD_FOLDER, files[0])
    df = pd.read_csv(file_path)

    required_columns = {"Year", "Temperature_C", "Humidity", "Wind_Speed_kph", "Precipitation_mm"}
    if not required_columns.issubset(df.columns):
        return jsonify({"error": f"CSV must have columns: {required_columns}"}), 400

    X = df[["Year", "Humidity", "Wind_Speed_kph", "Precipitation_mm"]]
    y = df["Temperature_C"]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = LinearRegression()
    model.fit(X_scaled, y)

    current_year = datetime.now().year
    future_years = np.array([[year, 65, 12.0, 2.5] for year in range(current_year + 1, current_year + 6)])
    future_years_scaled = scaler.transform(future_years)
    predictions = model.predict(future_years_scaled)

    forecast = [{"year": int(year[0]), "predicted_temperature": round(temp, 2)} for year, temp in zip(future_years, predictions)]
    
    return jsonify(forecast)

@app.route('/visualize', methods=['GET'])
def visualize_data():
    files = os.listdir(UPLOAD_FOLDER)
    if not files:
        return jsonify({"error": "No files uploaded"}), 400
    
    file_path = os.path.join(UPLOAD_FOLDER, files[0])
    df = pd.read_csv(file_path)
    
    if df.shape[1] < 2:
        return jsonify({"error": "CSV file must have at least two columns for visualization"}), 400
    
    plt.figure(figsize=(10, 5))
    sns.lineplot(x=df.columns[0], y=df.columns[1], data=df)
    plt.xlabel(df.columns[0])
    plt.ylabel(df.columns[1])
    plt.title("Climate Data Visualization")
    
    img = BytesIO()
    plt.savefig(img, format='png')
    plt.close()  
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    
    return f'<img src="data:image/png;base64,{plot_url}"/>'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

