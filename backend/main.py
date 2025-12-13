from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import random
import os
import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import httpx
import logging

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

try:
    from database import save_user
    from tools import get_nasa_weather
    from agent import handle_incoming_message
except ImportError:
    from backend.database import save_user
    from backend.tools import get_nasa_weather
    from backend.agent import handle_incoming_message

# MCP is optional (can be missing in hackathon env)
try:
    from mcp_client import mcp_manager
except Exception:
    try:
        from backend.mcp_client import mcp_manager
    except Exception:
        mcp_manager = None

try:
    from scheduler import scheduler_loop, morning_briefing_job
except ImportError:
    from backend.scheduler import scheduler_loop, morning_briefing_job

# Configure Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MAIN")

app = FastAPI()

# Serve backend/static at /static so MP3 links work
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# --- LIFECYCLE EVENTS ---
@app.on_event("startup")
async def startup_event():
    # Initialize MCP if available
    if mcp_manager is not None:
        await mcp_manager.initialize()
    
    # FIX: Prevent Double Scheduler using a simple flag check
    # The reloader sometimes runs startup twice. We only want one scheduler.
    if not hasattr(app.state, "scheduler_started"):
        app.state.scheduler_started = True
        import asyncio
        asyncio.create_task(scheduler_loop())

@app.on_event("shutdown")
async def shutdown_event():
    if mcp_manager is not None:
        print("🛑 Closing MCP Connections...")
        await mcp_manager.cleanup()

# --- EMAIL UTILS ---
def send_email_otp(to_email: str, otp: str):
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    
    if not smtp_user or not smtp_pass:
        print("⚠️ SMTP Credentials missing. Printing OTP to console instead.")
        print(f"📧 [MOCK EMAIL] To: {to_email} | OTP: {otp}")
        return

    msg = MIMEMultipart()
    msg['From'] = f"Spectra <{smtp_user}>"
    msg['To'] = to_email
    msg['Subject'] = "Your Spectra Verification Code"

    body = f"""
    <html>
        <body>
            <h2>Your Verification Code</h2>
            <p>Please use the following OTP to complete your verification:</p>
            <h1 style="color: #4CAF50; font-size: 32px; letter-spacing: 5px;">{otp}</h1>
            <p>This code is valid for 10 minutes.</p>
        </body>
    </html>
    """
    msg.attach(MIMEText(body, 'html'))

    try:
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        print(f"✅ Email sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        raise e

# --- 🛠️ DEBUGGING: CATCH 422 ERRORS ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    try:
        body = await request.body()
        body_str = body.decode()
        print(f"\n❌ REGISTRATION FAILED: Data Format Mismatch")
        print(f"📥 Incoming JSON from Frontend: {body_str}")
        print(f"⚠️ Specific Error: {exc.errors()}\n")
    except Exception:
        print("Could not print error details.")
        
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATA MODELS ---
class FarmerRegistration(BaseModel):
    name: str
    phone_number: str
    aadhar: str
    bank_acc: str
    language: str = "English"
    lat: Optional[float] = None
    long: Optional[float] = None
    crop: Optional[str] = None

class OTPRequest(BaseModel):
    phone_number: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None

class OTPVerify(BaseModel):
    phone_number: Optional[str] = None
    email: Optional[str] = None
    otp: str

# --- IN-MEMORY OTP STORAGE ---
otp_storage = {}

# --- ENDPOINTS ---

@app.get("/")
def read_root():
    return {"status": "Spectra Engine Online"}

@app.post("/send-otp")
def send_otp(request: OTPRequest):
    try:
        identifier = request.phone_number or request.email
        if not identifier:
            return {"success": False, "error": "Phone number or Email required"}

        otp = str(random.randint(100000, 999999))
        otp_storage[identifier] = otp
        
        print(f"\n🔐 [OTP SYSTEM] Generated OTP for {identifier}: {otp}\n")
        
        if request.email and "@" in request.email:
            send_email_otp(request.email, otp)

        return {"success": True}
    except Exception as e:
        print(f"Error sending OTP: {e}")
        return {"success": False, "error": str(e)}

@app.post("/verify-otp")
def verify_otp(request: OTPVerify):
    identifier = request.phone_number or request.email
    if not identifier:
        return {"success": False, "error": "Phone number or Email required"}

    stored_otp = otp_storage.get(identifier)
    if stored_otp and stored_otp == request.otp:
        del otp_storage[identifier]
        return {"success": True}
    else:
        return {"success": False, "error": "Invalid or Expired OTP"}

@app.post("/save")
def save_farmer_frontend(farmer: FarmerRegistration):
    print(f"📥 Received /save request for: {farmer.name}")
    return register_farmer(farmer)

@app.post("/api/register")
def register_farmer(farmer: FarmerRegistration):
    try:
        print(f"Incoming Data: {farmer.dict()}")
        
        formatted_phone = farmer.phone_number
        if not formatted_phone.startswith("91"):
            formatted_phone = "91" + formatted_phone
            
        result = save_user(
            phone=formatted_phone,
            name=farmer.name,
            aadhar=farmer.aadhar,
            bank_acc=farmer.bank_acc,
            language=farmer.language,
            lat=farmer.lat,
            lon=farmer.long,
            crop=farmer.crop
        )
        return {
            "status": "success", 
            "message": "Farmer Registered", 
            "user_id": str(result),
            "next_step": "Waiting for location via WhatsApp" if not farmer.lat else "Fetching NASA Data..."
        }
    except Exception as e:
        print(f"Error saving user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/whatsapp-webhook")
async def whatsapp_webhook(request: Request):
    try:
        payload = await request.json()
        logger.info(f"📩 WEBHOOK RECEIVED: {payload}")
        response = await handle_incoming_message(payload)
        return {"status": "received", "agent_response": response}
    except Exception as e:
        logger.error(f"❌ Webhook Error: {e}")
        return {"status": "error", "detail": str(e)}

@app.get("/api/test-nasa")
async def test_nasa(lat: float, lon: float):
    return get_nasa_weather(lat, lon)

@app.post("/admin/run-morning-brief")
async def run_morning_brief_now():
    """Manually triggers the morning briefing for all farmers."""
    asyncio.create_task(morning_briefing_job())
    return {"status": "success", "message": "Morning briefing job has been triggered."}