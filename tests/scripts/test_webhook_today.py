#!/usr/bin/env python3
"""
Test webhook with natural language date to ensure the full system works
"""
import requests
import json

def test_webhook_with_natural_date():
    """Test webhook endpoint with 'today' message"""
    
    webhook_url = "http://localhost:8000/webhook"
    
    # Simulate a WhatsApp message asking for availability "today"
    test_message = {
        "messages": [{
            "id": "test_msg_123",
            "from": "+97455555555",
            "type": "text", 
            "timestamp": "1695023400",
            "text": {
                "body": "I want to check availability for today"
            },
            "pushname": "Test User"
        }]
    }
    
    print("=== TESTING NATURAL LANGUAGE DATE WITH WEBHOOK ===")
    print(f"Sending message: '{test_message['messages'][0]['text']['body']}'")
    print(f"To webhook: {webhook_url}")
    print()
    
    try:
        response = requests.post(
            webhook_url,
            json=test_message,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")
        
        if response.status_code == 200:
            print("\n✅ SUCCESS: Webhook processed the message successfully!")
        else:
            print(f"\n❌ ERROR: Webhook returned status {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ CONNECTION ERROR: {e}")

if __name__ == "__main__":
    test_webhook_with_natural_date()