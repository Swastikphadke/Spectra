import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def test_register():
    print("\n--- Testing Registration ---")
    payload = {
        "name": "Test Farmer",
        "phone_number": "whatsapp:+919999999999",
        "aadhar": "123456789012",
        "bank_acc": "987654321",
        "language": "English",
        "lat": 12.9716, # Bangalore coordinates
        "long": 77.5946,
        "crop": "Wheat"
    }
    try:
        response = requests.post(f"{BASE_URL}/api/register", json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Failed to connect to backend: {e}")

def test_webhook_water():
    print("\n--- Testing WhatsApp Webhook (Water Query) ---")
    # This simulates a message from the user we just registered
    payload = {
        "from": "whatsapp:+919999999999",
        "type": "text",
        "content": "Should I water my crops?"
    }
    try:
        response = requests.post(f"{BASE_URL}/whatsapp-webhook", json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Failed to connect to backend: {e}")

def test_webhook_unknown():
    print("\n--- Testing WhatsApp Webhook (Unknown User) ---")
    # This simulates a message from a user NOT in the DB
    payload = {
        "from": "whatsapp:+910000000000",
        "type": "text",
        "content": "Hello"
    }
    try:
        response = requests.post(f"{BASE_URL}/whatsapp-webhook", json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Failed to connect to backend: {e}")

if __name__ == "__main__":
    print("⚠️  Make sure 'uvicorn main:app --reload' is running in another terminal! ⚠️")
    time.sleep(1)
    test_register()
    test_webhook_water()
    test_webhook_unknown()
