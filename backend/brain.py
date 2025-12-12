import google.generativeai as genai
import os
import logging
from dotenv import load_dotenv
from mcp_client import mcp_manager 

load_dotenv()
logger = logging.getLogger(__name__)

# Configure Gemini
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

# --- 🛰️ TOOL DEFINITIONS ---
async def get_nasa_satellite_weather(lat: float, lon: float):
    """Fetches real-time weather and rainfall data from NASA satellites for a farm."""
    logger.info(f"🎯 Gemini calling NASA Tool for Lat: {lat}, Lon: {lon}")
    return await mcp_manager.call_tool("nasa", "get_weather", {"lat": lat, "lon": lon})

async def get_gis_crop_health_map(farm_id: str = "Current"):
    """Fetches GIS crop health (NDVI) status for the farmer's land."""
    logger.info("🎯 Gemini calling GIS Tool")
    return await mcp_manager.call_tool("gis", "get_coordinates", {"location": farm_id})

# --- 🧠 MODEL SETUP ---
tools_list = [get_nasa_satellite_weather, get_gis_crop_health_map]

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    tools=tools_list,
    system_instruction="""
    You are 'Spectra', an AI Agri-Advisor. 
    You have access to NASA and GIS tools. Always use them when asked about weather or crop health.
    Always reply in the user's language (Hindi, Kannada, etc.). 
    Provide actionable, friendly advice.
    """
)

# Function used by main.py for general tasks
async def get_spectra_response(user_text: str, context_data: str = ""):
    chat = model.start_chat(enable_automatic_function_calling=True)
    full_prompt = f"{context_data}\n\nUser Question: {user_text}"
    response = await chat.send_message_async(full_prompt)
    return response.text