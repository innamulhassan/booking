"""
Therapy Booking Agent using Google Agent Development Kit (ADK)

This agent handles therapy appointment bookings through WhatsApp Business API
integrated with our existing booking system.
"""

import datetime
import json
import sys
import os
from typing import Dict, List, Optional
from google.adk.agents import Agent

# Add the main app directory to Python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'therapy_booking_app'))

from app.models.database import get_db
from app.services.booking_service import booking_service
from app.models.models import UserRole, ServiceType

def check_availability(date: str, service_type: str = "in_call") -> Dict:
    """Check available appointment slots for a given date.
    
    Args:
        date (str): The date to check availability for (format: YYYY-MM-DD)
        service_type (str): Type of service - "in_call" (office visit) or "out_call" (home visit)
        
    Returns:
        dict: Status and available time slots or error message
    """
    try:
        # Get database session
        db = next(get_db())
        
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
            
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error checking availability: {str(e)}"
        }
    finally:
        if 'db' in locals():
            db.close()


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
        # Get database session
        db = next(get_db())
        
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
            "date": date,
            "time": time,
            "service_type": service_type,
            "appointment_status": appointment.status.value,
            "message": f"Appointment booked successfully! Appointment ID: {appointment.id}. Status: Pending confirmation."
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error booking appointment: {str(e)}"
        }
    finally:
        if 'db' in locals():
            db.close()


def cancel_appointment(appointment_id: int, reason: str = "") -> Dict:
    """Cancel an existing appointment.
    
    Args:
        appointment_id (int): The ID of the appointment to cancel
        reason (str): Optional reason for cancellation
        
    Returns:
        dict: Status and cancellation details or error message
    """
    try:
        # Get database session
        db = next(get_db())
        
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
            "message": f"Appointment {appointment_id} has been cancelled successfully."
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error cancelling appointment: {str(e)}"
        }
    finally:
        if 'db' in locals():
            db.close()


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
        # Get database session
        db = next(get_db())
        
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
            "message": f"Appointment {appointment_id} has been rescheduled to {new_date} at {new_time}."
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error rescheduling appointment: {str(e)}"
        }
    finally:
        if 'db' in locals():
            db.close()


def get_therapist_info() -> Dict:
    """Get information about available therapists and services.
    
    Returns:
        dict: Therapist information and available services
    """
    return {
        "status": "success",
        "clinic_name": "Wellness Therapy Center",
        "therapist_name": "Dr. Sarah Smith",
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
                "location": "123 Health Street, Wellness City"
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
        "emergency_contact": "(555) 123-4567",
        "crisis_center": "Local Crisis Support Center"
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
        # Get database session
        db = next(get_db())
        
        # Get user by phone number
        from app.models.models import User
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
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error retrieving appointments: {str(e)}"
        }
    finally:
        if 'db' in locals():
            db.close()


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
        # Fixed therapist phone number from requirements
        therapist_phone = "+97471669569"
        
        # Get database session
        db = next(get_db())
        
        try:
            # Get client info and history
            from app.models.models import User, Appointment, AppointmentStatus
            client = db.query(User).filter(User.phone_number == client_phone).first()
            client_name = client.name if client else "Unknown Client"
            
            # Get client's appointment history for context
            client_history = ""
            if client:
                recent_appointments = db.query(Appointment).filter(
                    Appointment.client_id == client.id
                ).order_by(Appointment.preferred_datetime.desc()).limit(3).all()
                
                if recent_appointments:
                    client_history = "\n📋 Recent Appointments:"
                    for apt in recent_appointments:
                        client_history += f"\n  • {apt.preferred_datetime.strftime('%Y-%m-%d')}: {apt.service_type.value} - {apt.status.value}"
            
            # Get current appointment info if provided
            appointment_context = ""
            if appointment_id:
                appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
                if appointment:
                    appointment_context = f"\n🗓️ Current Appointment: #{appointment_id} on {appointment.preferred_datetime.strftime('%Y-%m-%d at %H:%M')} ({appointment.service_type.value})"
            
            # Create structured clarification questions based on reason
            clarification_questions = ""
            if reason == "medical_clarification":
                clarification_questions = "\n❓ Please clarify:\n  • Is this within scope of our therapy services?\n  • Any special precautions needed?\n  • Recommended approach or referral?"
            elif reason == "complex_request":
                clarification_questions = "\n❓ Please advise:\n  • How should we handle this request?\n  • Any special accommodations needed?\n  • Alternative solutions to suggest?"
            elif reason == "urgent_matter":
                clarification_questions = "\n❓ Urgent guidance needed:\n  • Immediate action required?\n  • How to prioritize this case?\n  • Emergency protocols to follow?"
            elif reason == "special_accommodation":
                clarification_questions = "\n❓ Accommodation request:\n  • Can we provide this accommodation?\n  • What modifications are needed?\n  • Any additional considerations?"
            
            # Enhanced therapist notification with context and clear questions
            therapist_message = f"""🔔 CLIENT ESCALATION - {reason.upper()}

👤 Client: {client_name} ({client_phone})
📅 Escalated: {datetime.datetime.now().strftime('%Y-%m-%d at %H:%M')}

💬 Client Message:
"{client_message}"
{appointment_context}
{client_history}
{clarification_questions}

📱 Please reply with your recommendation and I'll respond to the client accordingly.
🔄 Use format: RECOMMENDATION: [your guidance here]"""
            
            # Create escalation record
            escalation_data = {
                "client_phone": client_phone,
                "client_name": client_name,
                "therapist_phone": therapist_phone,
                "reason": reason,
                "client_message": client_message,
                "appointment_id": appointment_id,
                "escalated_at": datetime.datetime.now().isoformat(),
                "status": "pending_therapist_response"
            }
            
            return {
                "status": "escalated",
                "therapist_phone": therapist_phone,
                "client_name": client_name,
                "reason": reason,
                "escalation_data": escalation_data,
                "message": f"Thank you for your inquiry. I've forwarded your request to Dr. Smith for specialized guidance. You'll receive a personalized response within 2 hours during business hours (9 AM - 6 PM).",
                "therapist_notification": {
                    "recipient": therapist_phone,
                    "message": therapist_message,
                    "priority": "high" if reason in ["urgent_matter", "crisis"] else "normal"
                }
            }
        finally:
            db.close()
            
    except Exception as e:
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
        if therapist_phone != "+97471669569":
            return {
                "status": "unauthorized",
                "message": "Sorry, this function is only available to authorized therapists."
            }
        
        # Get database session
        db = next(get_db())
        
        try:
            from app.models.models import User, Appointment, AppointmentStatus
            
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
        return {
            "status": "error",
            "error_message": f"Error processing therapist query: {str(e)}"
        }


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
        # Verify this is the authorized therapist
        if therapist_phone != "+97471669569":
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
        db = next(get_db())
        
        try:
            from app.models.models import User
            
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
                
                # Create confirmation request for therapist before sending to client
                therapist_confirmation = f"""📋 FINAL CONFIRMATION REQUIRED

👤 Client: {client_name} ({client_phone})
📅 Response prepared: {datetime.datetime.now().strftime('%Y-%m-%d at %H:%M')}

💬 Prepared Response to Client:
""{client_response}""

✅ Please confirm:
Reply "APPROVE" to send this response to the client
Reply "REVISE: [your changes]" to modify the response
Reply "DECLINE" to cancel sending this response

⏰ Awaiting your confirmation..."""
                
                return {
                    "status": "awaiting_therapist_confirmation",
                    "therapist_phone": therapist_phone,
                    "client_phone": client_phone,
                    "client_name": client_name,
                    "recommendation": recommendation,
                    "prepared_response": client_response,
                    "message": "Client response prepared and sent to therapist for final confirmation.",
                    "therapist_confirmation": {
                        "recipient": therapist_phone,
                        "message": therapist_confirmation,
                        "priority": "high"
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
        return {
            "status": "error",
            "error_message": f"Error processing therapist recommendation: {str(e)}"
        }


def handle_therapist_confirmation(therapist_phone: str, confirmation_message: str, client_phone: str = None, prepared_response: str = None) -> Dict:
    """Handle therapist's final confirmation before sending response to client.
    
    Args:
        therapist_phone (str): Therapist's phone number (should match +97471669569)
        confirmation_message (str): Therapist's confirmation response (APPROVE/REVISE/DECLINE)
        client_phone (str, optional): Client phone for the pending response
        prepared_response (str, optional): The prepared client response awaiting confirmation
        
    Returns:
        dict: Confirmation processing results and next actions
    """
    try:
        # Verify this is the authorized therapist
        if therapist_phone != "+97471669569":
            return {
                "status": "unauthorized",
                "message": "Sorry, this function is only available to authorized therapists."
            }
        
        confirmation_text = confirmation_message.upper().strip()
        
        # Get database session for client info
        db = next(get_db())
        
        try:
            from app.models.models import User
            
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
        return {
            "status": "error",
            "error_message": f"Error processing therapist confirmation: {str(e)}"
        }


# Create the root agent following ADK patterns
root_agent = Agent(
    name="therapy_booking_agent",
    model="gemini-1.5-pro-002",
    description=(
        "Professional therapy booking agent that helps clients schedule, manage, and "
        "get information about therapy appointments through WhatsApp Business API."
    ),
    instruction="""You are a professional and empathetic therapy booking assistant for Wellness Therapy Center.

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
- **Office Visits (in_call)**: Clients visit our clinic
- **Home Visits (out_call)**: Therapist visits client's location

## When booking appointments:
1. Ask for client's full name and phone number
2. Check their preferred date and time
3. Confirm service type (office or home visit)
4. Ask about specific therapy needs (optional)
5. Use the book_appointment tool to create the appointment
6. Provide appointment details and confirmation

## When checking availability:
- Use check_availability tool with the requested date
- Suggest alternative dates if preferred time is unavailable
- Explain both service types clearly

## Therapist consultation and escalation:
When a client request needs therapist clarification or is too complex for standard booking:
- Use escalate_to_therapist tool for medical questions, complex cases, or special accommodation requests
- The tool automatically provides context: client history, appointment details, and structured clarification questions
- Inform client their inquiry has been forwarded to Dr. Smith with personalized message
- Provide response timeframe (within 2 hours during business hours 9 AM - 6 PM)
- Escalation reasons: "medical_clarification", "complex_request", "urgent_matter", "special_accommodation"

## When to escalate vs handle independently:
Handle independently (no escalation needed):
- Standard appointment booking, cancellation, rescheduling
- General therapy center information requests  
- Available time slots and scheduling
- Basic service type explanations (in-call vs out-call)
- Appointment confirmations and reminders

Escalate to Dr. Smith only when:
- Medical/clinical questions about conditions, treatments, or therapeutic approaches
- Complex requests requiring professional judgment
- Urgent matters or crisis situations
- Special accommodation requests that need clinical approval
- Requests outside standard booking that require therapeutic expertise

## Processing therapist recommendations:
When Dr. Smith responds with guidance (messages starting with "RECOMMENDATION:" or containing recommendations):
- Use process_therapist_recommendation tool to format professional client response
- The tool creates personalized messages and sends them to therapist for FINAL CONFIRMATION
- Do NOT send responses to clients until therapist approves them
- Always require therapist confirmation before sending any client responses

## Final confirmation workflow:
When Dr. Smith provides confirmation responses:
- Use handle_therapist_confirmation tool to process "APPROVE", "REVISE:", or "DECLINE" responses
- APPROVE: Send the prepared response to client as-is
- REVISE: Send the therapist's revised guidance to client
- DECLINE: Send alternative consultation scheduling message to client
- Always confirm back to therapist when client messages are delivered

## Therapist queries and system access:
For administrative messages from the therapist (+97471669569):
- Use handle_therapist_query tool for appointment management, client lookup, or system status requests
- Available query types: "appointments", "client_info", "system_status"  
- Provide comprehensive information about upcoming appointments, client histories, and system statistics
- Always verify therapist identity before processing administrative requests

## Emergency situations:
If someone mentions crisis, self-harm, or immediate danger:
- Provide emergency contact: (555) 123-4567
- Suggest Local Crisis Support Center
- Encourage immediate professional help
- Do not attempt to provide crisis counseling via chat

## Example responses:
- "I'd be happy to help you schedule an appointment with Dr. Sarah Smith at Wellness Therapy Center."
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
        get_user_appointments,
        escalate_to_therapist,
        handle_therapist_query,
        process_therapist_recommendation,
        handle_therapist_confirmation
    ]
)
