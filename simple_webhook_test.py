#!/usr/bin/env python3
"""
Simple Test - Single Message to ADK Agent
"""

import requests
import json

def test_single_message():
    """Test a single message to the webhook"""
    
    # Test webhook data
    webhook_data = {
        "data": {
            "id": "test_001",
            "from": "97450987654",  # Test client phone
            "to": "97450123456",    # Bot phone
            "body": "Hello, I want to book a therapy session. What services do you offer?",
            "type": "chat",
            "senderName": "Test Client",
            "timestamp": 1726488000
        }
    }
    
    try:
        print("🚀 Testing Webhook Endpoint...")
        print(f"Sending message: '{webhook_data['data']['body']}'")
        
        response = requests.post(
            "http://localhost:8000/webhook",
            json=webhook_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"\n✅ Response Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"📄 Response Data: {json.dumps(result, indent=2)}")
            except:
                print(f"📄 Response Text: {response.text}")
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.ConnectinError:
        print("❌ Cannot connect to server. Make sure it's running on port 8000.")
    except requests.exceptions.Timeout:
        print("❌ Request timed out. Server might be processing...")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_single_message()