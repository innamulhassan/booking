#!/usr/bin/env python3

import os
from dotenv import load_dotenv

# Test coordinator phone configuration
def test_coordinator_phone():
    print("=== TESTING COORDINATOR PHONE CONFIGURATION ===")
    
    # Load .env file
    load_dotenv()
    
    # Try to get coordinator phone from .env
    coordinator_phone = os.getenv('COORDINATOR_PHONE_NUMBER')
    print(f"From .env file: {coordinator_phone}")
    
    # Test the actual function
    try:
        import sys
        sys.path.append('therapy_booking_app')
        from app.services.adk_agent_service import get_coordinator_phone
        
        function_phone = get_coordinator_phone()
        print(f"From get_coordinator_phone(): {function_phone}")
        
        if coordinator_phone == function_phone:
            print("✅ Configuration MATCHES")
        else:
            print("❌ Configuration MISMATCH")
            
    except Exception as e:
        print(f"❌ Error calling get_coordinator_phone(): {e}")
        import traceback
        print(f"Full error: {traceback.format_exc()}")

if __name__ == "__main__":
    test_coordinator_phone()