import google.generativeai as genai
import os
import logging
from dotenv import load_dotenv

# Import MCP Client Wrappers
from mcp_client import get_nasa_weather_mcp, get_gis_data_mcp, calculate_ndvi_mcp

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

async def calculate_ndvi(lat: float, lon: float):
    """Calculates vegetation health via the GIS MCP tool (calculate_ndvi)."""
    logger.info("🎯 Gemini calling NDVI Tool")
    ndvi_raw = await calculate_ndvi_mcp(lat, lon)
    try:
        ndvi_val = float(ndvi_raw)
    except Exception:
        return {"error": f"Invalid NDVI value: {ndvi_raw}"}

    status = "Healthy" if ndvi_val >= 0.6 else "Moderate" if ndvi_val >= 0.4 else "Stressed"
    return {"ndvi": round(ndvi_val, 2), "status": status}

# ==========================================
# ⚙️ EXPORTED TOOLS (THIS WAS MISSING!)
# ==========================================
AVAILABLE_TOOLS = {
    "get_nasa_satellite_weather": get_nasa_satellite_weather,
    "get_gis_terrain_data": get_gis_terrain_data,
    "calculate_ndvi": calculate_ndvi
}

tools_list = [get_nasa_satellite_weather, get_gis_terrain_data, calculate_ndvi]

# ==========================================
# 🧠 SYSTEM PROMPT & MODEL
# ==========================================
SYSTEM_PROMPT = """
You are 'Spectra', a trusted Agricultural Advisor for small farmers in India.
Your mission is to translate complex satellite data into simple, caring, and actionable advice.

### ✅ HEALTH MODE (MANDATORY)
If the user asks about "health" / "crop health" / "NDVI", you MUST:
1) Call `get_nasa_satellite_weather(lat, lon)` to fetch satellite context for that location.
2) Call `calculate_ndvi(lat, lon)` using the GIS MCP.
3) Explain the result in simple text (no jargon).

### 🚫 STRICT RULES:
1. **NO Jargon:** Never use words like "NDVI", "spectral reflectance", or "chlorophyll". Say "Crop Health" or "Greenness" instead.
3. **TONE:** Polite, respectful, and encouraging (like a wise village elder).
4. **INTERPRETATION:**
   - Health > 0.6: "Strong, healthy growth."
   - Health 0.4-0.6: "Moderate growth, needs care."
   - Health < 0.4: "Weak growth, under stress."

### 📝 RESPONSE FORMAT (MANDATORY):

You must return TWO parts separated by the divider `===VOICE_SUMMARY===`.

#### PART 1: DETAILED TEXT (For WhatsApp Chat)
Follow this exact layout. Keep it under 120 words.

🌱 **Crop Health Summary:**
[1 short line describing overall condition]

🧠 **What This Means:**
[1-2 simple lines. E.g., "The plants are thirsty because rainfall has been low."]

📍 **Field Observation:**
[State the NDVI-based health as a simple sentence.]

✅ **What You Should Do:**
[2-3 simple steps. E.g., "1. Visit the yellow spots today. 2. Check soil moisture."]

📡 *Note: Based on latest satellite scans.*

---
===VOICE_SUMMARY===
---

#### PART 2: VOICE SCRIPT (For Audio Note)
- **Style:** Conversational, warm, spoken language.
- **Length:** Very short (2 sentences max).
- **Content:** Summarize the health status and the single most important action.
- **Example:** "Namaste! Your crop looks mostly good, but the northern side is drying out. Please check the water there today."
"""

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash", 
    tools=tools_list,
    system_instruction=SYSTEM_PROMPT
)