from __future__ import annotations

import asyncio
import os
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Load .env from repo root (d:\Spectra\.env)
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

from agent import handle_incoming_message
from database import (
    create_claim_record,
    get_all_claims_data,
    get_all_farmers_with_risk,
    save_user,
    update_claim_status,
)
from scheduler import morning_briefing_job, scheduler_loop

# MCP is optional at runtime (so backend can start even if MCP deps missing)
try:
    from mcp_client import mcp_manager  # type: ignore
except Exception:
    mcp_manager = None


app = FastAPI()

# Serve backend/static at /static (for MP3, etc.)
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# CORS: wildcard + credentials breaks browsers; use explicit localhost dev origins
# ✅ CORS FIX: allow any localhost/127.0.0.1 port; and do NOT use credentials unless needed
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    if mcp_manager is not None:
        print("🚀 Initializing MCP Connections...")
        try:
            await mcp_manager.initialize()
        except Exception as e:
            print(f"⚠️ MCP init failed (continuing without MCP): {e}")
    else:
        print("ℹ️ MCP not available (continuing without MCP).")

    print("⏰ Starting Morning Briefing Scheduler...")
    asyncio.create_task(scheduler_loop())


@app.on_event("shutdown")
async def shutdown_event():
    if mcp_manager is not None:
        print("🛑 Closing MCP Connections...")
        try:
            await mcp_manager.cleanup()
        except Exception as e:
            print(f"⚠️ MCP cleanup failed: {e}")


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
    msg["From"] = f"Spectra <{smtp_user}>"
    msg["To"] = to_email
    msg["Subject"] = "Your Spectra Verification Code"

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
    msg.attach(MIMEText(body, "html"))

    server = smtplib.SMTP(smtp_host, smtp_port)
    server.starttls()
    server.login(smtp_user, smtp_pass)
    server.send_message(msg)
    server.quit()
    print(f"✅ Email sent to {to_email}")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    try:
        body = await request.body()
        print("\n❌ REGISTRATION FAILED: Data Format Mismatch")
        print(f"📥 Incoming JSON from Frontend: {body.decode(errors='replace')}")
        print(f"⚠️ Specific Error: {exc.errors()}\n")
    except Exception:
        print("Could not print error details.")

    return JSONResponse(status_code=422, content={"detail": exc.errors()})


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


class PremiumRequest(BaseModel):
    lat: float
    lon: float
    crop: str


class VerifyClaimRequest(BaseModel):
    claim_id: str
    lat: float
    lon: float
    claim_type: str


class ClusterRequest(BaseModel):
    lat: float
    lon: float


class InsuranceSave(BaseModel):
    role: str = "insurance"
    companyName: str
    password: str
    email: str
    emailVerified: bool = True
    timestamp: Optional[str] = None


otp_storage: dict[str, str] = {}


@app.get("/")
def read_root():
    return {"status": "Spectra Engine Online"}


@app.post("/send-otp")
def send_otp(request: OTPRequest):
    identifier = request.phone_number or request.email
    if not identifier:
        return {"success": False, "error": "Phone number or Email required"}

    otp = str(random.randint(100000, 999999))
    otp_storage[identifier] = otp
    print(f"\n🔐 [OTP SYSTEM] Generated OTP for {identifier}: {otp}\n")

    if request.email and "@" in request.email:
        send_email_otp(request.email, otp)

    return {"success": True}


@app.post("/verify-otp")
def verify_otp(request: OTPVerify):
    identifier = request.phone_number or request.email
    if not identifier:
        return {"success": False, "error": "Phone number or Email required"}

    stored_otp = otp_storage.get(identifier)
    if stored_otp and stored_otp == request.otp:
        del otp_storage[identifier]
        return {"success": True}

    return {"success": False, "error": "Invalid or Expired OTP"}


@app.post("/save")
async def save_any(request: Request):
    """
    Accepts both:
    - InsuranceAuth.tsx payload (role=insurance)
    - FarmerRegistration payload (from farmer registration UI)
    """
    payload = await request.json()

    # insurance save path
    if isinstance(payload, dict) and payload.get("role") == "insurance":
        data = InsuranceSave.model_validate(payload)
        # Minimal demo behavior: accept and acknowledge (store later if needed)
        return {"success": True, "saved": "insurance", "company": data.companyName}

    # farmer save path (backward compatible)
    farmer = FarmerRegistration.model_validate(payload)
    return register_farmer(farmer)


@app.post("/api/register")
def register_farmer(farmer: FarmerRegistration):
    try:
        print(f"Incoming Data: {farmer.model_dump()}")

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
            crop=farmer.crop,
        )
        return {
            "status": "success",
            "message": "Farmer Registered",
            "user_id": str(result),
            "next_step": "Waiting for location via WhatsApp"
            if not farmer.lat
            else "Fetching NASA Data...",
        }
    except Exception as e:
        print(f"Error saving user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/whatsapp-webhook")
async def whatsapp_webhook(request: Request):
    payload = await request.json()
    print(f"📩 WhatsApp Payload: {payload}")
    response = await handle_incoming_message(payload)
    return {"status": "received", "agent_response": response}


@app.post("/admin/run-morning-brief")
async def run_morning_brief_now():
    asyncio.create_task(morning_briefing_job())
    return {"status": "success", "message": "Morning briefing job has been triggered."}


@app.get("/api/farmers")
async def get_farmers_api():
    return {"success": True, "farmers": get_all_farmers_with_risk()}


@app.get("/api/claims")
async def get_claims_api():
    claims = get_all_claims_data()
    if not claims:
        create_claim_record("919998887776", "Drought")
        claims = get_all_claims_data()
    return {"success": True, "claims": claims}


@app.post("/api/verify-claim")
async def verify_claim_api(req: VerifyClaimRequest):
    simulated_rain = random.randint(10, 150)
    simulated_ndvi = random.uniform(0.1, 0.8)

    recommendation = "REJECT"
    reason = (
        f"Satellite shows heavy rainfall ({simulated_rain}mm) and healthy vegetation "
        f"(NDVI: {simulated_ndvi:.2f})."
    )

    if req.claim_type == "Drought":
        if simulated_rain < 60 and simulated_ndvi < 0.35:
            recommendation = "APPROVE"
            reason = (
                f"Confirmed drought conditions. Rain: {simulated_rain}mm, "
                f"NDVI: {simulated_ndvi:.2f} (Critical)."
            )
    elif req.claim_type == "Flood":
        if simulated_rain > 120:
            recommendation = "APPROVE"
            reason = f"Confirmed flood conditions. Rain: {simulated_rain}mm."

    update_claim_status(req.claim_id, "Analyzed", reason)
    return {"success": True, "recommendation": recommendation, "reason": reason}


@app.post("/api/calculate-premium")
async def calculate_premium_api(req: PremiumRequest):
    base_rate = 500
    drought_risk_score = random.randint(1, 10)

    multiplier = 50
    if req.crop.lower() in ["rice", "sugarcane", "paddy"]:
        multiplier = 80

    final_premium = base_rate + (drought_risk_score * multiplier)

    return {
        "success": True,
        "premium": final_premium,
        "risk_level": "High"
        if drought_risk_score > 7
        else "Moderate"
        if drought_risk_score > 4
        else "Low",
        "breakdown": f"Base ({base_rate}) + Risk Charge ({drought_risk_score * multiplier})",
    }


@app.post("/api/cluster-analysis")
async def cluster_analysis_api(req: ClusterRequest):
    claimant_ndvi = random.uniform(0.1, 0.4)

    neighbors = []
    is_possible_fraud = random.choice([True, False])

    for i in range(1, 6):
        n_ndvi = random.uniform(0.6, 0.8) if is_possible_fraud else random.uniform(0.1, 0.3)
        neighbors.append(
            {
                "id": f"Neighbor-{i}",
                "distance": f"{random.randint(50, 500)}m",
                "ndvi": round(n_ndvi, 2),
            }
        )

    avg_neighbor_ndvi = sum(n["ndvi"] for n in neighbors) / 5
    verdict = "POSSIBLE FRAUD" if (avg_neighbor_ndvi - claimant_ndvi) > 0.3 else "GENUINE DISASTER"

    return {
        "success": True,
        "claimant_ndvi": round(claimant_ndvi, 2),
        "neighbors": neighbors,
        "verdict": verdict,
    }