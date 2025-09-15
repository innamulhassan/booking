from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.models import User, Appointment, UserRole, AppointmentStatus
from app.models.schemas import AppointmentResponse, TherapistResponse
from app.services.booking_service import booking_service
from app.services.ultramsg_service import ultramsg_service
from typing import List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/therapist", tags=["therapist"])

@router.get("/appointments", response_model=List[AppointmentResponse])
async def get_therapist_appointments(
    therapist_phone: str = Query(..., description="Therapist's phone number"),
    status: Optional[str] = Query(None, description="Filter by appointment status"),
    date_from: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get therapist's appointments with optional filtering"""
    try:
        # Get therapist user
        therapist = db.query(User).filter(
            User.phone_number == therapist_phone,
            User.role == UserRole.THERAPIST
        ).first()
        
        if not therapist:
            raise HTTPException(status_code=404, detail="Therapist not found")
        
        # Build query
        query = db.query(Appointment).filter(Appointment.therapist_id == therapist.id)
        
        # Apply filters
        if status:
            query = query.filter(Appointment.status == AppointmentStatus(status))
        
        if date_from:
            from_date = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Appointment.preferred_datetime >= from_date)
        
        if date_to:
            to_date = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Appointment.preferred_datetime < to_date)
        
        appointments = query.order_by(Appointment.preferred_datetime.asc()).all()
        
        return appointments
        
    except Exception as e:
        logger.error(f"Error getting therapist appointments: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/pending-clients")
async def get_pending_clients(
    therapist_phone: str = Query(..., description="Therapist's phone number"),
    db: Session = Depends(get_db)
):
    """Get list of clients with pending appointments"""
    try:
        # Get therapist user
        therapist = db.query(User).filter(
            User.phone_number == therapist_phone,
            User.role == UserRole.THERAPIST
        ).first()
        
        if not therapist:
            raise HTTPException(status_code=404, detail="Therapist not found")
        
        # Get pending appointments
        pending_appointments = db.query(Appointment).filter(
            Appointment.therapist_id == therapist.id,
            Appointment.status == AppointmentStatus.PENDING
        ).order_by(Appointment.created_at.desc()).all()
        
        # Format response
        clients = []
        for appointment in pending_appointments:
            clients.append({
                "appointment_id": appointment.id,
                "client_name": appointment.client.name,
                "client_phone": appointment.client.phone_number,
                "service_type": appointment.service_type.value,
                "preferred_datetime": appointment.preferred_datetime.isoformat(),
                "service_description": appointment.service_description,
                "created_at": appointment.created_at.isoformat()
            })
        
        return {"pending_clients": clients}
        
    except Exception as e:
        logger.error(f"Error getting pending clients: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/respond-appointment")
async def respond_to_appointment(
    response: TherapistResponse,
    therapist_phone: str = Query(..., description="Therapist's phone number"),
    db: Session = Depends(get_db)
):
    """Handle therapist response to appointment request"""
    try:
        # Get therapist user
        therapist = db.query(User).filter(
            User.phone_number == therapist_phone,
            User.role == UserRole.THERAPIST
        ).first()
        
        if not therapist:
            raise HTTPException(status_code=404, detail="Therapist not found")
        
        # Get appointment
        appointment = db.query(Appointment).filter(
            Appointment.id == response.appointment_id,
            Appointment.therapist_id == therapist.id
        ).first()
        
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        # Handle different response types
        if response.response_type == "confirm":
            appointment = booking_service.confirm_appointment(db, appointment.id)
            
            # Notify client
            client_message = f"""
✅ *Appointment Confirmed!*

Your therapy session has been confirmed:
📅 **Date & Time:** {appointment.confirmed_datetime.strftime('%Y-%m-%d at %H:%M')}
🏥 **Service:** {'In-call' if appointment.service_type.value == 'in_call' else 'Out-call'}

Your therapist will contact you if any additional details are needed. Looking forward to your session!
            """.strip()
            
            ultramsg_service.send_to_client(appointment.client.phone_number, client_message)
            
            return {"message": "Appointment confirmed successfully"}
            
        elif response.response_type == "reschedule" and response.new_datetime:
            appointment = booking_service.reschedule_appointment(
                db, appointment.id, response.new_datetime, response.notes
            )
            
            # Notify client
            client_message = f"""
📅 *Appointment Rescheduled*

Your therapist has suggested a new time for your appointment:

**New Date & Time:** {response.new_datetime.strftime('%Y-%m-%d at %H:%M')}
🏥 **Service:** {'In-call' if appointment.service_type.value == 'in_call' else 'Out-call'}

{f'**Note from therapist:** {response.notes}' if response.notes else ''}

Please reply "ACCEPT" to confirm this new time or suggest an alternative.
            """.strip()
            
            ultramsg_service.send_to_client(appointment.client.phone_number, client_message)
            
            return {"message": "Appointment rescheduled successfully"}
            
        elif response.response_type == "decline":
            appointment = booking_service.cancel_appointment(db, appointment.id, response.notes)
            
            # Notify client
            client_message = f"""
❌ *Appointment Not Available*

Unfortunately, your requested appointment time is not available.

{f'**Reason:** {response.notes}' if response.notes else ''}

Would you like to:
1. See available alternative times
2. Provide new preferred times
3. Speak with our booking team

Please let me know how you'd like to proceed!
            """.strip()
            
            ultramsg_service.send_to_client(appointment.client.phone_number, client_message)
            
            return {"message": "Appointment declined successfully"}
        
        else:
            raise HTTPException(status_code=400, detail="Invalid response type")
            
    except Exception as e:
        logger.error(f"Error responding to appointment: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/schedule")
async def get_therapist_schedule(
    therapist_phone: str = Query(..., description="Therapist's phone number"),
    days: int = Query(7, description="Number of days to show"),
    db: Session = Depends(get_db)
):
    """Get therapist's schedule for the next N days"""
    try:
        # Get therapist user
        therapist = db.query(User).filter(
            User.phone_number == therapist_phone,
            User.role == UserRole.THERAPIST
        ).first()
        
        if not therapist:
            raise HTTPException(status_code=404, detail="Therapist not found")
        
        # Get appointments for the next N days
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=days)
        
        appointments = db.query(Appointment).filter(
            Appointment.therapist_id == therapist.id,
            Appointment.preferred_datetime >= start_date,
            Appointment.preferred_datetime < end_date,
            Appointment.status.in_([AppointmentStatus.CONFIRMED, AppointmentStatus.PENDING])
        ).order_by(Appointment.preferred_datetime.asc()).all()
        
        # Group by date
        schedule = {}
        for appointment in appointments:
            date_key = appointment.preferred_datetime.date().isoformat()
            if date_key not in schedule:
                schedule[date_key] = []
            
            schedule[date_key].append({
                "id": appointment.id,
                "time": appointment.preferred_datetime.time().isoformat(),
                "client_name": appointment.client.name,
                "client_phone": appointment.client.phone_number,
                "service_type": appointment.service_type.value,
                "status": appointment.status.value,
                "description": appointment.service_description
            })
        
        return {"schedule": schedule, "days_shown": days}
        
    except Exception as e:
        logger.error(f"Error getting therapist schedule: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Add these methods to the DialogflowService class for therapist message handling
async def get_therapist_schedule_text(therapist_id: int, db: Session) -> str:
    """Get formatted schedule text for therapist"""
    try:
        # Get appointments for next 7 days
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=7)
        
        appointments = db.query(Appointment).filter(
            Appointment.therapist_id == therapist_id,
            Appointment.preferred_datetime >= start_date,
            Appointment.preferred_datetime < end_date,
            Appointment.status.in_([AppointmentStatus.CONFIRMED, AppointmentStatus.PENDING])
        ).order_by(Appointment.preferred_datetime.asc()).all()
        
        if not appointments:
            return "📅 Your schedule is clear for the next 7 days!"
        
        schedule_text = "📅 *Your Schedule (Next 7 Days)*\n\n"
        current_date = None
        
        for appointment in appointments:
            appointment_date = appointment.preferred_datetime.date()
            if current_date != appointment_date:
                current_date = appointment_date
                schedule_text += f"**{appointment_date.strftime('%A, %B %d')}**\n"
            
            time_str = appointment.preferred_datetime.strftime('%H:%M')
            status_emoji = "✅" if appointment.status == AppointmentStatus.CONFIRMED else "⏳"
            service_emoji = "🏠" if appointment.service_type.value == "in_call" else "🏥"
            
            schedule_text += f"{status_emoji} {time_str} - {appointment.client.name} {service_emoji}\n"
            schedule_text += f"   📱 {appointment.client.phone_number}\n"
            
            if appointment.service_description:
                schedule_text += f"   📝 {appointment.service_description}\n"
            
            schedule_text += "\n"
        
        return schedule_text.strip()
        
    except Exception as e:
        logger.error(f"Error getting therapist schedule text: {str(e)}")
        return "Sorry, I couldn't retrieve your schedule right now."

async def get_pending_clients_text(therapist_id: int, db: Session) -> str:
    """Get formatted pending clients text for therapist"""
    try:
        pending_appointments = db.query(Appointment).filter(
            Appointment.therapist_id == therapist_id,
            Appointment.status == AppointmentStatus.PENDING
        ).order_by(Appointment.created_at.desc()).all()
        
        if not pending_appointments:
            return "🎉 No pending appointment requests at the moment!"
        
        text = f"⏳ *Pending Appointment Requests ({len(pending_appointments)})*\n\n"
        
        for i, appointment in enumerate(pending_appointments, 1):
            service_emoji = "🏠" if appointment.service_type.value == "in_call" else "🏥"
            
            text += f"**{i}. {appointment.client.name}** {service_emoji}\n"
            text += f"📱 {appointment.client.phone_number}\n"
            text += f"📅 {appointment.preferred_datetime.strftime('%Y-%m-%d at %H:%M')}\n"
            
            if appointment.service_description:
                text += f"📝 {appointment.service_description}\n"
            
            text += f"🕒 Requested: {appointment.created_at.strftime('%H:%M today')}\n\n"
        
        text += "Reply 'CONFIRM', 'RESCHEDULE', or 'DECLINE' followed by details to respond."
        
        return text.strip()
        
    except Exception as e:
        logger.error(f"Error getting pending clients text: {str(e)}")
        return "Sorry, I couldn't retrieve pending appointments right now."
