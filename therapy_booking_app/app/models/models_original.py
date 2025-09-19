from sqlalchemy import Column, Integer, String, DateTime, Text, Enum, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.database import Base
import enum

class UserRole(enum.Enum):
    CLIENT = "client"
    COORDINATOR = "coordinator"
    THERAPIST = "therapist"

class ServiceType(enum.Enum):
    IN_CALL = "in_call"      # Client visits therapist clinic
    OUT_CALL = "out_call"    # Therapist visits client home

class AppointmentStatus(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class ConversationType(enum.Enum):
    CLIENT_BOT = "client_bot"
    THERAPIST_BOT = "therapist_bot"

class ServiceCategory(enum.Enum):
    INDIVIDUAL_THERAPY = "individual_therapy"
    COUPLE_THERAPY = "couple_therapy"
    FAMILY_THERAPY = "family_therapy"
    GROUP_THERAPY = "group_therapy"
    CONSULTATION = "consultation"
    ASSESSMENT = "assessment"
    WORKSHOP = "workshop"
    COUNSELING = "counseling"

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
    conversations = relationship("Conversation", back_populates="user")
    coordinator_profile = relationship("Coordinator", back_populates="user", uselist=False)

class Therapist(Base):
    __tablename__ = "therapists"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone_number = Column(String(15), unique=True, index=True, nullable=True)
    email = Column(String(255), nullable=True)
    photo_url = Column(String(500), nullable=True)
    specializations = Column(Text, nullable=True)  # JSON list
    experience_years = Column(Integer, nullable=True)
    education = Column(Text, nullable=True)
    languages = Column(String(255), nullable=True)  # Comma-separated
    bio = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    appointments = relationship("Appointment", back_populates="therapist")

class MainService(Base):
    __tablename__ = "main_services"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    category = Column(Enum(ServiceCategory), nullable=False)
    description = Column(Text, nullable=True)
    duration_minutes = Column(Integer, nullable=False, default=60)
    base_price = Column(Integer, nullable=False)  # Price in cents
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    therapist_services = relationship("TherapistService", back_populates="main_service")
    appointments = relationship("Appointment", back_populates="main_service")

class ExtraService(Base):
    __tablename__ = "extra_services"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    base_price = Column(Integer, nullable=False)  # Price in cents
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    therapist_extra_services = relationship("TherapistExtraService", back_populates="extra_service")

class TherapistService(Base):
    __tablename__ = "therapist_services"
    
    id = Column(Integer, primary_key=True, index=True)
    therapist_id = Column(Integer, ForeignKey("therapists.id"), nullable=False)
    main_service_id = Column(Integer, ForeignKey("main_services.id"), nullable=False)
    custom_price = Column(Integer, nullable=True)  # Override base price if needed
    is_available = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    therapist = relationship("Therapist", back_populates="therapist_services")
    main_service = relationship("MainService", back_populates="therapist_services")

class TherapistExtraService(Base):
    __tablename__ = "therapist_extra_services"
    
    id = Column(Integer, primary_key=True, index=True)
    therapist_id = Column(Integer, ForeignKey("therapists.id"), nullable=False)
    extra_service_id = Column(Integer, ForeignKey("extra_services.id"), nullable=False)
    custom_price = Column(Integer, nullable=True)  # Override base price if needed
    is_available = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    therapist = relationship("Therapist", back_populates="extra_services")
    extra_service = relationship("ExtraService", back_populates="therapist_extra_services")

class Coordinator(Base):
    __tablename__ = "coordinators"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    phone_number = Column(String(15), unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="coordinator_profile")
    managed_appointments = relationship("Appointment", back_populates="managing_coordinator")

class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    therapist_id = Column(Integer, ForeignKey("therapists.id"), nullable=False)
    service_type = Column(Enum(ServiceType), nullable=False)  # IN_CALL or OUT_CALL
    preferred_datetime = Column(DateTime(timezone=True), nullable=False)
    confirmed_datetime = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.PENDING)
    service_description = Column(Text, nullable=True)  # Description of the service requested
    client_notes = Column(Text, nullable=True)
    therapist_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    client = relationship("User", foreign_keys=[client_id], back_populates="client_appointments")
    therapist = relationship("Therapist", back_populates="appointments")

class AppointmentExtraService(Base):
    __tablename__ = "appointment_extra_services"
    
    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False)
    therapist_extra_service_id = Column(Integer, ForeignKey("therapist_extra_services.id"), nullable=False)
    price = Column(Integer, nullable=False)  # Price in cents
    
    # Relationships
    appointment = relationship("Appointment", back_populates="extra_services")
    therapist_extra_service = relationship("TherapistExtraService")

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
    sender = Column(String(20), nullable=False)  # 'user', 'bot', 'coordinator'
    message_text = Column(Text, nullable=False)
    whatsapp_message_id = Column(String(100), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

class TherapistAvailability(Base):
    __tablename__ = "therapist_availability"
    
    id = Column(Integer, primary_key=True, index=True)
    coordinator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = Column(String(5), nullable=False)  # Format: "09:00"
    end_time = Column(String(5), nullable=False)    # Format: "17:00"
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    coordinator = relationship("User", foreign_keys=[coordinator_id])
