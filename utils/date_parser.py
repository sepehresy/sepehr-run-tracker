"""
Date parsing utility for consistent date handling across the app.

This module provides bulletproof date parsing functions that handle:
- ISO format: YYYY-MM-DD
- European format: DD/MM/YYYY  
- Mixed formats in data
- Pandas NaT and None values
- Error handling with fallbacks

Usage:
    from utils.date_parser import safe_parse_date, safe_parse_date_series
    
    # Parse single date
    date_obj = safe_parse_date("2025-04-14")  # Returns datetime.date object
    
    # Parse pandas series/column
    df['Date'] = safe_parse_date_series(df['Date'])
"""

import pandas as pd
from datetime import datetime, date
import warnings
from typing import Union, Optional
import re

def detect_date_format(date_str: str) -> Optional[str]:
    """
    Detect the format of a date string.
    
    Args:
        date_str: String representation of date
        
    Returns:
        Format string for strptime or None if unrecognized
    """
    if not isinstance(date_str, str) or not date_str.strip():
        return None
        
    date_str = date_str.strip()
    
    # ISO format: YYYY-MM-DD
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return '%Y-%m-%d'
    
    # European format: DD/MM/YYYY
    if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', date_str):
        return '%d/%m/%Y'
    
    # European format with zero padding: DD/MM/YYYY
    if re.match(r'^\d{2}/\d{2}/\d{4}$', date_str):
        return '%d/%m/%Y'
    
    # US format: MM/DD/YYYY (less common in your app but handle it)
    if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', date_str):
        # Try both DD/MM and MM/DD - DD/MM is more likely
        # We'll handle this in the parsing function
        return '%d/%m/%Y'
    
    # ISO with time: YYYY-MM-DD HH:MM:SS
    if re.match(r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}', date_str):
        return '%Y-%m-%d %H:%M:%S'
    
    return None

def safe_parse_date(date_input: Union[str, date, datetime, pd.Timestamp, None], 
                   return_type: str = 'date') -> Optional[Union[date, datetime, pd.Timestamp]]:
    """
    Safely parse any date input into specified return type.
    
    Args:
        date_input: Date in various formats (string, date, datetime, Timestamp, None)
        return_type: 'date', 'datetime', or 'timestamp'
        
    Returns:
        Parsed date in requested format, or None if parsing fails
    """
    if date_input is None or pd.isna(date_input):
        return None
    
    # Already correct type
    if return_type == 'date' and isinstance(date_input, date) and not isinstance(date_input, datetime):
        return date_input
    if return_type == 'datetime' and isinstance(date_input, datetime):
        return date_input
    if return_type == 'timestamp' and isinstance(date_input, pd.Timestamp):
        return date_input
    
    # Convert from other types
    if isinstance(date_input, (datetime, pd.Timestamp)):
        parsed_dt = date_input if isinstance(date_input, datetime) else date_input.to_pydatetime()
        if return_type == 'date':
            return parsed_dt.date()
        elif return_type == 'datetime':
            return parsed_dt
        elif return_type == 'timestamp':
            return pd.Timestamp(parsed_dt)
    
    if isinstance(date_input, date):
        base_dt = datetime.combine(date_input, datetime.min.time())
        if return_type == 'date':
            return date_input
        elif return_type == 'datetime':
            return base_dt
        elif return_type == 'timestamp':
            return pd.Timestamp(base_dt)
    
    # String parsing
    if not isinstance(date_input, str):
        date_input = str(date_input)
    
    date_input = date_input.strip()
    if not date_input:
        return None
    
    # Try detecting format first
    detected_format = detect_date_format(date_input)
    if detected_format:
        try:
            parsed_dt = datetime.strptime(date_input, detected_format)
            if return_type == 'date':
                return parsed_dt.date()
            elif return_type == 'datetime':
                return parsed_dt
            elif return_type == 'timestamp':
                return pd.Timestamp(parsed_dt)
        except ValueError:
            pass  # Fall through to pandas parsing
    
    # Fallback to pandas with specific format attempts
    formats_to_try = [
        '%Y-%m-%d',      # ISO format
        '%d/%m/%Y',      # European format
        '%m/%d/%Y',      # US format (fallback)
        '%Y-%m-%d %H:%M:%S',  # ISO with time
        '%d/%m/%Y %H:%M:%S',  # European with time
    ]
    
    for fmt in formats_to_try:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                parsed_ts = pd.to_datetime(date_input, format=fmt, errors='raise')
                if pd.isna(parsed_ts):
                    continue
                    
                if return_type == 'date':
                    return parsed_ts.date()
                elif return_type == 'datetime':
                    return parsed_ts.to_pydatetime()
                elif return_type == 'timestamp':
                    return parsed_ts
        except (ValueError, TypeError):
            continue
    
    # Final fallback to pandas auto-detection (but suppress warnings)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # Don't use dayfirst to avoid conflicts - let pandas auto-detect
            parsed_ts = pd.to_datetime(date_input, errors='coerce')
            if pd.isna(parsed_ts):
                return None
                
            if return_type == 'date':
                return parsed_ts.date()
            elif return_type == 'datetime':
                return parsed_ts.to_pydatetime()
            elif return_type == 'timestamp':
                return parsed_ts
    except Exception:
        pass
    
    return None

def safe_parse_date_series(series: pd.Series, return_type: str = 'timestamp') -> pd.Series:
    """
    Safely parse a pandas Series of dates.
    
    Args:
        series: Pandas Series containing dates in various formats
        return_type: 'date', 'datetime', or 'timestamp'
        
    Returns:
        Pandas Series with parsed dates
    """
    if series is None or series.empty:
        return series
    
    # Create result series
    result = pd.Series(index=series.index, dtype='object')
    
    for idx, value in series.items():
        parsed = safe_parse_date(value, return_type)
        result.iloc[idx] = parsed
    
    # Convert to appropriate pandas dtype if possible
    if return_type == 'timestamp':
        try:
            return pd.to_datetime(result, errors='coerce')
        except Exception:
            return result
    
    return result

def format_date_for_display(date_obj: Union[date, datetime, pd.Timestamp, str, None], 
                           format_type: str = 'iso') -> str:
    """
    Format date for consistent display.
    
    Args:
        date_obj: Date object to format
        format_type: 'iso' (YYYY-MM-DD), 'european' (DD/MM/YYYY), or 'display' (DD Mon YYYY)
        
    Returns:
        Formatted date string or empty string if invalid
    """
    parsed_date = safe_parse_date(date_obj, 'date')
    if parsed_date is None:
        return ""
    
    if format_type == 'iso':
        return parsed_date.strftime('%Y-%m-%d')
    elif format_type == 'european':
        return parsed_date.strftime('%d/%m/%Y')
    elif format_type == 'display':
        return parsed_date.strftime('%d %b %Y')
    else:
        return parsed_date.strftime('%Y-%m-%d')  # Default to ISO

def dates_are_equal(date1: Union[date, datetime, str, None], 
                   date2: Union[date, datetime, str, None]) -> bool:
    """
    Compare two dates safely, handling different formats.
    
    Args:
        date1, date2: Dates to compare in any format
        
    Returns:
        True if dates are equal, False otherwise
    """
    parsed1 = safe_parse_date(date1, 'date')
    parsed2 = safe_parse_date(date2, 'date')
    
    if parsed1 is None or parsed2 is None:
        return parsed1 == parsed2  # Both None returns True
    
    return parsed1 == parsed2

# Convenience functions for common use cases
def parse_race_date(date_str: Union[str, date, datetime, None]) -> Optional[date]:
    """Parse race date consistently."""
    return safe_parse_date(date_str, 'date')

def parse_training_date(date_str: Union[str, date, datetime, None]) -> Optional[date]:
    """Parse training plan date consistently."""
    return safe_parse_date(date_str, 'date')

def parse_activity_date(date_str: Union[str, date, datetime, None]) -> Optional[pd.Timestamp]:
    """Parse activity date for dataframes."""
    return safe_parse_date(date_str, 'timestamp') 