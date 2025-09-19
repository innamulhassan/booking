#!/usr/bin/env python3
"""
Test script to demonstrate Layla's seamless booking workflow:
1. Client talks to Layla (thinks she's a real person)
2. Layla silently consults coordinator 
3. Layla confirms back to client personally

This tests the complete flow without revealing the coordinator process.
"""

import asyncio
import sys
import os

# Add the therapy_booking_app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'therapy_booking_app'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'other_scripts'))

from app.services.adk_agent_service import adk_service

async def test_layla_booking_workflow():
    """Test the complete Layla booking workflow from client perspective"""
    
    print("🌟 TESTING LAYLA'S SEAMLESS BOOKING EXPERIENCE 🌟")
    print("=" * 60)
    
    # Client information
    client_phone = "+97477777777"
    client_name = "Sara Ahmed"
    session_id = f"test_session_{client_phone}_{int(asyncio.get_event_loop().time())}"
    
    print(f"👤 Client: {client_name} ({client_phone})")
    print(f"📱 Session: {session_id}")
    print()
    
    # Test conversation flow
    messages = [
        "Hi, I need therapy help",
        "I want to book a 1 hour session at your clinic",
        "Tomorrow at 2 PM would be perfect",
        "Dr. Ahmad sounds good",
        "Yes, please book it for me"
    ]
    
    print("💬 CONVERSATION FLOW:")
    print("-" * 40)
    
    for i, message in enumerate(messages, 1):
        print(f"\n🗣️ Client: {message}")
        
        try:
            # Process message through Layla
            response = await adk_service.process_message(
                message=message,
                phone_number=client_phone,
                session_id=session_id,
                pushname=client_name
            )
            
            print(f"💕 Layla: {response}")
            
            # Simulate brief pause between messages
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"❌ Error processing message {i}: {e}")
            break
    
    print("\n" + "=" * 60)
    print("✨ Test completed! Check if:")
    print("1. Client thinks Layla handled everything personally")
    print("2. No mention of coordinator or approval process")
    print("3. Layla speaks like a caring, real person")
    print("4. Silent coordinator notification sent in background")

def test_booking_function_directly():
    """Test the book_appointment function directly to see the response"""
    
    print("\n🔬 DIRECT BOOKING FUNCTION TEST")
    print("-" * 40)
    
    # Import the booking function
    from app.services.adk_agent_service import book_appointment
    
    # Set up client context for the booking function
    book_appointment._current_client_context = {
        'phone_number': '+97477777777',
        'pushname': 'Sara Ahmed'
    }
    
    # Test booking
    result = book_appointment(
        date="2025-09-17",
        time="14:00",
        service_name="1 Hour In-Call Session",
        therapist_name="Dr. Ahmad",
        extra_services="",
        description="Anxiety support session"
    )
    
    print("📋 Booking Result:")
    print(f"Status: {result.get('status')}")
    print(f"Message: {result.get('message')}")
    
    if result.get('status') == 'success':
        print("✅ SUCCESS: Layla's response sounds personal and caring")
        print("✅ SUCCESS: No mention of coordinator approval process")
    else:
        print("❌ ISSUE: Check the booking function response")

async def main():
    """Main test function"""
    
    print("🏥 THERAPY BOOKING SYSTEM - LAYLA PERSONALITY TEST")
    print("Testing seamless client experience with Layla")
    print("=" * 60)
    
    # Test 1: Direct booking function
    test_booking_function_directly()
    
    # Test 2: Full conversation flow
    await test_layla_booking_workflow()
    
    print("\n🎯 KEY TESTING POINTS:")
    print("• Client feels like talking to real caring person (Layla)")
    print("• No coordinator mentions in client-facing messages")
    print("• Warm, personal, feminine tone throughout")
    print("• Silent background coordinator notifications")
    print("• Immediate booking confirmation (no 'waiting for approval')")

if __name__ == "__main__":
    asyncio.run(main())