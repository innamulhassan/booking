"""
Enhanced booking service with proper business logic separation.
Handles appointment creation, validation, and state management.
"""
import logging
from typing import Dict, Optional, Any, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

# Legacy imports for backward compatibility
from sqlalchemy.orm import Session
from app.models.models import User, Appointment, Conversation, Message, UserRole, ServiceType, AppointmentStatus, ConversationType
from app.models.schemas import UserCreate, AppointmentCreate
import uuid

logger = logging.getLogger(__name__)


class ModernAppointmentStatus(Enum):
    """Modern appointment status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed" 
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class BookingValidationError(Exception):
    """Custom exception for booking validation errors."""
    pass


@dataclass
class BookingRequest:
    """Structured booking request data."""
    client_name: str
    client_phone: str
    service_name: str
    appointment_date: str
    appointment_time: str
    therapist_name: str
    price: float
    description: Optional[str] = None
    extra_services: Optional[str] = None
    
    def validate(self) -> List[str]:
        """Validate booking request data."""
        errors = []
        
        # Required field validation
        if not self.client_name or len(self.client_name.strip()) < 2:
            errors.append("Client name must be at least 2 characters")
        
        if not self.client_phone:
            errors.append("Client phone number is required")
        elif not self._validate_phone(self.client_phone):
            errors.append("Invalid phone number format")
        
        if not self.service_name:
            errors.append("Service name is required")
        
        if not self.appointment_date:
            errors.append("Appointment date is required")
        elif not self._validate_date(self.appointment_date):
            errors.append("Invalid appointment date format")
        
        if not self.appointment_time:
            errors.append("Appointment time is required")
        elif not self._validate_time(self.appointment_time):
            errors.append("Invalid appointment time format")
        
        if not self.therapist_name:
            errors.append("Therapist name is required")
        
        if self.price is None or self.price < 0:
            errors.append("Price must be a non-negative number")
        
        return errors
    
    def _validate_phone(self, phone: str) -> bool:
        """Validate phone number format."""
        if not phone:
            return False
        
        # Remove common formatting characters
        cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
        
        # Must start with + and have 10-15 digits
        if not cleaned.startswith('+'):
            return False
        
        digits = cleaned[1:]  # Remove the +
        return len(digits) >= 10 and len(digits) <= 15 and digits.isdigit()
    
    def _validate_date(self, date_str: str) -> bool:
        """Validate date format (YYYY-MM-DD)."""
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False
    
    def _validate_time(self, time_str: str) -> bool:
        """Validate time format (HH:MM)."""
        try:
            datetime.strptime(time_str, '%H:%M')
            return True
        except ValueError:
            return False


@dataclass
class AppointmentRecord:
    """Database appointment record structure."""
    id: Optional[int]
    client_name: str
    client_phone: str
    service_name: str
    appointment_date: str
    appointment_time: str
    therapist_name: str
    price: float
    status: ModernAppointmentStatus
    description: Optional[str] = None
    extra_services: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'client_name': self.client_name,
            'client_phone': self.client_phone,
            'service_name': self.service_name,
            'appointment_date': self.appointment_date,
            'appointment_time': self.appointment_time,
            'therapist_name': self.therapist_name,
            'price': self.price,
            'status': self.status.value,
            'description': self.description,
            'extra_services': self.extra_services,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class BookingService:
    
    def get_or_create_user(self, db: Session, phone_number: str, role: str, name: str = None) -> User:
        """Get existing user or create new one"""
        try:
            # Check if user exists
            user = db.query(User).filter(User.phone_number == phone_number).first()
            
            if not user:
                # Create new user
                if role == "client":
                    user_role = UserRole.CLIENT
                elif role == "coordinator":
                    user_role = UserRole.COORDINATOR
                elif role == "therapist":
                    user_role = UserRole.THERAPIST
                else:
                    user_role = UserRole.CLIENT  # Default fallback
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
        """Create a pending appointment with therapist and main service"""
        try:
            # Parse datetime
            preferred_datetime = self._parse_datetime(booking_data['datetime'])
            
            # Create appointment with new fields
            service_type = ServiceType.IN_CALL if booking_data['service_type'] == 'in_call' else ServiceType.OUT_CALL
            
            appointment = Appointment(
                client_id=client_id,
                therapist_id=booking_data.get('therapist_id'),
                service_type=service_type,
                preferred_datetime=preferred_datetime,
                status=AppointmentStatus.PENDING,
                service_description=booking_data.get('service_description', booking_data.get('description', ''))
            )
            
            db.add(appointment)
            db.commit()
            db.refresh(appointment)
            
            logger.info(f"Created pending appointment {appointment.id} with therapist {booking_data.get('therapist_id')} for service: {booking_data.get('service_description', 'Not specified')}")
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
    
    def get_latest_pending_appointment(self, db: Session, coordinator_id: int) -> Optional[Appointment]:
        """Get the most recent pending appointment for a coordinator"""
        return db.query(Appointment).filter(
            Appointment.coordinator_id == coordinator_id,
            Appointment.status == AppointmentStatus.PENDING
        ).order_by(Appointment.created_at.desc()).first()
    
    def get_user_appointments(self, db: Session, user_id: int, status: str = None) -> List[Appointment]:
        """Get appointments for a user"""
        query = db.query(Appointment).filter(
            (Appointment.client_id == user_id) | (Appointment.coordinator_id == user_id)
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
    
    # =====================================================
    # NEW ENHANCED BOOKING METHODS
    # =====================================================
    
    def __init__(self):
        self._business_hours = {
            'start_time': '09:00',
            'end_time': '18:00',
            'days': [0, 1, 2, 3, 4, 5, 6]  # Monday=0, Sunday=6
        }
        self._appointment_duration_minutes = 60
        self._advance_booking_days = 30
    
    async def create_modern_appointment(self, booking_request: BookingRequest) -> Tuple[bool, Dict[str, Any]]:
        """
        Create a new appointment with enhanced validation.
        
        Args:
            booking_request: Validated booking request data
            
        Returns:
            Tuple of (success, result_data)
        """
        try:
            # Validate request
            validation_errors = booking_request.validate()
            if validation_errors:
                return False, {
                    'error': 'Validation failed',
                    'details': validation_errors
                }
            
            # Business rule validation
            business_errors = await self._validate_business_rules(booking_request)
            if business_errors:
                return False, {
                    'error': 'Business rule validation failed',
                    'details': business_errors
                }
            
            # Save to database using new structure
            appointment_id = await self._save_modern_appointment(booking_request)
            
            if appointment_id:
                appointment_record = await self.get_modern_appointment(appointment_id)
                return True, {
                    'appointment_id': appointment_id,
                    'appointment': appointment_record.to_dict() if appointment_record else None,
                    'status': 'pending_approval'
                }
            else:
                return False, {
                    'error': 'Failed to create appointment',
                    'details': ['Database operation failed']
                }
                
        except Exception as e:
            logger.error(f"Error creating modern appointment: {e}")
            return False, {
                'error': 'Internal error',
                'details': [str(e)]
            }
    
    async def _validate_business_rules(self, booking_request: BookingRequest) -> List[str]:
        """Validate business rules for appointment."""
        errors = []
        
        # Check if appointment is in the future
        try:
            appointment_datetime = datetime.strptime(
                f"{booking_request.appointment_date} {booking_request.appointment_time}",
                '%Y-%m-%d %H:%M'
            )
            
            now = datetime.now()
            if appointment_datetime <= now:
                errors.append("Appointment must be scheduled for a future date and time")
            
            # Check advance booking limit
            max_advance = now + timedelta(days=self._advance_booking_days)
            if appointment_datetime > max_advance:
                errors.append(f"Cannot book more than {self._advance_booking_days} days in advance")
        
        except ValueError as e:
            errors.append(f"Invalid date/time format: {e}")
        
        # Check business hours
        if not self._is_within_business_hours(booking_request.appointment_time):
            start = self._business_hours['start_time']
            end = self._business_hours['end_time']
            errors.append(f"Appointment must be within business hours ({start} - {end})")
        
        return errors
    
    def _is_within_business_hours(self, time_str: str) -> bool:
        """Check if time is within business hours."""
        try:
            appointment_time = datetime.strptime(time_str, '%H:%M').time()
            start_time = datetime.strptime(self._business_hours['start_time'], '%H:%M').time()
            end_time = datetime.strptime(self._business_hours['end_time'], '%H:%M').time()
            
            return start_time <= appointment_time <= end_time
        except ValueError:
            return False
    
    async def _save_modern_appointment(self, booking_request: BookingRequest) -> Optional[int]:
        """Save appointment to database with modern structure."""
        try:
            # This would need to be adapted to your actual database structure
            # For now, using a placeholder that matches the expected interface
            from app.core.database import get_db
            
            # Convert to legacy format for compatibility
            db = next(get_db())
            
            # Find or create client user
            client = self.get_or_create_user(db, booking_request.client_phone, "client", booking_request.client_name)
            
            # Create appointment data in legacy format
            booking_data = {
                'datetime': f"{booking_request.appointment_date}T{booking_request.appointment_time}:00",
                'service_type': 'in_call',  # Default
                'service_description': booking_request.service_name,
                'description': booking_request.description or '',
                'therapist_id': 1  # Default therapist ID - would need proper lookup
            }
            
            appointment = self.create_pending_appointment(db, client.id, booking_data)
            return appointment.id
            
        except Exception as e:
            logger.error(f"Error saving modern appointment: {e}")
            return None
    
    async def get_modern_appointment(self, appointment_id: int) -> Optional[AppointmentRecord]:
        """Get appointment by ID in modern format."""
        try:
            from app.core.database import get_db
            
            db = next(get_db())
            appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
            
            if appointment:
                # Convert legacy appointment to modern format
                client = self.get_user_by_id(db, appointment.client_id)
                
                return AppointmentRecord(
                    id=appointment.id,
                    client_name=client.name if client else "Unknown",
                    client_phone=client.phone_number if client else "Unknown",
                    service_name=appointment.service_description or "General Service",
                    appointment_date=appointment.preferred_datetime.strftime('%Y-%m-%d'),
                    appointment_time=appointment.preferred_datetime.strftime('%H:%M'),
                    therapist_name="Dr. Sarah",  # Default - would need proper lookup
                    price=150.0,  # Default price - would need proper calculation
                    status=ModernAppointmentStatus.PENDING if appointment.status == AppointmentStatus.PENDING else ModernAppointmentStatus.CONFIRMED,
                    description=appointment.service_description,
                    extra_services=None,
                    created_at=appointment.created_at,
                    updated_at=appointment.updated_at
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting modern appointment {appointment_id}: {e}")
            return None
    
    async def update_modern_appointment_status(self, appointment_id: int, status: ModernAppointmentStatus, notes: Optional[str] = None) -> bool:
        """Update appointment status."""
        try:
            from app.core.database import get_db
            
            db = next(get_db())
            appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
            
            if appointment:
                # Convert modern status to legacy status
                if status == ModernAppointmentStatus.CONFIRMED:
                    appointment.status = AppointmentStatus.CONFIRMED
                elif status == ModernAppointmentStatus.CANCELLED:
                    appointment.status = AppointmentStatus.CANCELLED
                elif status == ModernAppointmentStatus.COMPLETED:
                    appointment.status = AppointmentStatus.CONFIRMED  # No completed status in legacy
                
                db.commit()
                logger.info(f"Modern appointment {appointment_id} status updated to {status.value}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating modern appointment status: {e}")
            return False
    
    async def approve_modern_appointment(self, appointment_id: int) -> Tuple[bool, Optional[AppointmentRecord]]:
        """Approve an appointment."""
        success = await self.update_modern_appointment_status(appointment_id, ModernAppointmentStatus.CONFIRMED)
        if success:
            appointment = await self.get_modern_appointment(appointment_id)
            return True, appointment
        return False, None
    
    async def decline_modern_appointment(self, appointment_id: int, reason: Optional[str] = None) -> bool:
        """Decline an appointment."""
        success = await self.update_modern_appointment_status(appointment_id, ModernAppointmentStatus.CANCELLED, reason)
        return success
    
    def get_modern_booking_summary(self, appointment: AppointmentRecord) -> Dict[str, Any]:
        """Get formatted booking summary for notifications."""
        return {
            'appointment_id': appointment.id,
            'client_name': appointment.client_name,
            'client_phone': appointment.client_phone,
            'service_name': appointment.service_name,
            'service_description': appointment.service_name,
            'appointment_date': appointment.appointment_date,
            'appointment_time': appointment.appointment_time,
            'therapist_name': appointment.therapist_name,
            'price': appointment.price,
            'description': appointment.description or 'No additional notes',
            'extra_services': appointment.extra_services or 'None',
            'status': appointment.status.value
        }

# Create global instance
booking_service = BookingService()
