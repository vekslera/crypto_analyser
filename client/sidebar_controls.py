"""
Sidebar controls module for GUI dashboard
Handles all sidebar interactions and controls
"""

import sys
import os
import streamlit as st
import time

# Add the project root and client folder to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
client_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, client_root)

from core.config import (
    GUI_HEADERS, BUTTON_LABELS, BUTTON_HELP, UI_MESSAGES, 
    GUI_REFRESH_LABEL, TIME_RANGE_OPTIONS,
    get_user_parameter, set_user_parameter, get_all_user_parameters
)
from core.timezone_utils import get_available_timezones, set_default_timezone
from data_operations import clear_all_data, shutdown_application


def render_control_buttons():
    """Render main control buttons"""
    st.sidebar.header(GUI_HEADERS['controls'])
    
    # Auto-refresh is now always enabled by default, no toggle needed
    auto_refresh = st.session_state.auto_refresh
    
    # Action buttons
    refresh_button = st.sidebar.button(BUTTON_LABELS['refresh_now'])
    clear_data_button = st.sidebar.button(BUTTON_LABELS['clear_data'], type="secondary")
    
    st.sidebar.markdown("---")
    stop_button = st.sidebar.button(BUTTON_LABELS['stop_app'], type="primary", help=BUTTON_HELP['stop_app'])
    
    return {
        'auto_refresh': auto_refresh,
        'refresh_button': refresh_button,
        'clear_data_button': clear_data_button,
        'stop_button': stop_button
    }


def render_timezone_selector():
    """Render timezone selection controls"""
    st.sidebar.header(GUI_HEADERS['timezone_settings'])
    
    available_timezones = get_available_timezones()
    try:
        current_index = available_timezones.index(st.session_state.selected_timezone)
    except ValueError:
        current_index = 0
    
    selected_timezone = st.sidebar.selectbox(
        "Select Timezone",
        available_timezones,
        index=current_index,
        help="Choose your local timezone for time display"
    )
    
    # Handle timezone change
    if selected_timezone != st.session_state.selected_timezone:
        st.session_state.selected_timezone = selected_timezone
        set_default_timezone(selected_timezone)
        set_user_parameter('selected_timezone', selected_timezone)
        st.rerun()
    
    return selected_timezone


def render_data_settings():
    """Render data settings controls"""
    st.sidebar.header(GUI_HEADERS['data_settings'])
    
    # Time range selector
    time_range_options = list(get_user_parameter('time_range_options', TIME_RANGE_OPTIONS).keys())
    try:
        current_range_index = time_range_options.index(st.session_state.time_range)
    except ValueError:
        current_range_index = 2  # Default to "Last 1000 points"
    
    time_range = st.sidebar.selectbox(
        "Time Range",
        time_range_options,
        index=current_range_index,
        help="Select how much historical data to display"
    )
    
    # Update time range in session state and USER_PARAMETERS
    if time_range != st.session_state.time_range:
        st.session_state.time_range = time_range
        set_user_parameter('time_range_selection', time_range)
    
    return time_range


def render_user_settings_panel():
    """Render user settings display panel"""
    with st.sidebar.expander("🔧 Current Settings", expanded=False):
        st.write("**User Configuration:**")
        user_params = get_all_user_parameters()
        
        # Display key user settings in a readable format
        key_settings = {
            'Auto Refresh': "✅ Enabled" if user_params.get('auto_refresh_enabled', False) else "❌ Disabled",
            'Refresh Interval': f"{user_params.get('auto_refresh_interval', 60)}s",
            'Timezone': user_params.get('selected_timezone', 'UTC'),
            'Time Range': user_params.get('time_range_selection', 'Last 1000 points'),
            'Collection Interval': f"{user_params.get('collection_interval', 60)}s",
            'API Timeout': f"{user_params.get('api_request_timeout', 10)}s",
            'Rate Limit Interval': f"{user_params.get('rate_limit_interval', 15)}s",
        }
        
        for key, value in key_settings.items():
            st.write(f"• **{key}:** {value}")
        
        st.markdown("---")
        
        # Auto-refresh control (less prominent location)
        col1, col2 = st.columns(2)
        with col1:
            if st.session_state.auto_refresh:
                if st.button("⏸️ Stop Auto-Refresh", help="Disable automatic data refresh", type="secondary"):
                    st.session_state.auto_refresh = False
                    set_user_parameter('auto_refresh_enabled', False)
                    st.success("Auto-refresh disabled")
                    st.rerun()
            else:
                if st.button("▶️ Start Auto-Refresh", help="Enable automatic data refresh", type="secondary"):
                    st.session_state.auto_refresh = True
                    set_user_parameter('auto_refresh_enabled', True)
                    st.success("Auto-refresh enabled")
                    st.rerun()
        
        with col2:
            if st.button("🔄 Reset to Defaults", help="Reset all settings to default values", type="secondary"):
                from core.config import reset_user_parameters
                reset_user_parameters()
                st.success("Settings reset to defaults!")
                st.rerun()


def handle_button_actions(controls):
    """Handle actions from control buttons"""
    actions = {
        'refresh_requested': False,
        'data_cleared': False,
        'app_shutdown': False
    }
    
    # Handle manual refresh
    if controls['refresh_button']:
        st.session_state.last_refresh = time.time()
        actions['refresh_requested'] = True
        st.rerun()
    
    # Handle clear data
    if controls['clear_data_button']:
        if clear_all_data():
            st.sidebar.success(UI_MESSAGES['data_cleared_success'])
            actions['data_cleared'] = True
        else:
            st.sidebar.error(UI_MESSAGES['failed_clear_data'])
    
    # Handle stop application
    if controls['stop_button']:
        st.session_state.stop_confirmation = True
    
    # Handle stop confirmation dialog
    if st.session_state.stop_confirmation:
        st.sidebar.warning(UI_MESSAGES['confirm_stop_warning'])
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            if st.button(BUTTON_LABELS['confirm_stop'], key="confirm_stop"):
                st.sidebar.info(UI_MESSAGES['shutting_down'])
                if shutdown_application():
                    st.sidebar.success(UI_MESSAGES['app_stopped'])
                    st.sidebar.info(UI_MESSAGES['close_browser'])
                    actions['app_shutdown'] = True
                    st.stop()
                else:
                    st.sidebar.success(UI_MESSAGES['shutdown_initiated'])
                    st.sidebar.info(UI_MESSAGES['close_browser'])
                    actions['app_shutdown'] = True
                    st.stop()
        
        with col2:
            if st.button(BUTTON_LABELS['cancel_stop'], key="cancel_stop"):
                st.session_state.stop_confirmation = False
                st.rerun()
    
    return actions


def render_all_sidebar_controls():
    """Render all sidebar controls and return their states"""
    # Render control sections
    controls = render_control_buttons()
    selected_timezone = render_timezone_selector()
    time_range = render_data_settings()
    render_user_settings_panel()
    
    # Handle button actions
    actions = handle_button_actions(controls)
    
    return {
        'controls': controls,
        'selected_timezone': selected_timezone,
        'time_range': time_range,
        'actions': actions
    }