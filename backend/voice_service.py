import os
import httpx
import subprocess
import uuid
import logging
from gtts import gTTS

# Configure Logging
logger = logging.getLogger(__name__)

# Directory to store audio files (backend/static/audio)
# We use os.path.abspath to ensure we find the right folder relative to where you run the script
BASE_DIR = os.getcwd()
AUDIO_DIR = os.path.join(BASE_DIR, "static", "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

# Bridge Endpoints
# Primary: Your requested endpoint
BRIDGE_AUDIO_URL = "http://localhost:8080/api/send_audio" 
# Fallback: Standard file endpoint for many bridges
BRIDGE_FILE_URL = "http://localhost:8080/send/file" 

def convert_mp3_to_ogg(mp3_path: str) -> str:
    """
    Converts MP3 to OGG (Opus) using FFmpeg for WhatsApp compatibility.
    """
    ogg_path = mp3_path.replace(".mp3", ".ogg")
    
    # WhatsApp requires Opus codec for voice notes
    command = [
        "ffmpeg", "-y", 
        "-i", mp3_path, 
        "-c:a", "libopus", 
        "-b:a", "16k", 
        "-application", "voip",
        ogg_path
    ]
    
    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return ogg_path
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ FFmpeg Conversion Failed: {e}")
        return None
    except FileNotFoundError:
        logger.error("❌ FFmpeg not found! Install it and add to System PATH.")
        return None

async def send_voice_note(recipient_jid: str, text: str, language: str = 'en'):
    """
    Generates a voice note and sends it via the WhatsApp Bridge.
    """
    if not text: return

    # 1. Generate Unique Filename
    filename = f"voice_{uuid.uuid4().hex[:8]}"
    mp3_path = os.path.join(AUDIO_DIR, f"{filename}.mp3")

    try:
        # 2. Text-to-Speech
        logger.info(f"🎙️ Generating Voice Note...")
        tts = gTTS(text=text, lang=language, slow=False)
        tts.save(mp3_path)

        # 3. Convert to OGG
        ogg_path = convert_mp3_to_ogg(mp3_path)
        
        if not ogg_path or not os.path.exists(ogg_path):
            logger.error("❌ OGG file creation failed.")
            return

        # 4. Send to Bridge
        async with httpx.AsyncClient() as client:
            with open(ogg_path, 'rb') as f:
                file_content = f.read()

            files = {'file': (os.path.basename(ogg_path), file_content, 'audio/ogg')}
            
            # Send 'phone' and 'recipient' to be compatible with different bridges
            data = {
                "recipient": recipient_jid,
                "phone": recipient_jid.replace("@s.whatsapp.net", ""),
                "is_voice_note": "true" 
            }
            
            logger.info(f"📤 Uploading Voice Note to Bridge...")
            
            try:
                # Try primary endpoint
                resp = await client.post(BRIDGE_AUDIO_URL, data=data, files=files, timeout=60)
            except:
                resp = None

            # Fallback if primary fails or 404s
            if not resp or resp.status_code != 200:
                logger.warning(f"⚠️ Primary endpoint failed. Trying {BRIDGE_FILE_URL}...")
                # Reset file pointer or re-open
                files = {'file': (os.path.basename(ogg_path), file_content, 'audio/ogg')}
                resp = await client.post(BRIDGE_FILE_URL, data=data, files=files, timeout=60)

            if resp.status_code == 200:
                logger.info(f"✅ Voice Note Delivered! (Saved at: {ogg_path})")
            else:
                logger.error(f"⚠️ Bridge Failed ({resp.status_code}): {resp.text}")

    except Exception as e:
        logger.error(f"❌ Voice Service Error: {e}")

    finally:
        # 5. Cleanup ONLY MP3 (Keep OGG as requested)
        if os.path.exists(mp3_path):
            os.remove(mp3_path)