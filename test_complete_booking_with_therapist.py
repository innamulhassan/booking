#!/usr/bin/env python3
"""
Complete Booking Flow Test with Therapist Selection
This test properly completes the booking to trigger coordinator notifications
"""

import requests
import json
import time
import os
from datetime import datetime

# Configuration
WEBHOOK_URL = "https://webhook-booking.innamul.com/webhook"
TEST_CLIENT_PHONE = "+917401290081"
COORDINATOR_PHONE = "+97471669569"

def simulate_whatsapp_message(message, phone_number=TEST_CLIENT_PHONE):
    """Simulate a WhatsApp message to the webhook"""
    
    # Generate unique message ID
    message_id = f"test_{int(time.time() * 1000)}"
    
    # UltraMsg webhook format matching your existing format
    webhook_data = {
        "event_type": "message_received",
        "instanceId": "142693",
        "id": "",
        "referenceId": "",
        "hash": f"test_hash_{message_id}",
        "data": {
            "id": f"false_{phone_number.replace('+', '')}@c.us_{message_id}",
            "sid": message_id,
            "from": f"{phone_number.replace('+', '')}@c.us",
            "to": "97451334514@c.us",
            "author": "",
            "pushname": "Test User",
            "ack": "",
            "type": "chat",
            "body": message,
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
    
    print(f"\n📱 Sending: '{message}'")
    print(f"   From: {phone_number}")
    print(f"   Timestamp: {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            json=webhook_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"✅ Status: {response.status_code}")
        if response.text:
            print(f"📄 Response: {response.text[:200]}...")
            
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🎯 COMPLETE BOOKING FLOW TEST - WITH THERAPIST SELECTION")
    print("=" * 65)
    print(f"Test Client: {TEST_CLIENT_PHONE}")
    print(f"Coordinator: {COORDINATOR_PHONE}")
    print(f"Webhook URL: {WEBHOOK_URL}")
    print("=" * 65)
    
    # Step 1: Initial booking request
    print("\n🔹 STEP 1: Initial Booking Request")
    success = simulate_whatsapp_message("Hi Layla, I want to book Dr. Fatima for a home visit")
    if not success:
        print("❌ Failed to send initial message")
        return
    
    time.sleep(4)
    
    # Step 2: Provide date
    print("\n🔹 STEP 2: Provide Date")
    success = simulate_whatsapp_message("Tomorrow, September 18th")
    if not success:
        print("❌ Failed to send date")
        return
        
    time.sleep(4)
    
    # Step 3: Select time slot
    print("\n🔹 STEP 3: Select Time Slot")
    success = simulate_whatsapp_message("2:00 PM please")
    if not success:
        print("❌ Failed to send time selection")
        return
        
    time.sleep(4)
    
    # Step 4: Confirm service type
    print("\n🔹 STEP 4: Confirm Service Type")
    success = simulate_whatsapp_message("1 hour home visit")
    if not success:
        print("❌ Failed to send service confirmation")
        return
    
    time.sleep(4)
    
    # Step 5: Confirm therapist (THIS SHOULD TRIGGER book_appointment)
    print("\n🔹 STEP 5: Confirm Therapist (TRIGGERS COORDINATOR NOTIFICATION)")
    success = simulate_whatsapp_message("Yes, Dr. Fatima please")
    if not success:
        print("❌ Failed to send therapist confirmation")
        return
    
    print("\n🎉 COMPLETE BOOKING FLOW SENT!")
    print("📋 Expected Flow:")
    print("   1. ✅ Client requests Dr. Fatima for home visit")
    print("   2. ✅ Layla asks for date")  
    print("   3. ✅ Client provides date")
    print("   4. ✅ Layla shows available times")
    print("   5. ✅ Client picks 2:00 PM")
    print("   6. ✅ Client confirms 1 hour home visit")
    print("   7. ✅ Client confirms Dr. Fatima")
    print("   8. 🔔 BOOK_APPOINTMENT FUNCTION CALLED")
    print("   9. 🔔 COORDINATOR NOTIFICATION → +97471669569")
    print("  10. ✅ Layla confirms booking to client")
    
    print(f"\n📞 CHECK COORDINATOR PHONE: {COORDINATOR_PHONE}")
    print("📊 CHECK LOGS: logs/session_*/webhook_server.log")
    print("🔍 Look for:")
    print("   - 'Processing function call: book_appointment'")
    print("   - 'LAYLA BOOKING PROCESSED #[ID]'")
    print("   - 'Coordinator notification sent to +97471669569'")

if __name__ == "__main__":
    main()