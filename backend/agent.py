import logging
import httpx
import google.generativeai as genai
from database import get_user_by_phone
from brain import model, AVAILABLE_TOOLS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BRIDGE_URL = "http://localhost:8080/api/send"

def resolve_jid(sender_raw):
    """Standardizes JID for the WhatsApp Bridge."""
    sender = sender_raw.strip().replace("whatsapp:", "").replace("+", "").replace(" ", "")
    if "@" in sender: return sender
    if len(sender) >= 15: return f"{sender}@lid"
    return f"{sender}@s.whatsapp.net"

async def handle_incoming_message(payload: dict):
    """
    The Autonomous Agent Loop:
    Handles the 'Function Calling' turns between Gemini and your MCP tools.
    """
    sender_raw = payload.get("from", "")
    user_text = payload.get("content", "")
    
    if not sender_raw or not user_text: 
        return "Ignored"

    # 1. Database Lookup
    clean_phone = sender_raw.replace("whatsapp:", "").replace("+", "").strip()
    user = get_user_by_phone(clean_phone)
    recipient_id = resolve_jid(sender_raw)

    if not user:
        msg = "Namaste! 🙏 Please register your farm via our map portal first so I can analyze your crop data."
        await send_via_bridge(recipient_id, msg)
        return msg

    # 2. Autonomous Reasoning Loop
    try:
        # Context setup: Ensure Gemini knows WHERE the farm is
        lat = user.get('lat', 0.0)
        lon = user.get('lon', 0.0)
        farmer_context = (
            f"User Profile: {user.get('name')}. "
            f"Farm Location: Lat {lat}, Lon {lon}. "
            f"Crop: {user.get('crop')}."
        )
        
        # Check for invalid coordinates
        if lat == 0.0 and lon == 0.0:
            logger.warning(f"⚠️ User {user.get('name')} has 0.0 coordinates.")
        
        chat = model.start_chat()
        
        logger.info(f"🧠 Spectra analyzing request for {user.get('name')}...")
        response = await chat.send_message_async(f"{farmer_context}\n\nUser Question: {user_text}")

        # 🔄 THE TOOL LOOP: 
        # If Gemini requests a tool, we execute it using the protos.Part definition.
        while response.parts and response.parts[0].function_call:
            call = response.parts[0].function_call
            fn_name = call.name
            fn_args = call.args
            
            logger.info(f"🎯 Gemini decided to call: {fn_name}")
            
            # Execute the tool
            if fn_name in AVAILABLE_TOOLS:
                tool_result = await AVAILABLE_TOOLS[fn_name](**fn_args)
            else:
                tool_result = f"Error: Tool '{fn_name}' not recognized."

            # ✅ FIX: Use genai.protos for strict Protobuf alignment
            # This resolves the 'module types has no attribute Part' error
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

        # Final AI Text Response
        ai_reply = response.text
        
    except Exception as e:
        logger.error(f"❌ Spectra Reasoning Error: {e}")
        ai_reply = "I'm checking the satellite feeds for your farm. Please wait a moment!"

    # 3. Send final advice back via Bridge
    await send_via_bridge(recipient_id, ai_reply)
    return ai_reply

async def send_via_bridge(to_jid: str, text: str):
    """REST API call to the WhatsApp bridge."""
    async with httpx.AsyncClient() as client:
        payload = {"recipient": to_jid, "message": text}
        try:
            resp = await client.post(BRIDGE_URL, json=payload, timeout=15.0)
            if resp.status_code == 200:
                logger.info(f"✅ Advice delivered to {to_jid}")
            else:
                logger.error(f"⚠️ Bridge Error: {resp.text}")
        except Exception as e:
            logger.error(f"❌ Failed to reach Bridge: {e}")