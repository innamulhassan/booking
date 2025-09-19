#!/usr/bin/env python3
"""
Test the fixed function parameter handling
"""

import requests
import time
from dotenv import load_dotenv
import os

load_dotenv()

# Test configuration
WEBHOOK_URL = "https://webhook-booking.innamul.com/webhook"
CLIENT_PHONE = os.getenv("TESTCLIENT_PHONE_NUMBER", "917401290081")

def send_message(message_text):
    """Send a WhatsApp message simulation"""
    payload = {
        "event_type": "message_received",
        "instanceId": "142693", 
        "id": "",
        "referenceId": "",
        "hash": f"test_hash_{int(time.time())}",
        "data": {
            "id": f"false_{CLIENT_PHONE}@c.us_TEST{int(time.time())}",
            "sid": f"TEST{int(time.time())}",
            "from": f"{CLIENT_PHONE}@c.us",
            "to": "97451334514@c.us",
            "author": "",
            "pushname": "Test User",
            "ack": "",
            "type": "chat",
            "body": message_text,
            "media": "",
            "fromMe": False,
            "self": False,
            "isForwarded": False,
            "isMentioned": False,
            "quotedMsg": {},
            "mentionedIds": [],
            "time": int(time.time())
        }
    }
    
    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        print(f"✅ Status: {response.status_code}")
        print(f"💕 Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔧 TESTING FUNCTION PARAMETER FIX")
    print("=" * 50)
    print(f"Client: Test User ({CLIENT_PHONE})")
    print("=" * 50)
    
    # Test 1: Message that might trigger check_availability without date
    print("📱 Testing: Hi Layla, I want to book Dr. Fatima for a home visit")
    success = send_message("Hi Layla, I want to book Dr. Fatima for a home visit")
    if success:
        print("─" * 50)
        time.sleep(3)
        
        # Test 2: Follow up with specific date
        print("📱 Testing: Tomorrow, September 18th")
        success = send_message("Tomorrow, September 18th")
        if success:
            print("─" * 50)
    
    print("=" * 50)
    print("🎯 TEST COMPLETE - Check for error handling")
    print("=" * 50)