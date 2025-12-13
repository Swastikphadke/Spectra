import json
import logging
import os
import re
from typing import Any, Callable, Dict, Optional

import httpx
import google.generativeai as genai

try:
    from database import get_user_by_phone
except ImportError:
    from backend.database import get_user_by_phone

# MP3-only voice generation (no ogg/ffmpeg)
try:
    from voice_service import send_voice_note
except ImportError:
    from backend.voice_service import send_voice_note

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BRIDGE_BASE_URL = "http://localhost:8080"


def _is_health_request(text: str) -> bool:
    t = (text or "").lower()
    return "health" in t or "ndvi" in t or "crop health" in t


async def _handle_health_request(user: dict, recipient_id: str) -> None:
    """Health flow: use NASA MCP (location satellite data) + GIS MCP (NDVI)."""
    try:
        try:
            from mcp_client import get_nasa_weather_mcp, calculate_ndvi_mcp
        except ImportError:
            from backend.mcp_client import get_nasa_weather_mcp, calculate_ndvi_mcp

        lat = user.get("lat") or (user.get("location", {}) or {}).get("lat")
        lon = user.get("lon") or (user.get("location", {}) or {}).get("lon")
        crop = user.get("crop", "crop")
        if lat is None or lon is None:
            await send_text_via_bridge(recipient_id, "⚠️ I need your farm location (lat/lon) to check crop health.")
            return

        # NASA MCP: fetch satellite weather/soil moisture for this location (best-effort)
        nasa_raw = await get_nasa_weather_mcp(float(lat), float(lon))

        # GIS MCP: NDVI (mocked by GIS-Real server)
        ndvi_raw = await calculate_ndvi_mcp(float(lat), float(lon))

        ndvi_val: Optional[float] = None
        try:
            ndvi_val = float(ndvi_raw)
        except Exception:
            ndvi_val = None

        status = "Unknown"
        if ndvi_val is not None:
            if ndvi_val >= 0.6:
                status = "Healthy"
            elif ndvi_val >= 0.4:
                status = "Moderate"
            else:
                status = "Stressed"

        text_part = (
            "🌱 **Crop Health Summary:**\n"
            f"Your crop looks **{status}** based on satellite-style NDVI.\n\n"
            "🧠 **What This Means:**\n"
            "Healthy = strong growth, Moderate = needs attention, Stressed = urgent care.\n\n"
            "📍 **Field Observation:**\n"
            f"Location used: lat {lat}, lon {lon}. Crop: {crop}.\n\n"
            "✅ **What You Should Do:**\n"
            "1) Check low-growth patches today.\n2) Check soil moisture near roots.\n3) Irrigate only if soil is dry.\n\n"
            f"📡 NDVI: {ndvi_val if ndvi_val is not None else 'unavailable'}\n"
        )

        voice_part = (
            f"Namaste! Your crop health looks {status.lower()}. "
            "Please check the soil moisture and the weaker patches today."
        )

        await send_text_via_bridge(recipient_id, text_part)

        lang = "hi" if "hindi" in str(user.get("language", "")).lower() else "en"
        await send_voice_note(recipient_id, voice_part, language=lang)

    except Exception as e:
        logger.error("Health request failed: %s", e, exc_info=True)
        await send_text_via_bridge(recipient_id, "⚠️ Couldn't fetch crop health right now. Please try again.")


def _safe_import_rag() -> Optional[Callable[[str], str]]:
    """RAG is optional (langchain deps may be missing)."""
    try:
        from rag_engine import get_rag_context  # type: ignore

        return get_rag_context
    except Exception:
        return None


def _configure_gemini() -> None:
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GOOGLE_API_KEY (or GEMINI_API_KEY) in environment")
    genai.configure(api_key=api_key)


MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def _available_tools() -> Dict[str, Callable[..., Any]]:
    """Simple dict-based tools (no genai.protos)."""
    try:
        from tools import get_nasa_weather
    except ImportError:
        from backend.tools import get_nasa_weather

    return {
        "get_nasa_weather": get_nasa_weather,
    }


def _extract_json_object(text: str) -> Dict[str, Any]:
    """Extract the first JSON object from model output."""
    if not text:
        raise ValueError("Empty model response")

    # Common Gemini failure mode: wraps JSON in ```json fences
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        text = fenced.group(1)

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"No JSON object found in: {text[:200]}")

    candidate = text[start : end + 1]

    # Remove raw control characters that break json.loads (keep \t\n\r)
    # This does NOT fix all malformed JSON, but prevents hard crashes.
    candidate = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", candidate)

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        # Common failure: the model puts real newlines/tabs inside JSON strings.
        # Flatten whitespace and retry. This keeps JSON valid and avoids crashing.
        flattened = candidate.replace("\r", " ").replace("\n", " ").replace("\t", " ")
        flattened = re.sub(r"\s+", " ", flattened).strip()
        try:
            return json.loads(flattened)
        except Exception:
            # Absolute fallback: treat the whole response as final text.
            return {"final": text.strip()}


def _run_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    tools = _available_tools()
    if name not in tools:
        return {"error": f"Unknown tool '{name}'"}

    try:
        result = tools[name](**(args or {}))
        if isinstance(result, dict):
            return result
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}


async def _gemini_with_tools(prompt: str, max_steps: int = 4) -> str:
    """Robust tool loop using dict JSON protocol (no proto function calling)."""
    _configure_gemini()
    model = genai.GenerativeModel(MODEL_NAME)

    tool_results: list[Dict[str, Any]] = []
    for _ in range(max_steps):
        tools_desc = [
            {
                "name": "get_nasa_weather",
                "args": {"lat": "number", "lon": "number"},
                "returns": "{rainfall_mm:number, temperature_c:number, note?:string}",
            }
        ]

        protocol = (
            "Return ONLY valid JSON (no Markdown, no code fences). Choose ONE:\n"
            "- Tool call: {\"tool\": \"tool_name\", \"args\": {...}}\n"
            "- Final answer: {\"final\": \"text\"}\n"
            "If you need newlines inside a string, write them as \\n (escaped).\n"
        )

        tool_ctx = ""
        if tool_results:
            tool_ctx = "\n\nTOOL_RESULTS (most recent last):\n" + json.dumps(tool_results, ensure_ascii=False)

        full_prompt = (
            protocol
            + "\nTOOLS:\n"
            + json.dumps(tools_desc, ensure_ascii=False)
            + tool_ctx
            + "\n\nUSER_CONTEXT_AND_REQUEST:\n"
            + prompt
        )

        resp = model.generate_content(full_prompt)
        raw_text = getattr(resp, "text", "") or ""
        try:
            data = _extract_json_object(raw_text)
        except Exception as e:
            logger.warning("Gemini returned non-JSON; falling back to plain text (%s)", e)
            return raw_text.strip() or ""

        if isinstance(data, dict) and data.get("tool"):
            tool_name = str(data.get("tool"))
            args = data.get("args")
            if not isinstance(args, dict):
                args = {}
            tool_results.append({"tool": tool_name, "args": args, "result": _run_tool(tool_name, args)})
            continue

        final = data.get("final") if isinstance(data, dict) else None
        if isinstance(final, str) and final.strip():
            return final.strip()

        # Fallback: if model didn't follow schema
        return getattr(resp, "text", "").strip() or ""

    # If we hit max tool steps, provide best-effort summary
    if tool_results:
        return "Here is what I found: " + json.dumps(tool_results[-1]["result"], ensure_ascii=False)
    return ""

def resolve_jid(sender_raw):
    sender = sender_raw.strip().replace("whatsapp:", "").replace("+", "").replace(" ", "")
    if "@" in sender: return sender
    if len(sender) >= 15: return f"{sender}@lid"
    return f"{sender}@s.whatsapp.net"

# ==========================================
# 🧠 MAIN AUTONOMOUS AGENT
# ==========================================
async def handle_incoming_message(payload: dict):
    # "from" is now the Phone Number (thanks to main.go fix)
    phone_number_raw = payload.get("from", "") 
    # "sender_jid" is the specific device (LID) to reply to
    reply_to_jid = payload.get("sender_jid", "") 
    
    user_text = payload.get("content", "")

    if not phone_number_raw: return "Ignored"

    # Use the specific device JID if available, otherwise fallback to phone number
    recipient_id = reply_to_jid if reply_to_jid else resolve_jid(phone_number_raw)

    clean_phone = phone_number_raw.replace("whatsapp:", "").replace("+", "").replace(" ", "").strip()
    user = get_user_by_phone(clean_phone)

    if not user:
        await send_text_via_bridge(recipient_id, "Welcome to Spectra! 🌾\nI don't recognize this number. Please register via the app first.")
        return "Register Prompt"

    # If user asks about crop health, do the deterministic NASA+GIS MCP flow
    if _is_health_request(user_text):
        await _handle_health_request(user, recipient_id)
        return "Health Done"

    # Persist sender_jid for proactive messaging (scheduler)
    if reply_to_jid:
        try:
            try:
                from database import update_user_sender_jid
            except ImportError:
                from backend.database import update_user_sender_jid
            update_user_sender_jid(clean_phone, reply_to_jid)
        except Exception:
            pass

    try:
        lat = user.get("lat") or (user.get("location", {}) or {}).get("lat")
        lon = user.get("lon") or (user.get("location", {}) or {}).get("lon")

        rag_fn = _safe_import_rag()
        rag_text = ""
        if rag_fn:
            ctx = rag_fn(user_text) or ""
            if ctx:
                rag_text = f"\n\nRELEVANT_KB:\n{ctx}"

        prompt = (
            "You are Spectra, an agricultural assistant for Indian farmers.\n"
            "Keep answers simple, practical, and safe.\n\n"
            f"Farmer name: {user.get('name')}\n"
            f"Crop: {user.get('crop', 'crop')}\n"
            f"Location: lat={lat}, lon={lon}\n"
            + rag_text
            + "\n\n"
            "Respond in TWO parts separated by the divider '===VOICE_SUMMARY==='\n"
            "Part 1: WhatsApp text (<=120 words).\n"
            "Part 2: voice script (<=2 short sentences).\n\n"
            f"User message: {user_text}"
        )

        logger.info("🧠 Generating reply for %s", user.get("name"))
        ai_reply = await _gemini_with_tools(prompt)
        logger.info("🤖 [GEMINI REPLY] %s", ai_reply)

        if "===VOICE_SUMMARY===" in ai_reply:
            parts = ai_reply.split("===VOICE_SUMMARY===", 1)
            text_part = parts[0].strip()
            voice_part = parts[1].strip() if len(parts) > 1 else ""

            if text_part:
                await send_text_via_bridge(recipient_id, text_part)

            if voice_part:
                lang = "hi" if "hindi" in str(user.get("language", "")).lower() else "en"
                await send_voice_note(recipient_id, voice_part, language=lang)
        else:
            await send_text_via_bridge(recipient_id, ai_reply)

    except Exception as e:
        logger.error("❌ Agent error: %s", e, exc_info=True)
        await send_text_via_bridge(recipient_id, "System error. Please try again.")

    return "Done"

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
# IMPORTANT: Keep this for the scheduler!
async def generate_morning_brief(farmer: dict) -> str:
    """
    Generates a short, reliable morning advisory.
    This is used by the scheduler — NOT WhatsApp chat.
    """
    try:
        from tools import get_nasa_weather  # local import avoids circulars
    except ImportError:
        from backend.tools import get_nasa_weather

    lat = farmer.get("lat") or (farmer.get("location", {}) or {}).get("lat")
    lon = farmer.get("lon") or (farmer.get("location", {}) or {}).get("lon")
    crop = farmer.get("crop", "crop")
    language = str(farmer.get("language", "en") or "en")

    if lat is None or lon is None:
        return "⚠️ Location missing. Please share your farm location in the app."

    weather = get_nasa_weather(float(lat), float(lon))
    if not isinstance(weather, dict) or "error" in weather:
        return "⚠️ Unable to fetch weather right now. Please try later."

    rain = float(weather.get("rainfall_mm", 0) or 0)
    temp = float(weather.get("temperature_c", 0) or 0)

    advice = "Monitor your field today."
    if rain > 10:
        advice = "Rain expected. Avoid irrigation today."
    elif temp > 35:
        advice = "High heat expected. Check soil moisture and irrigate if dry."

    if language.lower().startswith("hi"):
        return (
            "🌅 सुप्रभात!\n\n"
            f"🌱 फसल: {crop}\n"
            f"🌧 वर्षा: {rain:.0f} मिमी\n"
            f"🌡 तापमान: {temp:.0f}°C\n\n"
            f"✅ सलाह: {advice}"
        )

    return (
        "🌅 Good Morning!\n\n"
        f"🌱 Crop: {crop}\n"
        f"🌧 Rain: {rain:.0f} mm\n"
        f"🌡 Temp: {temp:.0f} °C\n\n"
        f"✅ Advice: {advice}"
    )