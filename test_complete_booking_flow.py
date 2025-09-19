#!/usr/bin/env python3
"""
Test Complete Booking Flow with Coordinator Notification
This test simulates a complete booking conversation to verify:
1. Layla handles the booking seamlessly 
2. Coordinator gets notified in background
3. Client experience is smooth without backend awareness
"""

import requests
import json
import time
import asyncio
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment configuration
load_dotenv()

# Test configuration
WEBHOOK_URL = "https://webhook-booking.innamul.com/webhook"
TEST_CLIENT_PHONE = os.getenv("TESTCLIENT_PHONE_NUMBER", "+917401290081")  # India test number
TEST_CLIENT_NAME = "Test Client"

def send_webhook_message(message_text):
    """Send a WhatsApp message via webhook to simulate client conversation"""
    
    # Standard WhatsApp Business API webhook format
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
    
    print(f"📱 Client Message: {message_text}")
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            json=webhook_payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"✅ Webhook sent successfully")
            try:
                response_data = response.json()
                if 'message' in response_data:
                    print(f"💕 Layla's Response: {response_data['message']}")
                else:
                    print(f"📄 Response: {response_data}")
            except:
                print(f"📄 Response: {response.text[:200]}")
        else:
            print(f"❌ Webhook failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error sending webhook: {str(e)}")
    
    print("-" * 80)
    return response

def test_complete_booking_conversation():
    """Test the complete booking flow that should trigger coordinator notification"""
    
    coordinator_phone = os.getenv("COORDINATOR_PHONE_NUMBER", "+97471669569")
    
    print("🎯 TESTING COMPLETE BOOKING FLOW")
    print("=" * 80)
    print(f"Client: {TEST_CLIENT_NAME} ({TEST_CLIENT_PHONE})")
    print(f"Testing coordinator notification to: {coordinator_phone}")
    print("=" * 80)
    
    # Step 1: Initial greeting
    print("\n� STEP 1: Initial Contact")
    send_webhook_message("Hi Layla, I need help with therapy")
    time.sleep(3)
    
    # Step 2: Service request with specific details
    print("\n� STEP 2: Request specific service")
    send_webhook_message("I want to book a 1 hour session at the clinic")
    time.sleep(3)
    
    # Step 3: Provide date and time
    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow_str = tomorrow.strftime("%Y-%m-%d")
    print(f"\n🔸 STEP 3: Provide date/time (tomorrow: {tomorrow_str})")
    send_webhook_message("Tomorrow at 3 PM please")
    time.sleep(3)
    
    # Step 4: Choose therapist
    print("\n� STEP 4: Choose therapist")
    send_webhook_message("Dr. Ahmad would be perfect")
    time.sleep(3)
    
    # Step 5: Complete the booking with all details
    print("\n🔸 STEP 5: Complete booking request")
    send_webhook_message("Yes, please book a 1 hour session at the clinic with Dr. Ahmad for tomorrow at 3 PM")
    time.sleep(5)  # Give more time for booking processing
    
    # Step 6: Confirm completion
    print("\n� STEP 6: Confirm booking")
    send_webhook_message("Thank you so much!")
    time.sleep(2)
    
    coordinator_phone = os.getenv("COORDINATOR_PHONE_NUMBER", "+97471669569")
    
    print("\n" + "=" * 80)
    print("🎯 BOOKING FLOW TEST COMPLETED")
    print("=" * 80)
    print("Expected outcomes:")
    print("✅ Client should feel Layla handled everything personally")
    print(f"✅ Coordinator ({coordinator_phone}) should receive notification")
    print("✅ No mention of approvals/coordinators to client")
    print("=" * 80)

def test_specific_booking_parameters():
    """Test with very specific booking parameters to ensure function call"""
    
    print("\n🎯 TESTING SPECIFIC BOOKING PARAMETERS")
    print("=" * 80)
    
    # Direct booking request with all parameters
    tomorrow = datetime.now() + timedelta(days=1) 
    date_str = tomorrow.strftime("%Y-%m-%d")
    
    booking_message = f"""Book me an appointment please:
- Service: 1 Hour Session at Clinic  
- Date: {date_str}
- Time: 15:00
- Therapist: Dr. Ahmad Al-Rashid
- Notes: Feeling anxious lately, need support"""
    
    print(f"\n🔸 Direct booking request with all details:")
    send_webhook_message(booking_message)
    time.sleep(5)
    
    print("=" * 80)

if __name__ == "__main__":
    print("🚀 STARTING COORDINATOR FLOW TEST")
    print("This will test the complete booking process and verify coordinator notifications")
    print()
    
    # Test 1: Natural conversation flow
    test_complete_booking_conversation()
    
    # Wait between tests
    time.sleep(5)
    
    # Test 2: Specific parameters
    test_specific_booking_parameters()
    
    coordinator_phone = os.getenv("COORDINATOR_PHONE_NUMBER", "+97471669569")
    
    print("\n🏁 ALL TESTS COMPLETED")
    print(f"Check coordinator phone ({coordinator_phone}) for notifications!")
    print("Check webhook logs for booking function calls and coordinator notifications.")