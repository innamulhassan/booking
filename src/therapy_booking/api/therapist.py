"""
Therapist API endpoints
Migrated to new package structure with enhanced functionality and error handling.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import logging

# Import from new package structure
from ..models import get_db, User, Appointment, UserRole, AppointmentStatus
from ..models.schemas import AppointmentResponse, TherapistResponse
from ..services import booking_service
from ..external import ultramsg_service
from ..core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/therapist", tags=["therapist"])

# Get settings
settings = get_settings()

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
            try:
                query = query.filter(Appointment.status == AppointmentStatus(status))
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        if date_from:
            try:
                from_date = datetime.strptime(date_from, '%Y-%m-%d')
                query = query.filter(Appointment.preferred_datetime >= from_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_from format. Use YYYY-MM-DD")
        
        if date_to:
            try:
                to_date = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
                query = query.filter(Appointment.preferred_datetime < to_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_to format. Use YYYY-MM-DD")
        
        appointments = query.order_by(Appointment.preferred_datetime.asc()).all()
        
        return appointments
        
    except HTTPException:
        raise
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
                "service_type": appointment.service_type.value if appointment.service_type else "unknown",
                "preferred_datetime": appointment.preferred_datetime.isoformat(),
                "service_description": appointment.service_description,
                "created_at": appointment.created_at.isoformat(),
                "urgency_level": getattr(appointment, 'urgency_level', 'normal')
            })
        
        return {
            "pending_clients": clients,
            "total_count": len(clients),
            "therapist_name": therapist.name
        }
        
    except HTTPException:
        raise
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
        
        # Validate appointment is still pending
        if appointment.status != AppointmentStatus.PENDING:
            raise HTTPException(
                status_code=400, 
                detail=f"Appointment is already {appointment.status.value}"
            )
        
        # Handle different response types
        if response.response_type == "confirm":
            confirmed_datetime = response.new_datetime or appointment.preferred_datetime
            appointment = booking_service.update_appointment_status(
                db, appointment.id, AppointmentStatus.CONFIRMED
            )
            
            # Update confirmed datetime if provided
            if response.new_datetime:
                appointment.confirmed_datetime = response.new_datetime
                db.commit()
                db.refresh(appointment)
            
            # Prepare appointment data for notification
            appointment_data = {
                'appointment_id': appointment.id,
                'client_phone': appointment.client.phone_number,
                'client_name': appointment.client.name,
                'appointment_date': confirmed_datetime.strftime('%Y-%m-%d'),
                'appointment_time': confirmed_datetime.strftime('%H:%M'),
                'service_description': appointment.service_description or "therapy session",
                'therapist_name': therapist.name,
                'notes': response.notes
            }
            
            # Send confirmation notification
            try:
                await ultramsg_service.send_message(
                    f"+{appointment.client.phone_number}",
                    f"""✅ **Appointment Confirmed!**

Your therapy session has been confirmed:
📅 **Date & Time:** {confirmed_datetime.strftime('%B %d, %Y at %I:%M %p')}
👨‍⚕️ **Therapist:** {therapist.name}
🏥 **Service:** {appointment.service_description or 'Therapy session'}

{f'**Note:** {response.notes}' if response.notes else ''}

We look forward to your session! Please arrive 5 minutes early."""
                )
                logger.info(f"Confirmation sent to {appointment.client.phone_number}")
            except Exception as e:
                logger.error(f"Failed to send confirmation: {e}")
            
            return {
                "message": "Appointment confirmed successfully",
                "appointment_id": appointment.id,
                "confirmed_datetime": confirmed_datetime.isoformat()
            }
            
        elif response.response_type == "reschedule":
            if not response.new_datetime:
                raise HTTPException(status_code=400, detail="new_datetime is required for reschedule")
            
            # Update appointment with new datetime
            appointment.preferred_datetime = response.new_datetime
            appointment.status = AppointmentStatus.PENDING
            if response.notes:
                appointment.service_description = f"{appointment.service_description or ''}\n\nRescheduled: {response.notes}"
            db.commit()
            db.refresh(appointment)
            
            # Send reschedule notification
            try:
                await ultramsg_service.send_message(
                    f"+{appointment.client.phone_number}",
                    f"""📅 **Appointment Rescheduled**

Your therapist has suggested a new time:

**New Date & Time:** {response.new_datetime.strftime('%B %d, %Y at %I:%M %p')}
👨‍⚕️ **Therapist:** {therapist.name}
🏥 **Service:** {appointment.service_description or 'Therapy session'}

{f'**Note:** {response.notes}' if response.notes else ''}

Please reply "ACCEPT" to confirm this new time or suggest an alternative."""
                )
                logger.info(f"Reschedule notification sent to {appointment.client.phone_number}")
            except Exception as e:
                logger.error(f"Failed to send reschedule notification: {e}")
            
            return {
                "message": "Appointment rescheduled successfully",
                "appointment_id": appointment.id,
                "new_datetime": response.new_datetime.isoformat()
            }
            
        elif response.response_type == "decline":
            # Cancel the appointment
            appointment = booking_service.update_appointment_status(
                db, appointment.id, AppointmentStatus.CANCELLED, 
                f"Declined by therapist: {response.notes or 'No specific reason provided'}"
            )
            
            # Send decline notification
            try:
                await ultramsg_service.send_message(
                    f"+{appointment.client.phone_number}",
                    f"""❌ **Appointment Not Available**

Unfortunately, your requested appointment time is not available.

{f'**Reason:** {response.notes}' if response.notes else ''}

Would you like to:
1. 📅 See available alternative times
2. 🕒 Provide new preferred times
3. 📞 Speak with our booking team

Please let me know how you'd like to proceed!"""
                )
                logger.info(f"Decline notification sent to {appointment.client.phone_number}")
            except Exception as e:
                logger.error(f"Failed to send decline notification: {e}")
            
            return {
                "message": "Appointment declined successfully",
                "appointment_id": appointment.id
            }
        
        else:
            raise HTTPException(status_code=400, detail=f"Invalid response_type: {response.response_type}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error responding to appointment: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/schedule")
async def get_therapist_schedule(
    therapist_phone: str = Query(..., description="Therapist's phone number"),
    days: int = Query(7, description="Number of days to show", ge=1, le=30),
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
        total_appointments = 0
        
        for appointment in appointments:
            date_key = appointment.preferred_datetime.date().isoformat()
            if date_key not in schedule:
                schedule[date_key] = []
            
            schedule[date_key].append({
                "id": appointment.id,
                "time": appointment.preferred_datetime.time().isoformat(),
                "client_name": appointment.client.name,
                "client_phone": appointment.client.phone_number,
                "service_type": appointment.service_type.value if appointment.service_type else "unknown",
                "status": appointment.status.value,
                "description": appointment.service_description,
                "created_at": appointment.created_at.isoformat()
            })
            total_appointments += 1
        
        return {
            "schedule": schedule,
            "days_shown": days,
            "total_appointments": total_appointments,
            "therapist_name": therapist.name,
            "date_range": {
                "start": start_date.date().isoformat(),
                "end": (end_date - timedelta(days=1)).date().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting therapist schedule: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/stats")
async def get_therapist_stats(
    therapist_phone: str = Query(..., description="Therapist's phone number"),
    db: Session = Depends(get_db)
):
    """Get therapist's statistics and metrics"""
    try:
        # Get therapist user
        therapist = db.query(User).filter(
            User.phone_number == therapist_phone,
            User.role == UserRole.THERAPIST
        ).first()
        
        if not therapist:
            raise HTTPException(status_code=404, detail="Therapist not found")
        
        # Calculate various statistics
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # Today's appointments
        today_appointments = db.query(Appointment).filter(
            Appointment.therapist_id == therapist.id,
            Appointment.preferred_datetime >= today,
            Appointment.preferred_datetime < today + timedelta(days=1),
            Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED])
        ).count()
        
        # Pending appointments
        pending_count = db.query(Appointment).filter(
            Appointment.therapist_id == therapist.id,
            Appointment.status == AppointmentStatus.PENDING
        ).count()
        
        # This week's appointments
        week_appointments = db.query(Appointment).filter(
            Appointment.therapist_id == therapist.id,
            Appointment.preferred_datetime >= week_ago,
            Appointment.status == AppointmentStatus.CONFIRMED
        ).count()
        
        # This month's appointments
        month_appointments = db.query(Appointment).filter(
            Appointment.therapist_id == therapist.id,
            Appointment.preferred_datetime >= month_ago,
            Appointment.status == AppointmentStatus.CONFIRMED
        ).count()
        
        # Total clients served
        total_clients = db.query(Appointment.client_id).filter(
            Appointment.therapist_id == therapist.id,
            Appointment.status == AppointmentStatus.CONFIRMED
        ).distinct().count()
        
        return {
            "therapist_name": therapist.name,
            "therapist_phone": therapist.phone_number,
            "stats": {
                "today_appointments": today_appointments,
                "pending_appointments": pending_count,
                "week_appointments": week_appointments,
                "month_appointments": month_appointments,
                "total_clients_served": total_clients
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting therapist stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Utility functions for text-based responses
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
            service_emoji = "🏠" if appointment.service_type and appointment.service_type.value == "in_call" else "🏥"
            
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
            service_emoji = "🏠" if appointment.service_type and appointment.service_type.value == "in_call" else "🏥"
            
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