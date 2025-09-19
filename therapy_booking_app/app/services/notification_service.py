"""
Centralized notification service for all WhatsApp messaging.
Handles message templates, delivery, and tracking.
"""
import asyncio
import logging
from typing import Dict, Optional, List
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of messages that can be sent."""
    COORDINATOR_APPROVAL_REQUEST = "coordinator_approval_request"
    CLIENT_CONFIRMATION = "client_confirmation"
    CLIENT_DECLINE_NOTIFICATION = "client_decline_notification"
    CLIENT_MODIFICATION_REQUEST = "client_modification_request"
    COORDINATOR_FEEDBACK = "coordinator_feedback"
    ERROR_NOTIFICATION = "error_notification"


class MessagePriority(Enum):
    """Message priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class MessageTemplate:
    """Template for generating messages."""
    type: MessageType
    template: str
    priority: MessagePriority = MessagePriority.NORMAL
    requires_approval: bool = False


@dataclass
class NotificationRequest:
    """Request to send a notification."""
    recipient_phone: str
    message_type: MessageType
    template_data: Dict
    priority: MessagePriority = MessagePriority.NORMAL
    appointment_id: Optional[int] = None


class NotificationService:
    """Service for handling all WhatsApp notifications."""
    
    def __init__(self):
        self._setup_templates()
        self._message_queue = []
        self._delivery_stats = {
            'sent': 0,
            'failed': 0,
            'pending': 0
        }
    
    def _setup_templates(self):
        """Initialize message templates."""
        self.templates = {
            MessageType.COORDINATOR_APPROVAL_REQUEST: MessageTemplate(
                type=MessageType.COORDINATOR_APPROVAL_REQUEST,
                priority=MessagePriority.HIGH,
                template="""🔔 PENDING APPROVAL REQUIRED #{appointment_id}

📱 Client: {client_name} ({client_phone})
📅 Date & Time: {appointment_date} at {appointment_time}
🏥 Service: {service_name}
👨‍⚕️ Therapist: {therapist_name}
💰 Price: {price} QAR
📝 Notes: {description}
{extra_services}

⚠️ CLIENT IS WAITING FOR CONFIRMATION
Action required immediately:

✅ "APPROVE {appointment_id}" - Confirm & notify client
❌ "DECLINE {appointment_id}" - Cancel & notify client
📝 "MODIFY {appointment_id} [reason]" - Request changes"""
            ),
            
            MessageType.CLIENT_CONFIRMATION: MessageTemplate(
                type=MessageType.CLIENT_CONFIRMATION,
                priority=MessagePriority.HIGH,
                template="""All done, my love! ✨ 

Your appointment has been beautifully confirmed:

📅 Date: {appointment_date}
⏰ Time: {appointment_time}
🏥 Service: {service_description}
💖 Everything is perfectly arranged for you!

I've taken care of all the details. Just relax and I'll see you then, habibti! If you need anything else, you know I'm always here for you. 💕

Reference #{appointment_id}"""
            ),
            
            MessageType.CLIENT_DECLINE_NOTIFICATION: MessageTemplate(
                type=MessageType.CLIENT_DECLINE_NOTIFICATION,
                priority=MessagePriority.HIGH,
                template="""Oh my love, I have some news about your appointment... 💔

I've been working so hard to arrange everything perfectly for you, but unfortunately we need to adjust your request due to some scheduling challenges on our end.

But don't worry habibti! Let me help you find an even better solution:

✨ I can check different times that work perfectly
💫 Look at alternative days that suit you better  
🌟 Maybe find you an even more amazing slot!

Just tell me what would work best for you, and I'll make it happen. You know I always take care of you, my dear! 💕

What do you think? 💖"""
            ),
            
            MessageType.CLIENT_MODIFICATION_REQUEST: MessageTemplate(
                type=MessageType.CLIENT_MODIFICATION_REQUEST,
                priority=MessagePriority.NORMAL,
                template="""📝 BOOKING MODIFICATION REQUEST

Dear {client_name},

Regarding your appointment #{appointment_id}:

Our coordinator has reviewed your booking and suggests the following modification:

📝 **Coordinator Note:** {modification_reason}

Would you like to:
• Accept this modification
• Suggest an alternative
• Reschedule for a different time

Please let me know your preference, and I'll help arrange the best solution for you.

Best regards,
Wellness Therapy Center"""
            ),
            
            MessageType.COORDINATOR_FEEDBACK: MessageTemplate(
                type=MessageType.COORDINATOR_FEEDBACK,
                priority=MessagePriority.NORMAL,
                template="""{action_result}

📤 {delivery_status}"""
            )
        }
    
    async def send_notification(self, request: NotificationRequest) -> Dict:
        """
        Send a notification using the appropriate template.
        
        Args:
            request: NotificationRequest with recipient and template data
            
        Returns:
            Dict with delivery status and details
        """
        try:
            # Get template
            template = self.templates.get(request.message_type)
            if not template:
                raise ValueError(f"Unknown message type: {request.message_type}")
            
            # Generate message content
            message_content = self._generate_message(template, request.template_data)
            
            # Send message via UltraMsg
            result = await self._send_via_ultramsg(
                request.recipient_phone, 
                message_content, 
                request.priority
            )
            
            # Track delivery
            if result.get('success'):
                self._delivery_stats['sent'] += 1
                logger.info(f"Notification sent to {request.recipient_phone}: {request.message_type.value}")
            else:
                self._delivery_stats['failed'] += 1
                logger.error(f"Failed to send notification to {request.recipient_phone}: {result.get('error')}")
            
            return {
                'success': result.get('success', False),
                'message_type': request.message_type.value,
                'recipient': request.recipient_phone,
                'appointment_id': request.appointment_id,
                'delivery_id': result.get('delivery_id'),
                'error': result.get('error')
            }
            
        except Exception as e:
            self._delivery_stats['failed'] += 1
            logger.error(f"Error sending notification: {e}")
            return {
                'success': False,
                'error': str(e),
                'message_type': request.message_type.value,
                'recipient': request.recipient_phone
            }
    
    def _generate_message(self, template: MessageTemplate, data: Dict) -> str:
        """Generate message content from template and data."""
        try:
            # Handle optional fields
            extra_services = ""
            if data.get('extra_services'):
                extra_services = f"🌟 Extra Services: {data['extra_services']}"
            
            # Prepare template data with safe defaults
            template_data = {
                'extra_services': extra_services,
                **data
            }
            
            # Format message
            message = template.template.format(**template_data)
            return message
            
        except KeyError as e:
            logger.error(f"Missing template data: {e}")
            raise ValueError(f"Missing required template data: {e}")
        except Exception as e:
            logger.error(f"Error generating message: {e}")
            raise
    
    async def _send_via_ultramsg(self, phone: str, message: str, priority: MessagePriority) -> Dict:
        """Send message via UltraMsg service."""
        try:
            from app.services.ultramsg_service import ultramsg_service
            
            # Ensure phone number has + prefix
            if not phone.startswith('+'):
                phone = f"+{phone}"
            
            # Send message
            result = await ultramsg_service.send_message(phone, message)
            
            return {
                'success': True,
                'delivery_id': result.get('id'),
                'status': result.get('status')
            }
            
        except Exception as e:
            logger.error(f"UltraMsg send failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def send_coordinator_approval_request(self, appointment_data: Dict) -> Dict:
        """Send approval request to coordinator."""
        request = NotificationRequest(
            recipient_phone=appointment_data['coordinator_phone'],
            message_type=MessageType.COORDINATOR_APPROVAL_REQUEST,
            template_data=appointment_data,
            priority=MessagePriority.HIGH,
            appointment_id=appointment_data.get('appointment_id')
        )
        return await self.send_notification(request)
    
    async def send_client_confirmation(self, appointment_data: Dict) -> Dict:
        """Send confirmation to client."""
        request = NotificationRequest(
            recipient_phone=appointment_data['client_phone'],
            message_type=MessageType.CLIENT_CONFIRMATION,
            template_data=appointment_data,
            priority=MessagePriority.HIGH,
            appointment_id=appointment_data.get('appointment_id')
        )
        return await self.send_notification(request)
    
    async def send_client_decline_notification(self, client_phone: str) -> Dict:
        """Send decline notification to client."""
        request = NotificationRequest(
            recipient_phone=client_phone,
            message_type=MessageType.CLIENT_DECLINE_NOTIFICATION,
            template_data={},
            priority=MessagePriority.HIGH
        )
        return await self.send_notification(request)
    
    async def send_coordinator_feedback(self, coordinator_phone: str, feedback_data: Dict) -> Dict:
        """Send feedback to coordinator about action results."""
        request = NotificationRequest(
            recipient_phone=coordinator_phone,
            message_type=MessageType.COORDINATOR_FEEDBACK,
            template_data=feedback_data,
            priority=MessagePriority.NORMAL
        )
        return await self.send_notification(request)
    
    def get_delivery_stats(self) -> Dict:
        """Get message delivery statistics."""
        return self._delivery_stats.copy()
    
    def reset_stats(self):
        """Reset delivery statistics."""
        self._delivery_stats = {'sent': 0, 'failed': 0, 'pending': 0}


# Global instance
notification_service = NotificationService()