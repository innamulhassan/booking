"""
Unit tests for ADK Agent Service with comprehensive mocking
"""
import pytest
import unittest.mock as mock
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys
import os

# Add the app directory to sys.path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'therapy_booking_app'))


class TestADKAgentServiceFunctions:
    """Unit tests for individual ADK agent service functions with mocking"""
    
    @patch('app.services.adk_agent_service.parse_natural_date')
    @patch('app.services.adk_agent_service.get_db')
    def test_check_availability_with_natural_date(self, mock_get_db, mock_parse_date):
        """Test check_availability function with natural language date parsing"""
        from app.services.adk_agent_service import check_availability
        
        # Mock date parsing
        mock_parse_date.return_value = "2025-09-18"
        
        # Mock database
        mock_db = Mock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        
        # Mock appointment query (no conflicts)
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        # Test the function
        result = check_availability("today", "in_call")
        
        # Assertions
        assert result["status"] == "available"
        assert "2025-09-18" in result["message"]
        mock_parse_date.assert_called_once_with("today")
    
    @patch('app.services.adk_agent_service.parse_natural_date')
    def test_check_availability_invalid_date(self, mock_parse_date):
        """Test check_availability with invalid date"""
        from app.services.adk_agent_service import check_availability
        
        # Mock date parsing failure
        mock_parse_date.return_value = None
        
        result = check_availability("invalid_date", "in_call")
        
        assert result["status"] == "error"
        assert "couldn't understand the date" in result["error_message"]
    
    @patch('app.services.adk_agent_service.parse_natural_date')
    @patch('app.services.adk_agent_service.get_db')
    @patch('app.services.adk_agent_service.Appointment')
    @patch('app.services.adk_agent_service.threading')
    def test_book_appointment_success(self, mock_threading, mock_appointment_class, 
                                    mock_get_db, mock_parse_date):
        """Test successful appointment booking with mocking"""
        from app.services.adk_agent_service import book_appointment
        
        # Mock date parsing
        mock_parse_date.return_value = "2025-09-18"
        
        # Mock database and appointment
        mock_db = Mock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        
        mock_appointment = Mock()
        mock_appointment.id = 123
        mock_appointment.status.value = "pending_approval"
        mock_appointment_class.return_value = mock_appointment
        
        # Mock therapist query
        mock_therapist = Mock()
        mock_therapist.name = "Dr. Smith"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_therapist
        
        # Mock client context (simulate being called from ADK agent)
        with patch.object(book_appointment, '__globals__', {
            **book_appointment.__globals__,
            'client_context': {'test_session': {'phone_number': '+1234567890'}}
        }):
            # Test the function
            result = book_appointment("today", "14:00", "1 Hour In-Call Session")
        
        # Assertions
        assert result["status"] == "pending_approval"
        assert result["appointment_id"] == 123
        assert "submitted your request" in result["message"]
        mock_parse_date.assert_called_once_with("today")
    
    @patch('app.services.adk_agent_service.get_db')
    def test_get_clinic_info(self, mock_get_db):
        """Test get_clinic_info function with mocked config"""
        from app.services.adk_agent_service import get_clinic_info
        
        with patch('app.services.adk_agent_service.config') as mock_config:
            mock_config.CLINIC_NAME = "Test Clinic"
            mock_config.CLINIC_ADDRESS = "123 Test St"
            
            result = get_clinic_info()
            
            assert result["status"] == "success"
            assert result["clinic_name"] == "Test Clinic"
            assert result["assistant_name"] == "Layla"
            assert "specializations" in result


class TestADKAgentServiceClass:
    """Unit tests for ADK Agent Service class with mocking"""
    
    @patch('app.services.adk_agent_service.Agent')
    @patch('app.services.adk_agent_service.Runner')
    @patch('app.services.adk_agent_service.InMemorySessionService')
    def test_initialize_agent(self, mock_session_service, mock_runner, mock_agent):
        """Test ADK agent initialization with mocked components"""
        from app.services.adk_agent_service import ADKAgentService
        
        # Create service instance
        service = ADKAgentService()
        
        # Test initialization
        service._initialize_agent()
        
        # Verify mocks were called
        mock_agent.assert_called_once()
        mock_session_service.assert_called_once()
        mock_runner.assert_called_once()
        
        # Verify agent was set
        assert service.agent is not None
        assert service.runner is not None
    
    @patch('app.services.adk_agent_service.Agent')
    @patch('app.services.adk_agent_service.Runner')
    @patch('app.services.adk_agent_service.InMemorySessionService')
    async def test_process_message_success(self, mock_session_service, mock_runner, mock_agent):
        """Test message processing with mocked ADK components"""
        from app.services.adk_agent_service import ADKAgentService
        
        # Setup mocks
        mock_agent_instance = Mock()
        mock_agent.return_value = mock_agent_instance
        
        mock_runner_instance = Mock()
        mock_runner.return_value = mock_runner_instance
        
        # Mock events from runner
        mock_event = Mock()
        mock_event.is_final_response.return_value = True
        mock_event.content.parts = [Mock(text="Hello! How can I help you today?")]
        mock_runner_instance.run.return_value = [mock_event]
        
        # Mock session service
        mock_session_service_instance = Mock()
        mock_session_service.return_value = mock_session_service_instance
        
        # Create service and initialize
        service = ADKAgentService()
        service._initialize_agent()
        
        # Test message processing
        result = await service.process_message(
            message="Hello", 
            phone_number="+1234567890",
            session_id="test_session"
        )
        
        # Assertions
        assert "Hello! How can I help you today?" in result
        mock_runner_instance.run.assert_called_once()
    
    @patch('app.services.adk_agent_service.logger')
    async def test_process_message_error_handling(self, mock_logger):
        """Test error handling in message processing"""
        from app.services.adk_agent_service import ADKAgentService
        
        service = ADKAgentService()
        # Don't initialize agent to trigger error condition
        
        result = await service.process_message("test", "+1234567890")
        
        # Should return fallback message
        assert "booking system is temporarily unavailable" in result
        mock_logger.warning.assert_called()


class TestHelperFunctions:
    """Test helper functions with mocking"""
    
    @patch('app.services.adk_agent_service.logger')
    def test_get_coordinator_phone_success(self, mock_logger):
        """Test successful coordinator phone retrieval"""
        from app.services.adk_agent_service import get_coordinator_phone
        
        with patch('app.services.adk_agent_service.env_config') as mock_env:
            mock_env.COORDINATOR_PHONE_NUMBER = "+1234567890"
            
            result = get_coordinator_phone()
            
            assert result == "+1234567890"
            mock_logger.error.assert_not_called()
    
    @patch('app.services.adk_agent_service.logger')
    def test_get_coordinator_phone_error(self, mock_logger):
        """Test coordinator phone retrieval with error"""
        from app.services.adk_agent_service import get_coordinator_phone
        
        with patch('app.services.adk_agent_service.env_config') as mock_env:
            mock_env.side_effect = Exception("Config error")
            
            result = get_coordinator_phone()
            
            assert result is None
            mock_logger.error.assert_called()


class TestCoordinatorWorkflow:
    """Test coordinator workflow functions with mocking"""
    
    @patch('app.services.adk_agent_service.get_coordinator_phone')
    def test_process_coordinator_recommendation(self, mock_get_coordinator_phone):
        """Test coordinator recommendation processing"""
        from app.services.adk_agent_service import process_coordinator_recommendation
        
        mock_get_coordinator_phone.return_value = "+97471669569"
        
        result = process_coordinator_recommendation(
            coordinator_phone="+97471669569",
            recommendation_text="APPROVE 123",
            client_phone="+1234567890"
        )
        
        assert "status" in result
        mock_get_coordinator_phone.assert_called_once()


if __name__ == "__main__":
    # Run with pytest for better output
    pytest.main([__file__, "-v", "--tb=short"])