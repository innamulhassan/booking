#!/usr/bin/env python3
"""
Quick test for coordinator approval - single 'yes' response
"""
import requests
import time

webhook_url = "https://webhook-booking.innamul.com/webhook"
coordinator_phone = "97471669569"
agent_phone = "97451334514"

def send_coordinator_approval():
    """Test coordinator saying just 'yes' to approve pending appointment"""
    payload = {
        "event_type": "message_received",
        "instanceId": "142693",
        "data": {
            "from": f"{coordinator_phone}@c.us",
            "to": f"{agent_phone}@c.us", 
            "body": "yes",
            "pushname": "Coordinator",
            "fromMe": False,
            "type": "chat",
            "time": int(time.time())
        }
    }
    
    try:
        response = requests.post(webhook_url, json=payload)
        print(f"✅ Coordinator said 'yes' -> Response: {response.status_code}")
        if response.text:
            print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🎯 Testing coordinator approval with 'yes'...")
    send_coordinator_approval()
    print("Done!")