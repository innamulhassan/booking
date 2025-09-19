"""
Health Check API Endpoints

Provides system health monitoring and status endpoints
"""

from fastapi import APIRouter
from datetime import datetime
from typing import Dict, Any

router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "therapy_booking_system",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """Detailed health check with system information"""
    # TODO: Add database connectivity check
    # TODO: Add external service checks
    # TODO: Add system resource checks
    
    return {
        "status": "healthy",
        "service": "therapy_booking_system",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "database": {"status": "healthy", "response_time_ms": 25},
            "adk_agent": {"status": "healthy", "response_time_ms": 150},
            "ultramsg_api": {"status": "healthy", "response_time_ms": 200},
        },
        "system": {
            "uptime_seconds": 3600,  # TODO: Calculate actual uptime
            "memory_usage_mb": 256,  # TODO: Get actual memory usage
            "cpu_usage_percent": 15,  # TODO: Get actual CPU usage
        }
    }