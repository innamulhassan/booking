"""
Enhanced booking service with proper business logic separation.
Migrated to new package structure with improved organization.
"""
import logging
from typing import Dict, Optional, Any, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import uuid

from sqlalchemy.orm import Session
from ..models import (
    User, Appointment, Conversation, Message, Therapist,
    UserRole, ServiceType, AppointmentStatus, ConversationType,
    UserCreate, AppointmentCreate
)

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
    """Enhanced booking service with modern architecture."""
    
    def __init__(self):
        self._business_hours = {
            'start_time': '09:00',
            'end_time': '18:00',
            'days': [0, 1, 2, 3, 4, 5, 6]  # Monday=0, Sunday=6
        }
        self._appointment_duration_minutes = 60
        self._advance_booking_days = 30
    
    def get_or_create_user(self, db: Session, phone_number: str, role: str, name: str = None) -> User:
        """Get existing user or create new one"""
        try:
            # Clean phone number
            cleaned_phone = phone_number.replace('whatsapp:', '').strip()
            
            # Check if user exists
            user = db.query(User).filter(User.phone_number == cleaned_phone).first()
            
            if not user:
                # Create new user
                if role == "client":
                    user_role = UserRole.CLIENT
                elif role == "coordinator":
                    user_role = UserRole.COORDINATOR
                elif role == "therapist":
                    user_role = UserRole.THERAPIST
                elif role == "admin":
                    user_role = UserRole.ADMIN
                else:
                    user_role = UserRole.CLIENT  # Default fallback
                    
                display_name = name or f"{role.title()} {cleaned_phone[-4:]}"
                
                user = User(
                    phone_number=cleaned_phone,
                    name=display_name,
                    role=user_role
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                
                logger.info(f"Created new {role}: {cleaned_phone}")
            
            return user
            
        except Exception as e:
            logger.error(f"Error getting/creating user: {str(e)}")
            db.rollback()
            raise
    
    def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_phone(self, db: Session, phone_number: str) -> Optional[User]:
        """Get user by phone number"""
        cleaned_phone = phone_number.replace('whatsapp:', '').strip()
        return db.query(User).filter(User.phone_number == cleaned_phone).first()
    
    def get_or_create_conversation(self, db: Session, user_id: int, conversation_type: str) -> Conversation:
        """Get active conversation or create new one"""
        try:
            # Map conversation type string to enum
            conv_type_mapping = {
                "booking": ConversationType.BOOKING,
                "support": ConversationType.SUPPORT,
                "general": ConversationType.GENERAL,
                "therapist_bot": ConversationType.THERAPIST_BOT,
                "client_bot": ConversationType.BOOKING,  # Legacy mapping
            }
            
            conv_type = conv_type_mapping.get(conversation_type, ConversationType.GENERAL)
            
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
                
                logger.info(f"Created new {conversation_type} conversation for user {user_id}")
            
            return conversation
            
        except Exception as e:
            logger.error(f"Error getting/creating conversation: {str(e)}")
            db.rollback()
            raise
    
    def save_message(self, db: Session, conversation_id: int, sender: str, message_text: str, whatsapp_message_id: str = None) -> Message:
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
            
            logger.info(f"Saved message from {sender} to conversation {conversation_id}")
            return message
            
        except Exception as e:
            logger.error(f"Error saving message: {str(e)}")
            db.rollback()
            raise
    
    def create_appointment(self, db: Session, client_id: int, booking_data: dict) -> Appointment:
        """Create a new appointment"""
        try:
            # Parse datetime
            preferred_datetime = self._parse_datetime(booking_data['datetime'])
            
            # Determine service type
            service_type = ServiceType.IN_CALL if booking_data.get('service_type') == 'in_call' else ServiceType.OUT_CALL
            
            # Create appointment
            appointment = Appointment(
                client_id=client_id,
                therapist_id=booking_data.get('therapist_id', 1),  # Default therapist
                service_type=service_type,
                preferred_datetime=preferred_datetime,
                status=AppointmentStatus.PENDING,
                service_description=booking_data.get('service_description', booking_data.get('description', '')),
                client_notes=booking_data.get('client_notes', '')
            )
            
            db.add(appointment)
            db.commit()
            db.refresh(appointment)
            
            logger.info(f"Created appointment {appointment.id} for client {client_id}")
            return appointment
            
        except Exception as e:
            logger.error(f"Error creating appointment: {str(e)}")
            db.rollback()
            raise
    
    def update_appointment_status(self, db: Session, appointment_id: int, status: AppointmentStatus, notes: str = None) -> Optional[Appointment]:
        """Update appointment status"""
        try:
            appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
            
            if not appointment:
                logger.warning(f"Appointment {appointment_id} not found")
                return None
            
            appointment.status = status
            if status == AppointmentStatus.CONFIRMED:
                appointment.confirmed_datetime = appointment.preferred_datetime
            
            if notes:
                appointment.therapist_notes = notes
            
            db.commit()
            db.refresh(appointment)
            
            logger.info(f"Updated appointment {appointment_id} status to {status.value}")
            return appointment
            
        except Exception as e:
            logger.error(f"Error updating appointment status: {str(e)}")
            db.rollback()
            raise
    
    def get_user_appointments(self, db: Session, user_id: int, status: AppointmentStatus = None) -> List[Appointment]:
        """Get appointments for a user"""
        query = db.query(Appointment).filter(Appointment.client_id == user_id)
        
        if status:
            query = query.filter(Appointment.status == status)
        
        return query.order_by(Appointment.preferred_datetime.desc()).all()
    
    def get_therapist_appointments(self, db: Session, therapist_id: int, status: AppointmentStatus = None) -> List[Appointment]:
        """Get appointments for a therapist"""
        query = db.query(Appointment).filter(Appointment.therapist_id == therapist_id)
        
        if status:
            query = query.filter(Appointment.status == status)
        
        return query.order_by(Appointment.preferred_datetime.desc()).all()
    
    def get_appointment_by_id(self, db: Session, appointment_id: int) -> Optional[Appointment]:
        """Get appointment by ID"""
        return db.query(Appointment).filter(Appointment.id == appointment_id).first()
    
    def get_available_therapists(self, db: Session) -> List[Therapist]:
        """Get list of available therapists"""
        return db.query(Therapist).filter(Therapist.is_active == True).all()
    
    def get_available_slots(self, db: Session, date_str: str, therapist_id: int = None) -> List[str]:
        """Get available time slots for a given date"""
        try:
            # Parse the date
            target_date = datetime.strptime(date_str.split('T')[0], '%Y-%m-%d').date()
            
            # Define business hours (9 AM to 6 PM)
            business_start = 9
            business_end = 18
            slot_duration = 1  # 1 hour slots
            
            # Build query for existing appointments
            query = db.query(Appointment).filter(
                Appointment.preferred_datetime >= datetime.combine(target_date, datetime.min.time()),
                Appointment.preferred_datetime < datetime.combine(target_date, datetime.min.time()) + timedelta(days=1),
                Appointment.status.in_([AppointmentStatus.CONFIRMED, AppointmentStatus.PENDING])
            )
            
            # Filter by therapist if specified
            if therapist_id:
                query = query.filter(Appointment.therapist_id == therapist_id)
            
            existing_appointments = query.all()
            
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
    
    def reschedule_appointment(self, db: Session, appointment_id: int, new_datetime: datetime, notes: str = None) -> Optional[Appointment]:
        """Reschedule an appointment"""
        try:
            appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
            
            if not appointment:
                logger.warning(f"Appointment {appointment_id} not found for rescheduling")
                return None
            
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
    # ENHANCED BOOKING METHODS
    # =====================================================
    
    async def create_modern_appointment(self, db: Session, booking_request: BookingRequest) -> Tuple[bool, Dict[str, Any]]:
        """
        Create a new appointment with enhanced validation.
        
        Args:
            db: Database session
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
            appointment_id = await self._save_modern_appointment(db, booking_request)
            
            if appointment_id:
                appointment_record = await self.get_modern_appointment(db, appointment_id)
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
    
    async def _save_modern_appointment(self, db: Session, booking_request: BookingRequest) -> Optional[int]:
        """Save appointment to database with modern structure."""
        try:
            # Find or create client user
            client = self.get_or_create_user(db, booking_request.client_phone, "client", booking_request.client_name)
            
            # Find therapist by name (simplified - should be improved)
            therapist = db.query(Therapist).filter(
                Therapist.name.ilike(f"%{booking_request.therapist_name}%")
            ).first()
            
            if not therapist:
                # Use default therapist if not found
                therapist = db.query(Therapist).filter(Therapist.is_active == True).first()
            
            therapist_id = therapist.id if therapist else 1  # Default fallback
            
            # Create appointment data
            booking_data = {
                'datetime': f"{booking_request.appointment_date}T{booking_request.appointment_time}:00",
                'service_type': 'in_call',  # Default
                'service_description': booking_request.service_name,
                'description': booking_request.description or '',
                'therapist_id': therapist_id,
                'client_notes': booking_request.description or ''
            }
            
            appointment = self.create_appointment(db, client.id, booking_data)
            return appointment.id
            
        except Exception as e:
            logger.error(f"Error saving modern appointment: {e}")
            return None
    
    async def get_modern_appointment(self, db: Session, appointment_id: int) -> Optional[AppointmentRecord]:
        """Get appointment by ID in modern format."""
        try:
            appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
            
            if appointment:
                # Get related data
                client = self.get_user_by_id(db, appointment.client_id)
                therapist = db.query(Therapist).filter(Therapist.id == appointment.therapist_id).first()
                
                # Map appointment status
                status_mapping = {
                    AppointmentStatus.PENDING: ModernAppointmentStatus.PENDING,
                    AppointmentStatus.CONFIRMED: ModernAppointmentStatus.CONFIRMED,
                    AppointmentStatus.CANCELLED: ModernAppointmentStatus.CANCELLED,
                    AppointmentStatus.COMPLETED: ModernAppointmentStatus.COMPLETED
                }
                
                return AppointmentRecord(
                    id=appointment.id,
                    client_name=client.name if client else "Unknown",
                    client_phone=client.phone_number if client else "Unknown",
                    service_name=appointment.service_description or "General Service",
                    appointment_date=appointment.preferred_datetime.strftime('%Y-%m-%d'),
                    appointment_time=appointment.preferred_datetime.strftime('%H:%M'),
                    therapist_name=therapist.name if therapist else "Dr. Sarah",
                    price=150.0,  # Default price - should be calculated
                    status=status_mapping.get(appointment.status, ModernAppointmentStatus.PENDING),
                    description=appointment.service_description,
                    extra_services=None,
                    created_at=appointment.created_at,
                    updated_at=appointment.updated_at
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting modern appointment {appointment_id}: {e}")
            return None
    
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