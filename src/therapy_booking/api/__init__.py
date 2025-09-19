"""
API Layer - FastAPI endpoints and routing

This module contains all HTTP endpoints and routing logic for:
- Webhook endpoints (WhatsApp, external services)
- Appointment management endpoints
- Therapist management endpoints  
- Health check and monitoring endpoints
"""

from .webhooks import router as webhooks_router
from .therapist import router as therapist_router

__all__ = ["webhooks_router", "therapist_router"]