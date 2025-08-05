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
    # Auto refresh settings (default to True for better UX)
    if 'auto_refresh' not in st.session_state:
        st.session_state.auto_refresh = get_user_parameter('auto_refresh_enabled', True)
    
    # Timezone settings
    if 'selected_timezone' not in st.session_state:
        st.session_state.selected_timezone = get_user_parameter('selected_timezone', get_default_timezone())
    
    # Refresh timing
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = time.time()
    
    # UI state
    if 'stop_confirmation' not in st.session_state:
        st.session_state.stop_confirmation = False
    
    # Data display settings
    if 'time_range' not in st.session_state:
        st.session_state.time_range = get_user_parameter('time_range_selection', "Last 1000 points")
    
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


def should_fetch_historical_data(data_limit):
    """Determine if historical data should be fetched"""
    return (
        st.session_state.historical_data is None or
        time.time() - st.session_state.last_data_fetch >= AUTO_REFRESH_INTERVAL or
        len(st.session_state.historical_data) != data_limit  # Refetch if limit changed
    )


def update_historical_data_cache(df):
    """Update the historical data in session state cache"""
    if df is not None and not df.empty:
        st.session_state.historical_data = df
        st.session_state.last_data_fetch = time.time()


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


def get_data_limit_from_time_range(time_range):
    """Convert time range selection to data limit"""
    from core.config import TIME_RANGE_OPTIONS
    limit_map = TIME_RANGE_OPTIONS
    return limit_map.get(time_range)