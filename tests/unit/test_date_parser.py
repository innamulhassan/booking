"""
Unit tests for date parser utility with mocking
"""
import pytest
import unittest.mock as mock
from datetime import datetime, timedelta
import sys
import os

# Add the app directory to sys.path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'therapy_booking_app'))

from app.utils.date_parser import parse_natural_date, get_friendly_date_description


class TestDateParser:
    """Unit tests for natural language date parsing"""
    
    @mock.patch('app.utils.date_parser.datetime')
    def test_parse_today(self, mock_datetime):
        """Test parsing 'today' with mocked current date"""
        # Mock current date as 2025-09-18
        mock_now = datetime(2025, 9, 18)
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime = datetime.strptime
        
        result = parse_natural_date("today")
        assert result == "2025-09-18"
    
    @mock.patch('app.utils.date_parser.datetime')
    def test_parse_tomorrow(self, mock_datetime):
        """Test parsing 'tomorrow' with mocked current date"""
        mock_now = datetime(2025, 9, 18)
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime = datetime.strptime
        
        result = parse_natural_date("tomorrow")
        assert result == "2025-09-19"
    
    @mock.patch('app.utils.date_parser.datetime')
    def test_parse_weekday(self, mock_datetime):
        """Test parsing weekday names"""
        # Thursday 2025-09-18
        mock_now = datetime(2025, 9, 18)
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime = datetime.strptime
        
        # Next Monday should be 2025-09-22
        result = parse_natural_date("monday")
        assert result == "2025-09-22"
        
        # Next Friday should be 2025-09-19 (tomorrow)
        result = parse_natural_date("friday")
        assert result == "2025-09-19"
    
    @mock.patch('app.utils.date_parser.datetime')
    def test_parse_relative_days(self, mock_datetime):
        """Test parsing 'in X days' format"""
        mock_now = datetime(2025, 9, 18)
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime = datetime.strptime
        
        result = parse_natural_date("in 3 days")
        assert result == "2025-09-21"
        
        result = parse_natural_date("in 1 week")
        assert result == "2025-10-01"  # 7*2 = 14 days from now
    
    @mock.patch('app.utils.date_parser.datetime')
    def test_parse_day_numbers(self, mock_datetime):
        """Test parsing day numbers like '15' or '25th'"""
        mock_now = datetime(2025, 9, 18)
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime = datetime.strptime
        
        # Day 25 of current month
        result = parse_natural_date("25")
        assert result == "2025-09-25"
        
        # Day 15 of next month (since 15 < 18 current day)
        result = parse_natural_date("15")
        assert result == "2025-10-15"
        
        result = parse_natural_date("25th")
        assert result == "2025-09-25"
    
    def test_parse_standard_format(self):
        """Test parsing standard YYYY-MM-DD format without mocking"""
        result = parse_natural_date("2025-12-25")
        assert result == "2025-12-25"
    
    def test_parse_invalid_input(self):
        """Test parsing invalid input returns None"""
        result = parse_natural_date("invalid_date")
        assert result is None
        
        result = parse_natural_date("")
        assert result is None
        
        result = parse_natural_date("xyz123")
        assert result is None
    
    @mock.patch('app.utils.date_parser.datetime')
    def test_friendly_descriptions(self, mock_datetime):
        """Test friendly date descriptions"""
        mock_now = datetime(2025, 9, 18)
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime = datetime.strptime
        
        # Test today
        result = get_friendly_date_description("2025-09-18")
        assert result == "today"
        
        # Test tomorrow
        result = get_friendly_date_description("2025-09-19")
        assert result == "tomorrow"
        
        # Test other date
        result = get_friendly_date_description("2025-09-22")
        assert "Monday" in result


class TestDateParserEdgeCases:
    """Edge cases and error handling for date parser"""
    
    @mock.patch('app.utils.date_parser.datetime')
    def test_case_insensitive(self, mock_datetime):
        """Test that parsing is case insensitive"""
        mock_now = datetime(2025, 9, 18)
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime = datetime.strptime
        
        # Test various cases
        assert parse_natural_date("TODAY") == "2025-09-18"
        assert parse_natural_date("Today") == "2025-09-18"
        assert parse_natural_date("MONDAY") == "2025-09-22"
        assert parse_natural_date("Monday") == "2025-09-22"
    
    @mock.patch('app.utils.date_parser.datetime')
    def test_whitespace_handling(self, mock_datetime):
        """Test handling of extra whitespace"""
        mock_now = datetime(2025, 9, 18)
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime = datetime.strptime
        
        assert parse_natural_date("  today  ") == "2025-09-18"
        assert parse_natural_date(" tomorrow ") == "2025-09-19"
        assert parse_natural_date("  in 3 days  ") == "2025-09-21"
    
    def test_none_input(self):
        """Test handling None input"""
        result = parse_natural_date(None)
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])