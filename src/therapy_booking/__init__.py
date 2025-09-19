"""
Therapy Booking System - Main Package

A comprehensive WhatsApp-based therapy booking system with modern architecture:
- FastAPI REST API with async support
- AI-powered conversation handling
- Multi-provider WhatsApp integration (UltraMsg, Twilio)
- SQLAlchemy ORM with MySQL support
- Pydantic data validation and settings management
- Structured logging and monitoring
- Coordinator approval workflow
- Natural language appointment processing
"""

__version__ = "2.0.0"
__author__ = "Therapy Booking Team"
__description__ = "Modern WhatsApp Therapy Booking System with AI Integration"

# Package exports for easy importing
from .core.config import get_settings, settings
from .models import get_db, create_tables
from .services import booking_service, notification_service
from .external import ultramsg_service

__all__ = [
    "__version__",
    "__author__", 
    "__description__",
    "get_settings",
    "settings",
    "get_db",
    "create_tables",
    "booking_service",
    "notification_service",
    "ultramsg_service",
]