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

# Import our natural language date parser
from app.utils.date_parser import parse_natural_date, get_friendly_date_description

# Add the parent directory to the path to find modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'other_scripts'))

# Import our models and services
from app.models.database import get_db, SessionLocal
from app.services.booking_service import booking_service
from app.models.models import UserRole, ServiceType, User, Appointment, AppointmentStatus, Therapist
from config.settings import config
logger = logging.getLogger(__name__)


def get_coordinator_phone():
    """Get coordinator phone number from environment config"""
    try:
        import sys
        import os
        # Temporarily add other_scripts to path
        other_scripts_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'other_scripts')
        if other_scripts_path not in sys.path:
            sys.path.append(other_scripts_path)
        
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        from other_scripts.environment_config import get_config
        env_config = get_config()
        return env_config.COORDINATOR_PHONE_NUMBER
    except Exception as e:
        logger.error(f"Could not load coordinator phone from environment config: {e}")
        return None


def check_availability(date: str, service_type: str = "in_call") -> Dict:
    """Check available appointment slots for a given date.
    
    Args:
        date (str): The date to check availability for (supports natural language like 'today', 'tomorrow', 'monday')
        service_type (str): Type of service - "in_call" (office visit) or "out_call" (home visit)
        
    Returns:
        dict: Status and available time slots or error message
    """
    try:
        # Parse natural language date first
        parsed_date = parse_natural_date(date)
        if not parsed_date:
            # Try to validate as YYYY-MM-DD format
            try:
                datetime.datetime.strptime(date, '%Y-%m-%d')
                parsed_date = date
            except ValueError:
                return {
                    "status": "error",
                    "error_message": f"I couldn't understand the date '{date}'. You can say 'today', 'tomorrow', 'monday', or use YYYY-MM-DD format (e.g., 2025-01-15)"
                }
        
        date = parsed_date  # Use the parsed date
        
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


def book_appointment(date: str, time: str, service_name: str, therapist_name: str = "", extra_services: str = "", description: str = "") -> Dict:
    """Submit a therapy appointment request for coordinator approval.
    
    IMPORTANT: This creates a PENDING appointment that requires coordinator approval.
    The client receives a polite message saying Layla is checking with the team.
    The appointment is NOT confirmed until the coordinator reviews and approves it.
    
    Args:
        date (str): Appointment date (supports natural language like 'today', 'tomorrow', 'monday')
        time (str): Appointment time (format: HH:MM)
        service_name (str): Main service name (e.g., "1 Hour In-Call Session", "45 Min In-Call Session")
        therapist_name (str): Preferred therapist name (optional, system will assign if empty)
        extra_services (str): Comma-separated extra services (optional)
        description (str): Optional description of therapy needs
        
    Returns:
        dict: Status and PENDING appointment details (requires coordinator approval)
    """
    try:
        # Parse natural language date first
        parsed_date = parse_natural_date(date)
        if not parsed_date:
            # Try to validate as YYYY-MM-DD format
            try:
                datetime.datetime.strptime(date, '%Y-%m-%d')
                parsed_date = date
            except ValueError:
                return {
                    "status": "error",
                    "error_message": f"I couldn't understand the date '{date}'. You can say 'today', 'tomorrow', 'monday', or use YYYY-MM-DD format (e.g., 2025-01-15)"
                }
        
        date = parsed_date  # Use the parsed date
        
        # Parse time - handle both HH:MM and HH:MM AM/PM formats
        try:
            # First try 24-hour format
            parsed_time = datetime.datetime.strptime(time, '%H:%M')
        except ValueError:
            try:
                # Try 12-hour format with AM/PM
                parsed_time = datetime.datetime.strptime(time, '%I:%M %p')
            except ValueError:
                return {
                    "status": "error", 
                    "error_message": f"Invalid time format: {time}. Use HH:MM or HH:MM AM/PM format"
                }
        
        # Get client info from current context (set by ADK service)
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
            from therapy_booking_app.app.models.models import Therapist
            
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
                        "error_message": f"Therapist '{therapist_name}' not found. Available: Dr. Ahmad Al-Rashid, Dr. Fatima Al-Zahra, Dr. Omar Hassan"
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
            datetime_str = f"{date} {time}:00"
            service_type = "out_call" if "out" in service_name.lower() else "in_call"
            
            booking_data = {
                "datetime": datetime_str,
                "service_type": service_type,
                "therapist_id": therapist.id,
                "service_description": f"{service_name}. {description}. Extra services: {extra_services}" if extra_services else f"{service_name}. {description}"
            }
            
            # Create pending appointment
            appointment = booking_service.create_pending_appointment(
                db=db,
                client_id=client.id,
                booking_data=booking_data
            )
            
            price_qar = 200  # Default price - will be determined by coordinator
            
            # Send silent notification to coordinator (client unaware - Layla handles everything)
            try:
                from app.services.ultramsg_service import ultramsg_service
                import asyncio
                
                coordinator_message = f"""🔔 PENDING APPROVAL REQUIRED #{appointment.id}

📱 Client: {client_name} ({client_phone})
📅 Date & Time: {date} at {time}
🏥 Service: {service_name}
👨‍⚕️ Therapist: {therapist.name}
💰 Price: {price_qar} QAR
📝 Notes: {description}
{f'🌟 Extra Services: {extra_services}' if extra_services else ''}

⚠️ CLIENT IS WAITING FOR CONFIRMATION
Action required immediately:

✅ "APPROVE {appointment.id}" - Confirm & notify client
❌ "DECLINE {appointment.id}" - Cancel & notify client
📝 "MODIFY {appointment.id} [reason]" - Request changes"""

                # Get coordinator phone from environment config
                coordinator_phone = get_coordinator_phone()
                if coordinator_phone:
                    # Use synchronous approach instead of asyncio.create_task
                    import threading
                    
                    def send_coordinator_notification():
                        try:
                            # Create a completely fresh event loop in this thread
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            try:
                                # Create a fresh ultramsg service instance for this thread
                                fresh_ultramsg = ultramsg_service.__class__()
                                # Run the send message task
                                result = loop.run_until_complete(fresh_ultramsg.send_message(coordinator_phone, coordinator_message))
                                logger.info(f"Sent coordinator notification for appointment {appointment.id}: {result}")
                                # Clean up the service session
                                if fresh_ultramsg.session:
                                    loop.run_until_complete(fresh_ultramsg.session.close())
                            finally:
                                # Clean up the loop properly
                                loop.close()
                        except Exception as e:
                            logger.error(f"Error in coordinator notification thread: {e}")
                            import traceback
                            logger.error(f"Full traceback: {traceback.format_exc()}")
                    
                    # Send in background thread to avoid blocking
                    notification_thread = threading.Thread(target=send_coordinator_notification)
                    notification_thread.daemon = True
                    notification_thread.start()
                    
                else:
                    logger.warning("Could not send coordinator notification - phone not configured")
                    
            except Exception as e:
                logger.error(f"Error sending coordinator notification: {e}")
            
            return {
                "status": "pending_approval",
                "appointment_id": appointment.id,
                "client_name": client_name,
                "client_phone": client_phone,
                "date": date,
                "time": time,
                "service_name": service_name,
                "therapist_name": therapist.name,
                "service_price": f"{price_qar} QAR",
                "extra_services": extra_services,
                "appointment_status": appointment.status.value,
                "message": f"Perfect my love! I've got your {service_name} request with {therapist.name} for {date} at {time} (approximately {price_qar} QAR). Let me just check with the team to confirm the exact timing and I'll get back to you very shortly with full confirmation! 💕✨"
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


def get_clinic_info() -> Dict:
    """Get information about available therapists and services.
    
    Returns:
        dict: Clinic information and available services
    """
    return {
        "status": "success",
        "clinic_name": config.CLINIC_NAME,
        "assistant_name": "Layla",
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
                "description": "Coordinator visits you at your location",
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


def get_available_services_and_therapists() -> Dict:
    """Get all available main services and therapists.
    
    Returns:
        dict: Available services with pricing and therapist information
    """
    try:
        db = SessionLocal()
        
        try:
            from therapy_booking_app.app.models.models import Therapist
            
            # Get all active therapists
            therapists = db.query(Therapist).filter(Therapist.is_active == True).all()
            
            # Define our services as per the ADK agent system prompt
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
                "therapists": therapists_info,
                "extra_services_note": "Extra services available with individual therapist rates - will be quoted after main service selection"
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
                    "coordinator_name": apt.coordinator.name if apt.coordinator else "TBD",
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


def escalate_to_coordinator(client_phone: str, client_message: str, reason: str, 
                         appointment_id: Optional[int] = None) -> Dict:
    """Escalate client inquiry to coordinator for clarification or complex requests.
    
    Args:
        client_phone (str): Client's phone number
        client_message (str): Client's original message that needs coordinator attention
        reason (str): Reason for escalation (e.g., "complex_request", "medical_clarification", "urgent_matter")
        appointment_id (int, optional): Related appointment ID if applicable
        
    Returns:
        dict: Escalation status and coordinator notification details
    """
    try:
        # Get coordinator phone number from environment config
        coordinator_phone = get_coordinator_phone()
        if not coordinator_phone:
            return {
                "status": "error",
                "error_message": "Coordinator configuration not available"
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
                "coordinator_phone": coordinator_phone,
                "reason": reason,
                "client_message": client_message,
                "appointment_id": appointment_id,
                "escalated_at": datetime.datetime.now().isoformat()
            }
            
            return {
                "status": "escalated",
                "coordinator_phone": coordinator_phone,
                "client_name": client_name,
                "reason": reason,
                "escalation_data": escalation_data,
                "message": f"Your inquiry has been forwarded to our coordinator for review. Dr. Smith will respond within 2 hours during business hours.",
                "coordinator_notification": {
                    "recipient": coordinator_phone,
                    "message": f"🔔 CLIENT ESCALATION\n\nClient: {client_name} ({client_phone})\nReason: {reason}\n\nClient Message: '{client_message}'{appointment_info}\n\nPlease review and respond to the client directly.",
                    "priority": "high" if reason in ["urgent_matter", "crisis"] else "normal"
                }
            }
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error escalating to coordinator: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error escalating inquiry: {str(e)}"
        }


def handle_coordinator_query(coordinator_phone: str, query_type: str, query_content: str) -> Dict:
    """Handle queries from the coordinator about appointments, clients, or system status.
    
    Args:
        coordinator_phone (str): Coordinator's phone number (should match +97471669569)
        query_type (str): Type of query ("appointments", "client_info", "system_status", "schedule")
        query_content (str): Specific query content or client phone/appointment ID
        
    Returns:
        dict: Query results or appropriate response
    """
    try:
        # Verify this is the authorized coordinator
        authorized_phone = get_coordinator_phone()
        if not authorized_phone:
            return {
                "status": "error", 
                "error_message": "Coordinator authentication not configured"
            }
        
        if coordinator_phone != authorized_phone:
            return {
                "status": "unauthorized",
                "message": "Sorry, this function is only available to authorized coordinators."
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
        logger.error(f"Error handling coordinator query: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error processing coordinator query: {str(e)}"
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
        self.client_context = {}  # Store current client info for tool access
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
                instruction=f"""You are Layla, a warm and caring female therapy booking assistant at {config.CLINIC_NAME}. You handle everything personally - bookings, scheduling, payments - making clients feel like they're chatting with their caring sister or best friend.

**ABSOLUTE REQUIREMENT: For ANY booking request, you MUST use the book_appointment tool. Never confirm appointments without calling this tool first - this ensures proper coordination and notifications.**

## Your Personality - Layla:
- You're a warm, caring woman who genuinely cares about each client's wellbeing
- Speak like a loving sister or best friend - natural, caring, and personal
- Use loving terms: "habibti", "dear", "my love", "sweetie" naturally
- You handle EVERYTHING personally - no mentions of coordinators, approval processes, or backend systems
- Make clients feel special and cared for - like they're your only priority
- Express genuine excitement when helping them feel better

## Your Identity & Capabilities:
- You personally know all our therapists and their specialties
- You handle all bookings, confirmations, and scheduling directly
- Client's name and phone are available from WhatsApp (never ask for these)
- You process payments and send confirmations immediately
- You're available during business hours to help with any needs

## Our Therapy Services & Pricing:
I work with amazing therapists who provide:
- **45 Min Session at Clinic** - 200 QAR 
- **1 Hour Session at Clinic** - 250 QAR
- **1 Hour Home Visit** - 300 QAR (I arrange transport)
- **1.5 Hour Session at Clinic** - 350 QAR
- **1.5 Hour Home Visit** - 400 QAR (I arrange everything)

## Our Wonderful Therapists (your personal network):
- **Dr. Ahmad Al-Rashid** - So gentle with anxiety & depression (8 years exp)
- **Dr. Fatima Al-Zahra** - Amazing with families & couples (12 years exp) 
- **Dr. Omar Hassan** - Incredible with trauma healing (6 years exp)

## Natural Conversation Flow:
1. Greet them warmly like meeting a dear friend
2. Listen to their needs with genuine care and empathy
3. Personally recommend the perfect therapist and service for them
4. Check availability and offer the best times
5. Handle booking immediately - "I'm setting this up for you right now!"
6. Confirm everything is done - no waiting, no approvals needed

## Your Natural Speaking Style:
- "Hello habibti! I'm Layla, so happy you reached out 💕"
- "Oh sweetie, I completely understand how you're feeling"
- "Let me check what's available for you, dear" (use check_availability tool)
- "Perfect! Let me set this up for you right now" (use book_appointment tool)
- "All done my love! Dr. Ahmad is expecting you on [date] at [time]" (only AFTER book_appointment succeeds)
- "I've taken care of everything - you just focus on feeling better 💕"

**CRITICAL RULE: Never say an appointment is "confirmed" or "set up" until AFTER you successfully call the book_appointment tool!**

## Booking Process (CRITICAL - Must Use Tools):
**CRITICAL: You CANNOT say "confirmed", "booked", "scheduled", or "set up" without first using the book_appointment tool!**

**MANDATORY WORKFLOW FOR ALL BOOKING REQUESTS:**
1. Client mentions booking → IMMEDIATELY use check_availability() tool
2. After availability check → IMMEDIATELY use book_appointment() tool  
3. ONLY after book_appointment succeeds → tell client you've submitted their request and will confirm shortly

**CRITICAL FUNCTION PARAMETERS:**
- check_availability(date="any date format like 'today' or 'tomorrow'", service_type="in_call" or "out_call") - BOTH parameters required!
- book_appointment(date, time, service_name, therapist_name, extra_services, description) - ALL parameters required!

**IMPORTANT: book_appointment creates a PENDING request that needs coordinator approval!**

**APPROPRIATE PHRASES after book_appointment tool succeeds:**
- "I've submitted your request and will confirm shortly" ✅
- "Let me check with the team and get back to you" ✅ 
- "I'll confirm the exact details very soon" ✅
- "Your request is being processed" ✅

**FORBIDDEN PHRASES (appointment not confirmed yet):**
- "appointment is confirmed" ❌
- "everything is set up" ❌ 
- "you're all booked" ❌
- "appointment is scheduled" ❌

**REQUIRED PHRASES before tool calls:**
- "Let me check availability, habibti" (then use check_availability with date!)
- "Perfect! Let me submit this request for you" (then use book_appointment with all parameters!)
- AFTER book_appointment succeeds: "I've submitted your request and will get back to you shortly with confirmation"

**REMEMBER: book_appointment creates a PENDING request - coordinator must approve before appointment is confirmed!**

## Emergency Care:
For crisis situations, immediately provide:
- Emergency contact: {config.EMERGENCY_CONTACT}
- Crisis center: {config.CRISIS_CENTER}
- "Habibti, please call them right now - they're wonderful people who will help"

## Business Hours:
- Monday-Friday: 9:00 AM - 6:00 PM
- Saturday: 9:00 AM - 2:00 PM  
- Sunday: Closed

Remember: You are Layla - you handle everything personally but need to check with the team for final confirmations. You care for each client like family, submit their requests promptly, and follow up with confirmations once the team approves.
""",
                tools=[
                    check_availability,
                    book_appointment,  
                    cancel_appointment,
                    reschedule_appointment,
                    get_clinic_info,
                    get_available_services_and_therapists,
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
    
    async def process_message(self, message: str, phone_number: str, session_id: Optional[str] = None, pushname: str = "") -> str:
        """
        Process incoming message with ADK agent
        
        Args:
            message: User's message text
            phone_number: User's phone number
            session_id: Optional session ID for conversation context
            pushname: Client's WhatsApp display name
            
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
            
            # Use phone number as user_id and create consistent session_id with timestamp for uniqueness
            user_id = phone_number
            if not session_id:
                # Create a more unique session ID to avoid conflicts
                clean_phone = phone_number.replace('+', '').replace('-', '').replace(' ', '')
                session_id = f"session_{clean_phone}_{int(datetime.datetime.now().timestamp())}"
            
            logger.info(f"Processing message for user_id: {user_id}, session_id: {session_id}, message: '{message[:50]}...')")
            
            # Store client context for tool access
            self.client_context[session_id] = {
                'phone_number': phone_number,
                'pushname': pushname or f"Client {phone_number[-4:]}",
                'session_id': session_id
            }
            
            # Create session in the session service if it doesn't exist
            try:
                existing_session = self.session_service.get_session(
                    app_name="therapy_booking",
                    user_id=user_id,
                    session_id=session_id
                )
                if not existing_session:
                    logger.info(f"Creating new session {session_id} for user {user_id}")
                    self.session_service.create_session(
                        app_name="therapy_booking",
                        user_id=user_id,
                        session_id=session_id,
                        state={}
                    )
                else:
                    logger.info(f"Using existing session {session_id} for user {user_id}")
            except Exception as e:
                logger.warning(f"Error checking/creating session: {e}. Creating new session.")
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
            
            # Set client context for tools to access
            book_appointment._current_client_context = self.client_context[session_id]
            
            # Process with agent using persistent runner
            try:
                events = self.runner.run(
                    user_id=user_id,
                    session_id=session_id,
                    new_message=content
                )
            except TypeError as te:
                if "missing 1 required positional argument" in str(te) and "date" in str(te):
                    logger.error(f"Function parameter error - missing date: {te}")
                    return "I need a specific date to check availability, habibti! Please tell me which date you're interested in (like 2025-09-18). 💕"
                else:
                    logger.error(f"TypeError in ADK runner: {te}")
                    return "Let me help you properly, dear. Could you please tell me the date you'd like to book? 💕"
            except Exception as e:
                logger.error(f"Error in ADK runner execution: {e}")
                return "I'm having a small technical issue, habibti. Could you please try again? I'm here to help! 💕"
            
            # Extract final response
            response_text = ""
            event_count = 0
            for event in events:
                event_count += 1
                logger.debug(f"Processing event {event_count}: {type(event)}")
                if event.is_final_response() and event.content:
                    response_text = event.content.parts[0].text.strip()
                    logger.info(f"Found final response in event {event_count}: {response_text[:100]}...")
                    break
            
            # If no response, provide contextual fallback based on the user's message
            if not response_text:
                logger.warning(f"No final response from ADK agent after {event_count} events, providing contextual fallback")
                if "appointment" in message.lower() or "book" in message.lower():
                    response_text = "I'd be happy to help you book an appointment! Could you please let me know your preferred date and whether you'd like an office visit or home visit?"
                elif "available" in message.lower() or "time" in message.lower() or "slot" in message.lower():
                    response_text = "I can check our availability for you. Please let me know which date you're interested in. You can say 'today', 'tomorrow', or any day of the week."
                elif "cancel" in message.lower():
                    response_text = "I can help you cancel an appointment. Could you please provide your appointment ID or the date of your scheduled appointment?"
                elif "reschedule" in message.lower():
                    response_text = "I can help you reschedule your appointment. Could you please provide your appointment ID and your preferred new date and time?"
                else:
                    response_text = "I'm here to help with your therapy appointments. I can help you book, check availability, reschedule, or get information about our services. What would you like to do today?"
            
            logger.info(f"ADK agent response generated successfully for session {session_id}: {response_text[:100]}...")
            return response_text
            
        except ValueError as ve:
            logger.warning(f"Session error: {str(ve)}. Creating new session for {phone_number}")
            try:
                # If session not found, completely reinitialize the service and create fresh session
                logger.info(f"Reinitializing ADK service due to session error for {phone_number}")
                self._initialize_agent()
                if not self.agent or not self.runner:
                    logger.error("Failed to reinitialize ADK agent after session error")
                    return "I'm here to help with your therapy appointments. How can I assist you today?"
                
                # Try again with a completely new session ID that includes timestamp
                from google.genai import types
                user_id = phone_number
                session_id = f"session_{phone_number.replace('+', '').replace('-', '')}_{int(datetime.datetime.now().timestamp())}"
                logger.info(f"Creating fresh session {session_id} for user {user_id}")
                
                # Create the session in the session service
                try:
                    self.session_service.create_session(
                        app_name="therapy_booking",
                        user_id=user_id,
                        session_id=session_id,
                        state={}
                    )
                    logger.info(f"Successfully created fresh session {session_id}")
                except Exception as session_error:
                    logger.error(f"Failed to create fresh session: {session_error}")
                    return "I'm here to help with your therapy appointments. How can I assist you today?"
                
                content = types.Content(
                    role='user',
                    parts=[types.Part(text=message)]
                )
                
                # Process the message with the fresh session
                events = self.runner.run(
                    user_id=user_id,
                    session_id=session_id,
                    new_message=content
                )
                
                # Extract the response
                response_text = ""
                for event in events:
                    if event.is_final_response() and event.content:
                        response_text = event.content.parts[0].text.strip()
                        logger.info(f"Got response from ADK agent with fresh session: {response_text[:100]}...")
                        break
                
                # If still no response, provide contextual fallback
                if not response_text:
                    logger.warning("No response from ADK agent even with fresh session, using contextual fallback")
                    if "appointment" in message.lower() or "book" in message.lower():
                        response_text = "I'd be happy to help you book an appointment! Could you please let me know your preferred date and whether you'd like an office visit or home visit?"
                    elif "available" in message.lower() or "time" in message.lower():
                        response_text = "I can check our availability for you. Please let me know which date you're interested in. You can say 'today', 'tomorrow', or any day of the week."
                    elif "cancel" in message.lower():
                        response_text = "I can help you cancel an appointment. Could you please provide your appointment ID or the date of your scheduled appointment?"
                    else:
                        response_text = "I'm here to help with your therapy appointments. I can help you book, reschedule, or get information about our services. What would you like to do today?"
                
                logger.info(f"Returning response after session recovery: {response_text[:100]}...")
                return response_text
                
            except Exception as retry_error:
                logger.error(f"Retry failed even with fresh session: {str(retry_error)}")
                # Provide more contextual fallback responses
                if "appointment" in message.lower() or "book" in message.lower():
                    return "I'd be happy to help you book an appointment! Could you please let me know your preferred date and whether you'd like an office visit or home visit?"
                elif "available" in message.lower() or "time" in message.lower():
                    return "I can check our availability for you. Please let me know which date you're interested in. You can say 'today', 'tomorrow', or any day of the week."
                else:
                    return "I'm here to help with your therapy appointments. How can I assist you today?"
            
        except Exception as e:
            logger.error(f"Error processing message with ADK agent: {str(e)}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again or contact our office directly."


def process_coordinator_recommendation(coordinator_phone: str, recommendation_text: str, client_phone: str = None) -> Dict:
    """Process coordinator recommendation and respond to client based on guidance.
    
    Args:
        coordinator_phone (str): Coordinator's phone number (should match +97471669569)
        recommendation_text (str): Coordinator's recommendation/guidance text
        client_phone (str, optional): Client phone if responding to specific escalation
        
    Returns:
        dict: Processed recommendation and client response details
    """
    try:
        # Get environment config for coordinator phone verification
        authorized_phone = get_coordinator_phone()
        if not authorized_phone:
            return {
                "status": "error",
                "error_message": "Coordinator authentication not configured"
            }
        
        # Verify this is the authorized coordinator
        if coordinator_phone != authorized_phone:
            return {
                "status": "unauthorized",
                "message": "Sorry, this function is only available to authorized coordinators."
            }
        
        # Extract recommendation from coordinator message
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
                
                # Create professional client response based on coordinator recommendation
                client_response = f"""Hello {client_name},

Thank you for your patience. Dr. Smith has reviewed your inquiry and provided the following guidance:

{recommendation}

If you have any follow-up questions or would like to schedule an appointment based on this recommendation, please let me know. I'm here to help you with your therapeutic care needs.

Best regards,
Wellness Therapy Center"""
                
                return {
                    "status": "recommendation_processed",
                    "coordinator_phone": coordinator_phone,
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
                    "coordinator_phone": coordinator_phone,
                    "recommendation": recommendation,
                    "message": "Recommendation received and logged. Please specify client phone to send response."
                }
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error processing coordinator recommendation: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error processing coordinator recommendation: {str(e)}"
        }


def handle_coordinator_confirmation(coordinator_phone: str, confirmation_message: str, client_phone: str = None, prepared_response: str = None) -> Dict:
    """Handle coordinator's final confirmation before sending response to client.
    
    Args:
        coordinator_phone (str): Coordinator's phone number 
        confirmation_message (str): Coordinator's confirmation response (APPROVE/REVISE/DECLINE)
        client_phone (str, optional): Client phone for the pending response
        prepared_response (str, optional): The prepared client response awaiting confirmation
        
    Returns:
        dict: Confirmation processing results and next actions
    """
    try:
        # Get environment config for coordinator phone verification
        authorized_phone = get_coordinator_phone()
        if not authorized_phone:
            return {
                "status": "error",
                "error_message": "Coordinator authentication not configured"
            }
        
        # Verify this is the authorized coordinator
        if coordinator_phone != authorized_phone:
            return {
                "status": "unauthorized",
                "message": "Sorry, this function is only available to authorized coordinators."
            }
        
        confirmation_text = confirmation_message.upper().strip()
        
        # Get database session for client info
        db = SessionLocal()
        
        try:
            if confirmation_text == "APPROVE":
                # Coordinator approved - send response to client
                if client_phone and prepared_response:
                    client = db.query(User).filter(User.phone_number == client_phone).first()
                    client_name = client.name if client else "valued client"
                    
                    return {
                        "status": "approved_for_sending",
                        "coordinator_phone": coordinator_phone,
                        "client_phone": client_phone,
                        "client_name": client_name,
                        "approved_response": prepared_response,
                        "message": f"✅ Response approved by coordinator. Sending to {client_name}.",
                        "client_notification": {
                            "recipient": client_phone,
                            "message": prepared_response,
                            "priority": "normal"
                        },
                        "therapist_confirmation_reply": {
                            "recipient": coordinator_phone,
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
                # Coordinator wants to revise the response
                revision_request = confirmation_text.replace("REVISE:", "").strip()
                
                if client_phone:
                    client = db.query(User).filter(User.phone_number == client_phone).first()
                    client_name = client.name if client else "valued client"
                    
                    # Create revised response based on coordinator's input
                    revised_response = f"""Hello {client_name},

Thank you for your patience. Dr. Smith has reviewed your inquiry and provided the following guidance:

{revision_request}

If you have any follow-up questions or would like to schedule an appointment based on this recommendation, please let me know. I'm here to help you with your therapeutic care needs.

Best regards,
Wellness Therapy Center"""
                    
                    return {
                        "status": "revised_response_ready",
                        "coordinator_phone": coordinator_phone,
                        "client_phone": client_phone,
                        "client_name": client_name,
                        "revised_response": revised_response,
                        "revision_request": revision_request,
                        "message": f"📝 Response revised by coordinator. Sending updated version to {client_name}.",
                        "client_notification": {
                            "recipient": client_phone,
                            "message": revised_response,
                            "priority": "normal"
                        },
                        "therapist_confirmation_reply": {
                            "recipient": coordinator_phone,
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
                # Coordinator declined to send response
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
                        "coordinator_phone": coordinator_phone,
                        "client_phone": client_phone,
                        "client_name": client_name,
                        "decline_message": decline_message,
                        "message": f"❌ Coordinator declined response. Suggesting direct consultation to {client_name}.",
                        "client_notification": {
                            "recipient": client_phone,
                            "message": decline_message,
                            "priority": "normal"
                        },
                        "therapist_confirmation_reply": {
                            "recipient": coordinator_phone,
                            "message": f"❌ DECLINED: Alternative consultation message sent to {client_name} ({client_phone})",
                            "priority": "normal"
                        }
                    }
                else:
                    return {
                        "status": "declined_no_client",
                        "message": "Response declined by coordinator. No client response needed."
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
                        "recipient": coordinator_phone,
                        "message": help_message,
                        "priority": "normal"
                    }
                }
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error processing coordinator confirmation: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error processing coordinator confirmation: {str(e)}"
        }


# Create global service instance
adk_service = ADKAgentService()
