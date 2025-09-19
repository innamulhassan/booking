#!/usr/bin/env python3
"""
Test intelligent coordinator approval - handles natural human responses like 'approve', 'yes', 'ok' with typos
"""
import requests
import time
import json

# Test configuration
webhook_url = "https://webhook-booking.innamul.com/webhook"
client_phone = "917401290081"
coordinator_phone = "97471669569"
agent_phone = "97451334514"

def send_test_message(from_phone, to_phone, message):
    """Send a test message through webhook"""
    payload = {
        "event_type": "message_received",
        "instanceId": "142693",
        "data": {
            "from": f"{from_phone}@c.us",
            "to": f"{to_phone}@c.us", 
            "body": message,
            "pushname": "Test User",
            "fromMe": False,
            "type": "chat",
            "time": int(time.time())
        }
    }
    
    try:
        response = requests.post(webhook_url, json=payload)
        print(f"✅ Sent: '{message}' -> Response: {response.status_code}")
        if response.text and response.text != '{"status":"ok"}':
            print(f"   Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False

def test_natural_approval():
    """Test natural human coordinator responses"""
    print("🧠 Testing Intelligent Coordinator Approval System...")
    print("=" * 70)
    
    # Step 1: Start booking to create pending appointment
    print("\n📋 Step 1: Client starts booking")
    send_test_message(client_phone, agent_phone, "I want therapy session")
    time.sleep(2)
    
    print("\n📅 Step 2: Provide booking details")
    send_test_message(client_phone, agent_phone, "Tomorrow at 2 PM")
    time.sleep(2)
    
    send_test_message(client_phone, agent_phone, "1 hour home visit")
    time.sleep(2)
    
    send_test_message(client_phone, agent_phone, "Yes with Dr. Fatima")
    time.sleep(3)
    
    print("\n⏳ Pending appointment should be created...")
    print("   Coordinator should receive: 'PENDING APPROVAL REQUIRED'")
    
    time.sleep(5)
    
    # Now test various natural approval responses
    print("\n🗣️  Testing natural coordinator responses:")
    
    # Test different natural responses (you can uncomment and test one at a time)
    natural_responses = [
        "yes",           # Simple yes
        "approve",       # Direct approval  
        "ok",           # Casual ok
        "yep sounds good", # Conversational approval
        "approve it",    # Natural phrasing
        "looks good",    # Informal approval
        # "nope",        # Decline
        # "no thanks",   # Natural decline
        # "change time please" # Modification request
    ]
    
    # Test one response (change index to test different ones)
    test_response = natural_responses[0]  # Testing "yes"
    
    print(f"🎯 Testing coordinator response: '{test_response}'")
    send_test_message(coordinator_phone, agent_phone, test_response)
    
    print("\n🎉 Expected behavior:")
    print("   - System recognizes natural approval")
    print("   - Client gets beautiful Layla confirmation")
    print("   - Coordinator gets success feedback")
    
    print("\n" + "=" * 70)
    print("✅ Test completed! Check both phones for natural workflow.")

if __name__ == "__main__":
    test_natural_approval()