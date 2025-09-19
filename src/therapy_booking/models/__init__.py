"""
Data Models Layer

Contains all data models and schemas:
- SQLAlchemy database models
- Pydantic schemas for validation
- Enum definitions
- Type definitions
"""

# Database setup
from .database import Base, SessionLocal, engine, get_db, create_tables

# SQLAlchemy models
from .models import (
    User, Therapist, Appointment, Conversation, Message, TherapistAvailability,
    UserRole, AppointmentStatus, ServiceType, ConversationType
)

# Pydantic schemas
from .schemas import (
    # User schemas
    UserBase, UserCreate, UserUpdate, UserResponse,
    # Therapist schemas
    TherapistBase, TherapistCreate, TherapistUpdate, TherapistResponse,
    # Appointment schemas
    AppointmentBase, AppointmentCreate, AppointmentUpdate, AppointmentResponse,
    # Message schemas
    MessageBase, MessageCreate, MessageResponse,
    # Conversation schemas
    ConversationBase, ConversationCreate, ConversationResponse,
    # Availability schemas
    AvailabilityBase, AvailabilityCreate, AvailabilityResponse,
    # WhatsApp and special schemas
    WhatsAppMessage, BookingRequest, TherapistResponse,
    # Enums
    UserRoleEnum, ServiceTypeEnum, AppointmentStatusEnum, ConversationTypeEnum
)

__all__ = [
    # Database
    'Base', 'SessionLocal', 'engine', 'get_db', 'create_tables',
    # Models
    'User', 'Therapist', 'Appointment', 'Conversation', 'Message', 'TherapistAvailability',
    'UserRole', 'AppointmentStatus', 'ServiceType', 'ConversationType',
    # Schemas
    'UserBase', 'UserCreate', 'UserUpdate', 'UserResponse',
    'TherapistBase', 'TherapistCreate', 'TherapistUpdate', 'TherapistResponse',
    'AppointmentBase', 'AppointmentCreate', 'AppointmentUpdate', 'AppointmentResponse',
    'MessageBase', 'MessageCreate', 'MessageResponse',
    'ConversationBase', 'ConversationCreate', 'ConversationResponse',
    'AvailabilityBase', 'AvailabilityCreate', 'AvailabilityResponse',
    'WhatsAppMessage', 'BookingRequest', 'TherapistResponse',
    'UserRoleEnum', 'ServiceTypeEnum', 'AppointmentStatusEnum', 'ConversationTypeEnum'
]