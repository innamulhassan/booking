"""
Centralized notification service for all WhatsApp messaging.
Migrated to new package structure with improved organization.
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
    APPOINTMENT_REMINDER = "appointment_reminder"
    WELCOME_MESSAGE = "welcome_message"


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


@dataclass
class DeliveryResult:
    """Result of message delivery attempt."""
    success: bool
    message_type: str
    recipient: str
    appointment_id: Optional[int] = None
    delivery_id: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class NotificationService:
    """Service for handling all WhatsApp notifications."""
    
    def __init__(self):
        self._setup_templates()
        self._message_queue = []
        self._delivery_history: List[DeliveryResult] = []
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
            ),
            
            MessageType.APPOINTMENT_REMINDER: MessageTemplate(
                type=MessageType.APPOINTMENT_REMINDER,
                priority=MessagePriority.NORMAL,
                template="""🔔 Appointment Reminder

Dear {client_name},

This is a friendly reminder about your upcoming appointment:

📅 Date: {appointment_date}
⏰ Time: {appointment_time}
🏥 Service: {service_name}
👨‍⚕️ Therapist: {therapist_name}

Please arrive 15 minutes early. If you need to reschedule, please let us know as soon as possible.

Reference #{appointment_id}

We look forward to seeing you!"""
            ),
            
            MessageType.WELCOME_MESSAGE: MessageTemplate(
                type=MessageType.WELCOME_MESSAGE,
                priority=MessagePriority.NORMAL,
                template="""Welcome to Wellness Therapy Center! 💖

Hello {client_name}, I'm your personal wellness assistant, and I'm absolutely delighted to help you today! ✨

I can help you with:
🌟 Booking therapy appointments
💫 Checking available times
🌈 Answering questions about our services
💕 Anything else you need, habibti!

Just tell me what you'd like to do, and I'll take perfect care of you! 💖

What can I help you with today, my dear?"""
            ),
            
            MessageType.ERROR_NOTIFICATION: MessageTemplate(
                type=MessageType.ERROR_NOTIFICATION,
                priority=MessagePriority.HIGH,
                template="""❌ System Error Notification

Error Details: {error_message}
Time: {error_time}
User: {user_phone}
Context: {error_context}

Please investigate and resolve."""
            )
        }
    
    async def send_notification(self, request: NotificationRequest) -> DeliveryResult:
        """
        Send a notification using the appropriate template.
        
        Args:
            request: NotificationRequest with recipient and template data
            
        Returns:
            DeliveryResult with delivery status and details
        """
        try:
            # Get template
            template = self.templates.get(request.message_type)
            if not template:
                raise ValueError(f"Unknown message type: {request.message_type}")
            
            # Generate message content
            message_content = self._generate_message(template, request.template_data)
            
            # Send message via WhatsApp service
            result = await self._send_via_whatsapp(
                request.recipient_phone, 
                message_content, 
                request.priority
            )
            
            # Create delivery result
            delivery_result = DeliveryResult(
                success=result.get('success', False),
                message_type=request.message_type.value,
                recipient=request.recipient_phone,
                appointment_id=request.appointment_id,
                delivery_id=result.get('delivery_id'),
                error=result.get('error')
            )
            
            # Track delivery
            self._delivery_history.append(delivery_result)
            if delivery_result.success:
                self._delivery_stats['sent'] += 1
                logger.info(f"Notification sent to {request.recipient_phone}: {request.message_type.value}")
            else:
                self._delivery_stats['failed'] += 1
                logger.error(f"Failed to send notification to {request.recipient_phone}: {delivery_result.error}")
            
            return delivery_result
            
        except Exception as e:
            self._delivery_stats['failed'] += 1
            logger.error(f"Error sending notification: {e}")
            
            delivery_result = DeliveryResult(
                success=False,
                error=str(e),
                message_type=request.message_type.value,
                recipient=request.recipient_phone,
                appointment_id=request.appointment_id
            )
            self._delivery_history.append(delivery_result)
            return delivery_result
    
    def _generate_message(self, template: MessageTemplate, data: Dict) -> str:
        """Generate message content from template and data."""
        try:
            # Handle optional fields with safe defaults
            template_data = {
                'extra_services': self._format_extra_services(data.get('extra_services')),
                'description': data.get('description', 'No additional notes'),
                'price': data.get('price', 'TBD'),
                'service_name': data.get('service_name', data.get('service_description', 'Therapy Service')),
                'therapist_name': data.get('therapist_name', 'Our Professional Team'),
                'client_name': data.get('client_name', 'Valued Client'),
                'error_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
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
    
    def _format_extra_services(self, extra_services: Optional[str]) -> str:
        """Format extra services for display."""
        if not extra_services:
            return ""
        return f"🌟 Extra Services: {extra_services}"
    
    async def _send_via_whatsapp(self, phone: str, message: str, priority: MessagePriority) -> Dict:
        """Send message via WhatsApp service."""
        try:
            # Import WhatsApp service
            from ..external.ultramsg_service import ultramsg_service
            
            # Clean and format phone number
            phone = self._clean_phone_number(phone)
            
            # Send message
            result = await ultramsg_service.send_message(phone, message)
            
            return {
                'success': True,
                'delivery_id': result.get('id'),
                'status': result.get('status')
            }
            
        except ImportError:
            # Fallback for development/testing
            logger.warning("WhatsApp service not available, simulating send")
            return {
                'success': True,
                'delivery_id': f"sim_{datetime.now().timestamp()}",
                'status': 'simulated'
            }
        except Exception as e:
            logger.error(f"WhatsApp send failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _clean_phone_number(self, phone: str) -> str:
        """Clean and format phone number."""
        if not phone:
            raise ValueError("Phone number is required")
        
        # Remove whitespace and common prefixes
        cleaned = phone.strip().replace('whatsapp:', '')
        
        # Ensure + prefix
        if not cleaned.startswith('+'):
            cleaned = f"+{cleaned}"
        
        return cleaned
    
    # =====================================================
    # CONVENIENCE METHODS FOR COMMON NOTIFICATIONS
    # =====================================================
    
    async def send_coordinator_approval_request(self, appointment_data: Dict) -> DeliveryResult:
        """Send approval request to coordinator."""
        request = NotificationRequest(
            recipient_phone=appointment_data['coordinator_phone'],
            message_type=MessageType.COORDINATOR_APPROVAL_REQUEST,
            template_data=appointment_data,
            priority=MessagePriority.HIGH,
            appointment_id=appointment_data.get('appointment_id')
        )
        return await self.send_notification(request)
    
    async def send_client_confirmation(self, appointment_data: Dict) -> DeliveryResult:
        """Send confirmation to client."""
        request = NotificationRequest(
            recipient_phone=appointment_data['client_phone'],
            message_type=MessageType.CLIENT_CONFIRMATION,
            template_data=appointment_data,
            priority=MessagePriority.HIGH,
            appointment_id=appointment_data.get('appointment_id')
        )
        return await self.send_notification(request)
    
    async def send_client_decline_notification(self, client_phone: str, appointment_id: Optional[int] = None) -> DeliveryResult:
        """Send decline notification to client."""
        request = NotificationRequest(
            recipient_phone=client_phone,
            message_type=MessageType.CLIENT_DECLINE_NOTIFICATION,
            template_data={},
            priority=MessagePriority.HIGH,
            appointment_id=appointment_id
        )
        return await self.send_notification(request)
    
    async def send_appointment_reminder(self, appointment_data: Dict) -> DeliveryResult:
        """Send appointment reminder to client."""
        request = NotificationRequest(
            recipient_phone=appointment_data['client_phone'],
            message_type=MessageType.APPOINTMENT_REMINDER,
            template_data=appointment_data,
            priority=MessagePriority.NORMAL,
            appointment_id=appointment_data.get('appointment_id')
        )
        return await self.send_notification(request)
    
    async def send_welcome_message(self, client_phone: str, client_name: str = None) -> DeliveryResult:
        """Send welcome message to new client."""
        request = NotificationRequest(
            recipient_phone=client_phone,
            message_type=MessageType.WELCOME_MESSAGE,
            template_data={'client_name': client_name or 'dear'},
            priority=MessagePriority.NORMAL
        )
        return await self.send_notification(request)
    
    async def send_coordinator_feedback(self, coordinator_phone: str, feedback_data: Dict) -> DeliveryResult:
        """Send feedback to coordinator about action results."""
        request = NotificationRequest(
            recipient_phone=coordinator_phone,
            message_type=MessageType.COORDINATOR_FEEDBACK,
            template_data=feedback_data,
            priority=MessagePriority.NORMAL
        )
        return await self.send_notification(request)
    
    async def send_error_notification(self, admin_phone: str, error_data: Dict) -> DeliveryResult:
        """Send error notification to administrator."""
        request = NotificationRequest(
            recipient_phone=admin_phone,
            message_type=MessageType.ERROR_NOTIFICATION,
            template_data=error_data,
            priority=MessagePriority.URGENT
        )
        return await self.send_notification(request)
    
    # =====================================================
    # ANALYTICS AND MONITORING
    # =====================================================
    
    def get_delivery_stats(self) -> Dict:
        """Get message delivery statistics."""
        return {
            **self._delivery_stats,
            'total_history': len(self._delivery_history),
            'success_rate': self._calculate_success_rate()
        }
    
    def _calculate_success_rate(self) -> float:
        """Calculate success rate from recent deliveries."""
        if not self._delivery_history:
            return 0.0
        
        recent_deliveries = self._delivery_history[-100:]  # Last 100 messages
        successful = sum(1 for d in recent_deliveries if d.success)
        return (successful / len(recent_deliveries)) * 100
    
    def get_delivery_history(self, limit: int = 50) -> List[Dict]:
        """Get recent delivery history."""
        recent = self._delivery_history[-limit:] if limit else self._delivery_history
        return [
            {
                'success': d.success,
                'message_type': d.message_type,
                'recipient': d.recipient,
                'appointment_id': d.appointment_id,
                'timestamp': d.timestamp.isoformat(),
                'error': d.error
            }
            for d in recent
        ]
    
    def reset_stats(self):
        """Reset delivery statistics."""
        self._delivery_stats = {'sent': 0, 'failed': 0, 'pending': 0}
        self._delivery_history.clear()
    
    async def batch_send_notifications(self, requests: List[NotificationRequest]) -> List[DeliveryResult]:
        """Send multiple notifications in batch."""
        results = []
        for request in requests:
            try:
                result = await self.send_notification(request)
                results.append(result)
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Batch send error for {request.recipient_phone}: {e}")
                results.append(DeliveryResult(
                    success=False,
                    message_type=request.message_type.value,
                    recipient=request.recipient_phone,
                    error=str(e)
                ))
        
        return results


# Global instance
notification_service = NotificationService()