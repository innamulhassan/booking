#!/usr/bin/env python3
"""
Test script to check ADK Agent configuration and API key setup
"""

import sys
import os
from pathlib import Path

# Add the therapy_booking_app to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'therapy_booking_app'))

try:
    from config.settings import config
    print("✅ Configuration loaded successfully")
    
    # Check Google API Key
    print("\n🔍 GOOGLE API CONFIGURATION:")
    print(f"   Google API Key: {'✅ SET' if config.GOOGLE_API_KEY else '❌ NOT SET'}")
    print(f"   Model: {config.GOOGLE_GENAI_MODEL}")
    print(f"   Use Vertex AI: {config.GOOGLE_GENAI_USE_VERTEXAI}")
    
    # Check environment variables
    print("\n🔍 ENVIRONMENT VARIABLES:")
    print(f"   GOOGLE_API_KEY in env: {'✅' if os.getenv('GOOGLE_API_KEY') else '❌'}")
    
    if not config.GOOGLE_API_KEY:
        print("\n❌ CRITICAL ISSUE FOUND:")
        print("   The GOOGLE_API_KEY environment variable is missing!")
        print("   This is why the ADK Agent cannot process messages properly.")
        print("\n💡 SOLUTION:")
        print("   1. Get a Google AI API key from: https://makersuite.google.com/app/apikey")
        print("   2. Add it to your .env file: GOOGLE_API_KEY=your_api_key_here")
        print("   3. Restart the server")
        
    # Test ADK import
    print("\n🔍 ADK IMPORT TEST:")
    try:
        from google.adk.agents import Agent
        print("   ✅ Google ADK can be imported")
    except ImportError as e:
        print(f"   ❌ Google ADK import failed: {e}")
    except Exception as e:
        print(f"   ⚠️  Google ADK import error: {e}")
        
    # Test basic agent creation
    print("\n🔍 AGENT CREATION TEST:")
    try:
        if config.GOOGLE_API_KEY:
            from app.services.adk_agent_service import adk_service
            print("   ✅ ADK Agent service imported")
            if adk_service.agent:
                print("   ✅ ADK Agent initialized successfully")
            else:
                print("   ❌ ADK Agent not initialized")
        else:
            print("   ⚠️  Skipping agent creation - no API key")
    except Exception as e:
        print(f"   ❌ Agent creation failed: {e}")
        
except Exception as e:
    print(f"❌ Configuration error: {e}")
    
print("\n" + "="*60)