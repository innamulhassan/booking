"""
Pydantic schemas for request/response validation and serialization.
Reorganized with better validation and type safety.
"""

from pydantic import BaseModel, validator, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

# Enums for API schemas
class UserRoleEnum(str, Enum):
    CLIENT = "client"
    THERAPIST = "therapist"
    COORDINATOR = "coordinator"
    ADMIN = "admin"

class ServiceTypeEnum(str, Enum):
    IN_CALL = "in_call"
    OUT_CALL = "out_call"

class AppointmentStatusEnum(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class ConversationTypeEnum(str, Enum):
    BOOKING = "booking"
    SUPPORT = "support"
    GENERAL = "general"
    THERAPIST_BOT = "therapist_bot"

# User Schemas
class UserBase(BaseModel):
    """Base user schema"""
    phone_number: str = Field(..., min_length=10, max_length=15)
    name: str = Field(..., min_length=1, max_length=100)
    role: UserRoleEnum

    @validator('phone_number')
    def validate_phone_number(cls, v):
        # Remove common prefixes and validate
        cleaned = v.replace('+', '').replace('-', '').replace(' ', '')
        if not cleaned.isdigit():
            raise ValueError('Phone number must contain only digits')
        return cleaned

class UserCreate(UserBase):
    """Schema for creating a new user"""
    pass

class UserUpdate(BaseModel):
    """Schema for updating user information"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[UserRoleEnum] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    """Schema for user API responses"""
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Therapist Schemas
class TherapistBase(BaseModel):
    """Base therapist schema"""
    name: str = Field(..., min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, min_length=10, max_length=15)
    email: Optional[str] = Field(None, max_length=255)
    photo_url: Optional[str] = Field(None, max_length=500)
    specializations: Optional[str] = None
    experience_years: Optional[int] = Field(None, ge=0, le=50)
    education: Optional[str] = None
    languages: Optional[str] = Field(None, max_length=255)
    bio: Optional[str] = None

class TherapistCreate(TherapistBase):
    """Schema for creating a new therapist"""
    pass

class TherapistUpdate(BaseModel):
    """Schema for updating therapist information"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, min_length=10, max_length=15)
    email: Optional[str] = Field(None, max_length=255)
    photo_url: Optional[str] = Field(None, max_length=500)
    specializations: Optional[str] = None
    experience_years: Optional[int] = Field(None, ge=0, le=50)
    education: Optional[str] = None
    languages: Optional[str] = Field(None, max_length=255)
    bio: Optional[str] = None
    is_active: Optional[bool] = None

class TherapistResponse(TherapistBase):
    """Schema for therapist API responses"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Appointment Schemas
class AppointmentBase(BaseModel):
    """Base appointment schema"""
    service_type: ServiceTypeEnum
    preferred_datetime: datetime
    service_description: Optional[str] = Field(None, max_length=1000)

class AppointmentCreate(AppointmentBase):
    """Schema for creating a new appointment"""
    client_id: int
    therapist_id: int
    client_notes: Optional[str] = Field(None, max_length=1000)

class AppointmentUpdate(BaseModel):
    """Schema for updating appointment information"""
    confirmed_datetime: Optional[datetime] = None
    status: Optional[AppointmentStatusEnum] = None
    therapist_notes: Optional[str] = Field(None, max_length=1000)
    client_notes: Optional[str] = Field(None, max_length=1000)

class AppointmentResponse(AppointmentBase):
    """Schema for appointment API responses"""
    id: int
    client_id: int
    therapist_id: int
    confirmed_datetime: Optional[datetime] = None
    status: AppointmentStatusEnum
    client_notes: Optional[str] = None
    therapist_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Message Schemas
class MessageBase(BaseModel):
    """Base message schema"""
    message_text: str = Field(..., min_length=1, max_length=5000)
    sender: str = Field(..., min_length=1, max_length=20)

class MessageCreate(MessageBase):
    """Schema for creating a new message"""
    conversation_id: int
    whatsapp_message_id: Optional[str] = Field(None, max_length=100)

class MessageResponse(MessageBase):
    """Schema for message API responses"""
    id: int
    conversation_id: int
    whatsapp_message_id: Optional[str] = None
    timestamp: datetime
    
    class Config:
        from_attributes = True

# Conversation Schemas
class ConversationBase(BaseModel):
    """Base conversation schema"""
    conversation_type: ConversationTypeEnum
    session_id: str = Field(..., min_length=1, max_length=100)

class ConversationCreate(ConversationBase):
    """Schema for creating a new conversation"""
    user_id: int

class ConversationResponse(ConversationBase):
    """Schema for conversation API responses"""
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# WhatsApp Webhook Schemas
class WhatsAppMessage(BaseModel):
    """Schema for WhatsApp webhook messages"""
    From: str
    To: str
    Body: str
    MessageSid: str
    AccountSid: str
    
    @validator('From', 'To', pre=True)
    def clean_phone_number(cls, v):
        # Remove 'whatsapp:' prefix if present
        return v.replace('whatsapp:', '') if v else v

# Booking Request Schema
class BookingRequest(BaseModel):
    """Schema for booking requests from chat"""
    service_type: ServiceTypeEnum
    preferred_date: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$')  # Format: "2024-01-15"
    preferred_time: str = Field(..., pattern=r'^\d{2}:\d{2}$')        # Format: "14:30"
    service_description: Optional[str] = Field(None, max_length=1000)

# Therapist Response Schema
class TherapistResponse(BaseModel):
    """Schema for therapist responses to appointments"""
    appointment_id: int
    response_type: str = Field(..., pattern=r'^(confirm|reschedule|decline)$')
    new_datetime: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=1000)

# Availability Schemas
class AvailabilityBase(BaseModel):
    """Base availability schema"""
    day_of_week: int = Field(..., ge=0, le=6)  # 0=Monday, 6=Sunday
    start_time: str = Field(..., pattern=r'^\d{2}:\d{2}$')  # Format: "09:00"
    end_time: str = Field(..., pattern=r'^\d{2}:\d{2}$')    # Format: "17:00"

class AvailabilityCreate(AvailabilityBase):
    """Schema for creating therapist availability"""
    therapist_id: int

class AvailabilityResponse(AvailabilityBase):
    """Schema for availability API responses"""
    id: int
    therapist_id: int
    is_available: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True