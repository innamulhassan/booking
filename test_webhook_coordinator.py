#!/usr/bin/env python3
"""
Simple test to simulate a WhatsApp message requesting a booking to test coordinator notifications.
This will test the full webhook pipeline including coordinator notifications.
"""

import requests
import json
from datetime import datetime

def test_webhook_booking():
    """Test complete booking through webhook endpoint"""
    
    print("🔍 Testing Complete Booking Flow Through Webhook")
    print("=" * 55)
    
    # Use the actual webhook endpoint
    webhook_url = "https://webhook-booking.innamul.com/webhook"
    
    # Test message that should trigger booking
    booking_message = "I want to book a 1 hour session for tomorrow at 2 PM with Dr. Ahmad Al-Rashid"
    
    # Create the webhook payload (simulate Ultramsg webhook)
    webhook_payload = {
        "event_type": "message_received",
        "instanceId": "142693",
        "id": "",
        "referenceId": "",
        "hash": "test_hash_12345",
        "data": {
            "id": "test_message_id_12345",
            "sid": "test_sid_12345",
            "from": "917401290081@c.us",
            "to": "97451334514@c.us",
            "author": "",
            "pushname": "Test User",
            "ack": "",
            "type": "chat",
            "body": booking_message,
            "media": "",
            "fromMe": False,
            "self": False,
            "isForwarded": False,
            "isMentioned": False,
            "quotedMsg": {},
            "mentionedIds": [],
            "time": int(datetime.now().timestamp())
        }
    }
    
    print(f"📱 Sending booking message: '{booking_message}'")
    print(f"🌐 Webhook URL: {webhook_url}")
    
    try:
        # Send the webhook request
        response = requests.post(
            webhook_url,
            json=webhook_payload,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'axios/1.11.0'
            },
            timeout=30
        )
        
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Webhook processed successfully")
            
            # Try to parse response
            try:
                response_data = response.json()
                print(f"📋 Response: {response_data}")
            except:
                print(f"📋 Response Text: {response.text[:200]}...")
                
        else:
            print(f"❌ Webhook failed with status {response.status_code}")
            print(f"📋 Error: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out - this might mean the booking process is taking time")
        print("   Check the coordinator's WhatsApp for notifications")
        
    except Exception as e:
        print(f"❌ Error sending webhook: {e}")
    
    print("\n" + "=" * 55)
    print("🏁 Test Complete!")
    print("\nTo verify coordinator notifications:")
    print("1. Check the coordinator's WhatsApp (+97471669569)")
    print("2. Look for a message with booking details")
    print("3. The message should contain APPROVE/DECLINE/MODIFY options")
    print("4. Try replying with 'APPROVE' to test response handling")
    print("\nIf no message was received, the coordinator notification system needs debugging.")

if __name__ == "__main__":
    test_webhook_booking()