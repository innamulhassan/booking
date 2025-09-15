#!/usr/bin/env python3
"""
Test real Ultramsg webhook format
"""

import json
import aiohttp
import asyncio

async def test_real_webhook():
    print("🧪 Testing Real Ultramsg Webhook Format")
    print("=" * 50)
    
    # Real Ultramsg webhook payload format
    ultramsg_payload = {
        "id": "BAE5F6A1B2C3D4E5F6A7B8C9D0E1F2G3",
        "from": "1234567890@c.us",
        "to": "987654321@c.us", 
        "body": "Hi, I want to book a therapy appointment",
        "type": "text",  # Use "text" instead of "chat"
        "senderName": "Test User",
        "fromMe": False,
        "time": 1642687400,
        "chatId": "1234567890@c.us"
    }
    
    url = "http://localhost:8000/webhook"
    
    try:
        async with aiohttp.ClientSession() as session:
            print(f"📤 Sending webhook to: {url}")
            print(f"📝 Payload: {json.dumps(ultramsg_payload, indent=2)}")
            
            async with session.post(
                url,
                json=ultramsg_payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                response_text = await response.text()
                
                print(f"\n📊 Response Status: {response.status}")
                print(f"📋 Response: {response_text}")
                
                if response.status == 200:
                    print("✅ Webhook processed successfully!")
                else:
                    print("❌ Webhook failed!")
                    
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(test_real_webhook())