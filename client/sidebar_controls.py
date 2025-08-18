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
from data_operations import clear_all_data, fill_data_gaps, detect_data_gaps, create_database_backup, list_database_backups, recalculate_volatility


def render_chart_selector():
    """Render multiple chart selection checkboxes"""
    st.sidebar.header("📊 Chart Selection")
    
    # Initialize default chart selections in session state
    if 'chart_selections' not in st.session_state:
        st.session_state.chart_selections = {
            'price': True,
            'volume': False, 
            'volatility': True
        }
    
    # Multiple chart selection checkboxes
    st.sidebar.write("Choose charts to display:")
    
    # Price checkbox
    st.session_state.chart_selections['price'] = st.sidebar.checkbox(
        "Price",
        value=st.session_state.chart_selections['price'],
        help="Show/hide Bitcoin price chart"
    )
    
    # Volume checkbox  
    st.session_state.chart_selections['volume'] = st.sidebar.checkbox(
        "24h Trading Volume",
        value=st.session_state.chart_selections['volume'],
        help="Show/hide 24h trading volume chart"
    )
    
    # Volatility checkbox
    st.session_state.chart_selections['volatility'] = st.sidebar.checkbox(
        "24h Volatility", 
        value=st.session_state.chart_selections['volatility'],
        help="Show/hide 24h volatility chart"
    )
    
    # Build selected charts list
    selected_charts = [
        key for key, value in st.session_state.chart_selections.items() 
        if value
    ]
    
    return selected_charts


def render_control_buttons():
    """Render main control buttons"""
    st.sidebar.header(GUI_HEADERS['controls'])
    
    # Auto-refresh is now always enabled by default, no toggle needed
    auto_refresh = st.session_state.auto_refresh
    
    # Action buttons
    refresh_button = st.sidebar.button(BUTTON_LABELS['refresh_now'])
    clear_data_button = st.sidebar.button(BUTTON_LABELS['clear_data'], type="secondary")
    
    # Gap filling button
    fill_gaps_button = st.sidebar.button(
        "🔧 Fill Data Gaps", 
        help="Detect and fill missing data using CoinGecko API",
        type="secondary"
    )
    
    # Backup button
    backup_button = st.sidebar.button(
        "💾 Create Backup", 
        help="Create a backup of the database",
        type="secondary"
    )
    
    # Volatility calculation button
    volatility_button = st.sidebar.button(
        "📊 Recalculate Volatility", 
        help="Recalculate volatility for recent data",
        type="secondary"
    )
    
    return {
        'auto_refresh': auto_refresh,
        'refresh_button': refresh_button,
        'clear_data_button': clear_data_button,
        'fill_gaps_button': fill_gaps_button,
        'backup_button': backup_button,
        'volatility_button': volatility_button
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
    
    # Time range selector - session state should already be initialized
    time_range_options = list(get_user_parameter('time_range_options', TIME_RANGE_OPTIONS).keys())
    
    # The widget key should already be initialized in initialize_session_state()
    widget_key = "time_range_select"
    
    time_range = st.sidebar.selectbox(
        "Time Range",
        options=time_range_options,
        key=widget_key,
        help="Select time period for historical data display"
    )
    
    # Sync the main time_range session state with the widget value
    if st.session_state.time_range != time_range:
        st.session_state.time_range = time_range
        set_user_parameter('time_range_selection', time_range)
        # Clear cache to refresh data
        if hasattr(st.session_state, 'last_data_fetch'):
            st.session_state.last_data_fetch = 0
    
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
            'Time Range': user_params.get('time_range_selection', 'Last 7 days'),
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
        'gaps_filled': False,
        'backup_created': False,
        'volatility_recalculated': False
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
    
    # Handle gap filling
    if controls['fill_gaps_button']:
        with st.sidebar:
            with st.spinner("Detecting data gaps..."):
                gaps_info = detect_data_gaps()
                
                if gaps_info and gaps_info.get('gaps_found', 0) > 0:
                    st.info(f"Found {gaps_info['gaps_found']} gaps totaling {gaps_info['total_gap_hours']:.1f} hours")
                    
                    with st.spinner("Filling data gaps..."):
                        result = fill_data_gaps()
                        
                        if result and result.get('success'):
                            st.success(f"✅ {result['message']}")
                            st.info(f"Filled {result['gaps_filled']} gaps with {result['records_inserted']} records")
                            actions['gaps_filled'] = True
                            # Clear cache to refresh data
                            if hasattr(st.session_state, 'last_data_fetch'):
                                st.session_state.last_data_fetch = 0
                        else:
                            error_msg = result.get('message', 'Unknown error') if result else 'API call failed'
                            st.error(f"❌ Gap filling failed: {error_msg}")
                else:
                    st.success("✅ No gaps found! Database has continuous coverage.")
    
    # Handle backup creation
    if controls['backup_button']:
        with st.sidebar:
            with st.spinner("Creating database backup..."):
                result = create_database_backup()
                
                if result and result.get('message'):
                    st.success(f"✅ {result['message']}")
                    st.info(f"Backup file: {result.get('backup_file', 'N/A')}")
                    st.info(f"Records backed up: {result.get('record_count', 'N/A'):,}")
                    actions['backup_created'] = True
                else:
                    st.error("❌ Backup creation failed")
    
    # Handle volatility recalculation
    if controls['volatility_button']:
        with st.sidebar:
            with st.spinner("Recalculating volatility for recent data..."):
                result = recalculate_volatility(days_back=35)
                
                if result and result.get('message'):
                    st.success(f"✅ {result['message']}")
                    st.info(f"Records updated: {result.get('records_updated', 0):,}")
                    actions['volatility_recalculated'] = True
                    # Clear cache to refresh data
                    if hasattr(st.session_state, 'last_data_fetch'):
                        st.session_state.last_data_fetch = 0
                else:
                    st.error("❌ Volatility recalculation failed")
    
    return actions


def render_all_sidebar_controls():
    """Render all sidebar controls and return their states"""
    # Render control sections in order (chart selector at top)
    selected_charts = render_chart_selector()
    controls = render_control_buttons()
    selected_timezone = render_timezone_selector()
    time_range = render_data_settings()
    render_user_settings_panel()
    
    # Handle button actions
    actions = handle_button_actions(controls)
    
    return {
        'selected_charts': selected_charts,
        'controls': controls,
        'selected_timezone': selected_timezone,
        'time_range': time_range,
        'actions': actions
    }