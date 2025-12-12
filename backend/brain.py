import google.generativeai as genai
import os
import logging
from dotenv import load_dotenv

# Import the actual functions defined in your mcp_client.py
from mcp_client import (
    get_nasa_weather_mcp,
    get_gis_data_mcp
)

load_dotenv()
logger = logging.getLogger(__name__)

api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

# --- 🛰️ TOOL DEFINITIONS ---
# We wrap your existing MCP helpers so Gemini understands the arguments

async def get_nasa_satellite_weather(lat: float, lon: float):
    """Fetches real-time weather and rainfall data from NASA satellites for a farm."""
    logger.info(f"🎯 Gemini calling NASA Tool for Lat: {lat}, Lon: {lon}")
    # Using the correct function from your mcp_client
    return await get_nasa_weather_mcp(lat, lon)

async def get_gis_crop_health_map(farm_id: str = "Current"):
    """Fetches GIS crop health (NDVI) status for the farmer's land."""
    logger.info("🎯 Gemini calling GIS Tool")
    # Using the correct function from your mcp_client
    return await get_gis_data_mcp(farm_id)

# Map for the agent dispatcher
AVAILABLE_TOOLS = {
    "get_nasa_satellite_weather": get_nasa_satellite_weather,
    "get_gis_crop_health_map": get_gis_crop_health_map,
}

# --- 🧠 MODEL SETUP ---
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    tools=[get_nasa_satellite_weather, get_gis_crop_health_map],
    system_instruction="""
    You are 'Spectra', an AI Agri-Advisor. 
    You have access to NASA tools for weather/rain and GIS tools for crop health. 
    Use them whenever a farmer asks about their farm's condition.
    Always reply in the user's language (Hindi, Kannada, etc.).
    """
)

async def get_spectra_response(user_text: str, context_data: str = ""):
    """Standard response helper for simple tasks."""
    response = await model.generate_content_async(f"{context_data}\n\n{user_text}")
    return response.text