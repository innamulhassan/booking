"""
External Service Integrations Layer

Contains all external service client integrations:
- UltraMsg API client
- Google ADK client 
- Twilio integration
- Other third-party service integrations
"""

from .ultramsg_service import UltramsgService, ultramsg_service

__all__ = [
    'UltramsgService', 'ultramsg_service'
]