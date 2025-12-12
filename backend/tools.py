# tools.py
import requests
import os
import random
from datetime import datetime

# NASA POWER API Endpoint
NASA_API_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

def get_nasa_weather(lat: float, lon: float):
    """
    Fetches weather data from NASA POWER API.
    Falls back to realistic mock data if the API fails.
    """
    try:
        # Define parameters for the API call
        params = {
            "parameters": "PRECTOTCORR,T2M",  # Precipitation, Temperature at 2 Meters
            "community": "AG",
            "longitude": lon,
            "latitude": lat,
            "start": "20230101",  # NASA data has a delay, so we request a past date range
            "end": "20230105",
            "format": "JSON"
        }

        response = requests.get(NASA_API_URL, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            # Extract the latest available data point
            precip_data = data['properties']['parameter']['PRECTOTCORR']
            temp_data = data['properties']['parameter']['T2M']
            
            # Get the last value from the dictionary (simulating 'today')
            last_date = list(precip_data.keys())[-1]
            
            rain = precip_data[last_date]
            temp = temp_data[last_date]
            
            # Validate data (NASA sometimes returns -999 for missing data)
            if temp < -100 or rain < 0:
                raise ValueError("Invalid data from NASA")

            return {
                "rainfall_mm": round(rain, 2),
                "temperature_c": round(temp, 1)
            }
            
    except Exception as e:
        print(f"⚠️ NASA API Failed: {e}. Using Mock Data.")

    # --- FALLBACK: REALISTIC MOCK DATA ---
    # Generate realistic values for Indian agriculture context
    mock_temp = round(random.uniform(22.0, 34.0), 1)  # 22°C to 34°C
    mock_rain = round(random.uniform(0.0, 15.0), 2)   # 0mm to 15mm
    
    return {
        "rainfall_mm": mock_rain,
        "temperature_c": mock_temp,
        "note": "Simulated Data"
    }