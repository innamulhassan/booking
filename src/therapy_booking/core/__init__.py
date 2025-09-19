"""
Core Application Layer

Contains fundamental application components:
- Configuration management
- Database connection and setup
- Security and authentication
- Custom exceptions and error handling
- Application lifecycle management
"""

from .config import get_settings, settings

__all__ = ["get_settings", "settings"]