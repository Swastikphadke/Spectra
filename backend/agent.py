import logging
import httpx
import json
from database import get_user_by_phone
from mcp_client import (
    get_nasa_weather_mcp as get_weather_data,
    get_nasa_apod_mcp,
    get_gis_data_mcp
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WHATSAPP_BRIDGE_URL = "http://localhost:8080/api/send"

def resolve_jid(sender_raw):
    """Resolves the JID from the sender string, compatible with the bridge."""
    sender = sender_raw.strip().replace("whatsapp:", "").replace("+", "").replace(" ", "")
    if "@" in sender: return sender
    if "-" in sender: return f"{sender}@g.us"
    if len(sender) >= 15: return f"{sender}@lid"
    return f"{sender}@s.whatsapp.net"

async def handle_incoming_message(payload: dict) -> dict:
    """
    Handles incoming WhatsApp messages.
    """
    sender_phone = payload.get("from")
    msg_type = payload.get("type")
    content = payload.get("content", "").lower()

    if not sender_phone:
        return {"status": "error", "message": "No sender phone found"}

    # Resolve JID for the bridge
    recipient_id = resolve_jid(sender_phone)
    logger.info(f"Processing message from {sender_phone} (JID: {recipient_id})")

    # 1. Check if user exists
    user = get_user_by_phone(sender_phone)
    if not user:
        clean_phone = sender_phone.replace("whatsapp:+", "").replace("whatsapp:", "")
        user = get_user_by_phone(clean_phone)
    
    if not user:
        await send_via_bridge(recipient_id, "I don't have your farm details yet. Please register first.")
        return {"status": "handled", "action": "register_prompt"}

    # 2. Handle Commands
    if "nasa" in content:
        logger.info("Querying NASA APOD...")
        try:
            res_text = await get_nasa_apod_mcp()
            # Handle JSON vs Text return from NASA tool
            if res_text.strip().startswith("{"):
                data = json.loads(res_text)
                reply = f"🛰️ NASA: {data.get('title', 'Space Data')}"
            else:
                reply = f"🛰️ NASA: {res_text[:100]}..."
        except Exception as e:
            reply = "NASA Error."
            logger.error(f"NASA Error: {e}")
        
        await send_via_bridge(recipient_id, reply)
        return {"status": "handled", "action": "nasa_apod"}

    elif "map" in content:
        logger.info("Querying GIS...")
        try:
            res_text = await get_gis_data_mcp("Farm")
            reply = f"🗺️ GIS: {res_text}"
        except Exception as e:
            reply = "GIS Error."
            logger.error(f"GIS Error: {e}")
        
        await send_via_bridge(recipient_id, reply)
        return {"status": "handled", "action": "gis_map"}

    elif "water" in content or "should i water" in content:
        lat = user.get("lat")
        lon = user.get("lon")
        
        if not lat and "location" in user:
            lat = user["location"].get("lat")
            lon = user["location"].get("lon")

        if lat is None or lon is None:
            await send_via_bridge(recipient_id, "I need your farm location to advise on watering. Please update your profile.")
            return {"status": "handled", "action": "location_missing"}

        # Call tools (WITH AWAIT)
        logger.info(f"Fetching weather for {lat}, {lon}")
        weather_info = await get_weather_data(lat, lon)
        
        reply = compose_agronomist_reply(weather_info, user.get("name", "Farmer"))
        await send_via_bridge(recipient_id, reply)
        return {"status": "handled", "action": "water_advice"}

    # 3. Fallback / Echo
    fallback_msg = f"Spectra: {content}"
    await send_via_bridge(recipient_id, fallback_msg)
    return {"status": "handled", "action": "fallback"}

async def send_via_bridge(to_jid: str, text: str):
    """Sends a message via the WhatsApp bridge using HTTPX."""
    payload = {
        "recipient": to_jid,
        "message": text
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(WHATSAPP_BRIDGE_URL, json=payload)
            if response.status_code != 200:
                logger.error(f"Failed to send message: {response.text}")
            else:
                logger.info(f"Message sent to {to_jid}")
        except Exception as e:
            logger.error(f"Error sending message via bridge: {e}")

def compose_agronomist_reply(weather_data: str, name: str) -> str:
    """Generates a helpful message based on weather data."""
    if isinstance(weather_data, dict) and "error" in weather_data:
        return "I'm having trouble accessing satellite data right now. Please try again later."

    msg = f"🌱 *Spectra Agronomist Report for {name}* 🌱\n\n"
    msg += str(weather_data) # Ensure string
    return msg
