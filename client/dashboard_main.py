"""
Main dashboard module for Crypto Analyser GUI
Orchestrates all dashboard components following Single Responsibility Principle
"""

import sys
import os
import streamlit as st

# Add the project root and client folder to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
client_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, client_root)

# Import modular components
from session_manager import (
    initialize_page_config, 
    initialize_session_state, 
    should_fetch_current_price,
    update_current_price_cache,
    should_fetch_historical_data,
    update_historical_data_cache,
    handle_auto_refresh,
    get_data_limit_from_time_range
)
from ui_components import (
    apply_custom_css,
    show_main_header,
    display_price_cards,
    display_statistics_metrics,
    display_recent_data_table,
    display_no_data_message,
    display_footer
)
from sidebar_controls import render_all_sidebar_controls
from chart_components import create_price_chart, create_volume_chart, create_statistics_display
from data_operations import get_price_data_from_db, get_current_price_from_api


def main():
    """Main dashboard function that orchestrates all components"""
    # Initialize page and session
    initialize_page_config()
    initialize_session_state()
    apply_custom_css()
    
    # Show main header
    show_main_header()
    
    # Render sidebar controls and get current states
    sidebar_state = render_all_sidebar_controls()
    
    # Extract values from sidebar state
    auto_refresh_enabled = sidebar_state['controls']['auto_refresh']
    selected_timezone = sidebar_state['selected_timezone']
    time_range = sidebar_state['time_range']
    
    # Get current price if needed
    if should_fetch_current_price(auto_refresh_enabled):
        current_price_data = get_current_price_from_api()
        update_current_price_cache(current_price_data)
    else:
        current_price_data = st.session_state.get('current_price')
    
    # Display current price cards
    if current_price_data:
        display_price_cards(current_price_data)
    
    # Get historical data with caching
    data_limit = get_data_limit_from_time_range(time_range)
    if should_fetch_historical_data(data_limit):
        df = get_price_data_from_db(data_limit)
        update_historical_data_cache(df)
    else:
        df = st.session_state.historical_data
    
    if not df.empty:
        # Main price chart
        st.plotly_chart(
            create_price_chart(df, selected_timezone), 
            use_container_width=True
        )
        
        # Statistics metrics
        stats = create_statistics_display(df)
        display_statistics_metrics(stats)
        
        # Volume chart (if available)
        if 'volume_24h' in df.columns and df['volume_24h'].notna().any():
            st.plotly_chart(
                create_volume_chart(df, selected_timezone), 
                use_container_width=True
            )
        
        # Recent data table
        display_recent_data_table(df, selected_timezone)
        
    else:
        # No data available
        display_no_data_message()
    
    # Handle auto-refresh timing
    handle_auto_refresh(auto_refresh_enabled)
    
    # Display footer
    display_footer()


if __name__ == "__main__":
    main()