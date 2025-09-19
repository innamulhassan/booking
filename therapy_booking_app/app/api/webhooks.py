from fastapi import APIRouter, Depends, HTTPException, Form, Request
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.schemas import WhatsAppMessage
from app.services.ultramsg_service import ultramsg_service
from app.services.adk_agent_service import adk_service
from app.services.booking_service import booking_service

# New enhanced services
from app.services.coordinator_nlp_service import coordinator_nlp_service, ResponseType
from app.services.notification_service import notification_service, MessageType, NotificationRequest
from app.services.error_handler import error_handler, ErrorCategory, ErrorSeverity, ErrorContext
from app.services.config_service import config_service

import logging
import json
import asyncio
from datetime import datetime, date, timedelta

logger = logging.getLogger(__name__)

router = APIRouter()

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
            from app.models.models import Appointment, User, AppointmentStatus, UserRole
            
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
            
            return f"""Hello Dr. Smith! 👨‍⚕️

**Today's Overview:**
📅 Today's Appointments: {today_appointments}
⏳ Pending Confirmations: {pending_appointments}
👥 Active Clients: {active_clients}
💬 Recent Client Activity (24h): {recent_messages}

**System Status:** All systems operational ✅
**Time:** {datetime.now().strftime('%H:%M, %B %d, %Y')}

How can I assist you today?"""

        # Status and statistics queries
        elif any(word in message_lower for word in ['status', 'overview', 'summary', 'how are things', "how's it going"]):
            from app.models.models import Appointment, User, AppointmentStatus, UserRole, Conversation
            
            # Comprehensive statistics
            total_clients = db.query(User).filter(User.role == UserRole.CLIENT).count()
            active_clients = db.query(User).filter(
                User.role == UserRole.CLIENT,
                User.is_active == True
            ).count()
            
            # Appointments by status
            pending_count = db.query(Appointment).filter(Appointment.status == AppointmentStatus.PENDING).count()
            confirmed_count = db.query(Appointment).filter(Appointment.status == AppointmentStatus.CONFIRMED).count()
            completed_count = db.query(Appointment).filter(Appointment.status == AppointmentStatus.COMPLETED).count()
            
            # This week's activity
            week_start = datetime.now() - timedelta(days=7)
            week_appointments = db.query(Appointment).filter(
                Appointment.created_at >= week_start
            ).count()
            
            # Recent conversations
            active_conversations = db.query(Conversation).filter(
                Conversation.updated_at >= week_start
            ).count()
            
            return f"""📊 **System Status Report**

**Client Base:**
• Total Clients: {total_clients}
• Active Clients: {active_clients}
• New This Week: {week_appointments}

**Appointments:**
• ⏳ Pending: {pending_count}
• ✅ Confirmed: {confirmed_count}
• ✅ Completed: {completed_count}

**Recent Activity (7 days):**
• New Bookings: {week_appointments}
• Active Conversations: {active_conversations}

**System Health:** All services running smoothly ✅
**Last Update:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

Need details on any specific area?"""

        # Recent bookings and client activity
        elif any(word in message_lower for word in ['recent', 'new', 'bookings', 'appointments', 'clients']):
            from app.models.models import Appointment, User, AppointmentStatus, UserRole
            
            # Recent appointments (last 3 days)
            recent_date = datetime.now() - timedelta(days=3)
            recent_appointments = db.query(Appointment).filter(
                Appointment.created_at >= recent_date
            ).order_by(Appointment.created_at.desc()).limit(5).all()
            
            if recent_appointments:
                appointment_list = "**Recent Bookings (Last 3 Days):**\n\n"
                for apt in recent_appointments:
                    client_name = apt.client.name if apt.client else "Unknown"
                    date_str = apt.preferred_datetime.strftime('%m/%d')
                    time_str = apt.preferred_datetime.strftime('%H:%M')
                    status_emoji = "⏳" if apt.status == AppointmentStatus.PENDING else "✅"
                    
                    appointment_list += f"{status_emoji} **{client_name}**\n"
                    appointment_list += f"   📅 {date_str} at {time_str}\n"
                    appointment_list += f"   📋 {apt.service_type.value}\n"
                    appointment_list += f"   📱 {apt.client.phone_number}\n\n"
                
                # Add new clients
                new_clients = db.query(User).filter(
                    User.role == UserRole.CLIENT,
                    User.created_at >= recent_date
                ).count()
                
                appointment_list += f"👥 **New Clients:** {new_clients} joined recently"
                
                return appointment_list
            else:
                return "📅 **No recent bookings** in the last 3 days.\n\nAll current clients are managing their existing appointments. System ready for new bookings! ✅"

        # Today's schedule
        elif any(word in message_lower for word in ['today', 'schedule', 'agenda']):
            from app.models.models import Appointment, AppointmentStatus
            
            today = date.today()
            today_appointments = db.query(Appointment).filter(
                Appointment.preferred_datetime >= today,
                Appointment.preferred_datetime < today + timedelta(days=1),
                Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED])
            ).order_by(Appointment.preferred_datetime).all()
            
            if today_appointments:
                schedule = f"📅 **Today's Schedule - {today.strftime('%B %d, %Y')}**\n\n"
                for apt in today_appointments:
                    time_str = apt.preferred_datetime.strftime('%H:%M')
                    client_name = apt.client.name if apt.client else "Unknown"
                    status_emoji = "⏳" if apt.status == AppointmentStatus.PENDING else "✅"
                    service_icon = "🏥" if apt.service_type.value == "in_call" else "🏠"
                    
                    schedule += f"{status_emoji} **{time_str}** - {client_name}\n"
                    schedule += f"   {service_icon} {apt.service_type.value}\n"
                    schedule += f"   📱 {apt.client.phone_number}\n\n"
                
                return schedule
            else:
                return f"**Today's Schedule - {today.strftime('%B %d, %Y')}**\n\nNo appointments scheduled for today.\n\nEnjoy your free time! :)"

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

**System Management:**
• "Help" - Show this command list
• "Statistics" - Detailed system metrics

Just message me naturally - I understand context! :)

Example: "How's it going today?" or "Any recent client bookings?" """

        # Specific client lookup
        elif message_lower.startswith('client '):
            search_term = message_text[7:].strip()  # Remove "client " prefix
            from app.models.models import User, UserRole, Appointment
            
            # Search by phone or name
            if search_term.startswith('+') or search_term.isdigit():
                client = db.query(User).filter(
                    User.phone_number.like(f'%{search_term}%'),
                    User.role == UserRole.CLIENT
                ).first()
            else:
                client = db.query(User).filter(
                    User.name.ilike(f'%{search_term}%'),
                    User.role == UserRole.CLIENT
                ).first()
            
            if client:
                # Get client's appointments
                appointments = db.query(Appointment).filter(
                    Appointment.client_id == client.id
                ).order_by(Appointment.preferred_datetime.desc()).limit(3).all()
                
                client_info = f"👤 **Client: {client.name}**\n"
                client_info += f"📱 Phone: {client.phone_number}\n"
                client_info += f"📅 Joined: {client.created_at.strftime('%Y-%m-%d')}\n"
                client_info += f"🟢 Status: {'Active' if client.is_active else 'Inactive'}\n\n"
                
                if appointments:
                    client_info += "**Recent Appointments:**\n"
                    for apt in appointments:
                        date_str = apt.preferred_datetime.strftime('%m/%d/%Y')
                        status_emoji = {"PENDING": "⏳", "CONFIRMED": "✅", "COMPLETED": "✅", "CANCELLED": "❌"}.get(apt.status.value, "📅")
                        client_info += f"{status_emoji} {date_str} - {apt.service_type.value} ({apt.status.value})\n"
                else:
                    client_info += "📅 No appointment history found."
                
                return client_info
            else:
                return f"❌ No client found matching '{search_term}'\n\nTry searching by phone number or name."

        # Default response for general queries
        else:
            # Use the regular ADK agent for complex queries
            bot_response = await adk_service.process_message(
                message_text,
                coordinator_phone,
                session_id
            )
            
            # Add coordinator context note
            return f"{bot_response}\n\n---\n💡 **Coordinator Note:** Use commands like 'status', 'today', 'recent' for quick admin info!"

    except Exception as e:
        logger.error(f"Error processing coordinator message: {e}")
        return f"⚠️ **System Error:** Having trouble processing your request.\n\nError: {str(e)}\n\nPlease try again or contact system admin."

async def process_coordinator_response(db: Session, message_text: str, coordinator_phone: str) -> str:
    """
    Process coordinator approval/decline/modify responses for appointments
    Handles natural human responses like 'approve', 'yes', 'ok', 'decline', 'no' with typos
    Returns response message if handled, None if not an appointment response
    """
    try:
        # Create error context for better tracking
        context = ErrorContext(
            user_phone=coordinator_phone,
            endpoint="coordinator_response",
            request_data={"message": message_text},
            user_action="coordinator_approval"
        )
        
        # Find the most recent pending appointment
        from app.models.models import Appointment, AppointmentStatus
        recent_pending = db.query(Appointment).filter(
            Appointment.status == AppointmentStatus.PENDING
        ).order_by(Appointment.created_at.desc()).first()
        
        if not recent_pending:
            return None  # No pending appointments to process
        
        # Process message using NLP service
        processed_response = coordinator_nlp_service.process_response(message_text)
        
        # Check if response is actionable (not UNKNOWN)
        if processed_response.response_type == ResponseType.UNKNOWN:
            return None  # Not an appointment response
        
        # Handle based on response type using new NLP service
        if processed_response.response_type == ResponseType.APPROVAL:
            logger.info(f"✅ NLP Service detected APPROVAL (confidence: {processed_response.confidence:.0%})")
            # Continue to original approval logic below
        elif processed_response.response_type == ResponseType.DECLINE:
            logger.info(f"❌ NLP Service detected DECLINE (confidence: {processed_response.confidence:.0%})")
            # Continue to original decline logic below
        elif processed_response.response_type == ResponseType.MODIFICATION:
            logger.info(f"🔄 NLP Service detected MODIFICATION (confidence: {processed_response.confidence:.0%})")
            # Continue to original modification logic below
        else:
            return f"🤔 I understood your message (confidence: {processed_response.confidence:.0%}) but I'm not sure how to handle that action. Could you please be more specific?"
        
        # Prepare clean message for fallback pattern matching
        clean_message = message_text.lower().strip()
        
        # Smart pattern matching for approval (handle typos and variations)
        approval_patterns = [
            'approve', 'approved', 'aprove', 'aproved', 'approv', 'aproov',
            'yes', 'ye', 'yea', 'yeah', 'yep', 'yup', 'y',
            'ok', 'okay', 'oke', 'okey', 'k',
            'confirm', 'confirmed', 'confrim', 'conferm', 'good', 'fine', 'accept'
        ]
        
        # Smart pattern matching for decline
        decline_patterns = [
            'decline', 'declined', 'declin', 'declne', 'reject', 'rejected',
            'no', 'nope', 'nah', 'n', 'not', 'cancel', 'cancelled',
            'deny', 'denied', 'refuse', 'refused'
        ]
        
        # Check if message contains approval words
        is_approval = any(pattern in clean_message for pattern in approval_patterns)
        is_decline = any(pattern in clean_message for pattern in decline_patterns)
        
        # Handle explicit appointment ID (like "APPROVE 6" or "approve 6" or "yes 6")
        import re
        id_match = re.search(r'\b(\d+)\b', clean_message)
        if id_match:
            appointment_id = int(id_match.group(1))
            # Verify this appointment exists and is pending
            specific_appointment = db.query(Appointment).filter(
                Appointment.id == appointment_id,
                Appointment.status == AppointmentStatus.PENDING
            ).first()
            if specific_appointment:
                recent_pending = specific_appointment
        
        if is_approval and not is_decline:
            appointment_id = recent_pending.id
            
            # Get the appointment
            from app.models.models import Appointment, AppointmentStatus
            appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
            
            if not appointment:
                return f"❌ Appointment #{appointment_id} not found."
            
            if appointment.status != AppointmentStatus.PENDING:
                return f"❌ Appointment #{appointment_id} is not pending (Status: {appointment.status.value})"
            
            # Confirm the appointment
            try:
                confirmed_appointment = booking_service.confirm_appointment(db, appointment_id)
                
                # Send confirmation to client using Layla's personality
                client_phone = confirmed_appointment.client.phone_number
                client_name = confirmed_appointment.client.name
                
                # Get service details
                service_details = confirmed_appointment.service_description or "therapy session"
                appointment_date = confirmed_appointment.preferred_datetime.strftime('%Y-%m-%d')
                appointment_time = confirmed_appointment.preferred_datetime.strftime('%H:%M')
                
                client_confirmation = f"""All done, my love! ✨ 

Your appointment has been beautifully confirmed:

📅 Date: {appointment_date}
⏰ Time: {appointment_time}
🏥 Service: {service_details}
� Everything is perfectly arranged for you!

I've taken care of all the details. Just relax and I'll see you then, habibti! If you need anything else, you know I'm always here for you. 💕

Reference #{confirmed_appointment.id}"""

                # Send to client
                from app.services.ultramsg_service import ultramsg_service
                asyncio.create_task(ultramsg_service.send_message(f"+{client_phone}", client_confirmation))
                
                return f"✅ APPROVED: Appointment #{appointment_id} confirmed!\n\n📤 Layla sent beautiful confirmation to {client_name} ({client_phone})"
                
            except Exception as e:
                logger.error(f"Error confirming appointment: {e}")
                return f"❌ Error confirming appointment #{appointment_id}: {str(e)}"
        
        elif is_decline and not is_approval:
            # Handle decline/rejection
            appointment_id = recent_pending.id
            
            # Cancel the appointment
            try:
                cancelled_appointment = booking_service.cancel_appointment(db, appointment_id, "Declined by coordinator")
                
                # Send cancellation to client
                client_phone = cancelled_appointment.client.phone_number
                client_name = cancelled_appointment.client.name
                
                client_message = f"""Oh my love, I have some news about your appointment... 💔

I've been working so hard to arrange everything perfectly for you, but unfortunately we need to adjust your request due to some scheduling challenges on our end.

But don't worry habibti! Let me help you find an even better solution:

✨ I can check different times that work perfectly
💫 Look at alternative days that suit you better  
🌟 Maybe find you an even more amazing slot!

Just tell me what would work best for you, and I'll make it happen. You know I always take care of you, my dear! 💕

What do you think? 💖"""

                # Send to client
                from app.services.ultramsg_service import ultramsg_service
                asyncio.create_task(ultramsg_service.send_message(f"+{client_phone}", client_message))
                
                return f"❌ DECLINED: Appointment #{appointment_id} cancelled.\n\n📤 Alternative options sent to {client_name} ({client_phone})"
                
            except Exception as e:
                logger.error(f"Error cancelling appointment: {e}")
                return f"❌ Error declining appointment #{appointment_id}: {str(e)}"
        
        else:
            # Check if this looks like a modification request (contains keywords)
            modify_patterns = ['change', 'modify', 'different', 'reschedule', 'move', 'shift']
            is_modification = any(pattern in clean_message for pattern in modify_patterns)
            
            if is_modification:
                appointment_id = recent_pending.id
                modification_reason = message_text.strip()  # Use original message as reason
            
            # Get the appointment
            from app.models.models import Appointment, AppointmentStatus
            appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
            
            if not appointment:
                return f"❌ Appointment #{appointment_id} not found."
            
            if appointment.status != AppointmentStatus.PENDING:
                return f"❌ Appointment #{appointment_id} is not pending (Status: {appointment.status.value})"
            
            # Send modification request to client
            try:
                client_phone = appointment.client.phone_number
                client_name = appointment.client.name
                
                client_message = f"""📝 BOOKING MODIFICATION REQUEST

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

                # Send to client
                from app.services.ultramsg_service import ultramsg_service
                asyncio.create_task(ultramsg_service.send_message(f"+{client_phone}", client_message))
                
                return f"📝 MODIFICATION: Request sent to {client_name} ({client_phone})\n\nReason: {modification_reason}\n\nAppointment #{appointment_id} remains pending until client responds."
                
            except Exception as e:
                logger.error(f"Error processing modification: {e}")
                return f"❌ Error processing modification for appointment #{appointment_id}: {str(e)}"
        
        # Not an appointment response
        return None
        
    except Exception as e:
        logger.error(f"Error processing coordinator response: {e}")
        return f"❌ Error processing coordinator response: {str(e)}"

@router.post("/webhook")
async def general_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    General webhook endpoint for Ultramsg WhatsApp messages
    Handles both form data and JSON payload formats
    """
    try:
        # Get content type and log all request details
        content_type = request.headers.get("content-type", "")
        logger.info(f"Webhook request - Content-Type: {content_type}")
        logger.info(f"Request headers: {dict(request.headers)}")
        
        # Try to get raw body for debugging
        try:
            raw_body = await request.body()
            logger.info(f"Raw request body: {raw_body.decode('utf-8')}")
        except Exception as e:
            logger.warning(f"Could not read raw body: {e}")
        
        if "application/json" in content_type:
            # Handle JSON payload (Ultramsg format)
            payload = await request.json()
            logger.info(f"JSON payload: {payload}")
            
            # Handle WhatsApp Business API webhook format (entry structure)
            if 'entry' in payload and payload['entry'] and len(payload['entry']) > 0:
                entry = payload['entry'][0]
                if 'changes' in entry and entry['changes'] and len(entry['changes']) > 0:
                    change = entry['changes'][0]
                    if 'value' in change and 'messages' in change['value'] and change['value']['messages']:
                        # WhatsApp Business API format
                        message = change['value']['messages'][0]
                        from_phone = message.get('from', '')
                        message_id = message.get('id', '')
                        message_type = message.get('type', 'text')
                        
                        # Extract text from nested structure
                        if message_type == 'text' and 'text' in message:
                            message_text = message['text'].get('body', '')
                        else:
                            message_text = message.get('body', '')
                        
                        # Get contact info if available
                        pushname = ''
                        contacts = change['value'].get('contacts', [])
                        if contacts and 'profile' in contacts[0] and 'name' in contacts[0]['profile']:
                            pushname = contacts[0]['profile']['name']
                        
                        to_phone = change['value'].get('metadata', {}).get('phone_number_id', '')
                        from_me = False  # Incoming messages from clients
            
            # Handle direct messages format (fallback)
            elif 'messages' in payload and payload['messages']:
                # Direct message format
                message = payload['messages'][0]
                from_phone = message.get('from', '')
                message_id = message.get('id', '')
                message_type = message.get('type', 'text')
                
                # Extract text from nested structure
                if message_type == 'text' and 'text' in message:
                    message_text = message['text'].get('body', '')
                else:
                    message_text = message.get('body', '')
                
                # Get contact info if available
                pushname = ''
                if 'contacts' in payload and payload['contacts']:
                    contact = payload['contacts'][0]
                    if 'profile' in contact and 'name' in contact['profile']:
                        pushname = contact['profile']['name']
                
                to_phone = payload.get('metadata', {}).get('phone_number_id', '')
                from_me = False  # Incoming messages from clients
                
            # Ultramsg sends data in nested structure
            elif 'data' in payload:
                data = payload['data']
                from_phone = data.get('from', '')
                to_phone = data.get('to', '')
                message_text = data.get('body', '')
                message_id = data.get('id', '')
                message_type = data.get('type', 'text')
                from_me = data.get('fromMe', False)
                pushname = data.get('pushname', '')
                
                # Skip messages sent by us (outbound messages)
                if from_me:
                    logger.info(f"Skipping outbound message: {message_id}")
                    return {"status": "ok", "message": "Outbound message ignored"}
                
                # Map Ultramsg 'chat' type to 'text'
                if message_type == 'chat':
                    message_type = 'text'
            else:
                # Fallback for other JSON formats
                from_phone = payload.get('from', '')
                to_phone = payload.get('to', '')
                message_text = payload.get('body', '')
                message_id = payload.get('id', '')
                message_type = payload.get('type', 'text')
                from_me = payload.get('fromMe', False)
                pushname = payload.get('pushname', '')
                
                # Skip messages sent by us (outbound messages)
                if from_me:
                    logger.info(f"Skipping outbound message: {message_id}")
                    return {"status": "ok", "message": "Outbound message ignored"}
        else:
            # Handle form data - try multiple field names that Ultramsg might use
            form_data = await request.form()
            logger.info(f"Form data keys: {list(form_data.keys())}")
            logger.info(f"Form data: {dict(form_data)}")
            
            # Try different field names Ultramsg might use
            from_phone = (form_data.get('from') or form_data.get('From') or 
                         form_data.get('sender') or form_data.get('phone') or '')
            to_phone = (form_data.get('to') or form_data.get('To') or 
                       form_data.get('receiver') or form_data.get('instance') or '')
            message_text = (form_data.get('body') or form_data.get('Body') or 
                           form_data.get('message') or form_data.get('text') or '')
            message_id = (form_data.get('id') or form_data.get('messageId') or 
                         form_data.get('msgId') or '')
            message_type = (form_data.get('type') or form_data.get('messageType') or 'text')
            pushname = (form_data.get('pushname') or form_data.get('pushName') or 
                       form_data.get('name') or form_data.get('displayName') or '')
        
        # Clean phone numbers (handle Ultramsg format: "97471669569@c.us")
        sender_phone = from_phone.replace('whatsapp:', '').replace('+', '').split('@')[0]
        receiver_phone = to_phone.replace('whatsapp:', '').replace('+', '').split('@')[0]
        
        logger.info(f"Webhook received - From: {sender_phone}, To: {receiver_phone}, Message: {message_text}")
        logger.info(f"Message type debug: '{message_type}' (type: {type(message_type)}, len: {len(message_type) if isinstance(message_type, str) else 'N/A'})")
        
        # Skip non-text messages for now
        if message_type != 'text' or not message_text:
            logger.info(f"Skipping non-text message type: '{message_type}' != 'text' is {message_type != 'text'}")
            return {"status": "ok", "message": "Non-text message ignored"}
        
        # Determine if sender is coordinator or client
        # Use known phone numbers from environment config
        try:
            from config.settings import config
            coordinator_phone = config.COORDINATOR_PHONE_NUMBER.replace('+', '')  # Remove + for comparison
            agent_phone = config.AGENT_PHONE_NUMBER.replace('+', '')
        except Exception as e:
            logger.warning(f"Could not load config, using fallback numbers: {e}")
            coordinator_phone = "97471669569"  # Fallback coordinator number
            agent_phone = "97451334514"      # Fallback agent number
        
        # Route message based on sender
        if sender_phone == coordinator_phone:
            # Message from coordinator - handle immediately without delay
            user_type = "coordinator"
            user_name = "Coordinator"
            conversation_type = "therapist_admin"
            
            # Get or create coordinator user
            user = booking_service.get_or_create_user(
                db, sender_phone, user_type, name=user_name
            )
            
            # Get or create conversation
            conversation = booking_service.get_or_create_conversation(
                db, user.id, conversation_type
            )
            
            # Save incoming message
            booking_service.save_message(
                db, conversation.id, "coordinator", message_text, message_id
            )
            
            # Check if this is an approval/decline/modify response
            bot_response = await process_coordinator_response(db, message_text, sender_phone)
            
            # If not an appointment response, use regular therapist message processing
            if not bot_response:
                bot_response = await process_therapist_message(
                    db, message_text, sender_phone, conversation.session_id
                )
            
        else:
            # Message from client - each phone number is a separate client
            user_type = "client"
            user_name = f"Client {sender_phone[-4:]}"  # Use last 4 digits for friendly name
            conversation_type = "client_booking"
            
            # Get or create client user (each phone number = unique client)
            user = booking_service.get_or_create_user(
                db, sender_phone, user_type, name=user_name
            )
            
            # Get or create conversation (separate conversation per client)
            conversation = booking_service.get_or_create_conversation(
                db, user.id, conversation_type
            )
            
            # Save incoming message
            booking_service.save_message(
                db, conversation.id, "user", message_text, message_id
            )
            
            # Process with ADK Agent (standard client booking flow)
            bot_response = await adk_service.process_message(
                message_text,
                sender_phone,
                conversation.session_id,
                pushname
            )
        
        # Save bot response
        booking_service.save_message(
            db, conversation.id, "bot", bot_response
        )
        
        # Send response back via Ultramsg
        if bot_response and bot_response.strip():
            try:
                send_result = await ultramsg_service.send_message(
                    f"+{sender_phone}", 
                    bot_response
                )
                logger.info(f"Response sent to {sender_phone}: {send_result}")
            except Exception as e:
                logger.error(f"Failed to send response: {e}")
        
        return {"status": "ok", "message": "Message processed successfully"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return {"status": "error", "error": str(e)}

@router.post("/webhook/client")
async def client_webhook(
    request: Request,
    From: str = Form(...),
    To: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(...),
    AccountSid: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Handle incoming WhatsApp messages from clients
    """
    try:
        # Clean phone number (remove whatsapp: prefix)
        client_phone = From.replace('whatsapp:', '')
        message_text = Body
        
        logger.info(f"Received client message from {client_phone}: {message_text}")
        
        # Get or create user
        user = booking_service.get_or_create_user(
            db, client_phone, "client", name="Client"
        )
        
        # Get or create conversation
        conversation = booking_service.get_or_create_conversation(
            db, user.id, "client_bot"
        )
        
        # Save incoming message
        booking_service.save_message(
            db, conversation.id, "user", message_text, MessageSid
        )
        
        # Process message with ADK Agent Service
        bot_response = await adk_service.process_message(
            message_text, 
            client_phone,
            conversation.session_id
        )
        
        # Save bot response
        booking_service.save_message(
            db, conversation.id, "bot", bot_response
        )
        
        # Return TwiML response
        return ultramsg_service.create_webhook_response(bot_response)
        
    except Exception as e:
        logger.error(f"Error processing client webhook: {str(e)}")
        error_message = "Sorry, I'm having trouble processing your message right now. Please try again in a moment."
        return ultramsg_service.create_webhook_response(error_message)

@router.post("/webhook/coordinator")
async def therapist_webhook(
    request: Request,
    From: str = Form(...),
    To: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(...),
    AccountSid: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Handle incoming WhatsApp messages from coordinator
    """
    try:
        # Clean phone number (remove whatsapp: prefix)
        coordinator_phone = From.replace('whatsapp:', '')
        message_text = Body
        
        logger.info(f"Received coordinator message from {coordinator_phone}: {message_text}")
        
        # Get or create coordinator user
        coordinator = booking_service.get_or_create_user(
            db, coordinator_phone, "coordinator", name="Coordinator"
        )
        
        # Get or create conversation
        conversation = booking_service.get_or_create_conversation(
            db, coordinator.id, "therapist_bot"
        )
        
        # Save incoming message
        booking_service.save_message(
            db, conversation.id, "coordinator", message_text, MessageSid
        )
        
        # Process coordinator response
        bot_response = await adk_service.process_message(
            message_text,
            coordinator_phone,
            conversation.session_id
        )
        
        # Save bot response
        booking_service.save_message(
            db, conversation.id, "bot", bot_response
        )
        
        # Return TwiML response
        return ultramsg_service.create_webhook_response(bot_response)
        
    except Exception as e:
        logger.error(f"Error processing coordinator webhook: {str(e)}")
        error_message = "Sorry, I'm having trouble processing your message. Please try again."
        return ultramsg_service.create_webhook_response(error_message)

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "therapy_booking_app"}
