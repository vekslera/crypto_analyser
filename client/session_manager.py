"""
Session management module for GUI dashboard
Handles Streamlit session state initialization and management
"""

import sys
import os
import streamlit as st
import time

# Add the project root to Python path BEFORE any imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from core.config import APP_TITLE, APP_ICON, get_user_parameter, AUTO_REFRESH_INTERVAL
from core.timezone_utils import get_default_timezone


def initialize_page_config():
    """Initialize Streamlit page configuration"""
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=APP_ICON,
        layout="wide"
    )


def initialize_session_state():
    """Initialize session state with USER_PARAMETERS defaults"""
    # Initialize time range FIRST to prevent widget conflicts
    if 'time_range' not in st.session_state:
        from core.config import TIME_RANGE_OPTIONS
        default_time_range = "Last 7 days"
        # Ensure the default exists in our options
        if default_time_range in TIME_RANGE_OPTIONS:
            st.session_state.time_range = get_user_parameter('time_range_selection', default_time_range)
        else:
            # Fallback to first available option
            st.session_state.time_range = list(TIME_RANGE_OPTIONS.keys())[0]
    
    # Also initialize the widget-specific key
    if 'time_range_select' not in st.session_state:
        st.session_state.time_range_select = st.session_state.time_range
    
    # Auto refresh settings (default to True for better UX)
    if 'auto_refresh' not in st.session_state:
        st.session_state.auto_refresh = get_user_parameter('auto_refresh_enabled', True)
    
    # Timezone settings
    if 'selected_timezone' not in st.session_state:
        st.session_state.selected_timezone = get_user_parameter('selected_timezone', get_default_timezone())
    
    # Refresh timing
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = time.time()
    
    # Current price cache
    if 'current_price' not in st.session_state:
        st.session_state.current_price = None
    
    # Historical data cache
    if 'historical_data' not in st.session_state:
        st.session_state.historical_data = None
    
    # Last data fetch time
    if 'last_data_fetch' not in st.session_state:
        st.session_state.last_data_fetch = 0


def should_fetch_current_price(auto_refresh_enabled):
    """Determine if current price should be fetched"""
    return (
        'current_price' not in st.session_state or
        st.session_state.current_price is None or
        (auto_refresh_enabled and time.time() - st.session_state.last_refresh >= AUTO_REFRESH_INTERVAL)
    )


def update_current_price_cache(price_data):
    """Update the current price in session state cache"""
    if price_data:
        st.session_state.current_price = price_data


def should_fetch_historical_data(cache_key):
    """Determine if historical data should be fetched based on cache key"""
    return (
        st.session_state.historical_data is None or
        time.time() - st.session_state.last_data_fetch >= AUTO_REFRESH_INTERVAL or
        getattr(st.session_state, 'last_cache_key', None) != cache_key  # Refetch if time range changed
    )


def update_historical_data_cache(df, cache_key=None):
    """Update the historical data in session state cache"""
    if df is not None and not df.empty:
        st.session_state.historical_data = df
        st.session_state.last_data_fetch = time.time()
        if cache_key:
            st.session_state.last_cache_key = cache_key


def handle_auto_refresh(auto_refresh_enabled):
    """Handle auto-refresh logic with proper timing"""
    if auto_refresh_enabled:
        current_time = time.time()
        time_since_last = current_time - st.session_state.last_refresh
        
        if time_since_last >= AUTO_REFRESH_INTERVAL:
            st.session_state.last_refresh = current_time
            st.rerun()
        else:
            # Show countdown to next refresh
            time_remaining = AUTO_REFRESH_INTERVAL - time_since_last
            st.sidebar.info(f"Auto-refresh in: {int(time_remaining)} seconds")
            
            # Use Streamlit's automatic rerun mechanism with timer
            # Schedule a rerun when the time is up
            time.sleep(1)  # Small delay to update the countdown
            st.rerun()


def get_time_range_params(time_range):
    """Convert time range selection to API parameters"""
    from core.config import TIME_RANGE_OPTIONS
    from datetime import datetime, timedelta
    
    time_config = TIME_RANGE_OPTIONS.get(time_range)
    
    if time_config is None:  # "All data"
        return None
    
    # Calculate timestamp for the time range
    now = datetime.utcnow()
    if 'hours' in time_config:
        start_time = now - timedelta(hours=time_config['hours'])
    elif 'days' in time_config:
        start_time = now - timedelta(days=time_config['days'])
    else:
        return None
    
    return {
        'start_time': start_time.isoformat(),
        'end_time': now.isoformat()
    }