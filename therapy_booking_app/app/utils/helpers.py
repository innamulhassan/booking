import logging
import sys
from datetime import datetime

def setup_logging():
    """Configure logging for the application"""
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Create file handler
    file_handler = logging.FileHandler('therapy_booking.log')
    file_handler.setFormatter(formatter)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        handlers=[console_handler, file_handler]
    )
    
    # Set specific loggers
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('uvicorn').setLevel(logging.INFO)

def format_phone_number(phone: str) -> str:
    """Format phone number to standard format"""
    # Remove all non-digit characters except +
    cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
    
    # Ensure it starts with +
    if not cleaned.startswith('+'):
        if cleaned.startswith('0'):
            # Assume it's a local number, add country code (adjust as needed)
            cleaned = '+1' + cleaned[1:]  # Example for US numbers
        else:
            cleaned = '+' + cleaned
    
    return cleaned

def validate_datetime_string(dt_str: str) -> bool:
    """Validate if a string can be parsed as datetime"""
    formats = [
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%d/%m/%Y %H:%M',
        '%m/%d/%Y %H:%M'
    ]
    
    for fmt in formats:
        try:
            datetime.strptime(dt_str, fmt)
            return True
        except ValueError:
            continue
    
    return False

def extract_datetime_from_message(message: str) -> str:
    """Extract datetime information from natural language message"""
    import re
    
    # Simple patterns for date/time extraction
    patterns = [
        r'\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}',  # 2024-01-15 14:30
        r'\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}',  # 01/15/2024 14:30
        r'\d{1,2}:\d{2}\s*(am|pm)',  # 2:30 PM
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return match.group()
    
    return ""

def sanitize_message_text(text: str) -> str:
    """Sanitize message text for safe storage and display"""
    # Remove potentially harmful characters
    sanitized = text.replace('<', '&lt;').replace('>', '&gt;')
    
    # Limit length
    if len(sanitized) > 1000:
        sanitized = sanitized[:997] + "..."
    
    return sanitized.strip()
