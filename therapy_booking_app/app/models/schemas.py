from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserRoleEnum(str, Enum):
    CLIENT = "client"
    THERAPIST = "therapist"

class ServiceTypeEnum(str, Enum):
    IN_CALL = "in_call"
    OUT_CALL = "out_call"

class AppointmentStatusEnum(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class ConversationTypeEnum(str, Enum):
    CLIENT_BOT = "client_bot"
    THERAPIST_BOT = "therapist_bot"

# User Schemas
class UserBase(BaseModel):
    phone_number: str
    name: str
    role: UserRoleEnum

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Appointment Schemas
class AppointmentBase(BaseModel):
    service_type: ServiceTypeEnum
    preferred_datetime: datetime
    service_description: Optional[str] = None

class AppointmentCreate(AppointmentBase):
    client_id: int
    therapist_id: int

class AppointmentUpdate(BaseModel):
    confirmed_datetime: Optional[datetime] = None
    status: Optional[AppointmentStatusEnum] = None
    therapist_notes: Optional[str] = None

class AppointmentResponse(AppointmentBase):
    id: int
    client_id: int
    therapist_id: int
    confirmed_datetime: Optional[datetime] = None
    status: AppointmentStatusEnum
    client_notes: Optional[str] = None
    therapist_notes: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Message Schemas
class MessageBase(BaseModel):
    message_text: str
    sender: str

class MessageCreate(MessageBase):
    conversation_id: int
    whatsapp_message_id: Optional[str] = None

class MessageResponse(MessageBase):
    id: int
    conversation_id: int
    whatsapp_message_id: Optional[str] = None
    timestamp: datetime
    
    class Config:
        from_attributes = True

# WhatsApp Webhook Schemas
class WhatsAppMessage(BaseModel):
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
    service_type: ServiceTypeEnum
    preferred_date: str  # Format: "2024-01-15"
    preferred_time: str  # Format: "14:30"
    service_description: Optional[str] = None

# Therapist Response Schema
class TherapistResponse(BaseModel):
    appointment_id: int
    response_type: str  # "confirm", "reschedule", "decline"
    new_datetime: Optional[datetime] = None
    notes: Optional[str] = None
