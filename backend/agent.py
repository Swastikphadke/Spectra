import logging
import httpx
import os
import google.generativeai as genai
from database import get_user_by_phone
from brain import model, AVAILABLE_TOOLS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Endpoints
BRIDGE_TEXT_URL = "http://localhost:8080/api/send"
BRIDGE_IMAGE_URL = "http://localhost:8080/send/image"

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
    
    if not sender_raw: 
        return "Ignored"

    # 1. Database Lookup
    clean_phone = sender_raw.replace("whatsapp:", "").replace("+", "").strip()
    user = get_user_by_phone(clean_phone)
    recipient_id = resolve_jid(sender_raw)

    if not user:
        msg = "Namaste! 🙏 Please register your farm via our map portal first so I can analyze your crop data."
        await send_text_via_bridge(recipient_id, msg)
        return "Register Prompt"

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

                # 📸 IMAGE DETECTION LOGIC
                # If the tool generated an image, send it IMMEDIATELY
                if isinstance(tool_result, dict) and "image_path" in tool_result:
                    image_path = tool_result["image_path"]
                    logger.info(f"📸 Detected Image: {image_path}")
                    
                    # Send the image to WhatsApp
                    await send_image_via_bridge(recipient_id, image_path, "Here is your Satellite Health Scan 🛰️")
                    
                    # Modify result for Gemini so it knows we sent it
                    tool_result["system_note"] = "Image sent to user successfully via WhatsApp."
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

        # Final AI Text Response
        ai_reply = response.text
        
    except Exception as e:
        logger.error(f"❌ Spectra Reasoning Error: {e}")
        ai_reply = "I'm checking the satellite feeds for your farm. Please wait a moment!"

    # 3. Send final advice back via Bridge
    await send_text_via_bridge(recipient_id, ai_reply)
    return ai_reply

# --- 📤 TEXT SENDER ---
async def send_text_via_bridge(to_jid: str, text: str):
    """REST API call to the WhatsApp bridge for text."""
    async with httpx.AsyncClient() as client:
        payload = {"recipient": to_jid, "message": text}
        try:
            resp = await client.post(BRIDGE_TEXT_URL, json=payload, timeout=15.0)
            if resp.status_code == 200:
                logger.info(f"✅ Text delivered to {to_jid}")
            else:
                logger.error(f"⚠️ Bridge Error: {resp.text}")
        except Exception as e:
            logger.error(f"❌ Failed to reach Bridge: {e}")

# --- 📸 IMAGE SENDER (NEW) ---
async def send_image_via_bridge(to_jid: str, file_path: str, caption: str = ""):
    """Uploads the file to the bridge using Multipart Form Data."""
    if not os.path.exists(file_path):
        logger.error(f"❌ File not found: {file_path}")
        return

    async with httpx.AsyncClient() as client:
        try:
            # 1. Read file binary
            with open(file_path, 'rb') as f:
                file_content = f.read()

            # 2. Prepare Multipart (Try 'image' key first, it's most common)
            files = {
                'image': (os.path.basename(file_path), file_content, 'image/png')
            }
            
            # 3. Data Payload (Send both 'phone' and 'id' to be safe)
            data = {
                "phone": to_jid.replace("@s.whatsapp.net", ""), # Some bridges want just the number
                "caption": caption,
                "view_once": "false",
                "compress": "true"
            }

            logger.info(f"📤 Uploading image to: {BRIDGE_IMAGE_URL}")
            
            resp = await client.post(BRIDGE_IMAGE_URL, data=data, files=files, timeout=30)
            
            if resp.status_code == 200:
                logger.info("✅ Image sent successfully!")
            else:
                logger.error(f"⚠️ Upload Failed {resp.status_code}: {resp.text}")
                # Fallback: Try /api/send-image if /send/image failed
                if resp.status_code == 404:
                     logger.warning("Trying fallback endpoint: /api/send-image")
                     await client.post("http://localhost:8080/api/send-image", data=data, files=files)

        except Exception as e:
            logger.error(f"❌ Image Send Error: {e}")
    """Uploads the file to the bridge using Multipart Form Data."""
    if not os.path.exists(file_path):
        logger.error(f"❌ File not found: {file_path}")
        return

    async with httpx.AsyncClient() as client:
        try:
            # Prepare Multipart Upload
            files = {
                'file': (os.path.basename(file_path), open(file_path, 'rb'), 'image/png')
            }
            # Most bridges use 'phone', 'recipient', or 'jid'
            data = {
                "recipient": to_jid,
                "phone": to_jid, # Sending both to be safe
                "caption": caption
            }
            
            logger.info(f"📤 Uploading image to Bridge: {BRIDGE_IMAGE_URL}")
            resp = await client.post(BRIDGE_IMAGE_URL, data=data, files=files, timeout=30)
            
            if resp.status_code == 200:
                logger.info("✅ Image sent successfully!")
            else:
                logger.error(f"⚠️ Image Upload Failed {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.error(f"❌ Error uploading image: {e}")