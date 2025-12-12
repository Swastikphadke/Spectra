# database.py
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from typing import Optional
import datetime

# 1. Load the variables from .env
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

# 2. Connect to the Cloud Database
try:
    client = MongoClient(MONGO_URI)
    # Member 4 uses 'agrispace_db', so we must match that
    db = client['agrispace_db'] 
    # Member 4 uses 'users', so we must match that
    users_collection = db['users']
    print("✅ Connected to MongoDB successfully!")
except Exception as e:
    print(f"❌ Connection failed: {e}")

def save_user(phone: str, name: str, aadhar: str, bank_acc: str, language: str, lat: Optional[float] = None, lon: Optional[float] = None, crop: Optional[str] = None):
    """Save or Update farmer in MongoDB"""
    
    # Base Data
    user_data = {
        "phone": phone,
        "name": name,
        "aadhar": aadhar,
        "bank_acc": bank_acc,
        "language": language,
        "last_active": datetime.datetime.now()
    }
    
    # Member 4 Logic: Nest the location data if it exists
    if lat is not None and lon is not None:
        user_data["location"] = {"lat": lat, "lon": lon}
        # We also keep them flat if needed for quick searching, 
        # but the 'location' object is likely for the map UI.
        user_data["lat"] = lat
        user_data["lon"] = lon

    if crop is not None:
        user_data["crop"] = crop
    
    # Upsert (Update if exists, Insert if new)
    result = users_collection.update_one(
        {"phone": phone}, 
        {"$set": user_data}, 
        upsert=True
    )
    
    print(f"✅ User {name} saved to DB.")
    return result.upserted_id or "Updated"

def get_user_by_phone(phone: str):
    """Retrieve farmer by phone number"""
    return users_collection.find_one({"phone": phone})