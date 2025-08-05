"""
User parameter management
Handles user-configurable settings and preferences
"""

from .app_config import DEFAULT_TIMEZONE, API_REQUEST_TIMEOUT
from .api_config import (
    AUTO_REFRESH_INTERVAL, DEFAULT_COLLECTION_INTERVAL, DEFAULT_DB_QUERY_LIMIT,
    DEFAULT_API_LIMIT, DEFAULT_SERIES_LIMIT, RECENT_ENTRIES_DISPLAY_LIMIT,
    RATE_LIMIT_MIN_INTERVAL, RATE_LIMIT_CACHE_DURATION, RATE_LIMIT_MAX_CALLS_PER_MINUTE,
    TIME_RANGE_OPTIONS
)
from .app_config import FASTAPI_HOST, FASTAPI_PORT, STREAMLIT_PORT

# User-Configurable Parameters Collection
# This dictionary contains all parameters that users can modify, with their default values
USER_PARAMETERS = {
    # GUI Settings
    'auto_refresh_enabled': True,  # Default to enabled for better UX
    'auto_refresh_interval': AUTO_REFRESH_INTERVAL,
    'selected_timezone': DEFAULT_TIMEZONE,
    'time_range_selection': "Last 1000 points",
    
    # Data Collection Settings
    'collection_interval': DEFAULT_COLLECTION_INTERVAL,
    'api_request_timeout': API_REQUEST_TIMEOUT,
    
    # Data Display Limits
    'db_query_limit': DEFAULT_DB_QUERY_LIMIT,
    'api_response_limit': DEFAULT_API_LIMIT,
    'series_data_limit': DEFAULT_SERIES_LIMIT,
    'recent_entries_display': RECENT_ENTRIES_DISPLAY_LIMIT,
    
    # Rate Limiting Settings
    'rate_limit_interval': RATE_LIMIT_MIN_INTERVAL,
    'rate_limit_cache_duration': RATE_LIMIT_CACHE_DURATION,
    'max_calls_per_minute': RATE_LIMIT_MAX_CALLS_PER_MINUTE,
    
    # Server Configuration
    'fastapi_host': FASTAPI_HOST,
    'fastapi_port': FASTAPI_PORT,
    'streamlit_port': STREAMLIT_PORT,
    
    # Available Options for User Selection
    'timezone_options': None,  # Will be populated by timezone_utils
    'time_range_options': TIME_RANGE_OPTIONS,
}

# User Parameter Management Functions
def get_user_parameter(key: str, default=None):
    """Get a user parameter value, falling back to default if not found"""
    return USER_PARAMETERS.get(key, default)

def set_user_parameter(key: str, value):
    """Set a user parameter value"""
    if key in USER_PARAMETERS:
        USER_PARAMETERS[key] = value
        return True
    return False

def get_all_user_parameters():
    """Get a copy of all user parameters"""
    return USER_PARAMETERS.copy()

def update_user_parameters(updates: dict):
    """Update multiple user parameters at once"""
    for key, value in updates.items():
        if key in USER_PARAMETERS:
            USER_PARAMETERS[key] = value

def reset_user_parameters():
    """Reset all user parameters to their default values"""
    USER_PARAMETERS.update({
        'auto_refresh_enabled': False,
        'auto_refresh_interval': AUTO_REFRESH_INTERVAL,
        'selected_timezone': DEFAULT_TIMEZONE,
        'time_range_selection': "Last 1000 points",
        'collection_interval': DEFAULT_COLLECTION_INTERVAL,
        'api_request_timeout': API_REQUEST_TIMEOUT,
        'db_query_limit': DEFAULT_DB_QUERY_LIMIT,
        'api_response_limit': DEFAULT_API_LIMIT,
        'series_data_limit': DEFAULT_SERIES_LIMIT,
        'recent_entries_display': RECENT_ENTRIES_DISPLAY_LIMIT,
        'rate_limit_interval': RATE_LIMIT_MIN_INTERVAL,
        'rate_limit_cache_duration': RATE_LIMIT_CACHE_DURATION,
        'max_calls_per_minute': RATE_LIMIT_MAX_CALLS_PER_MINUTE,
        'fastapi_host': FASTAPI_HOST,
        'fastapi_port': FASTAPI_PORT,
        'streamlit_port': STREAMLIT_PORT,
        'time_range_options': TIME_RANGE_OPTIONS,
    })