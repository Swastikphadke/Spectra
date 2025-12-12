import logging
import httpx
from database import get_user_by_phone
from brain import model  # We only need the 'model' from brain.py

logger = logging.getLogger(__name__)
BRIDGE_URL = "http://localhost:8080/api/send"

def resolve_jid(sender_raw):
    """Standardizes JID for the WhatsApp Bridge."""
    sender = sender_raw.strip().replace("whatsapp:", "").replace("+", "").replace(" ", "")
    if "@" in sender: return sender
    if len(sender) >= 15: return f"{sender}@lid"
    return f"{sender}@s.whatsapp.net"

async def handle_incoming_message(payload: dict):
    sender_raw = payload.get("from", "")
    user_text = payload.get("content", "")
    
    if not sender_raw or not user_text: 
        return "Ignored"

    # 1. Clean Phone & DB Check
    clean_phone = sender_raw.replace("whatsapp:", "").replace("+", "").strip()
    user = get_user_by_phone(clean_phone)
    recipient_id = resolve_jid(sender_raw)

    if not user:
        msg = "Namaste! 🙏 Welcome to Spectra. Please register your farm via our portal first so I can access your data."
        await send_via_bridge(recipient_id, msg)
        return msg

    # 2. Start Autonomous Session
    try:
        # Give Gemini the context it needs to call tools automatically
        farmer_context = f"User: {user.get('name')}. Farm Location: Lat {user.get('lat')}, Lon {user.get('lon')}. Crop: {user.get('crop')}."
        
        # Start chat with automatic function calling enabled
        chat = model.start_chat(enable_automatic_function_calling=True)
        
        logger.info(f"🧠 Spectra Reasoning for {user.get('name')}...")
        response = await chat.send_message_async(f"{farmer_context}\n\nUser: {user_text}")
        ai_reply = response.text
        
    except Exception as e:
        logger.error(f"❌ AI Reasoning Error: {e}")
        ai_reply = "I'm checking my satellite links. Please hold on a moment!"

    # 3. Send back to WhatsApp
    await send_via_bridge(recipient_id, ai_reply)
    return ai_reply

async def send_via_bridge(to_jid: str, text: str):
    async with httpx.AsyncClient() as client:
        payload = {"recipient": to_jid, "message": text}
        try:
            resp = await client.post(BRIDGE_URL, json=payload, timeout=15.0)
            if resp.status_code == 200:
                logger.info(f"✅ Advice delivered to {to_jid}")
            else:
                logger.error(f"⚠️ Bridge Error: {resp.text}")
        except Exception as e:
            logger.error(f"❌ Bridge Connection Failed: {e}")