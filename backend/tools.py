# tools.py
import requests
import datetime

def get_nasa_weather(lat: float, lon: float):
    """
    Fetches 7-day trailing weather data (Soil Moisture & Rain) from NASA POWER.
    Iterates through dates to find the most recent valid data point (not -999).
    """
    if not lat or not lon:
        return {"error": "Coordinates missing."}

    today = datetime.date.today()
    start_date = (today - datetime.timedelta(days=7)).strftime("%Y%m%d")
    end_date = today.strftime("%Y%m%d")

    base_url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    params = {
        "parameters": "PRECTOTCORR,GWETTOP",
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "start": start_date,
        "end": end_date,
        "format": "JSON"
    }

    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status() # Raises an exception for HTTP errors (4xx or 5xx)
        data = response.json()
        
        properties = data.get("properties", {}).get("parameter", {})
        rain_data = properties.get("PRECTOTCORR", {})
        soil_data = properties.get("GWETTOP", {})

        # --- CRITICAL FIX START: Find the latest VALID date ---
        
        latest_valid_date = None
        dates = sorted(rain_data.keys(), reverse=True) # Sort keys descending

        for date_key in dates:
            rain_val = rain_data.get(date_key)
            soil_val = soil_data.get(date_key)
            
            # Check if both values are valid (not NASA's missing data code)
            if rain_val is not None and rain_val != -999.0 and soil_val is not None and soil_val != -999.0:
                latest_valid_date = date_key
                current_rain = rain_val
                current_soil = soil_val
                break # Found the newest reliable data, stop searching

        if not latest_valid_date:
            return {"error": "No valid NASA data found in the last 7 days."}
        # --- CRITICAL FIX END ---

        # Interpretation Logic (Revised)
        status = {
            "location": {"lat": lat, "lon": lon},
            "date": latest_valid_date,
            "rainfall_mm": round(current_rain, 2),
            "soil_moisture_index": round(current_soil, 3), # 0 to 1 scale
            "analysis": ""
        }

        # Simple Rule-Based Analysis to help the AI
        if current_soil < 0.2:
            status["analysis"] = "CRITICAL: Soil is extremely dry. Immediate irrigation required."
        elif current_soil < 0.4 and current_rain < 5:
             status["analysis"] = "Dry conditions persist. Monitor closely; irrigation recommended soon."
        elif current_rain > 10:
            status["analysis"] = "Heavy rain detected (over 10mm). No irrigation needed."
        else:
            status["analysis"] = "Conditions normal. Continue routine checks."

        return status

    except requests.exceptions.RequestException as e:
        return {"error": f"API Request Failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Internal Error: {str(e)}"}