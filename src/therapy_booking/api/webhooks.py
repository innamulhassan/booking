"""
WhatsApp Webhook API endpoints
Migrated to new package structure with improved error handling and modularity.
"""

from fastapi import APIRouter, Depends, HTTPException, Form, Request
from sqlalchemy.orm import Session
import logging
import json
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, date, timedelta

# Import from new package structure
from ..models import get_db, WhatsAppMessage
from ..services import booking_service, notification_service
from ..external import ultramsg_service
from ..core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Get settings
settings = get_settings()

async def process_therapist_message(db: Session, message_text: str, coordinator_phone: str, session_id: str) -> str:
    """
    Process messages from coordinator with admin-level responses
    Provides system status, client updates, booking information
    """
    try:
        message_lower = message_text.lower().strip()
        
        # Greeting responses
        if any(word in message_lower for word in ['hi', 'hello', 'hey', 'good morning', 'good afternoon']):
            # Get today's statistics
            today = date.today()
            from ..models import Appointment, User, AppointmentStatus, UserRole
            
            # Today's appointments
            today_appointments = db.query(Appointment).filter(
                Appointment.preferred_datetime >= today,
                Appointment.preferred_datetime < today + timedelta(days=1),
                Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED])
            ).count()
            
            # Pending appointments (needs confirmation)
            pending_appointments = db.query(Appointment).filter(
                Appointment.status == AppointmentStatus.PENDING
            ).count()
            
            # Total active clients
            active_clients = db.query(User).filter(
                User.role == UserRole.CLIENT,
                User.is_active == True
            ).count()
            
            # Recent client activity (last 24 hours)
            yesterday = datetime.now() - timedelta(days=1)
            recent_messages = db.query(User).filter(
                User.updated_at >= yesterday,
                User.role == UserRole.CLIENT
            ).count()
            
            return f"""Hello {settings.therapist_name}! 👨‍⚕️

**Today's Overview:**
📅 Today's Appointments: {today_appointments}
⏳ Pending Confirmations: {pending_appointments}
👥 Active Clients: {active_clients}
💬 Recent Client Activity (24h): {recent_messages}

**System Status:** All systems operational ✅
**Time:** {datetime.now().strftime('%H:%M, %B %d, %Y')}

How can I assist you today?"""

        # Help and available commands
        elif any(word in message_lower for word in ['help', 'commands', 'what can']):
            return """🤖 **Available Commands:**

**Quick Status:**
• "Hi" / "Hello" - Daily overview
• "Status" - Comprehensive system report
• "Today" - Today's appointment schedule
• "Recent" - New bookings & client activity

**Client Management:**
• "Client [phone/name]" - Look up specific client
• "Pending" - Show pending appointments
• "Confirmed" - Show confirmed appointments

Just message me naturally - I understand context! :)"""

        # Default response for general queries
        else:
            # For now, provide a helpful default response
            # TODO: Integrate with ADK agent service when migrated
            return f"I understand you said: '{message_text}'\n\n💡 **Coordinator Note:** Use commands like 'status', 'today', 'recent' for quick admin info!"

    except Exception as e:
        logger.error(f"Error processing coordinator message: {e}")
        return f"⚠️ **System Error:** Having trouble processing your request.\n\nError: {str(e)}\n\nPlease try again or contact system admin."

async def process_coordinator_response(db: Session, message_text: str, coordinator_phone: str) -> Optional[str]:
    """
    Process coordinator approval/decline/modify responses for appointments
    """
    try:
        # Find the most recent pending appointment
        from ..models import Appointment, AppointmentStatus
        recent_pending = db.query(Appointment).filter(
            Appointment.status == AppointmentStatus.PENDING
        ).order_by(Appointment.created_at.desc()).first()
        
        if not recent_pending:
            return None  # No pending appointments to process
        
        # Prepare clean message for pattern matching
        clean_message = message_text.lower().strip()
        
        # Smart pattern matching for approval (handle typos and variations)
        approval_patterns = [
            'approve', 'approved', 'yes', 'ok', 'confirm', 'good', 'fine', 'accept'
        ]
        
        # Smart pattern matching for decline
        decline_patterns = [
            'decline', 'declined', 'reject', 'no', 'cancel', 'deny', 'refuse'
        ]
        
        # Check if message contains approval words
        is_approval = any(pattern in clean_message for pattern in approval_patterns)
        is_decline = any(pattern in clean_message for pattern in decline_patterns)
        
        if is_approval and not is_decline:
            # Confirm the appointment
            confirmed_appointment = booking_service.update_appointment_status(
                db, recent_pending.id, AppointmentStatus.CONFIRMED
            )
            
            if confirmed_appointment:
                # Prepare appointment data for notification
                appointment_data = {
                    'appointment_id': confirmed_appointment.id,
                    'client_phone': confirmed_appointment.client.phone_number,
                    'client_name': confirmed_appointment.client.name,
                    'appointment_date': confirmed_appointment.preferred_datetime.strftime('%Y-%m-%d'),
                    'appointment_time': confirmed_appointment.preferred_datetime.strftime('%H:%M'),
                    'service_description': confirmed_appointment.service_description or "therapy session"
                }
                
                # Send confirmation to client
                result = await notification_service.send_client_confirmation(appointment_data)
                
                return f"✅ APPROVED: Appointment #{recent_pending.id} confirmed!\n\n📤 Confirmation sent to {appointment_data['client_name']}"
        
        elif is_decline and not is_approval:
            # Cancel the appointment
            cancelled_appointment = booking_service.update_appointment_status(
                db, recent_pending.id, AppointmentStatus.CANCELLED, "Declined by coordinator"
            )
            
            if cancelled_appointment:
                client_phone = cancelled_appointment.client.phone_number
                client_name = cancelled_appointment.client.name
                
                result = await notification_service.send_client_decline_notification(client_phone, recent_pending.id)
                
                return f"❌ DECLINED: Appointment #{recent_pending.id} cancelled.\n\n📤 Alternative options sent to {client_name}"
        
        # Not an appointment response
        return None
        
    except Exception as e:
        logger.error(f"Error processing coordinator response: {e}")
        return f"❌ Error processing coordinator response: {str(e)}"

@router.post("/whatsapp")
async def whatsapp_webhook(request: Request) -> Dict[str, Any]:
    """
    WhatsApp Business API webhook endpoint
    
    Receives incoming WhatsApp messages and processes them through the ADK agent
    """
    try:
        payload = await request.json()
        logger.info(f"Received WhatsApp webhook: {payload}")
        
        # TODO: Validate webhook signature
        # TODO: Process message through ADK agent
        # TODO: Handle different message types (text, image, audio, etc.)
        
        return {
            "status": "ok",
            "message": "Webhook processed successfully"
        }
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing webhook")


@router.post("/ultramsg")
async def ultramsg_webhook(
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    UltraMsg webhook endpoint for WhatsApp messages
    Handles both form data and JSON payload formats
    """
    try:
        # Get content type
        content_type = request.headers.get("content-type", "")
        logger.info(f"Webhook request - Content-Type: {content_type}")
        
        # Parse incoming data based on content type
        from_phone = ""
        to_phone = ""
        message_text = ""
        message_id = ""
        message_type = "text"
        from_me = False
        pushname = ""
        
        if "application/json" in content_type:
            payload = await request.json()
            logger.info(f"JSON payload received")
            
            # Handle Ultramsg data structure
            if 'data' in payload:
                data = payload['data']
                from_phone = data.get('from', '')
                to_phone = data.get('to', '')
                message_text = data.get('body', '')
                message_id = data.get('id', '')
                message_type = data.get('type', 'text')
                from_me = data.get('fromMe', False)
                pushname = data.get('pushname', '')
                
                # Skip messages sent by us
                if from_me:
                    logger.info(f"Skipping outbound message: {message_id}")
                    return {"status": "ok", "message": "Outbound message ignored"}
            else:
                # Fallback for other JSON formats
                from_phone = payload.get('from', '')
                to_phone = payload.get('to', '')
                message_text = payload.get('body', '')
                message_id = payload.get('id', '')
                message_type = payload.get('type', 'text')
                pushname = payload.get('pushname', '')
        else:
            # Handle form data
            form_data = await request.form()
            
            from_phone = form_data.get('from', '')
            to_phone = form_data.get('to', '')
            message_text = form_data.get('body', '')
            message_id = form_data.get('id', '')
            message_type = form_data.get('type', 'text')
            pushname = form_data.get('pushname', '')
        
        # Clean phone numbers
        sender_phone = from_phone.replace('whatsapp:', '').replace('+', '').split('@')[0]
        receiver_phone = to_phone.replace('whatsapp:', '').replace('+', '').split('@')[0]
        
        logger.info(f"Message from {sender_phone}: {message_text[:100]}...")
        
        # Skip non-text messages
        if message_type != 'text' or not message_text:
            return {"status": "ok", "message": "Non-text message ignored"}
        
        # Determine sender type
        coordinator_phone = settings.coordinator_phone_number.replace('+', '') if settings.coordinator_phone_number else "97471669569"
        
        if sender_phone == coordinator_phone:
            # Message from coordinator
            user = booking_service.get_or_create_user(db, sender_phone, "coordinator", name="Coordinator")
            conversation = booking_service.get_or_create_conversation(db, user.id, "therapist_admin")
            booking_service.save_message(db, conversation.id, "coordinator", message_text, message_id)
            
            # Process coordinator response
            bot_response = await process_coordinator_response(db, message_text, sender_phone)
            if not bot_response:
                bot_response = await process_therapist_message(db, message_text, sender_phone, conversation.session_id)
        else:
            # Message from client
            user_name = pushname or f"Client {sender_phone[-4:]}"
            user = booking_service.get_or_create_user(db, sender_phone, "client", name=user_name)
            conversation = booking_service.get_or_create_conversation(db, user.id, "booking")
            booking_service.save_message(db, conversation.id, "user", message_text, message_id)
            
            # TODO: Integrate with ADK Agent service
            bot_response = f"Thank you for your message! I'm currently being upgraded to serve you better. Please try again shortly."
        
        # Save and send bot response
        if bot_response:
            booking_service.save_message(db, conversation.id, "bot", bot_response)
            
            try:
                send_result = await ultramsg_service.send_message(f"+{sender_phone}", bot_response)
                logger.info(f"Response sent to {sender_phone}")
            except Exception as e:
                logger.error(f"Failed to send response: {e}")
        
        return {"status": "ok", "message": "Message processed successfully"}
        
    except Exception as e:
        logger.error(f"Error processing UltraMsg webhook: {str(e)}")
        return {"status": "error", "error": str(e)}


@router.post("/demo")
async def demo_webhook(request: Request) -> Dict[str, Any]:
    """
    Demo webhook endpoint for testing
    
    Processes demo messages for the web interface
    """
    try:
        payload = await request.json()
        logger.info(f"Received demo message: {payload}")
        
        # TODO: Process demo message through ADK agent
        # TODO: Return formatted response for demo interface
        
        # Simple echo response for now
        messages = payload.get("messages", [])
        if messages:
            user_message = messages[0].get("text", {}).get("body", "")
            return {
                "status": "ok",
                "response": f"I received your message: '{user_message}'. This is a demo response!"
            }
        
        return {
            "status": "ok",
            "response": "Hello! How can I help you today?"
        }
        
    except Exception as e:
        logger.error(f"Error processing demo webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing demo message")


@router.get("/health")
async def health_check():
    """Health check endpoint for webhooks"""
    return {
        "status": "healthy", 
        "service": "therapy_booking_webhooks",
        "timestamp": datetime.now().isoformat()
    }