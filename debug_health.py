import requests
try:
    print("Testing Health...")
    r = requests.get("http://127.0.0.1:5000/health", timeout=5)
    print(f"Status: {r.status_code}")
    print(f"Body: {r.text}")
except Exception as e:
    print(f"Error: {e}")
