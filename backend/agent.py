import logging
import httpx
import google.generativeai as genai
from database import get_user_by_phone
# ✅ THIS IMPORT MUST MATCH BRAIN.PY
from brain import model, AVAILABLE_TOOLS 
from mcp_client import get_nasa_weather_mcp
from voice_service import send_voice_note 

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BRIDGE_URL = "http://localhost:8080/api/send"

def resolve_jid(sender_raw):
    sender = sender_raw.strip().replace("whatsapp:", "").replace("+", "").replace(" ", "")
    if "@" in sender: return sender
    if len(sender) >= 15: return f"{sender}@lid"
    return f"{sender}@s.whatsapp.net"

# ... (Rest of the file remains the same as the "Safe Dictionary" version I sent earlier) ...

# ==========================================
# 🧠 MAIN AUTONOMOUS AGENT
# ==========================================
async def handle_incoming_message(payload: dict):
    sender_raw = payload.get("from", "")
    user_text = payload.get("content", "")
    
    if not sender_raw: return "Ignored"

    clean_phone = sender_raw.replace("whatsapp:", "").replace("+", "").replace(" ", "").strip()
    user = get_user_by_phone(clean_phone)
    recipient_id = resolve_jid(sender_raw)

    if not user:
        await send_text_via_bridge(recipient_id, "Please register first.")
        return "Register Prompt"

    try:
        lat = user.get('lat', 0.0)
        lon = user.get('lon', 0.0)
        farmer_context = f"User: {user.get('name')}. Lat: {lat}, Lon: {lon}."
        
        chat = model.start_chat()
        logger.info(f"🧠 Spectra analyzing for {user.get('name')}...")
        response = await chat.send_message_async(f"{farmer_context}\n\nUser Question: {user_text}")

        # 🔄 TOOL LOOP
        while response.parts and response.parts[0].function_call:
            call = response.parts[0].function_call
            fn_name = call.name
            fn_args = call.args
            
            logger.info(f"🎯 Gemini calling: {fn_name}")
            
            # Execute Tool
            tool_result = {"error": "Tool not found"}
            if fn_name in AVAILABLE_TOOLS:
                try:
                    tool_result = await AVAILABLE_TOOLS[fn_name](**fn_args)
                except Exception as e:
                    logger.error(f"Tool Error: {e}")
                    tool_result = {"error": str(e)}
                
                # Check for Map
                if isinstance(tool_result, dict) and "map_url" in tool_result:
                    logger.info(f"📸 Map Generated: {tool_result['map_url']}")
            
            # Send result back (Safe Dict Mode)
            function_response = {
                "parts": [{
                    "function_response": {
                        "name": fn_name,
                        "response": {"result": str(tool_result)} 
                    }
                }]
            }
            response = await chat.send_message_async(function_response)

        ai_reply = response.text

        # 🎤 SPLIT TEXT & VOICE
        if "===VOICE_SUMMARY===" in ai_reply:
            parts = ai_reply.split("===VOICE_SUMMARY===")
            text_part = parts[0].strip()
            voice_part = parts[1].strip() if len(parts) > 1 else ""
            
            if text_part:
                await send_text_via_bridge(recipient_id, text_part)
            
            if voice_part:
                logger.info("🎤 Sending Voice Note...")
                lang = 'hi' if 'hindi' in str(user.get('language', '')).lower() else 'en'
                await send_voice_note(recipient_id, voice_part, language=lang)
        else:
            await send_text_via_bridge(recipient_id, ai_reply)

    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        await send_text_via_bridge(recipient_id, "System error. Please try again.")

    return "Done"

async def send_text_via_bridge(to_jid: str, text: str):
    async with httpx.AsyncClient() as client:
        try:
            await client.post(BRIDGE_URL, json={"recipient": to_jid, "message": text}, timeout=15)
        except Exception as e:
            logger.error(f"❌ Text Send Failed: {e}")

# IMPORTANT: Keep this for the scheduler!
async def generate_morning_brief(farmer: dict) -> str:
    lat = farmer.get("lat")
    lon = farmer.get("lon")
    name = farmer.get("name", "Farmer")
    if not lat or not lon: return None
    try:
        weather = await get_nasa_weather_mcp(lat, lon)
        weather_summary = str(weather)[:200]
    except:
        weather_summary = "Weather data unavailable."
    return f"🌅 *Good Morning {name}!*\n\n{weather_summary}\n\nTip: Check soil moisture."