#!/usr/bin/env python3
"""
Test natural language date parsing functionality
"""
import sys
import os

# Add the therapy_booking_app directory to sys.path
current_dir = os.path.dirname(__file__)
root_dir = os.path.dirname(os.path.dirname(current_dir))
therapy_app_dir = os.path.join(root_dir, 'therapy_booking_app')
sys.path.insert(0, therapy_app_dir)

from app.utils.date_parser import parse_natural_date, get_friendly_date_description
from datetime import datetime

def test_date_parsing():
    """Test various natural language date inputs"""
    
    test_cases = [
        "today",
        "tomorrow", 
        "monday",
        "tuesday",
        "next monday",
        "in 2 days",
        "in 1 week",
        "15",  # Day number
        "25th",  # Day with suffix
        "2025-01-20",  # Standard format
    ]
    
    print("=== NATURAL LANGUAGE DATE PARSING TEST ===")
    print(f"Current date: {datetime.now().strftime('%Y-%m-%d (%A)')}")
    print()
    
    for test_input in test_cases:
        print(f"Input: '{test_input}'")
        
        # Test parsing
        parsed_date = parse_natural_date(test_input)
        if parsed_date:
            print(f"  ✅ Parsed: {parsed_date}")
            
            # Test friendly description
            friendly = get_friendly_date_description(parsed_date)
            print(f"  📅 Friendly: {friendly}")
        else:
            print(f"  ❌ Failed to parse")
        print()

if __name__ == "__main__":
    test_date_parsing()