#!/usr/bin/env python3
"""
Direct test of ADK Agent processing speed
"""

import sys
import os
import asyncio
import time
from pathlib import Path

# Add the therapy_booking_app to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'therapy_booking_app'))

async def test_adk_speed():
    try:
        print("🧪 ADK AGENT SPEED TEST")
        print("=" * 40)
        
        from app.services.adk_agent_service import adk_service
        
        test_messages = [
            "Hi",
            "I want to book an appointment", 
            "What services do you offer?"
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n📨 Test {i}: '{message}'")
            start_time = time.time()
            
            try:
                response = await adk_service.process_message(
                    message=message,
                    phone_number="+1234567890", 
                    session_id="test_session"
                )
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                print(f"⏱️  Processing Time: {processing_time:.2f} seconds")
                print(f"💬 Response: {response[:100]}...")
                
                if processing_time > 10:
                    print("⚠️  SLOW RESPONSE detected!")
                elif processing_time > 5:
                    print("⚠️  Moderate delay")
                else:
                    print("✅ Fast response")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print("\n" + "=" * 40)
        print("Test completed!")
        
    except Exception as e:
        print(f"❌ Test setup error: {e}")

if __name__ == "__main__":
    asyncio.run(test_adk_speed())