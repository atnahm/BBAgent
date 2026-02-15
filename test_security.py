"""
Test Suite for Security and Functionality.
Verifies API authentication and basic workflow.
"""
import unittest
import requests
import time
import os
import threading
from pathlib import Path
import json

# Configuration
BASE_URL = "http://localhost:5000"
API_KEY = "4dd59b7847bf0fdce7df56aa85eba3754aeabe318b"

class TestSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Wait for server to start."""
        print("⏳ Waiting for server to start...")
        for i in range(30):
            try:
                requests.get(f"{BASE_URL}/health", timeout=1)
                print("✅ Server is up!")
                return
            except requests.exceptions.ConnectionError:
                time.sleep(1)
        raise RuntimeError("Server failed to start in 30 seconds")
    
    def test_health_public(self):
        """Health endpoint should be public."""
        try:
            response = requests.get(f"{BASE_URL}/health")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data['status'], 'healthy')
            print("✅ Public Health Check Passed")
        except requests.exceptions.ConnectionError:
            self.fail("Could not connect to server. Is it running?")

    def test_upload_no_key(self):
        """Upload should fail without API key."""
        try:
            response = requests.post(f"{BASE_URL}/api/v1/invoice/upload", json={})
            self.assertEqual(response.status_code, 401)
            print("✅ Auth Check (No Key) Passed")
        except Exception as e:
            self.fail(f"Connection error: {e}")

    def test_upload_invalid_key(self):
        """Upload should fail with wrong API key."""
        headers = {"X-API-KEY": "wrong_key"}
        response = requests.post(f"{BASE_URL}/api/v1/invoice/upload", json={}, headers=headers)
        self.assertEqual(response.status_code, 401)
        print("✅ Auth Check (Invalid Key) Passed")

    def test_upload_valid_key_bad_data(self):
        """Upload should pass auth but fail validation with valid key."""
        headers = {"X-API-KEY": API_KEY}
        response = requests.post(f"{BASE_URL}/api/v1/invoice/upload", json={}, headers=headers)
        self.assertEqual(response.status_code, 400) # Bad Request (missing file_data)
        print("✅ Auth Check (Valid Key) Passed")

if __name__ == '__main__':
    print("⚠️  Make sure webhook_server.py is running in another terminal!")
    unittest.main()
