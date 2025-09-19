#!/usr/bin/env python3
"""
Test complete booking flow with natural language date
"""
import requests
import json
import time

def test_complete_booking():
    """Test complete booking flow with natural language"""
    
    webhook_url = "http://localhost:8000/webhook"
    
    # Test with a complete booking request using "today"
    test_message = {
        "messages": [{
            "id": "test_msg_456", 
            "from": "+97455555555",
            "type": "text",
            "timestamp": str(int(time.time())),
            "text": {
                "body": "I want to book an office visit for today at 2 PM"
            },
            "pushname": "Test User"
        }]
    }
    
    print("=== TESTING COMPLETE BOOKING WITH NATURAL DATE ===")
    print(f"Sending message: '{test_message['messages'][0]['text']['body']}'")
    print()
    
    try:
        response = requests.post(
            webhook_url,
            json=test_message,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("\n✅ SUCCESS: Natural language booking processed!")
            print("\nThis should trigger the availability check and booking process")
            print("without asking for date format clarification.")
        else:
            print(f"\n❌ ERROR: Status {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ CONNECTION ERROR: {e}")

if __name__ == "__main__":
    test_complete_booking()