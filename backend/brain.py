import google.generativeai as genai
import os
import logging
import numpy as np
import matplotlib.pyplot as plt
import uuid
from dotenv import load_dotenv
from mcp_client import get_nasa_weather_mcp, get_gis_data_mcp

load_dotenv()
logger = logging.getLogger(__name__)

api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

# --- 🛰️ TOOL 1: NASA ---
async def get_nasa_satellite_weather(lat: float, lon: float):
    """Fetches real-time weather and rainfall data."""
    logger.info(f"🎯 Gemini calling NASA Tool for Lat: {lat}, Lon: {lon}")
    return await get_nasa_weather_mcp(lat, lon)

# --- 🗺️ TOOL 2: GIS ---
async def get_gis_terrain_data(location_name: str = "Farm"):
    """Fetches GIS data including elevation/slope."""
    logger.info("🎯 Gemini calling GIS Tool")
    return await get_gis_data_mcp(location_name)

# --- 🎨 TOOL 3: NDVI HEATMAP (FILE GENERATOR) ---
async def generate_ndvi_analysis(lat: float, lon: float, soil_moisture: float = 20.0):
    """
    Generates a visual NDVI Crop Health map file.
    """
    logger.info(f"🎨 Generating NDVI Map File... Moisture: {soil_moisture}%")
    
    # 1. Simulate Grid
    base_health = min(soil_moisture / 35.0, 0.85)
    grid = np.full((10, 10), base_health)
    noise = np.random.normal(0, 0.08, (10, 10))
    ndvi_grid = np.clip(grid + noise, 0.1, 0.9)
    
    avg_ndvi = np.mean(ndvi_grid)
    status = "Healthy" if avg_ndvi > 0.6 else "Stressed"
    
    # 2. Plot Image
    plt.figure(figsize=(6, 5))
    plt.imshow(ndvi_grid, cmap='RdYlGn', vmin=0, vmax=1)
    plt.colorbar(label='NDVI Score')
    plt.title(f"Spectra Analysis: {status}\nAvg: {avg_ndvi:.2f}")
    plt.axis('off')
    
    # 3. Save LOCALLY (Not just for web)
    # We use an absolute path to be safe
    filename = f"ndvi_{uuid.uuid4().hex[:6]}.png"
    static_dir = os.path.join(os.getcwd(), "static")
    os.makedirs(static_dir, exist_ok=True)
    
    file_path = os.path.join(static_dir, filename)
    plt.savefig(file_path, bbox_inches='tight')
    plt.close()
    
    return {
        "status": status,
        "average_ndvi": round(avg_ndvi, 2),
        "image_path": file_path, # <--- SENDING LOCAL PATH NOW
        "advice": "Irrigate immediately" if avg_ndvi < 0.4 else "Crop is stable"
    }

# --- ⚙️ SETUP ---
AVAILABLE_TOOLS = {
    "get_nasa_satellite_weather": get_nasa_satellite_weather,
    "get_gis_terrain_data": get_gis_terrain_data,
    "generate_ndvi_analysis": generate_ndvi_analysis
}

tools_list = [get_nasa_satellite_weather, get_gis_terrain_data, generate_ndvi_analysis]

SYSTEM_PROMPT = """
You are 'Spectra', a Senior Satellite Agronomist.
### PROTOCOL
1. If the user asks about "Health", "Map", or "Yellowing":
2. Call `get_nasa_satellite_weather` -> Then call `generate_ndvi_analysis`.
3. The tool will return an `image_path`.
4. Tell the user: "I am sending the health map to your WhatsApp now."
"""

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    tools=tools_list,
    system_instruction=SYSTEM_PROMPT
)

async def get_spectra_response(user_text: str, context_data: str = ""):
    chat = model.start_chat(enable_automatic_function_calling=True)
    response = await chat.send_message_async(f"{context_data}\n\n{user_text}")
    return response.text