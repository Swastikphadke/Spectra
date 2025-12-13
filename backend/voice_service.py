import os
import uuid
import logging
from typing import Dict, Optional

import httpx
from gtts import gTTS

logger = logging.getLogger(__name__)

# Save audio under backend/static/audio so FastAPI can serve it via /static
BACKEND_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(BACKEND_DIR, "static")
AUDIO_DIR = os.path.join(STATIC_DIR, "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

BRIDGE_AUDIO_URL = "http://localhost:8080/api/send_audio"


def generate_mp3(text: str, language: str = "en") -> Dict[str, str]:
    """Generate an MP3 file using gTTS and return paths.

    Rule: MP3-only. No ffmpeg, no pydub, no ogg.
    """
    if not text or not text.strip():
        raise ValueError("Text is required for TTS")

    filename = f"voice_{uuid.uuid4().hex[:10]}.mp3"
    abs_path = os.path.join(AUDIO_DIR, filename)

    tts = gTTS(text=text.strip(), lang=language or "en", slow=False)
    tts.save(abs_path)

    return {
        "file_path": abs_path,
        "url_path": f"/static/audio/{filename}",
        "filename": filename,
    }


async def send_voice_note(recipient_jid: str, text: str, language: str = "en") -> Optional[str]:
    """Generate an MP3 voice note and upload it to the WhatsApp bridge.

    Returns the public URL path (served by FastAPI) if generation succeeds.
    """
    if not text or not text.strip():
        return None

    mp3 = generate_mp3(text=text, language=language)
    abs_path = mp3["file_path"]

    try:
        with open(abs_path, "rb") as f:
            file_bytes = f.read()

        files = {"file": (os.path.basename(abs_path), file_bytes, "audio/mpeg")}
        data = {
            "recipient": recipient_jid,
            "phone": recipient_jid,
            "is_voice_note": "true",
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(BRIDGE_AUDIO_URL, data=data, files=files, timeout=60)

        if resp.status_code != 200:
            logger.warning("Bridge rejected MP3 upload (%s): %s", resp.status_code, resp.text)

        return mp3["url_path"]
    except Exception as e:
        logger.error("Voice note send failed: %s", e)
        return mp3["url_path"]