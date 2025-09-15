#!/usr/bin/env python3
"""
Test simulated INCOMING client message (fromMe: false)
"""

import json
import aiohttp
import asyncio

async def test_real_client_message():
    print("🧪 Testing Real Incoming Client Message")
    print("=" * 50)
    
    # Simulate a real incoming message from a client (NOT the bot)
    client_payload = {
        "event_type": "message_create",
        "instanceId": "142693",
        "id": 999999,
        "referenceId": "",
        "hash": "test_hash_12345",
        "data": {
            "id": "test_incoming_message_123",
            "sid": "TEST_SID_123",
            "from": "1234567890@c.us",  # Different phone number (client)
            "to": "97451334514@c.us",    # Bot's number
            "author": "",
            "pushname": "Test Client",
            "ack": "",
            "type": "chat",
            "body": "Hi, I need to book an appointment for next Tuesday",
            "media": "",
            "fromMe": False,  # This is the key - incoming message
            "self": False,
            "isForwarded": False,
            "isMentioned": False,
            "quotedMsg": {},
            "mentionedIds": [],
            "time": 1757962500
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            print(f"📤 Sending simulated client message...")
            print(f"📱 From: 1234567890 (Client)")
            print(f"💬 Message: '{client_payload['data']['body']}'")
            print(f"🔍 fromMe: {client_payload['data']['fromMe']}")
            
            async with session.post(
                "http://localhost:8000/webhook",
                json=client_payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                response_text = await response.text()
                
                print(f"\n📊 Response Status: {response.status}")
                print(f"📋 Response: {response_text}")
                
                if response.status == 200:
                    print("✅ Message processed successfully!")
                    print("💡 Check if ADK agent generated a proper response!")
                else:
                    print("❌ Message failed!")
                    
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_real_client_message())