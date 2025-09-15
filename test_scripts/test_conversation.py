#!/usr/bin/env python3
"""
Test different conversation flows with real Ultramsg format
"""

import json
import aiohttp
import asyncio

test_messages = [
    {
        "name": "Greeting Test",
        "message": "Hi there!"
    },
    {
        "name": "Booking Request",
        "message": "I want to book an appointment"
    },
    {
        "name": "Service Inquiry", 
        "message": "What types of therapy do you offer?"
    },
    {
        "name": "Availability Check",
        "message": "What times are available tomorrow?"
    }
]

async def test_conversation_flow():
    print("🧪 Testing Conversation Flow with ADK Agent")
    print("=" * 60)
    
    for i, test in enumerate(test_messages, 1):
        print(f"\n📱 Test {i}: {test['name']}")
        print(f"💬 Message: '{test['message']}'")
        
        # Create Ultramsg webhook payload
        payload = {
            "id": f"TEST_MSG_{i:03d}_{hash(test['message']) % 1000}",
            "from": "1234567890@c.us",
            "to": "97451334514@c.us",  # Agent number
            "body": test["message"],
            "type": "text",
            "senderName": "Test Client",
            "fromMe": False,
            "time": 1642687400 + (i * 60),  # Different timestamps
            "chatId": "1234567890@c.us"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:8000/webhook",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    status = response.status
                    response_text = await response.text()
                    
                    if status == 200:
                        print(f"✅ Status: {status}")
                        print(f"📤 Response: {response_text}")
                    else:
                        print(f"❌ Error: {status} - {response_text}")
                        
        except Exception as e:
            print(f"❌ Connection Error: {e}")
        
        # Small delay between tests
        await asyncio.sleep(2)
    
    print("\n" + "=" * 60)
    print("✅ Conversation flow test completed!")

if __name__ == "__main__":
    asyncio.run(test_conversation_flow())