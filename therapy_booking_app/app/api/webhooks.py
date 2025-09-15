from fastapi import APIRouter, Depends, HTTPException, Form, Request
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.schemas import WhatsAppMessage
from app.services.ultramsg_service import ultramsg_service
from app.services.adk_agent_service import adk_service
from app.services.booking_service import booking_service
import logging
import json
from datetime import datetime, date, timedelta

logger = logging.getLogger(__name__)

router = APIRouter()

async def process_therapist_message(db: Session, message_text: str, therapist_phone: str, session_id: str) -> str:
    """
    Process messages from therapist with admin-level responses
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
                return f"📅 **Today's Schedule - {today.strftime('%B %d, %Y')}**\n\n✨ No appointments scheduled for today.\n\nEnjoy your free time! 😊"

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

Just message me naturally - I understand context! 😊

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
                therapist_phone,
                session_id
            )
            
            # Add therapist context note
            return f"{bot_response}\n\n---\n💡 **Therapist Note:** Use commands like 'status', 'today', 'recent' for quick admin info!"

    except Exception as e:
        logger.error(f"Error processing therapist message: {e}")
        return f"⚠️ **System Error:** Having trouble processing your request.\n\nError: {str(e)}\n\nPlease try again or contact system admin."

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
            
            # Ultramsg sends data in nested structure
            if 'data' in payload:
                data = payload['data']
                from_phone = data.get('from', '')
                to_phone = data.get('to', '')
                message_text = data.get('body', '')
                message_id = data.get('id', '')
                message_type = data.get('type', 'text')
                from_me = data.get('fromMe', False)
                
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
        
        # Clean phone numbers (handle Ultramsg format: "97471669569@c.us")
        sender_phone = from_phone.replace('whatsapp:', '').replace('+', '').split('@')[0]
        receiver_phone = to_phone.replace('whatsapp:', '').replace('+', '').split('@')[0]
        
        logger.info(f"Webhook received - From: {sender_phone}, To: {receiver_phone}, Message: {message_text}")
        
        # Skip non-text messages for now
        if message_type != 'text' or not message_text:
            logger.info(f"Skipping non-text message type: {message_type}")
            return {"status": "ok", "message": "Non-text message ignored"}
        
        # Determine if sender is therapist or client
        # Use known phone numbers from environment
        therapist_phone = "97471669569"  # Therapist number without +
        agent_phone = "97451334514"      # Agent number without +
        
        # Route message based on sender
        if sender_phone == therapist_phone:
            # Message from therapist - handle immediately without delay
            user_type = "therapist"
            user_name = "Dr. Therapist"
            conversation_type = "therapist_admin"
            
            # Get or create therapist user
            user = booking_service.get_or_create_user(
                db, sender_phone, user_type, name=user_name
            )
            
            # Get or create conversation
            conversation = booking_service.get_or_create_conversation(
                db, user.id, conversation_type
            )
            
            # Save incoming message
            booking_service.save_message(
                db, conversation.id, "therapist", message_text, message_id
            )
            
            # Process therapist message with special handling
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
                conversation.session_id
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

@router.post("/webhook/therapist")
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
    Handle incoming WhatsApp messages from therapist
    """
    try:
        # Clean phone number (remove whatsapp: prefix)
        therapist_phone = From.replace('whatsapp:', '')
        message_text = Body
        
        logger.info(f"Received therapist message from {therapist_phone}: {message_text}")
        
        # Get or create therapist user
        therapist = booking_service.get_or_create_user(
            db, therapist_phone, "therapist", name="Therapist"
        )
        
        # Get or create conversation
        conversation = booking_service.get_or_create_conversation(
            db, therapist.id, "therapist_bot"
        )
        
        # Save incoming message
        booking_service.save_message(
            db, conversation.id, "therapist", message_text, MessageSid
        )
        
        # Process therapist response
        bot_response = await adk_service.process_message(
            message_text,
            therapist_phone,
            conversation.session_id
        )
        
        # Save bot response
        booking_service.save_message(
            db, conversation.id, "bot", bot_response
        )
        
        # Return TwiML response
        return ultramsg_service.create_webhook_response(bot_response)
        
    except Exception as e:
        logger.error(f"Error processing therapist webhook: {str(e)}")
        error_message = "Sorry, I'm having trouble processing your message. Please try again."
        return ultramsg_service.create_webhook_response(error_message)

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "therapy_booking_app"}
