from pymongo import MongoClient
import os
from dotenv import load_dotenv
from typing import Optional
import datetime

# 1. Load variables
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

# 2. Connect
try:
    client = MongoClient(MONGO_URI)
    db = client['agrispace_db'] 
    users_collection = db['users']
    print("✅ Database: Connected successfully!")
except Exception as e:
    print(f"❌ Database Connection Failed: {e}")

# --- FUNCTION 1: For Backend Registration (Member 2) ---
def save_user(phone: str, name: str, aadhar: str, bank_acc: str, language: str, lat: Optional[float] = None, lon: Optional[float] = None, crop: Optional[str] = None):
    """Save or Update farmer in MongoDB"""
    user_data = {
        "phone": phone,
        "name": name,
        "aadhar": aadhar,
        "bank_acc": bank_acc,
        "language": language,
        "last_active": datetime.datetime.now()
    }
    
    # Handle Location (Critical for Map)
    if lat is not None and lon is not None:
        user_data["location"] = {"lat": lat, "lon": lon}
        # Flatten for easy access if needed
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

# --- FUNCTION 2: For AI Agent (Member 3) ---
def get_user_by_phone(phone: str):
    """Required by agent.py to identify users"""
    # Try exact match first
    user = users_collection.find_one({"phone": phone})
    if not user:
        # Try matching without the "whatsapp:" prefix just in case
        clean_phone = phone.replace("whatsapp:", "")
        user = users_collection.find_one({"phone": {"$regex": clean_phone}})
    return user

# --- FUNCTION 3: For Morning Briefing (Member 4 - You) ---
def get_all_farmers():
    """Required by scheduler.py"""
    return list(users_collection.find())