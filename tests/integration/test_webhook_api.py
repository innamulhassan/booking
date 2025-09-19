"""
Integration tests for FastAPI webhook endpoints with mocked external services
"""
import pytest
from fastapi.testclient import TestClient
import unittest.mock as mock
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add the app directory to sys.path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'therapy_booking_app'))


class TestWebhookEndpoints:
    """Integration tests for webhook API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client with mocked dependencies"""
        with patch('app.services.adk_agent_service.ADKAgentService'):
            with patch('app.services.ultramsg_service.UltramsgService'):
                # Import after patching to avoid initialization issues
                from app.main import app
                return TestClient(app)
    
    @patch('app.services.adk_agent_service.ADKAgentService')
    @patch('app.services.ultramsg_service.UltramsgService')
    def test_webhook_health_endpoint(self, mock_ultramsg, mock_adk):
        """Test health check endpoint"""
        from app.main import app
        client = TestClient(app)
        
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "therapy_booking_app"}
    
    @patch('app.services.adk_agent_service.ADKAgentService')
    @patch('app.services.ultramsg_service.UltramsgService')
    @patch('app.database.get_db')
    async def test_webhook_message_processing(self, mock_get_db, mock_ultramsg_class, mock_adk_class):
        """Test webhook message processing with mocked services"""
        from app.main import app
        
        # Mock ADK service
        mock_adk = Mock()
        mock_adk.process_message = AsyncMock(return_value="Hello! How can I help you today?")
        mock_adk_class.return_value = mock_adk
        
        # Mock Ultramsg service
        mock_ultramsg = Mock()
        mock_ultramsg.send_message = AsyncMock(return_value={
            "success": True,
            "message_id": "12345",
            "status": "sent"
        })
        mock_ultramsg_class.return_value = mock_ultramsg
        
        # Mock database
        mock_db = Mock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        
        # Test webhook payload
        webhook_payload = {
            "messages": [{
                "id": "test_msg_123",
                "from": "+1234567890",
                "type": "text",
                "timestamp": "1695023400",
                "text": {"body": "Hello"},
                "pushname": "Test Client"
            }]
        }
        
        # Create test client and make request
        client = TestClient(app)
        response = client.post("/webhook", json=webhook_payload)
        
        # Assertions
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        
        # Verify service interactions
        mock_adk.process_message.assert_called_once()
        mock_ultramsg.send_message.assert_called_once()
    
    @patch('app.services.adk_agent_service.ADKAgentService')
    @patch('app.services.ultramsg_service.UltramsgService')
    def test_webhook_invalid_payload(self, mock_ultramsg, mock_adk):
        """Test webhook with invalid payload"""
        from app.main import app
        client = TestClient(app)
        
        # Invalid payload (missing required fields)
        invalid_payload = {"invalid": "data"}
        
        response = client.post("/webhook", json=invalid_payload)
        
        # Should handle gracefully and return success
        # (Based on current webhook implementation)
        assert response.status_code == 200
    
    @patch('app.services.adk_agent_service.ADKAgentService')
    @patch('app.services.ultramsg_service.UltramsgService')
    def test_webhook_fromme_filtering(self, mock_ultramsg, mock_adk):
        """Test webhook filtering of fromMe messages"""
        from app.main import app
        client = TestClient(app)
        
        # Message with fromMe=True (should be filtered out)
        fromme_payload = {
            "messages": [{
                "id": "test_msg_123",
                "from": "+1234567890",
                "type": "text",
                "timestamp": "1695023400",
                "text": {"body": "Hello"},
                "pushname": "Test Client",
                "fromMe": True
            }]
        }
        
        response = client.post("/webhook", json=fromme_payload)
        
        assert response.status_code == 200
        # Verify ADK service was not called for fromMe message
        mock_adk.return_value.process_message.assert_not_called()


class TestWebhookErrorHandling:
    """Integration tests for webhook error scenarios"""
    
    @patch('app.services.adk_agent_service.ADKAgentService')
    @patch('app.services.ultramsg_service.UltramsgService')
    def test_adk_service_failure(self, mock_ultramsg_class, mock_adk_class):
        """Test handling of ADK service failure"""
        from app.main import app
        
        # Mock ADK service failure
        mock_adk = Mock()
        mock_adk.process_message = AsyncMock(side_effect=Exception("ADK Error"))
        mock_adk_class.return_value = mock_adk
        
        # Mock Ultramsg service (should still work)
        mock_ultramsg = Mock()
        mock_ultramsg.send_message = AsyncMock(return_value={
            "success": True,
            "message_id": "12345"
        })
        mock_ultramsg_class.return_value = mock_ultramsg
        
        client = TestClient(app)
        
        webhook_payload = {
            "messages": [{
                "id": "test_msg_123",
                "from": "+1234567890",
                "type": "text",
                "timestamp": "1695023400",
                "text": {"body": "Hello"},
                "pushname": "Test Client"
            }]
        }
        
        response = client.post("/webhook", json=webhook_payload)
        
        # Should handle ADK error gracefully
        assert response.status_code == 200
    
    @patch('app.services.adk_agent_service.ADKAgentService')
    @patch('app.services.ultramsg_service.UltramsgService')
    async def test_ultramsg_service_failure(self, mock_ultramsg_class, mock_adk_class):
        """Test handling of Ultramsg service failure"""
        from app.main import app
        
        # Mock ADK service (working)
        mock_adk = Mock()
        mock_adk.process_message = AsyncMock(return_value="Test response")
        mock_adk_class.return_value = mock_adk
        
        # Mock Ultramsg service failure
        mock_ultramsg = Mock()
        mock_ultramsg.send_message = AsyncMock(side_effect=Exception("Ultramsg Error"))
        mock_ultramsg_class.return_value = mock_ultramsg
        
        client = TestClient(app)
        
        webhook_payload = {
            "messages": [{
                "id": "test_msg_123",
                "from": "+1234567890",
                "type": "text",
                "timestamp": "1695023400",
                "text": {"body": "Hello"},
                "pushname": "Test Client"
            }]
        }
        
        response = client.post("/webhook", json=webhook_payload)
        
        # Should handle Ultramsg error gracefully
        assert response.status_code == 200


class TestCoordinatorWebhookIntegration:
    """Integration tests for coordinator-specific webhook functionality"""
    
    @patch('app.services.adk_agent_service.get_coordinator_phone')
    @patch('app.services.ultramsg_service.UltramsgService')
    def test_coordinator_approval_workflow(self, mock_ultramsg_class, mock_get_coord_phone):
        """Test coordinator approval message handling"""
        from app.main import app
        
        # Mock coordinator phone
        mock_get_coord_phone.return_value = "+97471669569"
        
        # Mock Ultramsg service
        mock_ultramsg = Mock()
        mock_ultramsg.send_message = AsyncMock(return_value={
            "success": True,
            "message_id": "coord_123"
        })
        mock_ultramsg_class.return_value = mock_ultramsg
        
        client = TestClient(app)
        
        # Coordinator approval message
        approval_payload = {
            "messages": [{
                "id": "coord_msg_123",
                "from": "+97471669569",  # Coordinator phone
                "type": "text",
                "timestamp": "1695023400",
                "text": {"body": "APPROVE 123"},
                "pushname": "Coordinator"
            }]
        }
        
        response = client.post("/webhook", json=approval_payload)
        
        assert response.status_code == 200
        # Verify coordinator workflow was triggered
        mock_get_coord_phone.assert_called()
    
    @patch('app.services.adk_agent_service.get_coordinator_phone')
    @patch('app.services.ultramsg_service.UltramsgService')
    def test_coordinator_rejection_workflow(self, mock_ultramsg_class, mock_get_coord_phone):
        """Test coordinator rejection message handling"""
        from app.main import app
        
        mock_get_coord_phone.return_value = "+97471669569"
        
        mock_ultramsg = Mock()
        mock_ultramsg.send_message = AsyncMock(return_value={
            "success": True,
            "message_id": "coord_456"
        })
        mock_ultramsg_class.return_value = mock_ultramsg
        
        client = TestClient(app)
        
        # Coordinator rejection message
        rejection_payload = {
            "messages": [{
                "id": "coord_msg_456",
                "from": "+97471669569",
                "type": "text",
                "timestamp": "1695023400",
                "text": {"body": "REJECT 123 Time not available"},
                "pushname": "Coordinator"
            }]
        }
        
        response = client.post("/webhook", json=rejection_payload)
        
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])