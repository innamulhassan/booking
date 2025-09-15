"""
Test All Ultramsg Webhook Types
Comprehensive testing for all enabled webhook types
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# Test webhook URL
WEBHOOK_URL = "http://localhost:8000/webhook"
STATUS_URL = "http://localhost:8000/webhook-types"

class WebhookTester:
    """Test all webhook types"""
    
    def __init__(self):
        self.test_results = {}
    
    async def test_webhook_type(self, webhook_name: str, webhook_data: dict):
        """Test a specific webhook type"""
        
        print(f"\n🧪 Testing: {webhook_name}")
        print(f"📋 Data: {json.dumps(webhook_data, indent=2)}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(WEBHOOK_URL, json=webhook_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ SUCCESS: {webhook_name}")
                        print(f"📊 Response: {json.dumps(result, indent=2)}")
                        self.test_results[webhook_name] = {"status": "success", "response": result}
                    else:
                        error_text = await response.text()
                        print(f"❌ FAILED: {webhook_name} - Status {response.status}")
                        print(f"📋 Error: {error_text}")
                        self.test_results[webhook_name] = {"status": "failed", "error": error_text}
                        
        except Exception as e:
            print(f"❌ ERROR: {webhook_name} - {str(e)}")
            self.test_results[webhook_name] = {"status": "error", "error": str(e)}
    
    async def test_all_webhooks(self):
        """Test all webhook types enabled in Ultramsg"""
        
        print("=" * 80)
        print("🚀 TESTING ALL ULTRAMSG WEBHOOK TYPES")
        print("=" * 80)
        
        # Test 1: Message Received (text message)
        await self.test_webhook_type("Message Received (Text)", {
            "id": "test_msg_001",
            "from": "+1234567890@c.us",
            "to": "instance142693@c.us",
            "body": "Hello! I need to book a therapy appointment for next week.",
            "type": "chat",
            "senderName": "Test User",
            "fromMe": False,
            "time": int(datetime.now().timestamp()),
            "chatId": "+1234567890@c.us"
        })
        
        # Test 2: Message Received (media)
        await self.test_webhook_type("Message Received (Image)", {
            "id": "test_media_001",
            "from": "+1234567890@c.us",
            "to": "instance142693@c.us",
            "body": "",
            "type": "image",
            "senderName": "Test User",
            "fromMe": False,
            "time": int(datetime.now().timestamp()),
            "chatId": "+1234567890@c.us",
            "caption": "Here's my insurance card",
            "filename": "insurance_card.jpg",
            "url": "https://example.com/media/insurance_card.jpg",
            "mimetype": "image/jpeg"
        })
        
        # Test 3: Message ACK
        await self.test_webhook_type("Message ACK (Delivered)", {
            "id": "test_ack_001", 
            "to": "+1234567890@c.us",
            "ack": 2,
            "status": "delivered",
            "time": int(datetime.now().timestamp())
        })
        
        # Test 4: Message ACK (Read)
        await self.test_webhook_type("Message ACK (Read)", {
            "id": "test_ack_002",
            "to": "+1234567890@c.us", 
            "ack": 3,
            "status": "read",
            "time": int(datetime.now().timestamp())
        })
        
        # Test 5: Message Create (outgoing)
        await self.test_webhook_type("Message Create (Outgoing)", {
            "id": "test_create_001",
            "from": "instance142693@c.us",
            "to": "+1234567890@c.us",
            "body": "Your appointment is confirmed for tomorrow at 2 PM.",
            "type": "chat",
            "fromMe": True,
            "time": int(datetime.now().timestamp())
        })
        
        # Test 6: Media Download
        await self.test_webhook_type("Media Download (Document)", {
            "id": "test_download_001",
            "from": "+1234567890@c.us",
            "to": "instance142693@c.us",
            "type": "document",
            "senderName": "Test User",
            "fromMe": False,
            "time": int(datetime.now().timestamp()),
            "filename": "medical_report.pdf",
            "url": "https://example.com/media/medical_report.pdf",
            "mimetype": "application/pdf",
            "caption": "My latest medical report"
        })
        
        # Test 7: Reaction
        await self.test_webhook_type("Reaction (Thumbs Up)", {
            "id": "test_reaction_001",
            "from": "+1234567890@c.us",
            "senderName": "Test User",
            "reaction": "👍",
            "reacted_message": "test_msg_001",
            "time": int(datetime.now().timestamp())
        })
        
        # Test 8: Reaction (Heart)
        await self.test_webhook_type("Reaction (Heart)", {
            "id": "test_reaction_002", 
            "from": "+1234567890@c.us",
            "senderName": "Test User",
            "reaction": "❤️",
            "reacted_message": "test_create_001",
            "time": int(datetime.now().timestamp())
        })
        
        await asyncio.sleep(1)  # Brief pause
        
        # Show results
        await self.show_test_results()
    
    async def show_test_results(self):
        """Show comprehensive test results"""
        
        print("\n" + "=" * 80)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 80)
        
        success_count = sum(1 for r in self.test_results.values() if r["status"] == "success")
        total_tests = len(self.test_results)
        
        print(f"✅ Successful: {success_count}/{total_tests}")
        print(f"❌ Failed: {total_tests - success_count}/{total_tests}")
        
        print(f"\n📋 DETAILED RESULTS:")
        for webhook_type, result in self.test_results.items():
            status_emoji = "✅" if result["status"] == "success" else "❌"
            print(f"   {status_emoji} {webhook_type}: {result['status'].upper()}")
            if result["status"] != "success":
                print(f"      Error: {result.get('error', 'Unknown error')}")
        
        # Check server webhook types endpoint
        await self.check_server_status()
    
    async def check_server_status(self):
        """Check server webhook types status"""
        
        print(f"\n🔍 CHECKING SERVER WEBHOOK SUPPORT:")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(STATUS_URL) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        print("✅ Server webhook types endpoint accessible")
                        print("\n📊 WEBHOOK STATISTICS:")
                        
                        for webhook_type, info in data.get("supported_webhooks", {}).items():
                            processed = info.get("processed", 0)
                            description = info.get("description", "No description")
                            print(f"   • {webhook_type}: {processed} processed - {description}")
                        
                        print(f"\n🔧 ULTRAMSG CONFIGURATION:")
                        for setting in data.get("ultramsg_configuration", {}).get("required_webhook_settings", []):
                            print(f"   {setting}")
                            
                    else:
                        print(f"❌ Server status check failed: {response.status}")
                        
        except Exception as e:
            print(f"❌ Could not check server status: {str(e)}")

async def main():
    """Run all webhook tests"""
    
    print("🧪 ULTRAMSG WEBHOOK COMPREHENSIVE TESTER")
    print("Testing all enabled webhook types...")
    print("\n⚠️  MAKE SURE:")
    print("1. The webhook server is running (START-ALL.bat)")
    print("2. All webhook types are enabled in Ultramsg dashboard")
    print("3. Webhook URL is set to: https://webhook-booking.innamul.com/webhook")
    
    input("\nPress Enter to start testing...")
    
    tester = WebhookTester()
    await tester.test_all_webhooks()
    
    print("\n" + "=" * 80)
    print("🎉 WEBHOOK TESTING COMPLETED!")
    print("=" * 80)
    print("\n💡 Next Steps:")
    print("1. Check the webhook server logs for detailed processing")
    print("2. Test with real WhatsApp messages to your business number")
    print("3. Monitor the /stats endpoint for live webhook statistics")
    print("4. Check /webhook-types endpoint for real-time processing counts")

if __name__ == "__main__":
    asyncio.run(main())
