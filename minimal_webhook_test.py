#!/usr/bin/env python3
"""
Minimal webhook test - isolate the issue
"""

import requests
import json
import time

def test_webhook_minimal():
    """Test minimal webhook functionality"""
    
    # Test 1: Test server health
    try:
        response = requests.get("http://localhost:8000/")
        print(f"✅ Server health check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Server health check failed: {e}")
        return False
    
    # Test 2: Simple webhook call
    webhook_data = {
        "data": {
            "id": "minimal_test",
            "from": "97450111222",  # Different test number
            "to": "97450123456",
            "body": "hi",  # Simple message
            "type": "chat",
            "senderName": "Test",
            "timestamp": int(time.time())
        }
    }
    
    try:
        print("📞 Sending minimal webhook request...")
        response = requests.post(
            "http://localhost:8000/webhook", 
            json=webhook_data, 
            headers={'Content-Type': 'application/json'},
            timeout=30  # 30 second timeout
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Minimal webhook test successful!")
            return True
        else:
            print(f"❌ Webhook returned error status: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Webhook request timed out (30s)")
        return False
    except Exception as e:
        print(f"❌ Webhook request failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Running minimal webhook test...")
    test_webhook_minimal()