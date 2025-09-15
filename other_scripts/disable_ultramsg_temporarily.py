#!/usr/bin/env python3
"""
Temporary script to disable Ultramsg webhook to stop infinite loop
"""

import requests
import json
import os

def disable_ultramsg_webhook():
    """Temporarily disable webhook to stop message loop"""
    
    # Ultramsg API settings
    instance_id = "142693"
    token = os.getenv('ULTRAMSG_TOKEN', 'YOUR_TOKEN_HERE')  # Add your token
    base_url = f"https://api.ultramsg.com/{instance_id}"
    
    print("🛑 Attempting to disable Ultramsg webhook...")
    
    try:
        # Try to disable webhook
        response = requests.post(
            f"{base_url}/settings/webhook",
            data={
                'token': token,
                'webhook': '',  # Empty webhook URL disables it
                'webhookMessage': 0,  # Disable message webhooks
                'webhookMessageAck': 0,  # Disable message ack webhooks
            }
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Webhook disabled successfully!")
            print("💡 This should stop the infinite message loop")
        else:
            print("❌ Failed to disable webhook")
            print("🔧 You may need to disable it manually in Ultramsg dashboard")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("🔧 Please disable webhook manually in Ultramsg dashboard")
        
    print("\n" + "="*50)
    print("NEXT STEPS:")
    print("1. Check if messages have stopped")
    print("2. Go to Ultramsg dashboard: https://ultramsg.com/")
    print("3. Navigate to Settings > Webhooks")
    print("4. Temporarily disable or clear webhook URL")
    print("5. Check for any auto-responder features")
    print("6. Look for welcome message settings")
    print("="*50)

if __name__ == "__main__":
    disable_ultramsg_webhook()