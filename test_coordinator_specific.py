#!/usr/bin/env python3
"""
Test coordinator notification flow with specific booking request
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
        "entry": [
            {
                "id": "123456789",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15551234567",
                                "phone_number_id": "123456789012345"
                            },
                            "contacts": [
                                {
                                    "profile": {"name": "Test Client"},
                                    "wa_id": CLIENT_PHONE
                                }
                            ],
                            "messages": [
                                {
                                    "from": CLIENT_PHONE,
                                    "id": f"msg_{int(time.time())}",
                                    "timestamp": str(int(time.time())),
                                    "text": {"body": message_text},
                                    "type": "text"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }
    
    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        print(f"✅ Status: {response.status_code}")
        print(f"💕 Layla: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🎯 COORDINATOR FLOW TEST - SPECIFIC BOOKING")
    print("=" * 54)
    print(f"Client: Test Client ({CLIENT_PHONE})")
    print("Coordinator: +97471669569")
    print("=" * 54)
    
    # Test 1: Initial greeting
    print("📱 Sending: Hi Layla")
    success = send_message("Hi Layla")
    if success:
        print("─" * 54)
        time.sleep(2)
        
        # Test 2: Book for available time (2 PM from previous test)
        print("🔸 Specific booking for available time:")
        print("📱 Sending: Book me for 2 PM (14:00) on 2025-09-18 with Dr. Ahmad for 1 Hour Session at Clinic")
        success = send_message("Book me for 2 PM (14:00) on 2025-09-18 with Dr. Ahmad for 1 Hour Session at Clinic")
        if success:
            print("─" * 54)
            time.sleep(2)
            
            # Test 3: Confirm specific booking
            print("📱 Sending: Yes, please confirm the 2 PM appointment")
            success = send_message("Yes, please confirm the 2 PM appointment")
            if success:
                print("─" * 54)
    
    print("=" * 54)
    print("🎯 TEST COMPLETE")
    print("✅ Check coordinator phone +97471669569 for notifications")
    print("✅ Check logs for 'LAYLA BOOKING PROCESSED' messages")
    print("=" * 54)