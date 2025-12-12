# main.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError # Import this
from fastapi.responses import JSONResponse # Import this
from pydantic import BaseModel
from typing import Optional
import random

from database import save_user
from tools import get_nasa_weather
from agent import handle_incoming_message
from mcp_client import mcp_manager

app = FastAPI()

# --- 🛠️ DEBUGGING: CATCH 422 ERRORS ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    This function runs automatically when data format is wrong.
    It prints the exact JSON received so you can fix the frontend/backend mismatch.
    """
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
# ---------------------------------------

# --- LIFECYCLE EVENTS ---
@app.on_event("startup")
async def startup_event():
    print("🚀 Initializing MCP Connections...")
    await mcp_manager.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 Closing MCP Connections...")
    await mcp_manager.cleanup()

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
    # Make sure these match your Frontend JSON keys EXACTLY
    name: str
    phone_number: str  # Frontend might be sending 'phoneNumber'
    aadhar: str
    bank_acc: str      # Frontend might be sending 'bankAccount'
    language: str = "English"
    lat: Optional[float] = None
    long: Optional[float] = None
    crop: Optional[str] = None

class OTPRequest(BaseModel):
    phone_number: str

class OTPVerify(BaseModel):
    phone_number: str
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
        otp = str(random.randint(100000, 999999))
        otp_storage[request.phone_number] = otp
        print(f"\n🔐 [OTP SYSTEM] Generated OTP for {request.phone_number}: {otp}\n")
        return {"status": "success", "message": "OTP sent successfully"}
    except Exception as e:
        print(f"Error sending OTP: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/verify-otp")
def verify_otp(request: OTPVerify):
    stored_otp = otp_storage.get(request.phone_number)
    if stored_otp and stored_otp == request.otp:
        del otp_storage[request.phone_number]
        return {"status": "success", "message": "OTP Verified"}
    else:
        raise HTTPException(status_code=400, detail="Invalid or Expired OTP")

@app.post("/save")
def save_farmer_frontend(farmer: FarmerRegistration):
    print(f"📥 Received /save request for: {farmer.name}")
    return register_farmer(farmer)

@app.post("/api/register")
def register_farmer(farmer: FarmerRegistration):
    try:
        print(f"Incoming Data: {farmer.dict()}")
        result = save_user(
            phone=farmer.phone_number,
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
        print(f"📩 Received WhatsApp Message: {payload}")
        response = await handle_incoming_message(payload)
        return {"status": "received", "agent_response": response}
    except Exception as e:
        print(f"❌ Error in Webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/test-nasa")
def test_nasa(lat: float, lon: float):
    data = get_nasa_weather(lat, lon)
    return data