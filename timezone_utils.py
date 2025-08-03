from datetime import datetime, timezone
import pytz
import locale
import os

# Default timezone - you can change this to your local timezone
DEFAULT_TIMEZONE = 'UTC'  # Change this to your timezone like 'US/Eastern', 'Europe/London', 'Asia/Tokyo', etc.

def get_available_timezones():
    """Get list of common timezones"""
    common_timezones = [
        'UTC',
        'US/Eastern',
        'US/Central', 
        'US/Mountain',
        'US/Pacific',
        'Europe/London',
        'Europe/Paris',
        'Europe/Berlin',
        'Europe/Rome',
        'Asia/Tokyo',
        'Asia/Shanghai',
        'Asia/Kolkata',
        'Asia/Jerusalem',
        'Australia/Sydney',
        'America/New_York',
        'America/Chicago',
        'America/Denver',
        'America/Los_Angeles',
        'America/Toronto',
        'America/Sao_Paulo',
    ]
    return sorted(common_timezones)

def get_system_timezone():
    """Get the system's local timezone"""
    try:
        # Try to get system timezone
        return str(datetime.now().astimezone().tzinfo)
    except:
        # Fallback to UTC if detection fails
        return 'UTC'

def convert_utc_to_local(utc_datetime, target_timezone=None):
    """Convert UTC datetime to local timezone"""
    if target_timezone is None:
        target_timezone = DEFAULT_TIMEZONE
    
    # If the datetime is naive (no timezone info), assume it's UTC
    if utc_datetime.tzinfo is None:
        utc_datetime = utc_datetime.replace(tzinfo=timezone.utc)
    
    # Convert to target timezone
    if target_timezone == 'UTC':
        return utc_datetime
    
    try:
        target_tz = pytz.timezone(target_timezone)
        return utc_datetime.astimezone(target_tz)
    except:
        # Fallback to UTC if timezone is invalid
        return utc_datetime

def format_datetime_local(dt, target_timezone=None, format_string=None):
    """Format datetime in local timezone"""
    if format_string is None:
        format_string = '%Y-%m-%d %H:%M:%S %Z'
    
    local_dt = convert_utc_to_local(dt, target_timezone)
    return local_dt.strftime(format_string)

def get_current_time_local(target_timezone=None):
    """Get current time in specified timezone"""
    utc_now = datetime.now(timezone.utc)
    return convert_utc_to_local(utc_now, target_timezone)

# Configuration functions
def set_default_timezone(tz_name):
    """Set the default timezone for the application"""
    global DEFAULT_TIMEZONE
    if tz_name in pytz.all_timezones:
        DEFAULT_TIMEZONE = tz_name
        return True
    return False

def get_default_timezone():
    """Get the current default timezone"""
    return DEFAULT_TIMEZONE