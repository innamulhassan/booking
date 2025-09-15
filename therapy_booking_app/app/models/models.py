from sqlalchemy import Column, Integer, String, DateTime, Text, Enum, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.database import Base
import enum

class UserRole(enum.Enum):
    CLIENT = "client"
    THERAPIST = "therapist"

class ServiceType(enum.Enum):
    IN_CALL = "in_call"
    OUT_CALL = "out_call"

class AppointmentStatus(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class ConversationType(enum.Enum):
    CLIENT_BOT = "client_bot"
    THERAPIST_BOT = "therapist_bot"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(15), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    client_appointments = relationship("Appointment", foreign_keys="Appointment.client_id", back_populates="client")
    therapist_appointments = relationship("Appointment", foreign_keys="Appointment.therapist_id", back_populates="therapist")
    conversations = relationship("Conversation", back_populates="user")

class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    therapist_id = Column(Integer, ForeignKey("users.id"), nullable=False)
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
    therapist = relationship("User", foreign_keys=[therapist_id], back_populates="therapist_appointments")

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    conversation_type = Column(Enum(ConversationType), nullable=False)
    session_id = Column(String(100), nullable=False)  # Dialogflow session ID
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    sender = Column(String(20), nullable=False)  # 'user', 'bot', 'therapist'
    message_text = Column(Text, nullable=False)
    whatsapp_message_id = Column(String(100), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

class TherapistAvailability(Base):
    __tablename__ = "therapist_availability"
    
    id = Column(Integer, primary_key=True, index=True)
    therapist_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = Column(String(5), nullable=False)  # Format: "09:00"
    end_time = Column(String(5), nullable=False)    # Format: "17:00"
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    therapist = relationship("User", foreign_keys=[therapist_id])
