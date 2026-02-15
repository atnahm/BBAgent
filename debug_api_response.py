import requests
import os

BASE_URL = "http://127.0.0.1:5000"

print("--- Debugging API Response ---")
try:
    print(f"1. Hitting {BASE_URL}/api/v1/invoice/upload without key...")
    r = requests.post(f"{BASE_URL}/api/v1/invoice/upload", json={})
    print(f"   Status: {r.status_code}")
    print(f"   Body: {r.text}")
    
    print("\n2. Hitting with INVALID key...")
    r = requests.post(f"{BASE_URL}/api/v1/invoice/upload", json={}, headers={"X-API-KEY": "wrong"})
    print(f"   Status: {r.status_code}")
    print(f"   Body: {r.text}")

    print("\n3. Hitting with VALID key (but no data)...")
    # key = os.getenv("API_SECRET_KEY") # We know it from previous steps
    key = "4dd59b7847bf0fdce7df56aa85eba3754aeabe318b"
    print(f"   Using Key: {key}")
    r = requests.post(f"{BASE_URL}/api/v1/invoice/upload", json={}, headers={"X-API-KEY": key})
    print(f"   Status: {r.status_code}")
    print(f"   Body: {r.text}")

except Exception as e:
    print(f"ERROR: {e}")
