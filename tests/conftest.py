"""
Test configuration and utilities
"""
import os
import sys
import pytest
from pathlib import Path

# Add the therapy_booking_app directory to Python path for imports
test_dir = Path(__file__).parent
app_dir = test_dir.parent / "therapy_booking_app"
sys.path.insert(0, str(app_dir))

# Test configuration
pytest_plugins = []

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment"""
    # Set test environment variables
    os.environ["TESTING"] = "1"
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    
    yield
    
    # Cleanup after tests
    if "TESTING" in os.environ:
        del os.environ["TESTING"]


@pytest.fixture
def mock_db_session():
    """Provide a mock database session"""
    from unittest.mock import Mock
    
    mock_session = Mock()
    mock_session.query.return_value.filter.return_value.first.return_value = None
    mock_session.query.return_value.filter.return_value.all.return_value = []
    mock_session.add.return_value = None
    mock_session.commit.return_value = None
    mock_session.rollback.return_value = None
    mock_session.close.return_value = None
    
    return mock_session


@pytest.fixture
def sample_webhook_payload():
    """Provide a sample webhook payload for testing"""
    return {
        "messages": [{
            "id": "test_msg_123",
            "from": "+1234567890",
            "type": "text",
            "timestamp": "1695023400",
            "text": {"body": "Hello, I need an appointment"},
            "pushname": "Test Client"
        }]
    }


@pytest.fixture
def sample_coordinator_phone():
    """Provide sample coordinator phone number"""
    return "+97471669569"


class MockResponse:
    """Mock HTTP response class for testing"""
    
    def __init__(self, status_code=200, json_data=None, text=""):
        self.status_code = status_code
        self.text = text
        self._json_data = json_data or {}
    
    def json(self):
        return self._json_data


class TestHelpers:
    """Helper methods for testing"""
    
    @staticmethod
    def create_mock_appointment(appointment_id=123, status="pending_approval"):
        """Create a mock appointment object"""
        from unittest.mock import Mock
        
        mock_appointment = Mock()
        mock_appointment.id = appointment_id
        mock_appointment.status.value = status
        mock_appointment.client_phone = "+1234567890"
        mock_appointment.date = "2025-09-18"
        mock_appointment.time = "14:00"
        mock_appointment.service_name = "1 Hour In-Call Session"
        
        return mock_appointment
    
    @staticmethod
    def create_mock_therapist(name="Dr. Smith", specialization="CBT"):
        """Create a mock therapist object"""
        from unittest.mock import Mock
        
        mock_therapist = Mock()
        mock_therapist.id = 1
        mock_therapist.name = name
        mock_therapist.specialization = specialization
        mock_therapist.available = True
        
        return mock_therapist
    
    @staticmethod
    def create_mock_ultramsg_response(success=True, message_id="12345"):
        """Create a mock Ultramsg API response"""
        return {
            "success": success,
            "message_id": message_id,
            "status": "sent" if success else "failed"
        }


# Test markers for categorizing tests
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )
    config.addinivalue_line(
        "markers", "external: marks tests that require external services"
    )