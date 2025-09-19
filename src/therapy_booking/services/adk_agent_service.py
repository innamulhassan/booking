"""
Google Agent Development Kit (ADK) service for therapy booking.

Migrated to new package structure with enhanced configuration management.
This service integrates Google's ADK with WhatsApp Business API for intelligent conversation handling.
"""

import asyncio
import logging
import datetime
import sys
import os
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

# Import from new package structure
from ..models import get_db, SessionLocal, User, Appointment, AppointmentStatus, UserRole, Therapist, ServiceType
from ..services import booking_service
from ..utils import parse_datetime_from_string, extract_datetime_from_message
from ..core import get_settings

# Get settings
settings = get_settings()
logger = logging.getLogger(__name__)

def get_coordinator_phone():
    """Get coordinator phone number from settings"""
    return settings.coordinator_phone_number

def check_availability(date: str, service_type: str = "in_call") -> Dict:
    """Check available appointment slots for a given date.
    
    Args:
        date (str): The date to check availability for (supports natural language like 'today', 'tomorrow')
        service_type (str): Type of service - "in_call" (office visit) or "out_call" (home visit)
        
    Returns:
        dict: Status and available time slots or error message
    """
    try:
        # Parse natural language date
        parsed_datetime = parse_datetime_from_string(date)
        if not parsed_datetime:
            return {
                "status": "error",
                "error_message": f"I couldn't understand the date '{date}'. You can say 'today', 'tomorrow', or use YYYY-MM-DD format (e.g., 2025-01-15)"
            }
        
        parsed_date = parsed_datetime.date().isoformat()
        
        # Get database session
        db = SessionLocal()
        
        try:
            # Get available slots
            available_slots = booking_service.get_available_slots(db, parsed_date)
            
            if available_slots:
                return {
                    "status": "success",
                    "date": parsed_date,
                    "service_type": service_type,
                    "available_slots": available_slots,
                    "message": f"Found {len(available_slots)} available slots for {parsed_date}"
                }
            else:
                return {
                    "status": "no_availability",
                    "date": parsed_date,
                    "service_type": service_type,
                    "available_slots": [],
                    "message": f"No available slots found for {parsed_date}. Please try another date."
                }
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error checking availability: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error checking availability: {str(e)}"
        }

def book_appointment(date: str, time: str, service_name: str, therapist_name: str = "", 
                    extra_services: str = "", description: str = "") -> Dict:
    """Submit a therapy appointment request for coordinator approval.
    
    IMPORTANT: This creates a PENDING appointment that requires coordinator approval.
    
    Args:
        date (str): Appointment date (supports natural language)
        time (str): Appointment time (format: HH:MM)
        service_name (str): Main service name (e.g., "1 Hour In-Call Session")
        therapist_name (str): Preferred therapist name (optional)
        extra_services (str): Comma-separated extra services (optional)
        description (str): Optional description of therapy needs
        
    Returns:
        dict: Status and PENDING appointment details (requires coordinator approval)
    """
    try:
        # Parse date
        parsed_datetime = parse_datetime_from_string(date)
        if not parsed_datetime:
            return {
                "status": "error",
                "error_message": f"I couldn't understand the date '{date}'. Please use a clear date format."
            }
        
        parsed_date = parsed_datetime.date().isoformat()
        
        # Parse time
        try:
            parsed_time = datetime.datetime.strptime(time, '%H:%M')
        except ValueError:
            try:
                parsed_time = datetime.datetime.strptime(time, '%I:%M %p')
            except ValueError:
                return {
                    "status": "error", 
                    "error_message": f"Invalid time format: {time}. Use HH:MM or HH:MM AM/PM format"
                }
        
        # Get client info from current context
        client_context = getattr(book_appointment, '_current_client_context', None)
        if not client_context:
            return {
                "status": "error",
                "error_message": "Client context not available. Please restart the conversation."
            }
            
        client_phone = client_context['phone_number']
        client_name = client_context['pushname']
        
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
            
            # Find therapist if specified
            therapist = None
            if therapist_name:
                therapist = db.query(Therapist).filter(
                    Therapist.name.ilike(f"%{therapist_name}%"),
                    Therapist.is_active == True
                ).first()
                
                if not therapist:
                    return {
                        "status": "error", 
                        "error_message": f"Therapist '{therapist_name}' not found."
                    }
            else:
                # Auto-assign first available therapist
                therapist = db.query(Therapist).filter(
                    Therapist.is_active == True
                ).first()
            
            if not therapist:
                return {
                    "status": "error",
                    "error_message": "No therapist available at this time"
                }
            
            # Prepare booking data
            datetime_str = f"{parsed_date} {time}:00"
            service_type = "out_call" if "out" in service_name.lower() else "in_call"
            
            booking_data = {
                "datetime": datetime_str,
                "service_type": service_type,
                "therapist_id": therapist.id,
                "service_description": f"{service_name}. {description}. Extra services: {extra_services}" if extra_services else f"{service_name}. {description}"
            }
            
            # Create appointment
            appointment = booking_service.create_appointment(
                db=db,
                client_id=client.id,
                booking_data=booking_data
            )
            
            # Notify coordinator (background task)
            try:
                from ..external import ultramsg_service
                import threading
                
                coordinator_message = f"""🔔 PENDING APPROVAL REQUIRED #{appointment.id}

📱 Client: {client_name} ({client_phone})
📅 Date & Time: {parsed_date} at {time}
🏥 Service: {service_name}
👨‍⚕️ Therapist: {therapist.name}
📝 Notes: {description}
{f'🌟 Extra Services: {extra_services}' if extra_services else ''}

⚠️ CLIENT IS WAITING FOR CONFIRMATION
Action required immediately:

✅ "APPROVE {appointment.id}" - Confirm & notify client
❌ "DECLINE {appointment.id}" - Cancel & notify client
📝 "MODIFY {appointment.id} [reason]" - Request changes"""

                coordinator_phone = get_coordinator_phone()
                if coordinator_phone:
                    def send_notification():
                        try:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            try:
                                result = loop.run_until_complete(
                                    ultramsg_service.send_message(coordinator_phone, coordinator_message)
                                )
                                logger.info(f"Sent coordinator notification for appointment {appointment.id}")
                            finally:
                                loop.close()
                        except Exception as e:
                            logger.error(f"Error in coordinator notification: {e}")
                    
                    thread = threading.Thread(target=send_notification)
                    thread.daemon = True
                    thread.start()
                    
            except Exception as e:
                logger.error(f"Error sending coordinator notification: {e}")
            
            price_qar = 200  # Default price
            
            return {
                "status": "pending_approval",
                "appointment_id": appointment.id,
                "client_name": client_name,
                "client_phone": client_phone,
                "date": parsed_date,
                "time": time,
                "service_name": service_name,
                "therapist_name": therapist.name,
                "service_price": f"{price_qar} QAR",
                "extra_services": extra_services,
                "appointment_status": appointment.status.value,
                "message": f"Perfect! I've got your {service_name} request with {therapist.name} for {parsed_date} at {time}. Let me check with the team to confirm and I'll get back to you shortly! 💕"
            }
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Error booking appointment: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error booking appointment: {str(e)}"
        }

def cancel_appointment(appointment_id: int, reason: str = "") -> Dict:
    """Cancel an existing appointment."""
    try:
        if appointment_id <= 0:
            return {
                "status": "error",
                "error_message": "Invalid appointment ID"
            }
        
        db = SessionLocal()
        
        try:
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

def get_clinic_info() -> Dict:
    """Get information about available therapists and services."""
    return {
        "status": "success",
        "clinic_name": settings.clinic_name,
        "therapist_name": settings.therapist_name,
        "clinic_address": settings.clinic_address,
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
                "location": settings.clinic_address
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
        "emergency_contact": settings.emergency_contact,
        "crisis_center": getattr(settings, 'crisis_center', 'Local Crisis Support Center')
    }

def get_available_services_and_therapists() -> Dict:
    """Get all available main services and therapists."""
    try:
        db = SessionLocal()
        
        try:
            # Get all active therapists
            therapists = db.query(Therapist).filter(Therapist.is_active == True).all()
            
            services_info = [
                {
                    "name": "45 Min In-Call Session",
                    "description": "45-minute therapy session at our clinic",
                    "duration_minutes": 45,
                    "price": "200 QAR",
                    "category": "in_call"
                },
                {
                    "name": "1 Hour In-Call Session", 
                    "description": "1-hour therapy session at our clinic",
                    "duration_minutes": 60,
                    "price": "250 QAR",
                    "category": "in_call"
                },
                {
                    "name": "1 Hour Out-Call Session",
                    "description": "1-hour therapy session at client's home (includes transport)",
                    "duration_minutes": 60,
                    "price": "300 QAR",
                    "category": "out_call"
                },
                {
                    "name": "1.5 Hour In-Call Session",
                    "description": "Extended 1.5-hour therapy session at our clinic",
                    "duration_minutes": 90,
                    "price": "350 QAR",
                    "category": "in_call"
                },
                {
                    "name": "1.5 Hour Out-Call Session",
                    "description": "Extended 1.5-hour therapy session at client's home (includes transport)",
                    "duration_minutes": 90,
                    "price": "400 QAR",
                    "category": "out_call"
                }
            ]
            
            therapists_info = []
            for therapist in therapists:
                therapists_info.append({
                    "name": therapist.name,
                    "specializations": therapist.specializations,
                    "experience_years": therapist.experience_years,
                    "languages": therapist.languages,
                    "bio": therapist.bio
                })
            
            return {
                "status": "success",
                "main_services": services_info,
                "therapists": therapists_info
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error getting services and therapists: {str(e)}")
        return {
            "status": "error", 
            "error_message": f"Error retrieving services: {str(e)}"
        }

def get_user_appointments(client_phone: str, status: Optional[str] = None) -> Dict:
    """Get appointments for a specific client."""
    try:
        if not client_phone:
            return {
                "status": "error",
                "error_message": "Phone number is required"
            }
        
        db = SessionLocal()
        
        try:
            user = db.query(User).filter(User.phone_number == client_phone).first()
            
            if not user:
                return {
                    "status": "not_found",
                    "message": "No appointments found for this phone number."
                }
            
            appointments = booking_service.get_user_appointments(db, user.id, status)
            
            appointment_list = []
            for apt in appointments:
                appointment_list.append({
                    "appointment_id": apt.id,
                    "date": apt.preferred_datetime.strftime('%Y-%m-%d'),
                    "time": apt.preferred_datetime.strftime('%H:%M'),
                    "service_type": apt.service_type.value if apt.service_type else "unknown",
                    "status": apt.status.value,
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
        self.client_context = {}
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize the ADK agent with therapy booking tools"""
        try:
            from google.adk.agents import Agent
            
            self.agent = Agent(
                name="therapy_booking_agent",
                model=settings.google_genai_model,
                description=(
                    "Professional therapy booking agent that helps clients schedule, manage, and "
                    "get information about therapy appointments through WhatsApp Business API."
                ),
                instruction=f"""You are Layla, a warm and caring female therapy booking assistant at {settings.clinic_name}. 

**CRITICAL RULE: For ANY booking request, you MUST use the book_appointment tool first!**

## Your Personality:
- Warm, caring woman who genuinely cares about each client's wellbeing
- Speak like a loving sister or best friend - natural, caring, and personal
- Use loving terms: "habibti", "dear", "my love", "sweetie" naturally
- Express genuine excitement when helping them feel better

## Our Services & Pricing:
- **45 Min Session at Clinic** - 200 QAR 
- **1 Hour Session at Clinic** - 250 QAR
- **1 Hour Home Visit** - 300 QAR
- **1.5 Hour Session at Clinic** - 350 QAR
- **1.5 Hour Home Visit** - 400 QAR

## Therapist: {settings.therapist_name}

## Booking Process:
1. Client mentions booking → use check_availability() tool
2. After availability → use book_appointment() tool  
3. ONLY after book_appointment succeeds → tell client you've submitted their request

**CRITICAL: book_appointment creates a PENDING request that needs coordinator approval!**

## Business Hours:
- Monday-Friday: 9:00 AM - 6:00 PM
- Saturday: 9:00 AM - 2:00 PM  
- Sunday: Closed

## Emergency:
- Emergency contact: {settings.emergency_contact}
- Crisis center: {getattr(settings, 'crisis_center', 'Local Crisis Support Center')}
""",
                tools=[
                    check_availability,
                    book_appointment,  
                    cancel_appointment,
                    get_clinic_info,
                    get_available_services_and_therapists,
                    get_user_appointments
                ]
            )
            
            from google.adk.runners import Runner
            from google.adk.sessions import InMemorySessionService
            
            self.session_service = InMemorySessionService()
            self.runner = Runner(
                agent=self.agent,
                app_name="therapy_booking",
                session_service=self.session_service
            )
            
            logger.info("ADK Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing ADK agent: {str(e)}")
            self.agent = None
            self.session_service = None
            self.runner = None
    
    async def process_message(self, message: str, phone_number: str, session_id: Optional[str] = None, 
                            pushname: str = "") -> str:
        """Process incoming message with ADK agent"""
        try:
            if not self.agent or not self.runner:
                logger.warning("ADK agent not initialized, reinitializing...")
                self._initialize_agent()
                if not self.agent or not self.runner:
                    return "I'm sorry, the booking system is temporarily unavailable. Please try again later."
            
            from google.genai import types
            
            user_id = phone_number
            if not session_id:
                clean_phone = phone_number.replace('+', '').replace('-', '').replace(' ', '')
                session_id = f"session_{clean_phone}_{int(datetime.datetime.now().timestamp())}"
            
            logger.info(f"Processing message for user {user_id}, session {session_id}")
            
            # Store client context
            self.client_context[session_id] = {
                'phone_number': phone_number,
                'pushname': pushname or f"Client {phone_number[-4:]}",
                'session_id': session_id
            }
            
            # Create session if needed
            try:
                existing_session = self.session_service.get_session(
                    app_name="therapy_booking",
                    user_id=user_id,
                    session_id=session_id
                )
                if not existing_session:
                    self.session_service.create_session(
                        app_name="therapy_booking",
                        user_id=user_id,
                        session_id=session_id,
                        state={}
                    )
            except Exception as e:
                logger.warning(f"Session error: {e}. Creating new session.")
                self.session_service.create_session(
                    app_name="therapy_booking",
                    user_id=user_id,
                    session_id=session_id,
                    state={}
                )
            
            # Create message content
            content = types.Content(
                role='user',
                parts=[types.Part(text=message)]
            )
            
            # Set context for tools
            book_appointment._current_client_context = self.client_context[session_id]
            
            # Process with agent
            try:
                events = self.runner.run(
                    user_id=user_id,
                    session_id=session_id,
                    new_message=content
                )
            except Exception as e:
                logger.error(f"Error in ADK runner: {e}")
                return "I'm having a small technical issue, habibti. Could you please try again? 💕"
            
            # Extract response
            response_text = ""
            for event in events:
                if event.is_final_response() and event.content:
                    response_text = event.content.parts[0].text.strip()
                    break
            
            # Fallback responses if no response
            if not response_text:
                if "appointment" in message.lower() or "book" in message.lower():
                    response_text = "I'd be happy to help you book an appointment! Could you please let me know your preferred date and whether you'd like an office visit or home visit?"
                elif "available" in message.lower():
                    response_text = "I can check our availability for you. Please let me know which date you're interested in."
                else:
                    response_text = "I'm here to help with your therapy appointments. How can I assist you today?"
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again."

# Create global service instance
adk_service = ADKAgentService()