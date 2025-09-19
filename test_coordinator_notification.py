#!/usr/bin/env python3
"""
Simple Coordinator Flow Test
Test a focused booking conversation to verify coordinator notifications
"""

import requests
import json
import time
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment configuration
load_dotenv()

# Configuration
WEBHOOK_URL = "https://webhook-booking.innamul.com/webhook"
TEST_CLIENT_PHONE = os.getenv("TESTCLIENT_PHONE_NUMBER", "+917401290081")
TEST_CLIENT_NAME = "Test Client"

def send_message(message_text):
    """Send WhatsApp message using the correct webhook format"""
    
    webhook_payload = {
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
                                    "profile": {
                                        "name": TEST_CLIENT_NAME
                                    },
                                    "wa_id": TEST_CLIENT_PHONE.replace("+", "")
                                }
                            ],
                            "messages": [
                                {
                                    "from": TEST_CLIENT_PHONE.replace("+", ""),
                                    "id": f"msg_{int(time.time())}",
                                    "timestamp": str(int(time.time())),
                                    "text": {
                                        "body": message_text
                                    },
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
    
    print(f"📱 Sending: {message_text}")
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            json=webhook_payload,
            headers={'Content-Type': 'application/json'},
            timeout=15
        )
        
        if response.status_code == 200:
            print(f"✅ Status: {response.status_code}")
            try:
                data = response.json()
                print(f"💕 Layla: {data.get('message', data)}")
            except:
                print(f"📄 Raw: {response.text[:100]}")
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    print("-" * 60)

def test_booking_with_coordinator_check():
    """Test complete booking flow focusing on coordinator notification"""
    
    coordinator_phone = os.getenv("COORDINATOR_PHONE_NUMBER", "+97471669569")
    
    print("🎯 COORDINATOR FLOW TEST")
    print("=" * 60)
    print(f"Client: {TEST_CLIENT_NAME} ({TEST_CLIENT_PHONE})")
    print(f"Coordinator: {coordinator_phone}")
    print("=" * 60)
    
    # Step 1: Greeting
    send_message("Hi Layla")
    time.sleep(2)
    
    # Step 2: Complete booking request with all details
    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow_str = tomorrow.strftime("%Y-%m-%d")
    
    booking_request = f"""I need to book therapy please:
- 1 Hour Session at Clinic 
- Date: {tomorrow_str}
- Time: 15:00 (3 PM)
- Therapist: Dr. Ahmad Al-Rashid
- I'm feeling anxious and need support"""
    
    print("🔸 Complete booking request:")
    send_message(booking_request)
    time.sleep(5)  # More time for processing
    
    # Step 3: Confirmation
    send_message("Please confirm this booking")
    time.sleep(3)
    
    coordinator_phone = os.getenv("COORDINATOR_PHONE_NUMBER", "+97471669569")
    
    print("=" * 60)
    print("🎯 TEST COMPLETE")
    print(f"✅ Check coordinator phone {coordinator_phone} for notifications")
    print("✅ Check logs for 'LAYLA BOOKING PROCESSED' messages")
    print("=" * 60)

if __name__ == "__main__":
    test_booking_with_coordinator_check()