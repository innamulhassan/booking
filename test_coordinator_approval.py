#!/usr/bin/env python3
"""
Test coordinator approval workflow - verify client only gets confirmation after coordinator approval
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
        "event_type": "message_create",
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
        if response.text:
            print(f"   Response body: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False

def test_approval_workflow():
    """Test complete booking workflow with coordinator approval requirement"""
    print("🔄 Starting Coordinator Approval Workflow Test...")
    print("=" * 60)
    
    # Step 1: Start booking conversation
    print("\n📋 Step 1: Client initiates booking")
    send_test_message(client_phone, agent_phone, "I need to book therapy")
    time.sleep(3)
    
    # Step 2: Request date
    print("\n📅 Step 2: Client provides date")
    send_test_message(client_phone, agent_phone, "Tomorrow")
    time.sleep(3)
    
    # Step 3: Request time  
    print("\n⏰ Step 3: Client provides time")
    send_test_message(client_phone, agent_phone, "3:00 PM")
    time.sleep(3)
    
    # Step 4: Request service
    print("\n🏥 Step 4: Client chooses service")
    send_test_message(client_phone, agent_phone, "1 hour home visit")
    time.sleep(3)
    
    # Step 5: Confirm therapist (this should trigger pending approval)
    print("\n👨‍⚕️ Step 5: Client confirms therapist (should create PENDING appointment)")
    send_test_message(client_phone, agent_phone, "Yes Dr. Fatima is perfect")
    time.sleep(5)
    
    print("\n⏳ At this point:")
    print("   - Client should receive: 'Let me coordinate with team...'")
    print("   - Coordinator should receive: 'PENDING APPROVAL REQUIRED #X'") 
    print("   - NO final confirmation should be sent to client yet")
    
    # Wait for coordinator notification
    print("\n⏸️  Waiting 10 seconds for coordinator notification...")
    time.sleep(10)
    
    # Step 6: Coordinator approves (you need to manually send this)
    appointment_id = input("\n🔍 What appointment ID was sent to coordinator? (check +97471669569): ")
    
    if appointment_id:
        print(f"\n✅ Step 6: Simulating coordinator approval for appointment #{appointment_id}")
        send_test_message(coordinator_phone, agent_phone, f"APPROVE {appointment_id}")
        time.sleep(3)
        
        print("\n🎉 Expected results:")
        print("   - Coordinator gets: 'APPROVED: Appointment #X confirmed!'")
        print("   - Client gets: 'BOOKING CONFIRMED!' with full details")
        print("   - Workflow complete!")
    else:
        print("\n⚠️  Manual approval needed - check coordinator phone for notification")
    
    print("\n" + "=" * 60)
    print("✅ Test completed! Check both phones for expected messages.")

if __name__ == "__main__":
    test_approval_workflow()