from pymongo import MongoClient
import os
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any
import datetime
import random

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

try:
    client = MongoClient(MONGO_URI)
    db = client['agrispace_db'] 
    users_collection = db['users']
    claims_collection = db['claims']
    print("✅ Database: Connected successfully!")
except Exception as e:
    print(f"❌ Database Connection Failed: {e}")

def save_user(phone: str, name: str, aadhar: str, bank_acc: str, language: str, lat: Optional[float] = None, lon: Optional[float] = None, crop: Optional[str] = None):
    user_data = {
        "phone": phone,
        "name": name,
        "aadhar": aadhar,
        "bank_acc": bank_acc,
        "language": language,
        "last_active": datetime.datetime.now()
    }
    
    if lat is not None and lon is not None:
        user_data["location"] = {"lat": lat, "lon": lon}
        user_data["lat"] = lat
        user_data["lon"] = lon

    if crop is not None:
        user_data["crop"] = crop
    
    result = users_collection.update_one(
        {"phone": phone}, 
        {"$set": user_data}, 
        upsert=True
    )
    print(f"✅ User {name} saved.")
    return result.upserted_id or "Updated"

def get_user_by_phone(phone: str):
    user = users_collection.find_one({"phone": phone})
    if not user:
        clean_phone = phone.replace("whatsapp:", "")
        user = users_collection.find_one({"phone": {"$regex": clean_phone}})
    return user

def get_all_farmers():
    return list(users_collection.find())

def get_all_farmers_with_risk():
    farmers = list(users_collection.find({}, {"_id": 0}))
    enhanced_farmers = []
    
    for f in farmers:
        if "risk_score" not in f:
            f["risk_score"] = random.randint(10, 95)
            f["ndvi_history"] = [random.uniform(0.1, 0.8) for _ in range(5)]
        
        if "crop" not in f or not f["crop"]:
            f["crop"] = "Unknown"
            
        enhanced_farmers.append(f)
        
    return enhanced_farmers

def create_claim_record(phone: str, claim_type: str):
    user = get_user_by_phone(phone)
    farmer_name = user.get("name", "Unknown") if user else "Unknown"

    claim = {
        "claim_id": f"CLM-{random.randint(10000, 99999)}",
        "phone": phone,
        "farmer_name": farmer_name,
        "claim_type": claim_type,
        "date": datetime.datetime.now().isoformat(),
        "status": "Pending",
        "ai_analysis": "Pending"
    }
    claims_collection.insert_one(claim)
    return claim

def get_all_claims_data():
    return list(claims_collection.find({}, {"_id": 0}))

def update_claim_status(claim_id: str, status: str, analysis: str):
    claims_collection.update_one(
        {"claim_id": claim_id},
        {"$set": {"status": status, "ai_analysis": analysis}}
    )