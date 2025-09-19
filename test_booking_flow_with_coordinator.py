#!/usr/bin/env python3
"""
Test script to simulate a complete booking flow and verify coordinator notifications.
This will help us verify if the coordinator notification system is working.
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timedelta

# Add the necessary paths
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), 'therapy_booking_app'))

async def test_booking_flow():
    """Test the complete booking flow with coordinator notification"""
    
    print("🔍 Testing Complete Booking Flow with Coordinator Notifications")
    print("=" * 60)
    
    # Test 1: Check if coordinator phone is properly configured
    print("\n1. Testing Coordinator Phone Configuration")
    print("-" * 40)
    
    try:
        from src.therapy_booking.core.config import get_settings
        config = get_settings()
        coordinator_phone = getattr(config, 'coordinator_phone_number', None)
        print(f"✅ Coordinator phone from config: {coordinator_phone}")
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        
    # Test 2: Check environment variable directly
    print("\n2. Testing Environment Variable")
    print("-" * 40)
    
    try:
        from src.therapy_booking.core.config import get_settings
        env_config = get_settings()
        print(f"✅ Coordinator phone from env: {env_config.coordinator_phone_number}")
        print(f"✅ Ultramsg instance: {env_config.ultramsg_instance_id}")
        print(f"✅ Ultramsg token: {env_config.ultramsg_token[:10]}...")
    except Exception as e:
        print(f"❌ Error loading environment config: {e}")
    
    # Test 3: Test booking service functions
    print("\n3. Testing Booking Service Functions")
    print("-" * 40)
    
    try:
        from src.therapy_booking.services.booking_service import booking_service
        from src.therapy_booking.models.database import SessionLocal
        
        # Test database connection
        db = SessionLocal()
        print("✅ Database connection successful")
        
        # Test user lookup
        test_phone = "917401290081"  # From the logs
        user = booking_service.get_or_create_user(db, test_phone, "Test User")
        print(f"✅ User lookup/creation successful: {user.name} ({user.phone_number})")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error testing booking service: {e}")
    
    # Test 4: Test UltraMsg service
    print("\n4. Testing UltraMsg Service")
    print("-" * 40)
    
    try:
        from src.therapy_booking.external.ultramsg_service import ultramsg_service
        
        # Test coordinator phone retrieval
        coordinator_phone = ultramsg_service.get_coordinator_phone()
        print(f"✅ Coordinator phone from ultramsg service: {coordinator_phone}")
        
        # Note: We won't actually send a test message to avoid spam
        print("ℹ️  Skipping actual message send to avoid spam")
        
    except Exception as e:
        print(f"❌ Error testing UltraMsg service: {e}")
    
    # Test 5: Simulate booking function call
    print("\n5. Testing Booking Function (Simulation)")
    print("-" * 40)
    
    try:
        from src.therapy_booking.services.adk_agent_service import book_appointment
        
        # Get tomorrow's date
        tomorrow = datetime.now() + timedelta(days=1)
        test_date = tomorrow.strftime("%Y-%m-%d")
        
        print(f"📅 Simulating booking for date: {test_date}")
        print(f"⏰ Time: 10:00 AM")
        print(f"🏥 Service: 1 Hour In-Call Session")
        print(f"👨‍⚕️ Therapist: Dr. Ahmad Al-Rashid")
        
        # Simulate the booking (this will actually create an appointment)
        print("\n⚠️  This will create a real appointment in PENDING status...")
        
        # Set up client context (simulate what the ADK service does)
        book_appointment._current_client_context = {
            'phone_number': '917401290081',
            'pushname': 'Test User',
            'session_id': 'test-session-12345'
        }
        
        # Create the booking
        result = book_appointment(
            date=test_date,
            time="10:00 AM", 
            service_name="1 Hour In-Call Session",
            therapist_name="Dr. Ahmad Al-Rashid",
            extra_services="None",
            description="Test booking for coordinator notification verification"
        )
        
        print(f"📋 Booking result: {result}")
        
    except Exception as e:
        print(f"❌ Error testing booking function: {e}")
        
    print("\n" + "=" * 60)
    print("🏁 Test Complete!")
    print("\nTo verify coordinator notifications:")
    print("1. Check the coordinator's WhatsApp (+97471669569)")
    print("2. Look for a message with booking details")
    print("3. The message should contain APPROVE/DECLINE options")
    print("4. Reply with APPROVE or DECLINE to test the response handling")

if __name__ == "__main__":
    print("Starting Booking Flow Test...")
    asyncio.run(test_booking_flow())