from sqlalchemy.orm import Session
from app.models.models import User, Appointment, Conversation, Message, UserRole, ServiceType, AppointmentStatus, ConversationType
from app.models.schemas import UserCreate, AppointmentCreate
from datetime import datetime, timedelta
from typing import List, Optional
import uuid
import logging

logger = logging.getLogger(__name__)

class BookingService:
    
    def get_or_create_user(self, db: Session, phone_number: str, role: str, name: str = None) -> User:
        """Get existing user or create new one"""
        try:
            # Check if user exists
            user = db.query(User).filter(User.phone_number == phone_number).first()
            
            if not user:
                # Create new user
                user_role = UserRole.CLIENT if role == "client" else UserRole.THERAPIST
                display_name = name or f"{role.title()} {phone_number[-4:]}"
                
                user = User(
                    phone_number=phone_number,
                    name=display_name,
                    role=user_role
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                
                logger.info(f"Created new {role}: {phone_number}")
            
            return user
            
        except Exception as e:
            logger.error(f"Error getting/creating user: {str(e)}")
            db.rollback()
            raise
    
    def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    def get_or_create_conversation(self, db: Session, user_id: int, conversation_type: str) -> Conversation:
        """Get active conversation or create new one"""
        try:
            conv_type = ConversationType.CLIENT_BOT if conversation_type == "client_bot" else ConversationType.THERAPIST_BOT
            
            # Check for active conversation
            conversation = db.query(Conversation).filter(
                Conversation.user_id == user_id,
                Conversation.conversation_type == conv_type,
                Conversation.is_active == True
            ).first()
            
            if not conversation:
                # Create new conversation
                session_id = str(uuid.uuid4())
                conversation = Conversation(
                    user_id=user_id,
                    conversation_type=conv_type,
                    session_id=session_id,
                    is_active=True
                )
                db.add(conversation)
                db.commit()
                db.refresh(conversation)
                
                logger.info(f"Created new conversation for user {user_id}")
            
            return conversation
            
        except Exception as e:
            logger.error(f"Error getting/creating conversation: {str(e)}")
            db.rollback()
            raise
    
    def save_message(self, db: Session, conversation_id: int, sender: str, message_text: str, whatsapp_message_id: str = None):
        """Save message to database"""
        try:
            message = Message(
                conversation_id=conversation_id,
                sender=sender,
                message_text=message_text,
                whatsapp_message_id=whatsapp_message_id
            )
            db.add(message)
            db.commit()
            db.refresh(message)
            
            return message
            
        except Exception as e:
            logger.error(f"Error saving message: {str(e)}")
            db.rollback()
            raise
    
    def create_pending_appointment(self, db: Session, client_id: int, booking_data: dict) -> Appointment:
        """Create a pending appointment"""
        try:
            # Get default therapist (in a real app, you might have logic to assign therapists)
            therapist = db.query(User).filter(User.role == UserRole.THERAPIST).first()
            
            if not therapist:
                raise Exception("No therapist available")
            
            # Parse datetime
            preferred_datetime = self._parse_datetime(booking_data['datetime'])
            
            # Create appointment
            service_type = ServiceType.IN_CALL if booking_data['service_type'] == 'in_call' else ServiceType.OUT_CALL
            
            appointment = Appointment(
                client_id=client_id,
                therapist_id=therapist.id,
                service_type=service_type,
                preferred_datetime=preferred_datetime,
                status=AppointmentStatus.PENDING,
                service_description=booking_data.get('description', '')
            )
            
            db.add(appointment)
            db.commit()
            db.refresh(appointment)
            
            logger.info(f"Created pending appointment {appointment.id}")
            return appointment
            
        except Exception as e:
            logger.error(f"Error creating appointment: {str(e)}")
            db.rollback()
            raise
    
    def confirm_appointment(self, db: Session, appointment_id: int) -> Appointment:
        """Confirm an appointment"""
        try:
            appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
            
            if not appointment:
                raise Exception("Appointment not found")
            
            appointment.status = AppointmentStatus.CONFIRMED
            appointment.confirmed_datetime = appointment.preferred_datetime
            
            db.commit()
            db.refresh(appointment)
            
            logger.info(f"Confirmed appointment {appointment_id}")
            return appointment
            
        except Exception as e:
            logger.error(f"Error confirming appointment: {str(e)}")
            db.rollback()
            raise
    
    def get_latest_pending_appointment(self, db: Session, therapist_id: int) -> Optional[Appointment]:
        """Get the most recent pending appointment for a therapist"""
        return db.query(Appointment).filter(
            Appointment.therapist_id == therapist_id,
            Appointment.status == AppointmentStatus.PENDING
        ).order_by(Appointment.created_at.desc()).first()
    
    def get_user_appointments(self, db: Session, user_id: int, status: str = None) -> List[Appointment]:
        """Get appointments for a user"""
        query = db.query(Appointment).filter(
            (Appointment.client_id == user_id) | (Appointment.therapist_id == user_id)
        )
        
        if status:
            query = query.filter(Appointment.status == AppointmentStatus(status))
        
        return query.order_by(Appointment.preferred_datetime.desc()).all()
    
    def get_available_slots(self, db: Session, date_str: str) -> List[str]:
        """Get available time slots for a given date"""
        try:
            # Parse the date
            target_date = datetime.strptime(date_str.split('T')[0], '%Y-%m-%d').date()
            
            # Define business hours (9 AM to 6 PM)
            business_start = 9
            business_end = 18
            slot_duration = 1  # 1 hour slots
            
            # Get existing appointments for the date
            existing_appointments = db.query(Appointment).filter(
                Appointment.preferred_datetime >= datetime.combine(target_date, datetime.min.time()),
                Appointment.preferred_datetime < datetime.combine(target_date, datetime.min.time()) + timedelta(days=1),
                Appointment.status.in_([AppointmentStatus.CONFIRMED, AppointmentStatus.PENDING])
            ).all()
            
            # Generate all possible slots
            available_slots = []
            for hour in range(business_start, business_end):
                slot_time = f"{hour:02d}:00"
                slot_datetime = datetime.combine(target_date, datetime.strptime(slot_time, '%H:%M').time())
                
                # Check if slot is available
                is_available = True
                for appointment in existing_appointments:
                    if abs((appointment.preferred_datetime - slot_datetime).total_seconds()) < 3600:  # 1 hour buffer
                        is_available = False
                        break
                
                if is_available:
                    available_slots.append(slot_time)
            
            return available_slots
            
        except Exception as e:
            logger.error(f"Error getting available slots: {str(e)}")
            return []
    
    def reschedule_appointment(self, db: Session, appointment_id: int, new_datetime: datetime, notes: str = None) -> Appointment:
        """Reschedule an appointment"""
        try:
            appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
            
            if not appointment:
                raise Exception("Appointment not found")
            
            appointment.preferred_datetime = new_datetime
            appointment.confirmed_datetime = new_datetime
            appointment.status = AppointmentStatus.CONFIRMED
            
            if notes:
                appointment.therapist_notes = notes
            
            db.commit()
            db.refresh(appointment)
            
            logger.info(f"Rescheduled appointment {appointment_id}")
            return appointment
            
        except Exception as e:
            logger.error(f"Error rescheduling appointment: {str(e)}")
            db.rollback()
            raise
    
    def cancel_appointment(self, db: Session, appointment_id: int, reason: str = None) -> Appointment:
        """Cancel an appointment"""
        try:
            appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
            
            if not appointment:
                raise Exception("Appointment not found")
            
            appointment.status = AppointmentStatus.CANCELLED
            
            if reason:
                appointment.therapist_notes = f"Cancelled: {reason}"
            
            db.commit()
            db.refresh(appointment)
            
            logger.info(f"Cancelled appointment {appointment_id}")
            return appointment
            
        except Exception as e:
            logger.error(f"Error cancelling appointment: {str(e)}")
            db.rollback()
            raise
    
    def _parse_datetime(self, datetime_str: str) -> datetime:
        """Parse datetime string to datetime object"""
        try:
            # Try different datetime formats
            formats = [
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M',
                '%d/%m/%Y %H:%M',
                '%m/%d/%Y %H:%M'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(datetime_str, fmt)
                except ValueError:
                    continue
            
            # If no format matches, try to parse date only and add default time
            try:
                date_part = datetime_str.split('T')[0] if 'T' in datetime_str else datetime_str.split(' ')[0]
                parsed_date = datetime.strptime(date_part, '%Y-%m-%d')
                return parsed_date.replace(hour=10, minute=0)  # Default to 10 AM
            except ValueError:
                pass
            
            # Last resort: use current time + 1 day
            return datetime.now() + timedelta(days=1)
            
        except Exception as e:
            logger.error(f"Error parsing datetime '{datetime_str}': {str(e)}")
            return datetime.now() + timedelta(days=1)

# Create global instance
booking_service = BookingService()
