"""
Natural Language Date Parser for Therapy Booking System
=====================================================
Converts natural language date expressions to YYYY-MM-DD format
"""

import datetime
import re
from typing import Optional

def parse_natural_date(date_text: str) -> Optional[str]:
    """
    Parse natural language date expressions to YYYY-MM-DD format.
    
    Handles:
    - "today" -> current date
    - "tomorrow" -> next day 
    - "monday", "tuesday", etc. -> next occurrence of that weekday
    - "next week", "next monday" -> following week
    - Numbers like "18", "18th" -> this month or next month
    - Relative dates: "in 3 days", "3 days from now"
    """
    if not date_text or not isinstance(date_text, str):
        return None
    
    # Clean up the input
    date_text = date_text.lower().strip()
    today = datetime.date.today()
    
    # Handle "today"
    if "today" in date_text:
        return today.strftime('%Y-%m-%d')
    
    # Handle "tomorrow" 
    if "tomorrow" in date_text:
        tomorrow = today + datetime.timedelta(days=1)
        return tomorrow.strftime('%Y-%m-%d')
    
    # Handle weekdays
    weekdays = {
        'monday': 0, 'mon': 0,
        'tuesday': 1, 'tue': 1, 'tues': 1,
        'wednesday': 2, 'wed': 2,
        'thursday': 3, 'thu': 3, 'thur': 3, 'thurs': 3,
        'friday': 4, 'fri': 4,
        'saturday': 5, 'sat': 5,
        'sunday': 6, 'sun': 6
    }
    
    for day_name, day_num in weekdays.items():
        if day_name in date_text:
            days_ahead = day_num - today.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7  # Get next occurrence
            
            # Handle "next monday" specifically 
            if "next" in date_text:
                days_ahead += 7
                
            target_date = today + datetime.timedelta(days=days_ahead)
            return target_date.strftime('%Y-%m-%d')
    
    # Handle relative days ("in 3 days", "3 days from now", "after 2 days")
    relative_match = re.search(r'(?:in|after)\s+(\d+)\s+days?', date_text)
    if not relative_match:
        relative_match = re.search(r'(\d+)\s+days?\s+from\s+now', date_text)
    
    if relative_match:
        days_ahead = int(relative_match.group(1))
        target_date = today + datetime.timedelta(days=days_ahead)
        return target_date.strftime('%Y-%m-%d')
    
    # Handle day numbers (18, 18th, etc.)
    day_match = re.search(r'\b(\d{1,2})(?:st|nd|rd|th)?\b', date_text)
    if day_match:
        day = int(day_match.group(1))
        if 1 <= day <= 31:
            # Try this month first
            try:
                target_date = today.replace(day=day)
                if target_date < today:  # If date has passed this month, use next month
                    if today.month == 12:
                        target_date = datetime.date(today.year + 1, 1, day)
                    else:
                        target_date = datetime.date(today.year, today.month + 1, day)
                return target_date.strftime('%Y-%m-%d')
            except ValueError:
                # Day doesn't exist in current month, try next month
                try:
                    if today.month == 12:
                        target_date = datetime.date(today.year + 1, 1, day)
                    else:
                        target_date = datetime.date(today.year, today.month + 1, day)
                    return target_date.strftime('%Y-%m-%d')
                except ValueError:
                    pass  # Invalid day number
    
    # Handle "next week"
    if "next week" in date_text:
        next_week = today + datetime.timedelta(days=7)
        return next_week.strftime('%Y-%m-%d')
    
    # Handle "this week" 
    if "this week" in date_text:
        return today.strftime('%Y-%m-%d')
    
    # If already in YYYY-MM-DD format, validate and return
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_text):
        try:
            datetime.datetime.strptime(date_text, '%Y-%m-%d')
            return date_text
        except ValueError:
            pass
    
    # If no pattern matched, return None
    return None


def get_friendly_date_description(date_str: str) -> str:
    """Convert YYYY-MM-DD format back to friendly description for confirmation."""
    try:
        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        today = datetime.date.today()
        
        if date_obj == today:
            return "today"
        elif date_obj == today + datetime.timedelta(days=1):
            return "tomorrow"
        else:
            day_name = date_obj.strftime('%A')
            return f"{day_name} ({date_str})"
    except:
        return date_str