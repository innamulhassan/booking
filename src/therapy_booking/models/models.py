"""
SQLAlchemy models for the therapy booking application.
Reorganized and cleaned up for better maintainability.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import relationship
import enum
from .database import Base

class UserRole(enum.Enum):
    CLIENT = "client"
    THERAPIST = "therapist"
    COORDINATOR = "coordinator"
    ADMIN = "admin"

class AppointmentStatus(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ServiceType(enum.Enum):
    IN_CALL = "in_call"
    OUT_CALL = "out_call"

class ConversationType(enum.Enum):
    BOOKING = "booking"
    SUPPORT = "support"
    GENERAL = "general"
    THERAPIST_BOT = "therapist_bot"

class User(Base):
    """User model for clients, therapists, and staff"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(15), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.CLIENT)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    client_appointments = relationship("Appointment", foreign_keys="Appointment.client_id", back_populates="client")
    conversations = relationship("Conversation", back_populates="user")

class Therapist(Base):
    """Therapist model with professional information"""
    __tablename__ = "therapists"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone_number = Column(String(15), nullable=True)
    email = Column(String(255), nullable=True)
    photo_url = Column(String(500), nullable=True)
    specializations = Column(Text, nullable=True)
    experience_years = Column(Integer, nullable=True)
    education = Column(Text, nullable=True)
    languages = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    appointments = relationship("Appointment", back_populates="therapist")
    availability = relationship("TherapistAvailability", back_populates="therapist")

class Appointment(Base):
    """Appointment model for booking management"""
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    therapist_id = Column(Integer, ForeignKey("therapists.id"), nullable=False)
    service_type = Column(Enum(ServiceType), nullable=False)
    preferred_datetime = Column(DateTime(timezone=True), nullable=False)
    confirmed_datetime = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.PENDING)
    service_description = Column(Text, nullable=True)
    client_notes = Column(Text, nullable=True)
    therapist_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    client = relationship("User", foreign_keys=[client_id], back_populates="client_appointments")
    therapist = relationship("Therapist", back_populates="appointments")

class Conversation(Base):
    """Conversation model for chat session management"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    conversation_type = Column(Enum(ConversationType), nullable=False)
    session_id = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    """Message model for conversation history"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    sender = Column(String(20), nullable=False)  # 'user', 'bot', 'coordinator'
    message_text = Column(Text, nullable=False)
    whatsapp_message_id = Column(String(100), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

class TherapistAvailability(Base):
    """Therapist availability schedule model"""
    __tablename__ = "therapist_availability"
    
    id = Column(Integer, primary_key=True, index=True)
    therapist_id = Column(Integer, ForeignKey("therapists.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = Column(String(5), nullable=False)  # Format: "09:00"
    end_time = Column(String(5), nullable=False)    # Format: "17:00"
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    therapist = relationship("Therapist", back_populates="availability")