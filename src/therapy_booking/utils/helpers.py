"""
Utility Functions

Common helper functions and utilities used across the application
"""

import logging
import sys
import re
from datetime import datetime
from typing import Optional
from pathlib import Path

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Configure logging for the application with enhanced configuration
    """
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Handlers list
    handlers = [console_handler]
    
    # Create file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        handlers=handlers,
        force=True  # Override any existing configuration
    )
    
    # Set specific logger levels
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('uvicorn').setLevel(logging.INFO)
    logging.getLogger('httpx').setLevel(logging.WARNING)

def format_phone_number(phone: str) -> str:
    """
    Format phone number to standard international format
    
    Args:
        phone: Raw phone number string
        
    Returns:
        Formatted phone number with country code
    """
    if not phone:
        return ""
    
    # Remove all non-digit characters except +
    cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
    
    # Ensure it starts with +
    if not cleaned.startswith('+'):
        if cleaned.startswith('0'):
            # Assume it's a Qatar local number, add country code
            cleaned = '+974' + cleaned[1:]
        elif len(cleaned) == 8:
            # Qatar local number without leading 0
            cleaned = '+974' + cleaned
        else:
            # Add + if not present
            cleaned = '+' + cleaned
    
    return cleaned

def validate_datetime_string(dt_str: str) -> bool:
    """
    Validate if a string can be parsed as datetime
    
    Args:
        dt_str: Datetime string to validate
        
    Returns:
        True if string is a valid datetime format
    """
    if not dt_str:
        return False
        
    formats = [
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%d/%m/%Y %H:%M',
        '%m/%d/%Y %H:%M',
        '%Y-%m-%dT%H:%M:%S.%f',  # ISO format with microseconds
        '%Y-%m-%d'  # Date only
    ]
    
    for fmt in formats:
        try:
            datetime.strptime(dt_str.strip(), fmt)
            return True
        except ValueError:
            continue
    
    return False

def parse_datetime_from_string(dt_str: str) -> Optional[datetime]:
    """
    Parse datetime from string with multiple format support
    
    Args:
        dt_str: Datetime string to parse
        
    Returns:
        Parsed datetime object or None if parsing failed
    """
    if not dt_str:
        return None
        
    formats = [
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%d/%m/%Y %H:%M',
        '%m/%d/%Y %H:%M',
        '%Y-%m-%dT%H:%M:%S.%f',
        '%Y-%m-%d'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(dt_str.strip(), fmt)
        except ValueError:
            continue
    
    return None

def extract_datetime_from_message(message: str) -> str:
    """
    Extract datetime information from natural language message
    
    Args:
        message: Natural language message
        
    Returns:
        Extracted datetime string or empty string
    """
    if not message:
        return ""
    
    # Enhanced patterns for date/time extraction
    patterns = [
        r'\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}(?::\d{2})?',  # 2024-01-15 14:30(:00)
        r'\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}(?::\d{2})?',  # 01/15/2024 14:30
        r'\d{1,2}-\d{1,2}-\d{4}\s+\d{1,2}:\d{2}(?::\d{2})?',  # 15-01-2024 14:30
        r'\d{1,2}:\d{2}\s*(?:am|pm)',  # 2:30 PM
        r'\d{4}-\d{2}-\d{2}',  # 2024-01-15 (date only)
        r'\d{1,2}/\d{1,2}/\d{4}',  # 01/15/2024 (date only)
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return match.group().strip()
    
    return ""

def sanitize_message_text(text: str, max_length: int = 1000) -> str:
    """
    Sanitize message text for safe storage and display
    
    Args:
        text: Text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove potentially harmful characters and HTML
    sanitized = text.replace('<', '&lt;').replace('>', '&gt;')
    sanitized = sanitized.replace('&', '&amp;').replace('"', '&quot;')
    
    # Remove control characters except newlines and tabs
    sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\n\t')
    
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length-3] + "..."
    
    return sanitized.strip()

def extract_service_type(message: str) -> str:
    """
    Extract service type preference from message
    
    Args:
        message: Message to analyze
        
    Returns:
        Service type ('in_call', 'out_call', or 'unknown')
    """
    message_lower = message.lower()
    
    # In-call indicators
    in_call_keywords = [
        'home', 'house', 'in-call', 'incall', 'my place', 'at home', 
        'come to me', 'visit me', 'home visit'
    ]
    
    # Out-call indicators
    out_call_keywords = [
        'clinic', 'office', 'out-call', 'outcall', 'your place', 
        'come to you', 'visit you', 'at clinic', 'center'
    ]
    
    for keyword in in_call_keywords:
        if keyword in message_lower:
            return 'in_call'
    
    for keyword in out_call_keywords:
        if keyword in message_lower:
            return 'out_call'
    
    return 'unknown'

def format_appointment_summary(appointment_data: dict) -> str:
    """
    Format appointment data into a readable summary
    
    Args:
        appointment_data: Dictionary containing appointment information
        
    Returns:
        Formatted appointment summary string
    """
    summary_parts = []
    
    # Client information
    if appointment_data.get('client_name'):
        summary_parts.append(f"👤 **Client:** {appointment_data['client_name']}")
    
    if appointment_data.get('client_phone'):
        summary_parts.append(f"📱 **Phone:** {appointment_data['client_phone']}")
    
    # Appointment details
    if appointment_data.get('appointment_date'):
        summary_parts.append(f"📅 **Date:** {appointment_data['appointment_date']}")
    
    if appointment_data.get('appointment_time'):
        summary_parts.append(f"🕒 **Time:** {appointment_data['appointment_time']}")
    
    if appointment_data.get('service_description'):
        summary_parts.append(f"🏥 **Service:** {appointment_data['service_description']}")
    
    if appointment_data.get('notes'):
        summary_parts.append(f"📝 **Notes:** {appointment_data['notes']}")
    
    return '\n'.join(summary_parts) if summary_parts else "No appointment details available"

def validate_phone_number(phone: str) -> bool:
    """
    Validate phone number format
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if phone number is valid
    """
    if not phone:
        return False
    
    # Clean the number
    cleaned = format_phone_number(phone)
    
    # Basic validation: should start with + and have 8-15 digits
    if not cleaned.startswith('+'):
        return False
    
    digits_only = cleaned[1:]  # Remove the +
    
    if not digits_only.isdigit():
        return False
    
    if len(digits_only) < 8 or len(digits_only) > 15:
        return False
    
    return True

def create_session_id() -> str:
    """
    Create a unique session ID
    
    Returns:
        Unique session identifier
    """
    import uuid
    return str(uuid.uuid4())[:8]

def safe_get(dictionary: dict, key: str, default=None):
    """
    Safely get value from dictionary with nested key support
    
    Args:
        dictionary: Dictionary to search
        key: Key to find (supports dot notation for nested keys)
        default: Default value if key not found
        
    Returns:
        Value if found, default otherwise
    """
    if not isinstance(dictionary, dict):
        return default
    
    keys = key.split('.')
    value = dictionary
    
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    
    return value