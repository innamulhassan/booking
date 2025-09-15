"""
Standalone Therapy Booking Agent using Google Agent Development Kit (ADK)

This is a simplified version for testing ADK integration without external dependencies.
"""

import datetime
import json
from typing import Dict, List, Optional
from google.adk.agents import Agent

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
        
        # Mock available slots (in a real implementation, this would check the database)
        mock_available_slots = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
        
        return {
            "status": "success",
            "date": date,
            "service_type": service_type,
            "available_slots": mock_available_slots,
            "message": f"Found {len(mock_available_slots)} available slots for {date}"
        }
        
    except ValueError:
        return {
            "status": "error",
            "error_message": f"Invalid date format. Please use YYYY-MM-DD format (e.g., 2025-01-15)"
        }
    except Exception as e:
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
        
        # Generate mock appointment ID
        appointment_id = abs(hash(f"{client_phone}_{date}_{time}")) % 10000
        
        return {
            "status": "success",
            "appointment_id": appointment_id,
            "client_name": client_name,
            "client_phone": client_phone,
            "date": date,
            "time": time,
            "service_type": service_type,
            "appointment_status": "pending",
            "message": f"Appointment booked successfully! Appointment ID: {appointment_id}. Status: Pending confirmation."
        }
        
    except ValueError as e:
        return {
            "status": "error",
            "error_message": f"Invalid date or time format: {str(e)}"
        }
    except Exception as e:
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
        
        return {
            "status": "success",
            "appointment_id": appointment_id,
            "new_status": "cancelled",
            "reason": reason,
            "message": f"Appointment {appointment_id} has been cancelled successfully."
        }
        
    except Exception as e:
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
        
        return {
            "status": "success",
            "appointment_id": appointment_id,
            "new_date": new_date,
            "new_time": new_time,
            "appointment_status": "confirmed",
            "notes": notes,
            "message": f"Appointment {appointment_id} has been rescheduled to {new_date} at {new_time}."
        }
        
    except ValueError as e:
        return {
            "status": "error",
            "error_message": f"Invalid date or time format: {str(e)}"
        }
    except Exception as e:
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
        if not client_phone:
            return {
                "status": "error",
                "error_message": "Phone number is required"
            }
        
        # Mock appointments data
        mock_appointments = [
            {
                "appointment_id": 1234,
                "date": "2025-01-15",
                "time": "10:00",
                "service_type": "in_call",
                "status": "confirmed",
                "therapist_name": "Dr. Sarah Smith",
                "description": "Initial consultation"
            },
            {
                "appointment_id": 5678,
                "date": "2025-01-22", 
                "time": "14:00",
                "service_type": "in_call",
                "status": "pending",
                "therapist_name": "Dr. Sarah Smith",
                "description": "Follow-up session"
            }
        ]
        
        # Filter by status if provided
        if status:
            filtered_appointments = [apt for apt in mock_appointments if apt["status"] == status]
        else:
            filtered_appointments = mock_appointments
        
        return {
            "status": "success",
            "client_phone": client_phone,
            "appointments": filtered_appointments,
            "total_appointments": len(filtered_appointments)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error retrieving appointments: {str(e)}"
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
- **Office Visits (in_call)**: Clients visit our clinic at 123 Health Street, Wellness City
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
- Provide emergency contact: (555) 123-4567
- Suggest Local Crisis Support Center
- Encourage immediate professional help
- Do not attempt to provide crisis counseling via chat

## Business Hours:
- Monday-Friday: 9:00 AM - 6:00 PM
- Saturday: 9:00 AM - 2:00 PM
- Sunday: Closed

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
        get_user_appointments
    ]
)
