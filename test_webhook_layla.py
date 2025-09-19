#!/usr/bin/env python3
"""
Test webhook message to verify Layla's seamless booking experience.
This simulates a real WhatsApp message coming through the webhook.
"""

import requests
import json

def test_webhook_message():
    """Test sending a message through the webhook to see Layla in action"""
    
    webhook_url = "http://localhost:8000/webhook"
    
    # Simulate WhatsApp webhook message
    test_message = {
        "messages": [{
            "id": "wamid.test123",
            "from": "97477777777",
            "timestamp": "1726523067",
            "text": {
                "body": "Hi Layla, I need to book a therapy session"
            },
            "type": "text"
        }],
        "contacts": [{
            "profile": {
                "name": "Sara Ahmed"
            },
            "wa_id": "97477777777"
        }]
    }
    
    try:
        print("🌟 TESTING LAYLA VIA WEBHOOK")
        print("=" * 40)
        print(f"📱 Sending: Hi Layla, I need to book a therapy session")
        print(f"👤 Client: Sara Ahmed (97477777777)")
        print()
        
        response = requests.post(webhook_url, json=test_message)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Message processed successfully")
            print("💕 Layla should respond with warm, personal greeting")
            print("🔇 Client unaware of any coordinator involvement")
        else:
            print(f"❌ ERROR: {response.status_code} - {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Is the webhook server running?")
        print("💡 Try: Check if localhost:8000 is accessible")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_booking_flow():
    """Test complete booking conversation flow"""
    
    webhook_url = "http://localhost:8000/webhook"
    client_phone = "97477777777"
    
    messages = [
        "Hi Layla, I need help with therapy",
        "I want to book a 1 hour session at your clinic", 
        "Tomorrow at 2 PM please",
        "Dr. Ahmad would be perfect",
        "Yes, please book it for me"
    ]
    
    print("\n💬 TESTING COMPLETE BOOKING FLOW")
    print("=" * 40)
    
    for i, message_text in enumerate(messages, 1):
        test_message = {
            "messages": [{
                "id": f"wamid.test{i}",
                "from": client_phone,
                "timestamp": str(1726523067 + i),
                "text": {"body": message_text},
                "type": "text"
            }],
            "contacts": [{
                "profile": {"name": "Sara Ahmed"},
                "wa_id": client_phone
            }]
        }
        
        try:
            print(f"\n{i}. 🗣️ Client: {message_text}")
            
            response = requests.post(webhook_url, json=test_message)
            
            if response.status_code == 200:
                print(f"   ✅ Processed successfully")
            else:
                print(f"   ❌ Error {response.status_code}")
                
            # Brief pause between messages
            import time
            time.sleep(2)
            
        except requests.exceptions.ConnectionError:
            print("   ❌ Connection Error")
            break
        except Exception as e:
            print(f"   ❌ Error: {e}")
            break

if __name__ == "__main__":
    print("🏥 LAYLA WEBHOOK TESTING")
    print("Testing seamless client experience")
    
    # Test 1: Simple message
    test_webhook_message()
    
    # Test 2: Complete booking flow
    test_booking_flow()
    
    print("\n🎯 EXPECTED RESULTS:")
    print("✅ Layla responds as warm, caring female assistant")
    print("✅ No coordinator mentions in any client messages")
    print("✅ Immediate booking confirmations (no 'waiting')")
    print("✅ Silent coordinator notifications in background")
    print("✅ Client feels like talking to real person")