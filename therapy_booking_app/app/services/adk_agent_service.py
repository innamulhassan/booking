"""
Google Agent Development Kit (ADK) service for therapy booking.

This service integrates Google's ADK with our WhatsApp Business API
to provide intelligent conversation handling for therapy appointments.
"""

import asyncio
import logging
import datetime
import sys
import os
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

# Add the parent directory to the path to find modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'other_scripts'))

# Import our models and services
from app.models.database import get_db, SessionLocal
from app.services.booking_service import booking_service
from app.models.models import UserRole, ServiceType, User, Appointment, AppointmentStatus
from config.settings import config
logger = logging.getLogger(__name__)


def get_therapist_phone():
    """Get therapist phone number from environment config"""
    try:
        import sys
        import os
        # Temporarily add other_scripts to path
        other_scripts_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'other_scripts')
        if other_scripts_path not in sys.path:
            sys.path.append(other_scripts_path)
        
        from environment_config import get_config
        env_config = get_config()
        return env_config.THERAPIST_PHONE_NUMBER
    except Exception as e:
        logger.error(f"Could not load therapist phone from environment config: {e}")
        return None


def check_availability(date: str, service_type: str = "in_call") -> Dict:
    """Check available appointment slots for a given date.
    
    Args:
        date (str): The date to check availability for (format: YYYY-MM-DD)
        service_type (str): Type of service - "in_call" (office visit) or "out_call" (home visit)
        
    Returns:
        dict: Status and available time slots or error message
    """
    try:
        # Validate date format
        datetime.datetime.strptime(date, '%Y-%m-%d')
        
        # Get database session
        db = SessionLocal()
        
        try:
            # Get available slots
            available_slots = booking_service.get_available_slots(db, date)
            
            if available_slots:
                return {
                    "status": "success",
                    "date": date,
                    "service_type": service_type,
                    "available_slots": available_slots,
                    "message": f"Found {len(available_slots)} available slots for {date}"
                }
            else:
                return {
                    "status": "no_availability",
                    "date": date,
                    "service_type": service_type,
                    "available_slots": [],
                    "message": f"No available slots found for {date}. Please try another date."
                }
        finally:
            db.close()
            
    except ValueError:
        return {
            "status": "error",
            "error_message": f"Invalid date format. Please use YYYY-MM-DD format (e.g., 2025-01-15)"
        }
    except Exception as e:
        logger.error(f"Error checking availability: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error checking availability: {str(e)}"
        }


def book_appointment(client_phone: str, client_name: str, date: str, time: str, 
                    service_type: str = "in_call", description: str = "") -> Dict:
    """Book a therapy appointment for a client.
    
    Args:
        client_phone (str): Client's phone number (international format)
        client_name (str): Client's full name
        date (str): Appointment date (format: YYYY-MM-DD)
        time (str): Appointment time (format: HH:MM)
        service_type (str): "in_call" for office visit or "out_call" for home visit
        description (str): Optional description of therapy needs
        
    Returns:
        dict: Status and appointment details or error message
    """
    try:
        # Validate inputs
        datetime.datetime.strptime(date, '%Y-%m-%d')
        datetime.datetime.strptime(time, '%H:%M')
        
        if not client_phone or not client_name:
            return {
                "status": "error",
                "error_message": "Client phone number and name are required"
            }
        
        # Get database session
        db = SessionLocal()
        
        try:
            # Get or create client user
            client = booking_service.get_or_create_user(
                db=db,
                phone_number=client_phone,
                role="client",
                name=client_name
            )
            
            # Prepare booking data
            datetime_str = f"{date} {time}:00"
            booking_data = {
                "datetime": datetime_str,
                "service_type": service_type,
                "description": description
            }
            
            # Create pending appointment
            appointment = booking_service.create_pending_appointment(
                db=db,
                client_id=client.id,
                booking_data=booking_data
            )
            
            return {
                "status": "success",
                "appointment_id": appointment.id,
                "client_name": client_name,
                "client_phone": client_phone,
                "date": date,
                "time": time,
                "service_type": service_type,
                "appointment_status": appointment.status.value,
                "message": f"Appointment booked successfully! Appointment ID: {appointment.id}. Status: Pending confirmation."
            }
        finally:
            db.close()
        
    except ValueError as e:
        return {
            "status": "error",
            "error_message": f"Invalid date or time format: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Error booking appointment: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error booking appointment: {str(e)}"
        }


def cancel_appointment(appointment_id: int, reason: str = "") -> Dict:
    """Cancel an existing appointment.
    
    Args:
        appointment_id (int): The ID of the appointment to cancel
        reason (str): Optional reason for cancellation
        
    Returns:
        dict: Status and cancellation details or error message
    """
    try:
        if appointment_id <= 0:
            return {
                "status": "error",
                "error_message": "Invalid appointment ID"
            }
        
        # Get database session
        db = SessionLocal()
        
        try:
            # Cancel the appointment
            appointment = booking_service.cancel_appointment(
                db=db,
                appointment_id=appointment_id,
                reason=reason
            )
            
            return {
                "status": "success",
                "appointment_id": appointment_id,
                "new_status": appointment.status.value,
                "reason": reason,
                "message": f"Appointment {appointment_id} has been cancelled successfully."
            }
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Error cancelling appointment: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error cancelling appointment: {str(e)}"
        }


def reschedule_appointment(appointment_id: int, new_date: str, new_time: str, 
                         notes: str = "") -> Dict:
    """Reschedule an existing appointment.
    
    Args:
        appointment_id (int): The ID of the appointment to reschedule
        new_date (str): New appointment date (format: YYYY-MM-DD)
        new_time (str): New appointment time (format: HH:MM)
        notes (str): Optional notes about the rescheduling
        
    Returns:
        dict: Status and new appointment details or error message
    """
    try:
        # Validate inputs
        datetime.datetime.strptime(new_date, '%Y-%m-%d')
        datetime.datetime.strptime(new_time, '%H:%M')
        
        if appointment_id <= 0:
            return {
                "status": "error", 
                "error_message": "Invalid appointment ID"
            }
        
        # Get database session
        db = SessionLocal()
        
        try:
            # Parse new datetime
            new_datetime_str = f"{new_date} {new_time}:00"
            new_datetime = datetime.datetime.strptime(new_datetime_str, '%Y-%m-%d %H:%M:%S')
            
            # Reschedule the appointment
            appointment = booking_service.reschedule_appointment(
                db=db,
                appointment_id=appointment_id,
                new_datetime=new_datetime,
                notes=notes
            )
            
            return {
                "status": "success",
                "appointment_id": appointment_id,
                "new_date": new_date,
                "new_time": new_time,
                "appointment_status": appointment.status.value,
                "notes": notes,
                "message": f"Appointment {appointment_id} has been rescheduled to {new_date} at {new_time}."
            }
        finally:
            db.close()
        
    except ValueError as e:
        return {
            "status": "error",
            "error_message": f"Invalid date or time format: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Error rescheduling appointment: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error rescheduling appointment: {str(e)}"
        }


def get_therapist_info() -> Dict:
    """Get information about available therapists and services.
    
    Returns:
        dict: Therapist information and available services
    """
    return {
        "status": "success",
        "clinic_name": config.CLINIC_NAME,
        "therapist_name": config.THERAPIST_NAME,
        "clinic_address": config.CLINIC_ADDRESS,
        "specializations": [
            "Cognitive Behavioral Therapy (CBT)",
            "Anxiety and Depression Treatment", 
            "Stress Management",
            "Relationship Counseling",
            "Trauma Therapy"
        ],
        "services": {
            "in_call": {
                "name": "Office Visit",
                "description": "Visit our clinic for your therapy session",
                "location": config.CLINIC_ADDRESS
            },
            "out_call": {
                "name": "Home Visit", 
                "description": "Therapist visits you at your location",
                "coverage_area": "City center and surrounding areas"
            }
        },
        "business_hours": {
            "monday_friday": "9:00 AM - 6:00 PM",
            "saturday": "9:00 AM - 2:00 PM", 
            "sunday": "Closed"
        },
        "emergency_contact": config.EMERGENCY_CONTACT,
        "crisis_center": config.CRISIS_CENTER
    }


def get_user_appointments(client_phone: str, status: Optional[str] = None) -> Dict:
    """Get appointments for a specific client.
    
    Args:
        client_phone (str): Client's phone number
        status (str): Optional status filter (pending, confirmed, cancelled, completed)
        
    Returns:
        dict: List of appointments or error message
    """
    try:
        if not client_phone:
            return {
                "status": "error",
                "error_message": "Phone number is required"
            }
        
        # Get database session
        db = SessionLocal()
        
        try:
            # Get user by phone number
            user = db.query(User).filter(User.phone_number == client_phone).first()
            
            if not user:
                return {
                    "status": "not_found",
                    "message": "No appointments found for this phone number."
                }
            
            # Get user's appointments
            appointments = booking_service.get_user_appointments(db, user.id, status)
            
            appointment_list = []
            for apt in appointments:
                appointment_list.append({
                    "appointment_id": apt.id,
                    "date": apt.preferred_datetime.strftime('%Y-%m-%d'),
                    "time": apt.preferred_datetime.strftime('%H:%M'),
                    "service_type": apt.service_type.value,
                    "status": apt.status.value,
                    "therapist_name": apt.therapist.name if apt.therapist else "TBD",
                    "description": apt.service_description or ""
                })
            
            return {
                "status": "success",
                "client_name": user.name,
                "client_phone": client_phone,
                "appointments": appointment_list,
                "total_appointments": len(appointment_list)
            }
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Error retrieving appointments: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error retrieving appointments: {str(e)}"
        }


def escalate_to_therapist(client_phone: str, client_message: str, reason: str, 
                         appointment_id: Optional[int] = None) -> Dict:
    """Escalate client inquiry to therapist for clarification or complex requests.
    
    Args:
        client_phone (str): Client's phone number
        client_message (str): Client's original message that needs therapist attention
        reason (str): Reason for escalation (e.g., "complex_request", "medical_clarification", "urgent_matter")
        appointment_id (int, optional): Related appointment ID if applicable
        
    Returns:
        dict: Escalation status and therapist notification details
    """
    try:
        # Get therapist phone number from environment config
        therapist_phone = get_therapist_phone()
        if not therapist_phone:
            return {
                "status": "error",
                "error_message": "Therapist configuration not available"
            }
        
        # Get database session
        db = SessionLocal()
        
        try:
            # Get client info
            client = db.query(User).filter(User.phone_number == client_phone).first()
            client_name = client.name if client else "Unknown Client"
            
            # Get appointment info if provided
            appointment_info = ""
            if appointment_id:
                appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
                if appointment:
                    appointment_info = f"\nRelated Appointment: #{appointment_id} on {appointment.preferred_datetime.strftime('%Y-%m-%d at %H:%M')}"
            
            # Create escalation record (you might want to add this to your database model)
            escalation_data = {
                "client_phone": client_phone,
                "client_name": client_name,
                "therapist_phone": therapist_phone,
                "reason": reason,
                "client_message": client_message,
                "appointment_id": appointment_id,
                "escalated_at": datetime.datetime.now().isoformat()
            }
            
            return {
                "status": "escalated",
                "therapist_phone": therapist_phone,
                "client_name": client_name,
                "reason": reason,
                "escalation_data": escalation_data,
                "message": f"Your inquiry has been forwarded to our therapist for review. Dr. Smith will respond within 2 hours during business hours.",
                "therapist_notification": {
                    "recipient": therapist_phone,
                    "message": f"🔔 CLIENT ESCALATION\n\nClient: {client_name} ({client_phone})\nReason: {reason}\n\nClient Message: '{client_message}'{appointment_info}\n\nPlease review and respond to the client directly.",
                    "priority": "high" if reason in ["urgent_matter", "crisis"] else "normal"
                }
            }
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error escalating to therapist: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error escalating inquiry: {str(e)}"
        }


def handle_therapist_query(therapist_phone: str, query_type: str, query_content: str) -> Dict:
    """Handle queries from the therapist about appointments, clients, or system status.
    
    Args:
        therapist_phone (str): Therapist's phone number (should match +97471669569)
        query_type (str): Type of query ("appointments", "client_info", "system_status", "schedule")
        query_content (str): Specific query content or client phone/appointment ID
        
    Returns:
        dict: Query results or appropriate response
    """
    try:
        # Verify this is the authorized therapist
        authorized_phone = get_therapist_phone()
        if not authorized_phone:
            return {
                "status": "error", 
                "error_message": "Therapist authentication not configured"
            }
        
        if therapist_phone != authorized_phone:
            return {
                "status": "unauthorized",
                "message": "Sorry, this function is only available to authorized therapists."
            }
        
        # Get database session
        db = SessionLocal()
        
        try:
            if query_type == "appointments":
                # Get today's and upcoming appointments
                today = datetime.datetime.now().date()
                upcoming_appointments = db.query(Appointment).filter(
                    Appointment.preferred_datetime >= today,
                    Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED])
                ).order_by(Appointment.preferred_datetime).all()
                
                appointment_list = []
                for apt in upcoming_appointments:
                    appointment_list.append({
                        "appointment_id": apt.id,
                        "client_name": apt.client.name,
                        "client_phone": apt.client.phone_number,
                        "date": apt.preferred_datetime.strftime('%Y-%m-%d'),
                        "time": apt.preferred_datetime.strftime('%H:%M'),
                        "service_type": apt.service_type.value,
                        "status": apt.status.value,
                        "description": apt.service_description or "No specific notes"
                    })
                
                return {
                    "status": "success",
                    "query_type": "appointments",
                    "appointments": appointment_list,
                    "total_appointments": len(appointment_list),
                    "message": f"Found {len(appointment_list)} upcoming appointments."
                }
                
            elif query_type == "client_info":
                # Look up client by phone number or name
                search_term = query_content.strip()
                
                if search_term.startswith('+'):
                    # Search by phone number
                    client = db.query(User).filter(User.phone_number == search_term).first()
                else:
                    # Search by name (partial match)
                    client = db.query(User).filter(
                        User.name.ilike(f'%{search_term}%'),
                        User.role == UserRole.CLIENT
                    ).first()
                
                if not client:
                    return {
                        "status": "not_found",
                        "message": f"No client found matching '{search_term}'"
                    }
                
                # Get client's recent appointments
                recent_appointments = db.query(Appointment).filter(
                    Appointment.client_id == client.id
                ).order_by(Appointment.preferred_datetime.desc()).limit(5).all()
                
                appointment_history = []
                for apt in recent_appointments:
                    appointment_history.append({
                        "appointment_id": apt.id,
                        "date": apt.preferred_datetime.strftime('%Y-%m-%d'),
                        "time": apt.preferred_datetime.strftime('%H:%M'),
                        "service_type": apt.service_type.value,
                        "status": apt.status.value
                    })
                
                return {
                    "status": "success",
                    "query_type": "client_info",
                    "client": {
                        "name": client.name,
                        "phone": client.phone_number,
                        "created_at": client.created_at.strftime('%Y-%m-%d'),
                        "is_active": client.is_active
                    },
                    "recent_appointments": appointment_history,
                    "total_appointments": len(appointment_history)
                }
                
            elif query_type == "system_status":
                # Get system statistics
                total_clients = db.query(User).filter(User.role == UserRole.CLIENT).count()
                pending_appointments = db.query(Appointment).filter(
                    Appointment.status == AppointmentStatus.PENDING
                ).count()
                today_appointments = db.query(Appointment).filter(
                    Appointment.preferred_datetime >= datetime.datetime.now().date(),
                    Appointment.preferred_datetime < datetime.datetime.now().date() + datetime.timedelta(days=1),
                    Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED])
                ).count()
                
                return {
                    "status": "success",
                    "query_type": "system_status",
                    "statistics": {
                        "total_clients": total_clients,
                        "pending_appointments": pending_appointments,
                        "today_appointments": today_appointments,
                        "system_time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    },
                    "message": f"System Status: {total_clients} clients, {pending_appointments} pending appointments, {today_appointments} appointments today."
                }
                
            else:
                return {
                    "status": "error",
                    "error_message": f"Unknown query type: {query_type}. Available types: appointments, client_info, system_status"
                }
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error handling therapist query: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error processing therapist query: {str(e)}"
        }


class ADKAgentService:
    """
    ADK Agent Service that provides intelligent conversation handling
    for therapy appointment booking through WhatsApp Business API.
    """
    
    def __init__(self):
        """Initialize the ADK Agent Service"""
        self.agent = None
        self.session_service = None
        self.runner = None
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize the ADK agent with therapy booking tools"""
        try:
            # Import here to avoid circular imports
            from google.adk.agents import Agent
            
            self.agent = Agent(
                name="therapy_booking_agent",
                model=config.GOOGLE_GENAI_MODEL,
                description=(
                    "Professional therapy booking agent that helps clients schedule, manage, and "
                    "get information about therapy appointments through WhatsApp Business API."
                ),
                instruction=f"""You are a professional and empathetic therapy booking assistant for {config.CLINIC_NAME}.

Your role is to:
1. Help clients book therapy appointments
2. Check availability and suggest alternative times
3. Provide information about therapists and services
4. Manage existing appointments (reschedule, cancel)
5. Maintain professional, caring, and supportive communication

## Guidelines:
- Always be professional, empathetic, and respectful
- Use proper mental health language and avoid stigma
- Protect client privacy and confidentiality
- Provide clear, helpful information about services
- Be supportive while maintaining professional boundaries

## Available Services:
- **Office Visits (in_call)**: Clients visit our clinic at {config.CLINIC_ADDRESS}
- **Home Visits (out_call)**: Therapist visits client's location within city center and surrounding areas

## When booking appointments:
1. Ask for client's full name and phone number (international format like +97471669569)
2. Check their preferred date and time using check_availability
3. Confirm service type (office or home visit)
4. Ask about specific therapy needs (optional)
5. Use the book_appointment tool to create the appointment
6. Provide appointment details and confirmation

## When checking availability:
- Use check_availability tool with the requested date (YYYY-MM-DD format)
- Suggest alternative dates if preferred time is unavailable
- Explain both service types clearly

## Emergency situations:
If someone mentions crisis, self-harm, or immediate danger:
- Provide emergency contact: {config.EMERGENCY_CONTACT}
- Suggest {config.CRISIS_CENTER}
- Encourage immediate professional help
- Do not attempt to provide crisis counseling via chat

## Business Hours:
- Monday-Friday: 9:00 AM - 6:00 PM
- Saturday: 9:00 AM - 2:00 PM
- Sunday: Closed

## Example responses:
- "I'd be happy to help you schedule an appointment with {config.THERAPIST_NAME} at {config.CLINIC_NAME}."
- "Let me check our availability for that date and get back to you with options."
- "Your appointment has been confirmed. We'll send you a reminder closer to your appointment date."

Always end interactions by asking if there's anything else you can help with regarding their appointment or our services.
""",
                tools=[
                    check_availability,
                    book_appointment,  
                    cancel_appointment,
                    reschedule_appointment,
                    get_therapist_info,
                    get_user_appointments
                ]
            )
            
            # Initialize persistent session service and runner
            from google.adk.runners import Runner
            from google.adk.sessions import InMemorySessionService
            
            self.session_service = InMemorySessionService()
            self.runner = Runner(
                agent=self.agent,
                app_name="therapy_booking",
                session_service=self.session_service
            )
            
            logger.info("ADK Agent and session service initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing ADK agent: {str(e)}")
            self.agent = None
            self.session_service = None
            self.runner = None
    
    async def process_message(self, message: str, phone_number: str, session_id: Optional[str] = None) -> str:
        """
        Process incoming message with ADK agent
        
        Args:
            message: User's message text
            phone_number: User's phone number
            session_id: Optional session ID for conversation context
            
        Returns:
            Agent's response text
        """
        try:
            if not self.agent or not self.runner:
                logger.warning("ADK agent or runner not initialized, reinitializing...")
                self._initialize_agent()
                if not self.agent or not self.runner:
                    return "I'm sorry, the booking system is temporarily unavailable. Please try again later."
            
            # Import ADK components
            from google.genai import types
            
            # Use phone number as user_id and create consistent session_id
            user_id = phone_number
            if not session_id:
                session_id = f"session_{phone_number.replace('+', '').replace('-', '')}"
            
            logger.info(f"Processing message for user_id: {user_id}, session_id: {session_id}")
            
            # Create message content
            content = types.Content(
                role='user',
                parts=[types.Part(text=message)]
            )
            
            # Process with agent using persistent runner
            events = self.runner.run(
                user_id=user_id,
                session_id=session_id,
                new_message=content
            )
            
            # Extract final response
            response_text = ""
            for event in events:
                if event.is_final_response() and event.content:
                    response_text = event.content.parts[0].text.strip()
                    break
            
            if not response_text:
                response_text = "I'm here to help with your therapy appointments. How can I assist you today?"
            
            logger.info(f"ADK agent response generated successfully for session {session_id}")
            return response_text
            
        except ValueError as ve:
            logger.warning(f"Session error: {str(ve)}. Creating new session for {phone_number}")
            try:
                # If session not found, try to reinitialize and create new session
                self._initialize_agent()
                if not self.agent or not self.runner:
                    return "I'm here to help with your therapy appointments. How can I assist you today?"
                
                # Try again with fresh session
                from google.genai import types
                user_id = phone_number
                session_id = f"session_{phone_number.replace('+', '').replace('-', '')}_{int(datetime.datetime.now().timestamp())}"
                
                content = types.Content(
                    role='user',
                    parts=[types.Part(text=message)]
                )
                
                events = self.runner.run(
                    user_id=user_id,
                    session_id=session_id,
                    new_message=content
                )
                
                response_text = ""
                for event in events:
                    if event.is_final_response() and event.content:
                        response_text = event.content.parts[0].text.strip()
                        break
                
                if not response_text:
                    response_text = "I'm here to help with your therapy appointments. How can I assist you today?"
                
                return response_text
                
            except Exception as retry_error:
                logger.error(f"Retry failed: {str(retry_error)}")
                return "I'm here to help with your therapy appointments. How can I assist you today?"
            
        except Exception as e:
            logger.error(f"Error processing message with ADK agent: {str(e)}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again or contact our office directly."


def process_therapist_recommendation(therapist_phone: str, recommendation_text: str, client_phone: str = None) -> Dict:
    """Process therapist recommendation and respond to client based on guidance.
    
    Args:
        therapist_phone (str): Therapist's phone number (should match +97471669569)
        recommendation_text (str): Therapist's recommendation/guidance text
        client_phone (str, optional): Client phone if responding to specific escalation
        
    Returns:
        dict: Processed recommendation and client response details
    """
    try:
        # Get environment config for therapist phone verification
        authorized_phone = get_therapist_phone()
        if not authorized_phone:
            return {
                "status": "error",
                "error_message": "Therapist authentication not configured"
            }
        
        # Verify this is the authorized therapist
        if therapist_phone != authorized_phone:
            return {
                "status": "unauthorized",
                "message": "Sorry, this function is only available to authorized therapists."
            }
        
        # Extract recommendation from therapist message
        recommendation = ""
        if "RECOMMENDATION:" in recommendation_text:
            recommendation = recommendation_text.split("RECOMMENDATION:", 1)[1].strip()
        else:
            recommendation = recommendation_text.strip()
        
        # Get database session
        db = SessionLocal()
        
        try:
            # If client phone provided, format personalized response
            if client_phone:
                client = db.query(User).filter(User.phone_number == client_phone).first()
                client_name = client.name if client else "valued client"
                
                # Create professional client response based on therapist recommendation
                client_response = f"""Hello {client_name},

Thank you for your patience. Dr. Smith has reviewed your inquiry and provided the following guidance:

{recommendation}

If you have any follow-up questions or would like to schedule an appointment based on this recommendation, please let me know. I'm here to help you with your therapeutic care needs.

Best regards,
Wellness Therapy Center"""
                
                return {
                    "status": "recommendation_processed",
                    "therapist_phone": therapist_phone,
                    "client_phone": client_phone,
                    "client_name": client_name,
                    "recommendation": recommendation,
                    "client_response": client_response,
                    "message": "Recommendation processed and client response prepared.",
                    "client_notification": {
                        "recipient": client_phone,
                        "message": client_response,
                        "priority": "normal"
                    }
                }
            else:
                # General recommendation processing without specific client
                return {
                    "status": "recommendation_received",
                    "therapist_phone": therapist_phone,
                    "recommendation": recommendation,
                    "message": "Recommendation received and logged. Please specify client phone to send response."
                }
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error processing therapist recommendation: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error processing therapist recommendation: {str(e)}"
        }


def handle_therapist_confirmation(therapist_phone: str, confirmation_message: str, client_phone: str = None, prepared_response: str = None) -> Dict:
    """Handle therapist's final confirmation before sending response to client.
    
    Args:
        therapist_phone (str): Therapist's phone number 
        confirmation_message (str): Therapist's confirmation response (APPROVE/REVISE/DECLINE)
        client_phone (str, optional): Client phone for the pending response
        prepared_response (str, optional): The prepared client response awaiting confirmation
        
    Returns:
        dict: Confirmation processing results and next actions
    """
    try:
        # Get environment config for therapist phone verification
        authorized_phone = get_therapist_phone()
        if not authorized_phone:
            return {
                "status": "error",
                "error_message": "Therapist authentication not configured"
            }
        
        # Verify this is the authorized therapist
        if therapist_phone != authorized_phone:
            return {
                "status": "unauthorized",
                "message": "Sorry, this function is only available to authorized therapists."
            }
        
        confirmation_text = confirmation_message.upper().strip()
        
        # Get database session for client info
        db = SessionLocal()
        
        try:
            if confirmation_text == "APPROVE":
                # Therapist approved - send response to client
                if client_phone and prepared_response:
                    client = db.query(User).filter(User.phone_number == client_phone).first()
                    client_name = client.name if client else "valued client"
                    
                    return {
                        "status": "approved_for_sending",
                        "therapist_phone": therapist_phone,
                        "client_phone": client_phone,
                        "client_name": client_name,
                        "approved_response": prepared_response,
                        "message": f"✅ Response approved by therapist. Sending to {client_name}.",
                        "client_notification": {
                            "recipient": client_phone,
                            "message": prepared_response,
                            "priority": "normal"
                        },
                        "therapist_confirmation_reply": {
                            "recipient": therapist_phone,
                            "message": f"✅ CONFIRMED: Response sent to {client_name} ({client_phone})\n\n📤 Message delivered successfully.",
                            "priority": "normal"
                        }
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Cannot approve - missing client phone or prepared response."
                    }
                    
            elif confirmation_text.startswith("REVISE:"):
                # Therapist wants to revise the response
                revision_request = confirmation_text.replace("REVISE:", "").strip()
                
                if client_phone:
                    client = db.query(User).filter(User.phone_number == client_phone).first()
                    client_name = client.name if client else "valued client"
                    
                    # Create revised response based on therapist's input
                    revised_response = f"""Hello {client_name},

Thank you for your patience. Dr. Smith has reviewed your inquiry and provided the following guidance:

{revision_request}

If you have any follow-up questions or would like to schedule an appointment based on this recommendation, please let me know. I'm here to help you with your therapeutic care needs.

Best regards,
Wellness Therapy Center"""
                    
                    return {
                        "status": "revised_response_ready",
                        "therapist_phone": therapist_phone,
                        "client_phone": client_phone,
                        "client_name": client_name,
                        "revised_response": revised_response,
                        "revision_request": revision_request,
                        "message": f"📝 Response revised by therapist. Sending updated version to {client_name}.",
                        "client_notification": {
                            "recipient": client_phone,
                            "message": revised_response,
                            "priority": "normal"
                        },
                        "therapist_confirmation_reply": {
                            "recipient": therapist_phone,
                            "message": f"✅ REVISED: Updated response sent to {client_name} ({client_phone})\n\n📤 Revised message delivered successfully.",
                            "priority": "normal"
                        }
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Cannot revise - missing client phone information."
                    }
                    
            elif confirmation_text == "DECLINE":
                # Therapist declined to send response
                if client_phone:
                    client = db.query(User).filter(User.phone_number == client_phone).first()
                    client_name = client.name if client else "valued client"
                    
                    # Send alternative message to client
                    decline_message = f"""Hello {client_name},

Thank you for your inquiry. Dr. Smith has reviewed your request and would prefer to discuss this matter with you directly during a consultation.

Please let me know if you'd like to schedule an appointment so Dr. Smith can provide you with personalized guidance regarding your concerns.

Best regards,
Wellness Therapy Center"""
                    
                    return {
                        "status": "response_declined",
                        "therapist_phone": therapist_phone,
                        "client_phone": client_phone,
                        "client_name": client_name,
                        "decline_message": decline_message,
                        "message": f"❌ Therapist declined response. Suggesting direct consultation to {client_name}.",
                        "client_notification": {
                            "recipient": client_phone,
                            "message": decline_message,
                            "priority": "normal"
                        },
                        "therapist_confirmation_reply": {
                            "recipient": therapist_phone,
                            "message": f"❌ DECLINED: Alternative consultation message sent to {client_name} ({client_phone})",
                            "priority": "normal"
                        }
                    }
                else:
                    return {
                        "status": "declined_no_client",
                        "message": "Response declined by therapist. No client response needed."
                    }
                    
            else:
                # Unrecognized confirmation format
                help_message = """❓ CONFIRMATION FORMAT:

Please respond with one of:
✅ "APPROVE" - Send the prepared response as-is
📝 "REVISE: [your updated guidance]" - Send modified response  
❌ "DECLINE" - Don't send response, suggest consultation instead

Example: "REVISE: I recommend starting with weekly CBT sessions focusing on anxiety management techniques."""
                
                return {
                    "status": "invalid_confirmation_format",
                    "message": "Invalid confirmation format. Please use APPROVE, REVISE, or DECLINE.",
                    "therapist_help": {
                        "recipient": therapist_phone,
                        "message": help_message,
                        "priority": "normal"
                    }
                }
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error processing therapist confirmation: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error processing therapist confirmation: {str(e)}"
        }


# Create global service instance
adk_service = ADKAgentService()
