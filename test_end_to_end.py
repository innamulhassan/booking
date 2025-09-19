"""
End-to-end testing script for the refactored therapy booking system.
Tests all new services: NLP, notification, error handling, configuration.
"""
import asyncio
import sys
import os
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add the project root to Python path
project_root = Path(__file__).parent / "therapy_booking_app"
sys.path.insert(0, str(project_root))

# Import our new services
try:
    from app.services.coordinator_nlp_service import coordinator_nlp_service, ResponseType
    from app.services.notification_service import notification_service, MessageType, NotificationRequest, MessagePriority
    from app.services.error_handler import error_handler, ErrorCategory, ErrorSeverity, ErrorContext
    from app.services.config_service import config_service
    print("✅ Successfully imported all new services!")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


class TestResults:
    """Track test results."""
    def __init__(self):
        self.tests = []
    
    def add_result(self, test_name: str, passed: bool, details: str = ""):
        self.tests.append({
            'name': test_name,
            'passed': passed,
            'details': details,
            'timestamp': datetime.now()
        })
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details and not passed:
            print(f"   Details: {details}")
    
    def summary(self):
        total = len(self.tests)
        passed = sum(1 for test in self.tests if test['passed'])
        failed = total - passed
        
        print("\n" + "="*60)
        print(f"TEST SUMMARY: {passed}/{total} tests passed")
        print("="*60)
        
        if failed > 0:
            print(f"\n❌ FAILED TESTS ({failed}):")
            for test in self.tests:
                if not test['passed']:
                    print(f"   • {test['name']}: {test['details']}")
        
        return passed == total


async def test_configuration_service():
    """Test the configuration service."""
    print("\n🔧 Testing Configuration Service...")
    results = TestResults()
    
    # Test 1: Configuration loading
    try:
        config_service.load_configuration()
        results.add_result("Configuration loading", True)
    except Exception as e:
        results.add_result("Configuration loading", False, str(e))
    
    # Test 2: Validation
    validation_result = config_service.validate_required_config()
    results.add_result(
        "Configuration validation", 
        validation_result['is_valid'],
        f"Missing: {validation_result['missing_config']}" if not validation_result['is_valid'] else ""
    )
    
    # Test 3: Get specific config values
    try:
        ultramsg_config = config_service.get_ultramsg_config()
        coordinator_phone = config_service.get_coordinator_phone()
        
        has_ultramsg = bool(ultramsg_config.get('ULTRAMSG_TOKEN') and ultramsg_config.get('ULTRAMSG_INSTANCE_ID'))
        has_coordinator = bool(coordinator_phone)
        
        results.add_result("UltraMsg configuration", has_ultramsg, "Missing token or instance ID" if not has_ultramsg else "")
        results.add_result("Coordinator phone", has_coordinator, "No coordinator phone configured" if not has_coordinator else "")
        
    except Exception as e:
        results.add_result("Configuration access", False, str(e))
    
    return results


async def test_nlp_service():
    """Test the NLP service for coordinator responses."""
    print("\n🧠 Testing NLP Service...")
    results = TestResults()
    
    # Test cases for different response types
    test_cases = [
        ("yes", ResponseType.APPROVAL, "Simple approval"),
        ("approve 123", ResponseType.APPROVAL, "Approval with ID"),
        ("no", ResponseType.DECLINE, "Simple decline"),
        ("decline 456", ResponseType.DECLINE, "Decline with ID"),
        ("modify the time please", ResponseType.MODIFICATION, "Modification request"),
        ("hello how are you", None, "Non-actionable message"),
        ("aprove", ResponseType.APPROVAL, "Typo handling"),
        ("ok", ResponseType.APPROVAL, "Alternative approval"),
        ("nope", ResponseType.DECLINE, "Alternative decline")
    ]
    
    for message, expected_type, description in test_cases:
        try:
            result = coordinator_nlp_service.process_response(message)
            
            # Check if response is actionable (not UNKNOWN)
            is_actionable = result.response_type != ResponseType.UNKNOWN
            
            if expected_type is None:
                # Should not be actionable
                passed = not is_actionable
                details = "Expected non-actionable" if passed else f"Got actionable: {result.response_type}"
            else:
                # Should match expected type
                passed = is_actionable and result.response_type == expected_type
                details = "" if passed else f"Expected {expected_type}, got {result.response_type if is_actionable else 'non-actionable'}"
            
            results.add_result(f"NLP: {description}", passed, details)
            
        except Exception as e:
            results.add_result(f"NLP: {description}", False, str(e))
    
    return results


async def test_error_handler():
    """Test the error handling service."""
    print("\n🛡️ Testing Error Handler...")
    results = TestResults()
    
    # Test 1: Basic error handling
    try:
        test_error = ValueError("Test error for validation")
        context = ErrorContext(
            user_phone="+1234567890",
            endpoint="test_endpoint",
            user_action="test_action"
        )
        
        error_result = await error_handler.handle_error(
            test_error,
            ErrorCategory.VALIDATION,
            ErrorSeverity.LOW,
            context,
            "Custom test message"
        )
        
        passed = error_result.get('handled', False) and 'user_message' in error_result
        results.add_result("Basic error handling", passed, "Missing handled flag or user_message" if not passed else "")
        
    except Exception as e:
        results.add_result("Basic error handling", False, str(e))
    
    # Test 2: Error summary
    try:
        summary = error_handler.get_error_summary(1)  # Last 1 hour
        passed = isinstance(summary, dict) and 'total_errors' in summary
        results.add_result("Error summary", passed, "Invalid summary format" if not passed else "")
        
    except Exception as e:
        results.add_result("Error summary", False, str(e))
    
    return results


async def test_notification_service():
    """Test the notification service (without actually sending messages)."""
    print("\n📬 Testing Notification Service...")
    results = TestResults()
    
    # Test 1: Service initialization
    try:
        stats = notification_service.get_delivery_stats()
        passed = isinstance(stats, dict) and 'sent' in stats
        results.add_result("Notification service init", passed, "Invalid stats format" if not passed else "")
    except Exception as e:
        results.add_result("Notification service init", False, str(e))
    
    # Test 2: Template generation (without sending)
    try:
        # Test coordinator approval request template
        test_data = {
            'appointment_id': 123,
            'client_name': 'Test Client',
            'client_phone': '+1234567890',
            'appointment_date': '2025-09-19',
            'appointment_time': '14:00',
            'service_name': 'Test Therapy',
            'therapist_name': 'Dr. Test',
            'price': 150.0,
            'description': 'Test appointment',
            'extra_services': 'None'
        }
        
        # Get the template and try to format it
        template = notification_service.templates.get(MessageType.COORDINATOR_APPROVAL_REQUEST)
        if template:
            message_content = notification_service._generate_message(template, test_data)
            passed = len(message_content) > 0 and 'Test Client' in message_content
            results.add_result("Template generation", passed, "Template not generated or missing client name" if not passed else "")
        else:
            results.add_result("Template generation", False, "Coordinator approval template not found")
            
    except Exception as e:
        results.add_result("Template generation", False, str(e))
    
    return results


async def test_integration():
    """Test integration between services."""
    print("\n🔗 Testing Service Integration...")
    results = TestResults()
    
    # Test 1: NLP + Notification integration
    try:
        # Process a coordinator approval
        nlp_result = coordinator_nlp_service.process_response("yes 123")
        
        # Check if response is actionable (not UNKNOWN)
        is_actionable = nlp_result.response_type != ResponseType.UNKNOWN
        
        if is_actionable and nlp_result.response_type == ResponseType.APPROVAL:
            # Try to prepare notification data
            notification_data = {
                'appointment_id': nlp_result.appointment_id,
                'client_name': 'Integration Test Client',
                'client_phone': '+1234567890',
                'appointment_date': '2025-09-19',
                'appointment_time': '14:00',
                'service_description': 'Integration Test'
            }
            
            # Test template formatting
            template = notification_service.templates.get(MessageType.CLIENT_CONFIRMATION)
            if template:
                message = notification_service._generate_message(template, notification_data)
                passed = 'Integration Test' in message  # Check for service_description which is in the template
                results.add_result("NLP + Notification integration", passed, "Service description not in message" if not passed else "")
            else:
                results.add_result("NLP + Notification integration", False, "Client confirmation template not found")
        else:
            results.add_result("NLP + Notification integration", False, "NLP didn't process approval correctly")
            
    except Exception as e:
        results.add_result("NLP + Notification integration", False, str(e))
    
    # Test 2: Error handling with context
    try:
        context = ErrorContext(
            user_phone=config_service.get_coordinator_phone() or "+1234567890",
            endpoint="integration_test",
            user_action="test_integration"
        )
        
        test_error = RuntimeError("Integration test error")
        error_result = await error_handler.handle_error(
            test_error,
            ErrorCategory.SYSTEM,
            ErrorSeverity.MEDIUM,
            context
        )
        
        passed = error_result.get('handled', False)
        results.add_result("Error handling with context", passed, "Error not properly handled" if not passed else "")
        
    except Exception as e:
        results.add_result("Error handling with context", False, str(e))
    
    return results


async def main():
    """Run all tests."""
    print("🚀 Starting End-to-End Testing of Refactored Therapy Booking System")
    print("=" * 70)
    
    all_results = []
    
    try:
        # Run all test suites
        config_results = await test_configuration_service()
        all_results.extend(config_results.tests)
        
        nlp_results = await test_nlp_service()
        all_results.extend(nlp_results.tests)
        
        error_results = await test_error_handler()
        all_results.extend(error_results.tests)
        
        notification_results = await test_notification_service()
        all_results.extend(notification_results.tests)
        
        integration_results = await test_integration()
        all_results.extend(integration_results.tests)
        
    except Exception as e:
        import traceback
        print(f"\n❌ Testing failed with exception: {e}")
        print(f"Traceback:\n{traceback.format_exc()}")
        return False
    
    # Generate summary
    total_tests = len(all_results)
    passed_tests = sum(1 for test in all_results if test['passed'])
    failed_tests = total_tests - passed_tests
    
    print("\n" + "="*70)
    print(f"🎯 FINAL TEST RESULTS: {passed_tests}/{total_tests} PASSED")
    print("="*70)
    
    if failed_tests > 0:
        print(f"\n❌ FAILED TESTS ({failed_tests}):")
        for test in all_results:
            if not test['passed']:
                print(f"   • {test['name']}: {test['details']}")
    else:
        print("\n🎉 ALL TESTS PASSED! System is ready for deployment.")
    
    # Configuration summary
    print(f"\n📋 CONFIGURATION STATUS:")
    validation = config_service.validate_required_config()
    if validation['is_valid']:
        print("✅ All required configuration is present")
    else:
        print(f"❌ Missing configuration: {validation['missing_config']}")
    
    print(f"\n🔧 SYSTEM INFO:")
    print(f"   • Coordinator Phone: {config_service.get_coordinator_phone()}")
    print(f"   • UltraMsg Instance: {config_service.get_config('ultramsg', 'ULTRAMSG_INSTANCE_ID')}")
    print(f"   • Database Host: {config_service.get_config('database', 'DB_HOST')}")
    
    return failed_tests == 0


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Testing failed with exception: {e}")
        sys.exit(1)