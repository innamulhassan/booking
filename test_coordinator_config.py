#!/usr/bin/env python3
"""
Test script to verify coordinator phone number configuration
"""

import sys
import os

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'therapy_booking_app'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'other_scripts'))

def test_environment_config():
    """Test environment config loading"""
    print("=" * 60)
    print("TESTING ENVIRONMENT CONFIGURATION")
    print("=" * 60)
    
    try:
        from environment_config import get_config
        env_config = get_config()
        
        print(f"✅ Environment Config Loaded")
        print(f"   • Agent Phone: {env_config.AGENT_PHONE_NUMBER}")
        print(f"   • Coordinator Phone: {env_config.COORDINATOR_PHONE_NUMBER}")
        
        return env_config.COORDINATOR_PHONE_NUMBER
        
    except Exception as e:
        print(f"❌ Environment Config Failed: {e}")
        return None

def test_app_config():
    """Test app config loading"""
    print(f"\nTESTING APP CONFIGURATION")
    print("-" * 40)
    
    try:
        from config.settings import config
        
        print(f"✅ App Config Loaded")
        print(f"   • Agent Phone: {config.AGENT_PHONE_NUMBER}")
        print(f"   • Coordinator Phone: {config.COORDINATOR_PHONE_NUMBER}")
        
        return config.COORDINATOR_PHONE_NUMBER
        
    except Exception as e:
        print(f"❌ App Config Failed: {e}")
        return None

def test_adk_service():
    """Test ADK service coordinator phone"""
    print(f"\nTESTING ADK SERVICE")
    print("-" * 40)
    
    try:
        from app.services.adk_agent_service import get_coordinator_phone
        
        coordinator_phone = get_coordinator_phone()
        print(f"✅ ADK Service Get Coordinator Phone")
        print(f"   • Coordinator Phone: {coordinator_phone}")
        
        return coordinator_phone
        
    except Exception as e:
        print(f"❌ ADK Service Failed: {e}")
        return None

def test_webhook_detection():
    """Test webhook phone number detection"""
    print(f"\nTESTING WEBHOOK PHONE DETECTION")
    print("-" * 40)
    
    try:
        # Simulate what happens in webhook
        from config.settings import config
        coordinator_phone = config.COORDINATOR_PHONE_NUMBER.replace('+', '')
        test_number = "97471669569"
        
        print(f"✅ Webhook Detection Logic")
        print(f"   • Expected Coordinator (no +): {coordinator_phone}")
        print(f"   • Test Number: {test_number}")
        print(f"   • Match: {coordinator_phone == test_number}")
        
        return coordinator_phone == test_number
        
    except Exception as e:
        print(f"❌ Webhook Detection Failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 COORDINATOR PHONE NUMBER CONFIGURATION TEST")
    
    # Test all components
    env_phone = test_environment_config()
    app_phone = test_app_config()
    adk_phone = test_adk_service()
    webhook_match = test_webhook_detection()
    
    # Summary
    print(f"\n" + "=" * 60)
    print("CONFIGURATION TEST SUMMARY")
    print("=" * 60)
    
    all_phones = [env_phone, app_phone, adk_phone]
    phones_consistent = len(set(filter(None, all_phones))) <= 1
    
    if phones_consistent and webhook_match:
        print("✅ SUCCESS: All configurations are consistent!")
        print(f"   • Coordinator Phone: {env_phone}")
        print(f"   • Webhook Detection: Working")
    else:
        print("❌ ERROR: Configuration inconsistencies found!")
        print(f"   • Environment Config: {env_phone}")
        print(f"   • App Config: {app_phone}")
        print(f"   • ADK Service: {adk_phone}")
        print(f"   • Webhook Match: {webhook_match}")
    
    print(f"\n🎯 EXPECTED RESULT:")
    print(f"   • All phone numbers should be: +97471669569")
    print(f"   • Webhook should detect: 97471669569 (without +)")