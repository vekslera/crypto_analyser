"""
User interface configuration
Colors, styling, labels, and GUI-related settings
"""

# CSS Colors and Styling
COLORS = {
    'bitcoin_orange': '#F7931A',
    'bitcoin_light': '#FFB84D',
    'text_dark': '#1f2937',
    'grid_light': '#e5e7eb',
    'background_light': '#f0f2f6',
    'blue': '#3b82f6'
}

# CSS Measurements
CSS_SIZES = {
    'header_font_size': '3rem',
    'chart_title_font_size': 20,
    'card_padding': '20px',
    'card_border_radius': '10px',
    'card_margin': '10px 0',
    'metric_card_padding': '15px',
    'metric_card_border_radius': '8px',
    'metric_card_margin': '5px 0',
    'chart_height': 500,
    'volume_chart_height': 300,
    'line_width': 2
}

# GUI Layout
GUI_COLUMNS = {
    'price_display': 3,
    'statistics': 4,
    'confirmation_buttons': 2
}

# Chart Configuration
CHART_CONFIG = {
    'price_line_color': COLORS['bitcoin_orange'],
    'volume_bar_color': COLORS['blue'],
    'grid_color': COLORS['grid_light'],
    'background_color': 'white',
    'hover_mode': 'x unified',
    'tick_format_currency': '$,.0f',
    'tick_format_price': '$,.2f'
}

# Messages and Labels
MESSAGES = {
    'api_root': "Crypto Analyser API",
    'status_running': "running",
    'data_cleared': "All data cleared successfully",
    'no_data_available': "No data available",
    'unable_to_fetch': "Unable to fetch current price",
    'server_shutdown': "Server shutdown initiated",
    'status_shutting_down': "shutting_down",
    'startup_gui': "Starting Crypto Analyser with GUI...",
    'startup_services': "Press Ctrl+C to stop all services",
    'fastapi_starting': f"FastAPI server starting on http://localhost:8000",
    'streamlit_starting': f"Starting Streamlit GUI on http://localhost:8501",
    'stopping_app': "Stopping Crypto Analyser...",
    'no_historical_data': "No historical data available. Start the data collection service first!",
    'start_collection': "Run `python run.py` to start collecting crypto price data.",
    'data_source_footer': f"**Data Source:** CoinGecko API | **Collection Rate:** 300 seconds | **Auto-refresh:** 60 seconds (when enabled)"
}

# Logging Messages
LOG_MESSAGES = {
    'price_fetched': "Fetched Bitcoin price: ${price:,.2f}",
    'price_stored': "Successfully collected and stored Bitcoin price: ${price:,.2f}",
    'rate_limit_wait': "Global rate limiter: waiting {wait_time:.1f} seconds",
    'rate_limit_error': "429 rate limit error - enforcing delay",
    'api_call_completed': "API call #{call_count} completed successfully",
    'using_cached_data': "Returning cached data",
    'cached_due_to_error': "Returning cached data due to API error"
}

# GUI Section Headers
GUI_HEADERS = {
    'controls': "Controls",
    'timezone_settings': "🌍 Timezone Settings",
    'data_settings': "📊 Data Settings"
}

# Button Labels
BUTTON_LABELS = {
    'refresh_now': "🔄 Refresh Now",
    'clear_data': "🗑️ Clear All Data",
    'stop_app': "🛑 Stop Application",
    'confirm_stop': "✅ Yes, Stop",
    'cancel_stop': "❌ Cancel"
}

# Button Help Text
BUTTON_HELP = {
    'stop_app': "Gracefully shutdown the entire Crypto Analyser application"
}

# Metric Labels
METRIC_LABELS = {
    'current_price': "Current Bitcoin Price",
    'market_cap': "Market Cap",
    'volume_24h': "24h Volume",
    'volume_velocity': "Volume Velocity (USD/min)",
    'data_points': "Data Points",
    'average_price': "Average Price",
    'min_price': "Min Price",
    'max_price': "Max Price"
}

# Chart Titles and Labels
CHART_LABELS = {
    'main_title': "📊 Crypto Analyser",
    'price_chart_title': "Bitcoin Price Chart ({timezone})",
    'volume_chart_title': "24h Trading Volume ({timezone})",
    'velocity_chart_title': "Volume Velocity ({timezone})",
    'recent_data_title': "Recent Price Data ({timezone})",
    'time_axis': "Time",
    'price_axis': "Price (USD)",
    'volume_axis': "Volume (USD)",
    'velocity_axis': "Volume Velocity (USD/min)",
    'volume_name': "24h Volume",
    'velocity_name': "Volume Velocity"
}

# Warning and Info Messages
UI_MESSAGES = {
    'confirm_stop_warning': "⚠️ Are you sure you want to stop the application?",
    'shutting_down': "Shutting down application...",
    'app_stopped': "Application stopped successfully!",
    'close_browser': "You can close this browser tab now.",
    'shutdown_initiated': "Shutdown initiated (connection timed out as expected)",
    'click_confirm': "Click 'Confirm Stop' to shutdown the application",
    'auto_refresh_countdown': "Auto-refresh in: {seconds} seconds",
    'data_cleared_success': "Data cleared successfully!",
    'failed_clear_data': "Failed to clear data",
    'failed_stop_app': "Failed to stop application",
    'could_not_connect': "Could not connect to API"
}