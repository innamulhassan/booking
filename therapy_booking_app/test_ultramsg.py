"""
Quick Ultramsg Test Script
Test your WhatsApp integration
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ultramsg_service import ultramsg_service

async def test_ultramsg():
    """Test Ultramsg integration"""
    
    print("🧪 Testing Ultramsg WhatsApp Integration")
    print("=" * 50)
    
    # Test 1: Check instance status
    print("1️⃣ Checking instance status...")
    try:
        status = await ultramsg_service.get_instance_status()
        if status.get('account_status') == 'authenticated':
            print("✅ Instance is authenticated and ready")
        else:
            print(f"⚠️ Instance status: {status}")
    except Exception as e:
        print(f"❌ Status check failed: {e}")
    
    # Test 2: Send test message
    print("\n2️⃣ Sending test message...")
    test_phone = "+97471669569"  # Your test number with country code
    test_message = """
🩺 *Therapy Booking Test*

Hello! This is a test message from your therapy booking system.

✅ Ultramsg integration is working
📱 WhatsApp API is connected
🚀 Ready for appointment bookings!

Reply with "BOOK" to test the booking flow.
    """.strip()
    
    try:
        result = await ultramsg_service.send_therapeutic_message(
            test_phone, 
            "Your therapy booking system is now connected and ready! 🎉",
            "welcome"
        )
        
        if result.get('success'):
            print(f"✅ Test message sent successfully!")
            print(f"   Message ID: {result.get('message_id')}")
        else:
            print(f"❌ Test message failed: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Test message error: {e}")
    
    # Test 3: Send appointment card
    print("\n3️⃣ Testing appointment card...")
    appointment_data = {
        'client_name': 'Test Client',
        'date': '2025-09-15',
        'time': '2:00 PM',
        'service_type': 'in-call',
        'location': 'Video Call'
    }
    
    try:
        result = await ultramsg_service.send_appointment_card(test_phone, appointment_data)
        
        if result.get('success'):
            print("✅ Appointment card sent successfully!")
        else:
            print(f"❌ Appointment card failed: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Appointment card error: {e}")
    
    # Test 4: Send service menu
    print("\n4️⃣ Testing service menu...")
    try:
        result = await ultramsg_service.send_service_menu(test_phone)
        
        if result.get('success'):
            print("✅ Service menu sent successfully!")
        else:
            print(f"❌ Service menu failed: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Service menu error: {e}")
    
    # Cleanup
    await ultramsg_service.close_session()
    
    print("\n🎉 Ultramsg integration test completed!")
    print("\n📱 Check your WhatsApp for the test messages")
    print("🚀 Your therapy booking system is ready!")

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_ultramsg())
