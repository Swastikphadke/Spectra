# main.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware # Import CORS
from pydantic import BaseModel
from typing import Optional
from database import save_user
from tools import get_nasa_weather
from agent import handle_incoming_message
from mcp_client import mcp_manager # Import the manager

app = FastAPI()

# --- LIFECYCLE EVENTS ---
@app.on_event("startup")
async def startup_event():
    print("🚀 Initializing MCP Connections...")
    await mcp_manager.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 Closing MCP Connections...")
    await mcp_manager.cleanup()
# ------------------------

# --- CRITICAL FIX: Allow Frontend to talk to Backend ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (Member 1's React app)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (POST, GET, etc.)
    allow_headers=["*"],
)
# -------------------------------------------------------

# Data Model (Updated based on your requirements)
class FarmerRegistration(BaseModel):
    name: str
    phone_number: str
    aadhar: str
    bank_acc: str
    language: str = "English" # Default to English if not sent
    
    # Making these optional for now, so you can choose Frontend OR WhatsApp later
    lat: Optional[float] = None
    long: Optional[float] = None
    crop: Optional[str] = None

@app.get("/")
def read_root():
    return {"status": "Spectra Engine Online"}

@app.post("/api/register")
def register_farmer(farmer: FarmerRegistration):
    try:
        print(f"Incoming Data: {farmer.dict()}") # Debug print to see what Member 1 sends
        
        # Save to MongoDB via Member 4's database.py
        result = save_user(
            phone=farmer.phone_number,
            name=farmer.name,
            aadhar=farmer.aadhar,
            bank_acc=farmer.bank_acc,
            language=farmer.language,
            # Pass None if they aren't provided yet
            lat=farmer.lat,
            lon=farmer.long,  # <--- CRITICAL: Map 'long' (frontend) to 'lon' (database)
            crop=farmer.crop
        )
        
        return {
            "status": "success", 
            "message": "Farmer Registered", 
            "user_id": str(result),
            "next_step": "Waiting for location via WhatsApp" if not farmer.lat else "Fetching NASA Data..."
        }
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/whatsapp-webhook")
async def whatsapp_webhook(request: Request):
    """
    Receives messages from the WhatsApp Bridge.
    """
    try:
        payload = await request.json()
        print(f"📩 Received WhatsApp Message: {payload}")
        
        # Delegate to the AI Agent
        response = await handle_incoming_message(payload)
        
        return {"status": "received", "agent_response": response}
    except Exception as e:
        print(f"❌ Error in Webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/test-nasa")
def test_nasa(lat: float, lon: float):
    """
    Test endpoint to see if NASA API is returning data.
    """
    data = get_nasa_weather(lat, lon)
    return data