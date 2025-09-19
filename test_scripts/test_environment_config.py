"""
Test Environment Configuration
Verify all environment variables are loaded correctly
"""

import sys
from pathlib import Path

# Add path to our scripts
sys.path.append(str(Path(__file__).parent.parent / "other_scripts"))

try:
    from environment_config import get_config
    
    print("=" * 80)
    print("🔧 TESTING ENVIRONMENT CONFIGURATION")
    print("=" * 80)
    
    # Load configuration
    config = get_config()
    
    # Print configuration
    config.print_configuration()
    
    # Validate configuration
    print("\n🔍 VALIDATION RESULTS:")
    is_valid = config.validate_configuration()
    
    if is_valid:
        print("\n✅ CONFIGURATION TEST PASSED!")
        print(f"   • Server will run on port {config.SERVER_PORT}")
        print(f"   • Agent phone: {config.AGENT_PHONE_NUMBER}")
        print(f"   • Coordinator phone: {config.COORDINATOR_PHONE_NUMBER}")
        print(f"   • Webhook URL: {config.WEBHOOK_URL}")
        print(f"   • Database: {config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}")
    else:
        print("\n❌ CONFIGURATION TEST FAILED!")
        print("   Please check the errors above and fix them in the .env file")
    
    # Test phone number access
    print(f"\n📞 PHONE NUMBERS TEST:")
    phone_numbers = config.get_phone_numbers()
    for key, value in phone_numbers.items():
        print(f"   • {key}: {value}")
    
    # Test server info
    print(f"\n🌐 SERVER INFO TEST:")
    server_info = config.get_server_info()
    for key, value in server_info.items():
        print(f"   • {key}: {value}")
    
    print("\n" + "=" * 80)
    print("🎉 ENVIRONMENT CONFIGURATION TEST COMPLETED")
    print("=" * 80)
    
except ImportError as e:
    print(f"❌ Failed to import environment_config: {e}")
    print("Make sure the environment_config.py file exists in other_scripts/")
    
except Exception as e:
    print(f"❌ Error testing configuration: {e}")
    import traceback
    traceback.print_exc()

print("\nPress Enter to exit...")
input()
