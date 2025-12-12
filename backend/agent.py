import logging
import httpx
import os
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from database import get_user_by_phone
from brain import model, AVAILABLE_TOOLS
from tools import get_nasa_weather # Import directly for the brief

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Endpoints
BRIDGE_BASE_URL = "http://localhost:8080"

def resolve_jid(sender_raw):
    sender = sender_raw.strip().replace("whatsapp:", "").replace("+", "").replace(" ", "")
    if "@" in sender: return sender
    if len(sender) >= 15: return f"{sender}@lid"
    return f"{sender}@s.whatsapp.net"

async def handle_incoming_message(payload: dict):
    sender_raw = payload.get("from", "")
    user_text = payload.get("content", "")
    
    if not sender_raw: return "Ignored"

    clean_phone = sender_raw.replace("whatsapp:", "").replace("+", "").strip()
    user = get_user_by_phone(clean_phone)
    recipient_id = resolve_jid(sender_raw)

    if not user:
        await send_text_via_bridge(recipient_id, "Please register first.")
        return "Register Prompt"

    try:
        # Context setup
        lat = user.get('lat', 0.0)
        lon = user.get('lon', 0.0)
        
        # ⭐ SYSTEM INSTRUCTION: Force text-only mode
        system_instruction = (
            "You are an agricultural AI assistant. "
            "IMPORTANT: You CANNOT send images directly. "
            "When a tool generates a map or image, you must READ the data values (like NDVI, moisture, stress levels) "
            "and DESCRIBE the situation to the farmer in simple text. "
            "Never say 'I am sending an image'. Instead say 'Based on the satellite analysis, here is the status...'."
        )

        farmer_context = (
            f"{system_instruction}\n\n"
            f"User Profile: {user.get('name')}. "
            f"Farm Location: Lat {lat}, Lon {lon}. "
            f"Crop: {user.get('crop')}."
        )
        
        chat = model.start_chat()
        
        print(f"\n🧠 [GEMINI] Analyzing request for {user.get('name')}...")
        response = await chat.send_message_async(f"{farmer_context}\n\nUser Question: {user_text}")

        # 🔄 THE TOOL LOOP
        while response.parts and response.parts[0].function_call:
            call = response.parts[0].function_call
            fn_name = call.name
            fn_args = call.args
            
            print(f"🎯 [GEMINI] Calling Tool: {fn_name} with args: {fn_args}")
            
            if fn_name in AVAILABLE_TOOLS:
                tool_result = await AVAILABLE_TOOLS[fn_name](**fn_args)
                print(f"✅ [TOOL RESULT RAW] {str(tool_result)[:100]}...") 

                # 🛠️ INTERCEPT & MODIFY RESULT FOR GEMINI
                if isinstance(tool_result, dict) and "image_path" in tool_result:
                    # Extract useful data for the AI to talk about
                    avg_ndvi = tool_result.get('average_ndvi', 'Unknown')
                    status = tool_result.get('status', 'Unknown')
                    
                    # HIDE the image path so Gemini doesn't get tempted
                    tool_result.pop("image_path", None) 
                    
                    # Inject a strong instruction
                    tool_result["system_instruction"] = (
                        f"Analysis Complete. Status: {status}. Average NDVI: {avg_ndvi}. "
                        "Do NOT mention sending an image. "
                        "Explain this status to the farmer. If NDVI is low (<0.3), warn about stress. "
                        "If high (>0.5), say crop is healthy."
                    )
            else:
                tool_result = f"Error: Tool '{fn_name}' not recognized."

            # Feed result back to Gemini
            response = await chat.send_message_async(
                genai.protos.Content(
                    parts=[genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=fn_name,
                            response={'result': str(tool_result)}
                        )
                    )]
                )
            )

        ai_reply = response.text
        print(f"🤖 [GEMINI REPLY] {ai_reply}")

    except ResourceExhausted:
        print("❌ [GEMINI] Quota Exceeded")
        ai_reply = "I am currently overloaded. Please try again in 1 minute."
    except Exception as e:
        print(f"❌ [ERROR] {e}")
        ai_reply = "System error. Please try again."

    await send_text_via_bridge(recipient_id, ai_reply)
    return ai_reply

# --- 📤 TEXT SENDER ---
async def send_text_via_bridge(to_jid: str, text: str):
    async with httpx.AsyncClient() as client:
        payload = {
            "recipient": to_jid,
            "phone": to_jid,
            "message": text
        }
        
        endpoints = ["/api/send", "/send/text", "/send"]
        
        for endpoint in endpoints:
            url = f"{BRIDGE_BASE_URL}{endpoint}"
            try:
                # print(f"📤 Trying Bridge Endpoint: {url}...")
                resp = await client.post(url, json=payload, timeout=5)
                
                if resp.status_code == 200:
                    print(f"✅ Message Delivered via {endpoint}!")
                    return 
                elif resp.status_code != 404:
                    print(f"⚠️ Bridge Error ({resp.status_code}): {resp.text}")
                    return 
            except Exception as e:
                print(f"❌ Connection Error to {endpoint}: {e}")

        print("❌ Failed to send message on all known endpoints.")

# =========================================================
# 🔥 NEW FEATURE — Proactive Morning Brief (Scheduler Use)
# =========================================================
async def generate_morning_brief(farmer: dict) -> str:
    """
    Generates a short, reliable morning advisory.
    This is used by the scheduler — NOT WhatsApp chat.
    """

    lat = farmer.get("lat")
    lon = farmer.get("lon")
    crop = farmer.get("crop", "crop")
    language = farmer.get("language", "en")

    if not lat or not lon:
        return "⚠️ Location not available. Please update your farm location."

    # ❌ REMOVED 'await' because get_nasa_weather is synchronous in tools.py
    weather = get_nasa_weather(lat, lon)

    if isinstance(weather, str) or "error" in weather:
        return "⚠️ Unable to fetch today's weather data."

    rain = weather.get("rainfall_mm", 0)
    temp = weather.get("temperature_c", 0)

    # Simple, deterministic advice
    advice = "Monitor your field today."

    if rain > 10:
        advice = "Rain expected. Avoid irrigation."
    elif temp > 35:
        advice = "High temperature. Ensure adequate soil moisture."

    # Language handling (basic)
    if language and language.lower().startswith("hi"):
        return (
            "🌅 सुप्रभात!\n\n"
            f"🌱 फसल: {crop}\n"
            f"🌧 वर्षा: {rain} मिमी\n"
            f"🌡 तापमान: {temp}°C\n\n"
            f"✅ सलाह: {advice}"
        )

    # Default: English
    return (
        "🌅 Good Morning!\n\n"
        f"🌱 Crop: {crop}\n"
        f"🌧 Rain: {rain} mm\n"
        f"🌡 Temp: {temp} °C\n\n"
        f"✅ Advice: {advice}"
    )