import google.generativeai as genai
import os
import logging
import numpy as np
import matplotlib.pyplot as plt
import uuid
from dotenv import load_dotenv

# Import MCP Client Wrappers
from mcp_client import get_nasa_weather_mcp, get_gis_data_mcp

load_dotenv()
logger = logging.getLogger("BRAIN")

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    logger.error("❌ GOOGLE_API_KEY is missing!")
else:
    logger.info(f"✅ GOOGLE_API_KEY loaded: {api_key[:5]}...")

genai.configure(api_key=api_key)

# ==========================================
# 🛰️ TOOL DEFINITIONS
# ==========================================

async def get_nasa_satellite_weather(lat: float, lon: float):
    """Fetches real-time weather and rainfall data from NASA satellites."""
    logger.info(f"🎯 Gemini calling NASA Tool for Lat: {lat}, Lon: {lon}")
    return await get_nasa_weather_mcp(lat, lon)

async def get_gis_terrain_data(location_name: str = "Farm"):
    """Fetches GIS data including elevation/slope."""
    logger.info("🎯 Gemini calling GIS Tool")
    return await get_gis_data_mcp(location_name)

async def generate_ndvi_analysis(lat: float, lon: float, soil_moisture: float = 20.0):
    """
    Generates a visual NDVI Crop Health map file based on moisture data.
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
    
    # 3. Save LOCALLY
    filename = f"ndvi_{uuid.uuid4().hex[:6]}.png"
    static_dir = os.path.join(os.getcwd(), "static")
    os.makedirs(static_dir, exist_ok=True)
    
    file_path = os.path.join(static_dir, filename)
    plt.savefig(file_path, bbox_inches='tight')
    plt.close()
    
    # 4. Return Data
    # We return the RELATIVE URL for the link and the ABSOLUTE PATH for the file uploader
    return {
        "status": status,
        "average_ndvi": round(avg_ndvi, 2),
        "map_url": f"http://localhost:8000/static/{filename}", # For Text Link
        "image_path": file_path, # For Voice/Image Uploader
        "advice": "Irrigate immediately" if avg_ndvi < 0.4 else "Crop is stable"
    }

# ==========================================
# ⚙️ EXPORTED TOOLS (THIS WAS MISSING!)
# ==========================================
AVAILABLE_TOOLS = {
    "get_nasa_satellite_weather": get_nasa_satellite_weather,
    "get_gis_terrain_data": get_gis_terrain_data,
    "generate_ndvi_analysis": generate_ndvi_analysis
}

tools_list = [get_nasa_satellite_weather, get_gis_terrain_data, generate_ndvi_analysis]

# ==========================================
# 🧠 SYSTEM PROMPT & MODEL
# ==========================================
SYSTEM_PROMPT = """
You are 'Spectra', an AI Agronomist Assistant.

### 📝 RESPONSE FORMAT:
Split your response into two parts using '===VOICE_SUMMARY==='.

1. **DETAILED TEXT:**
   - Use Markdown. Be analytical. Show the numbers.
   - If a map is generated, say: "Here is your Health Map: [Link]" using the `map_url` from the tool.

===VOICE_SUMMARY===

2. **VOICE SCRIPT:**
   - Conversational, warm, short (2 sentences).
   - "I've analyzed your farm. The crop looks stressed due to low moisture..."
"""

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash", 
    tools=tools_list,
    system_instruction=SYSTEM_PROMPT
)