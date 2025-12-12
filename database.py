from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://username:password@cluster.mongodb.net/")
client = MongoClient(MONGO_URI)
db = client["agrispace"]
users_collection = db["farmers"]

def save_user(phone: str, name: str, lat: float, lon: float, crop: str, language: str):
    """Save farmer to MongoDB"""
    user_data = {
        "phone": phone,
        "name": name,
        "lat": lat,
        "lon": lon,
        "crop": crop,
        "language": language
    }
    result = users_collection.insert_one(user_data)
    return result.inserted_id

def get_user_by_phone(phone: str):
    """Retrieve farmer by phone number"""
    return users_collection.find_one({"phone": phone})