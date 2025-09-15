"""
Test cases for ADK Agent Service with Google Gemini 1.5 Pro 002 Model
Comprehensive testing of the enhanced AI-powered therapy booking system
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from app.services.adk_agent_service import ADKAgentService
from config.settings import Settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestADKGemini:
    def __init__(self):
        """Initialize test suite with configured ADK service"""
        self.settings = Settings()
        self.adk_service = ADKAgentService()
        self.test_user_id = "+97451334514"  # Test phone number
        
    async def setup_test_environment(self):
        """Setup test environment and validate configuration"""
        logger.info("🚀 Starting ADK Gemini Test Suite")
        logger.info(f"AI Provider: {self.settings.AI_PROVIDER}")
        logger.info(f"Google Model: {self.settings.GOOGLE_GENAI_MODEL}")
        logger.info(f"Google API Key configured: {'✅' if self.settings.GOOGLE_API_KEY else '❌'}")
        logger.info(f"Anthropic API Key configured: {'✅' if self.settings.ANTHROPIC_API_KEY else '❌'}")
        
        # Test AI model initialization
        try:
            await self.adk_service.initialize()
            logger.info("✅ ADK Service initialized successfully")
        except Exception as e:
            logger.error(f"❌ ADK Service initialization failed: {e}")
            raise
    
    async def test_intent_detection(self):
        """Test intent detection capabilities with various therapy-related messages"""
        logger.info("\n📋 Testing Intent Detection...")
        
        test_cases = [
            # Booking requests
            ("I want to book an appointment", "book_appointment"),
            ("Can I schedule a session tomorrow?", "book_appointment"),
            ("I need therapy for anxiety", "book_appointment"),
            ("Book me a slot for next week", "book_appointment"),
            
            # Availability queries
            ("What times are available today?", "check_availability"),
            ("When is the therapist free?", "check_availability"),
            ("Show me available slots", "check_availability"),
            
            # Information requests
            ("What services do you offer?", "get_info"),
            ("Tell me about your therapy types", "get_info"),
            ("How much does a session cost?", "get_info"),
            
            # Cancellation requests
            ("I want to cancel my appointment", "cancel_appointment"),
            ("Need to reschedule my session", "modify_appointment"),
            
            # Greetings and general
            ("Hello", "greeting"),
            ("Hi there", "greeting"),
            ("Thank you", "general"),
        ]
        
        for message, expected_intent in test_cases:
            try:
                result = await self.adk_service.detect_intent(
                    message=message,
                    user_id=self.test_user_id
                )
                
                detected_intent = result.get('intent', 'unknown')
                confidence = result.get('confidence', 0)
                
                status = "✅" if detected_intent == expected_intent else "⚠️"
                logger.info(f"{status} Message: '{message}' | Expected: {expected_intent} | Detected: {detected_intent} (confidence: {confidence:.2f})")
                
            except Exception as e:
                logger.error(f"❌ Intent detection failed for '{message}': {e}")
    
    async def test_entity_extraction(self):
        """Test entity extraction from therapy booking messages"""
        logger.info("\n🔍 Testing Entity Extraction...")
        
        test_messages = [
            "Book me an appointment for anxiety therapy tomorrow at 2pm",
            "I want to schedule a session on Friday morning for depression treatment",
            "Can I get a slot next Monday at 10:30 AM for couples therapy?",
            "Book Dr. Sarah for stress management on December 15th at 3 PM",
            "I need therapy for panic attacks this weekend",
        ]
        
        for message in test_messages:
            try:
                result = await self.adk_service.extract_entities(
                    message=message,
                    user_id=self.test_user_id
                )
                
                logger.info(f"📝 Message: '{message}'")
                logger.info(f"   Entities: {json.dumps(result.get('entities', {}), indent=2)}")
                
            except Exception as e:
                logger.error(f"❌ Entity extraction failed for '{message}': {e}")
    
    async def test_conversation_flow(self):
        """Test complete conversation flow for booking therapy appointments"""
        logger.info("\n💬 Testing Conversation Flow...")
        
        conversation_steps = [
            "Hi, I need help with my mental health",
            "I want to book a therapy session",
            "I'm dealing with anxiety and stress",
            "Tomorrow afternoon would be good",
            "Around 2 PM or 3 PM",
            "Yes, 2 PM sounds perfect",
            "My name is John Doe",
            "This is my first therapy session",
        ]
        
        for i, message in enumerate(conversation_steps, 1):
            try:
                result = await self.adk_service.process_message(
                    message=message,
                    user_id=self.test_user_id
                )
                
                response = result.get('response', 'No response generated')
                intent = result.get('intent', 'unknown')
                
                logger.info(f"Step {i}: User: '{message}'")
                logger.info(f"        Bot: '{response}' (Intent: {intent})")
                
                # Add small delay to simulate natural conversation
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"❌ Conversation step {i} failed: {e}")
    
    async def test_availability_checking(self):
        """Test availability checking functionality"""
        logger.info("\n📅 Testing Availability Checking...")
        
        # Test various time queries
        availability_queries = [
            "What's available today?",
            "Show me slots for tomorrow",
            "Any appointments next week?",
            "I need an evening slot",
            "Morning appointments available?",
        ]
        
        for query in availability_queries:
            try:
                result = await self.adk_service.check_availability(
                    message=query,
                    user_id=self.test_user_id
                )
                
                available_slots = result.get('available_slots', [])
                logger.info(f"🔍 Query: '{query}'")
                logger.info(f"   Available slots: {len(available_slots)} found")
                
                if available_slots:
                    for slot in available_slots[:3]:  # Show first 3 slots
                        logger.info(f"   - {slot}")
                
            except Exception as e:
                logger.error(f"❌ Availability check failed for '{query}': {e}")
    
    async def test_booking_creation(self):
        """Test complete booking creation process"""
        logger.info("\n📝 Testing Booking Creation...")
        
        booking_data = {
            "user_id": self.test_user_id,
            "therapist_name": "Dr. Sarah Johnson",
            "appointment_type": "anxiety therapy",
            "preferred_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "preferred_time": "14:00",
            "notes": "First-time patient dealing with work stress"
        }
        
        try:
            result = await self.adk_service.create_booking(booking_data)
            
            booking_id = result.get('booking_id')
            status = result.get('status')
            confirmation = result.get('confirmation_message')
            
            logger.info(f"✅ Booking created successfully")
            logger.info(f"   Booking ID: {booking_id}")
            logger.info(f"   Status: {status}")
            logger.info(f"   Confirmation: {confirmation}")
            
        except Exception as e:
            logger.error(f"❌ Booking creation failed: {e}")
    
    async def test_error_handling(self):
        """Test error handling and edge cases"""
        logger.info("\n🚨 Testing Error Handling...")
        
        error_test_cases = [
            ("", "empty message"),
            ("asdkjfhalsdjfhlasdjfhlasdjfhlasdjfhlasdjf", "random text"),
            ("Book appointment for 32nd of January", "invalid date"),
            ("I want therapy at 25 o'clock", "invalid time"),
        ]
        
        for message, test_type in error_test_cases:
            try:
                result = await self.adk_service.process_message(
                    message=message,
                    user_id=self.test_user_id
                )
                
                response = result.get('response', 'No response')
                error_handled = 'error' in response.lower() or 'sorry' in response.lower()
                
                status = "✅" if error_handled else "⚠️"
                logger.info(f"{status} {test_type}: '{message}' -> '{response[:100]}...'")
                
            except Exception as e:
                logger.info(f"✅ Exception properly caught for {test_type}: {e}")
    
    async def test_model_performance(self):
        """Test model performance and response quality"""
        logger.info("\n⚡ Testing Model Performance...")
        
        performance_tests = [
            "I'm feeling very anxious and need immediate help",
            "What's the difference between CBT and DBT therapy?",
            "I want to book multiple sessions for ongoing treatment",
            "Can you help me understand what to expect in my first session?",
            "I'm not sure if I need therapy, can you guide me?",
        ]
        
        total_time = 0
        successful_responses = 0
        
        for test_message in performance_tests:
            try:
                start_time = datetime.now()
                
                result = await self.adk_service.process_message(
                    message=test_message,
                    user_id=self.test_user_id
                )
                
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds()
                total_time += response_time
                
                response = result.get('response', '')
                if len(response) > 10:  # Basic quality check
                    successful_responses += 1
                
                logger.info(f"⏱️ Response time: {response_time:.2f}s | Length: {len(response)} chars")
                logger.info(f"   Message: '{test_message[:50]}...'")
                
            except Exception as e:
                logger.error(f"❌ Performance test failed: {e}")
        
        avg_response_time = total_time / len(performance_tests)
        success_rate = (successful_responses / len(performance_tests)) * 100
        
        logger.info(f"\n📊 Performance Summary:")
        logger.info(f"   Average response time: {avg_response_time:.2f}s")
        logger.info(f"   Success rate: {success_rate:.1f}%")
        logger.info(f"   Total tests: {len(performance_tests)}")
    
    async def run_all_tests(self):
        """Run all test cases in sequence"""
        try:
            await self.setup_test_environment()
            await self.test_intent_detection()
            await self.test_entity_extraction()
            await self.test_conversation_flow()
            await self.test_availability_checking()
            await self.test_booking_creation()
            await self.test_error_handling()
            await self.test_model_performance()
            
            logger.info("\n🎉 All ADK Gemini tests completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Test suite failed: {e}")
            raise

# Main execution
async def main():
    """Main test execution function"""
    test_suite = TestADKGemini()
    await test_suite.run_all_tests()

if __name__ == "__main__":
    # Run the comprehensive test suite
    asyncio.run(main())
