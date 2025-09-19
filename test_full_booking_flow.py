#!/usr/bin/env python3
"""
Complete Booking Flow Test with Coordinator Notifications
This test simulates a full client conversation to trigger coordinator notifications
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
    
    # UltraMsg webhook format
    webhook_data = {
        "instanceId": "instance142693",
        "data": {
            "id": f"test_{int(time.time())}",
            "from": phone_number,
            "to": "+97451334514",  # Agent phone
            "body": message,
            "type": "chat",
            "senderName": "Test Client",
            "timestamp": int(time.time())
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
    print("🎯 COMPLETE BOOKING FLOW TEST - COORDINATOR NOTIFICATIONS")
    print("=" * 60)
    print(f"Test Client: {TEST_CLIENT_PHONE}")
    print(f"Coordinator: {COORDINATOR_PHONE}")
    print(f"Webhook URL: {WEBHOOK_URL}")
    print("=" * 60)
    
    # Step 1: Initial booking request
    print("\n🔹 STEP 1: Initial Booking Request")
    success = simulate_whatsapp_message("Hi Layla, I want to book Dr. Fatima for a home visit")
    if not success:
        print("❌ Failed to send initial message")
        return
    
    time.sleep(3)
    
    # Step 2: Provide date
    print("\n🔹 STEP 2: Provide Date")
    success = simulate_whatsapp_message("Tomorrow, September 18th")
    if not success:
        print("❌ Failed to send date")
        return
        
    time.sleep(3)
    
    # Step 3: Select time slot (this should trigger book_appointment)
    print("\n🔹 STEP 3: Select Time Slot (TRIGGERS COORDINATOR NOTIFICATION)")
    success = simulate_whatsapp_message("2:00 PM please")
    if not success:
        print("❌ Failed to send time selection")
        return
        
    time.sleep(3)
    
    # Step 4: Confirm service type
    print("\n🔹 STEP 4: Confirm Service (if needed)")
    success = simulate_whatsapp_message("1 hour home visit")
    if not success:
        print("❌ Failed to send service confirmation")
        return
    
    print("\n🎉 COMPLETE BOOKING FLOW SENT!")
    print("📋 Expected Flow:")
    print("   1. ✅ Client requests booking")
    print("   2. ✅ Layla asks for date")  
    print("   3. ✅ Client provides date")
    print("   4. ✅ Layla shows available times")
    print("   5. ✅ Client picks time → BOOK_APPOINTMENT CALLED")
    print("   6. 🔔 COORDINATOR NOTIFICATION SENT TO +97471669569")
    print("   7. ✅ Layla confirms to client")
    
    print(f"\n📞 CHECK COORDINATOR PHONE: {COORDINATOR_PHONE}")
    print("📊 CHECK LOGS: logs/session_*/webhook_server.log")
    print("🔍 Look for: 'LAYLA BOOKING PROCESSED #[ID]' message")

if __name__ == "__main__":
    main()