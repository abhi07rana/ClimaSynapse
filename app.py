from flask import Flask, request, jsonify
from flask_cors import CORS  
import requests

app = Flask(__name__)
CORS(app)  

API_KEY = "06da29eebb4f45c595e45001251002"
WEATHER_API_URL = "http://api.weatherapi.com/v1/forecast.json"

@app.route('/')
def home():
    return "Welcome to ClimaSynapse™ - AI Climate Forecasting System"

@app.route('/climate', methods=['GET'])
def get_climate_forecast():
    city = request.args.get("city")
    if not city:
        return jsonify({"error": "City parameter is required"}), 400
    
    params = {
        "key": API_KEY,
        "q": city,
        "days": 7,
        "aqi": "no",
        "alerts": "yes"
    }

    try:
        response = requests.get(WEATHER_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to fetch weather data: {str(e)}"}), 400

    forecast_days = data.get("forecast", {}).get("forecastday", [])
    
    if not forecast_days:
        return jsonify({"error": "No forecast data available"}), 400

    # Categorized forecast layers
    temperature_forecast = []
    precipitation_forecast = []
    extreme_weather_forecast = []

    EXTREME_WEATHER_KEYWORDS = ["storm", "heat", "hurricane", "tornado", "blizzard", 
                                "thunder", "cyclone", "snowstorm", "hail", "flood", "wildfire"]

    for day in forecast_days:
        date = day["date"]
        temp = day["day"]["avgtemp_c"]
        precip = day["day"]["totalprecip_mm"]
        condition = day["day"]["condition"]["text"].lower()

        # Check for extreme weather conditions
        extreme = any(keyword in condition for keyword in EXTREME_WEATHER_KEYWORDS)

        temperature_forecast.append({"date": date, "avg_temperature": temp})
        precipitation_forecast.append({"date": date, "precipitation_mm": precip})

        if extreme:
            extreme_weather_forecast.append({"date": date, "condition": condition})

    # Ensure extreme weather layers exist even if empty
    while len(extreme_weather_forecast) < 7:
        extreme_weather_forecast.append({"date": forecast_days[len(extreme_weather_forecast)]["date"], "condition": "Normal"})

    # Divide forecasts into short (2 days), medium (3-5 days), and long-term (6-7 days)
    forecast_data = {
        "city": city,
        "temperature_layers": {
            "short_term_forecast": temperature_forecast[:2],
            "medium_term_forecast": temperature_forecast[2:5],
            "long_term_forecast": temperature_forecast[5:]
        },
        "precipitation_layers": {
            "short_term_forecast": precipitation_forecast[:2],
            "medium_term_forecast": precipitation_forecast[2:5],
            "long_term_forecast": precipitation_forecast[5:]
        },
        "extreme_weather_layers": {
            "short_term_forecast": extreme_weather_forecast[:2],
            "medium_term_forecast": extreme_weather_forecast[2:5],
            "long_term_forecast": extreme_weather_forecast[5:]
        }
    }

    return jsonify(forecast_data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=1000, debug=True)
