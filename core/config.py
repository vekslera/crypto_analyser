"""
Configuration file for Crypto Analyser
Contains all constants, URLs, and configuration values
"""

# Application Information
APP_TITLE = "Crypto Analyser"
APP_VERSION = "1.0.0"
APP_ICON = "📊"

# Database Configuration
DATABASE_NAME = "crypto_analyser.db"
DATABASE_FOLDER = "data"
DATABASE_URL = f"sqlite:///./{DATABASE_FOLDER}/{DATABASE_NAME}"

# API Configuration
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
COINGECKO_PING_URL = f"{COINGECKO_BASE_URL}/ping"

# Server Configuration
FASTAPI_HOST = "0.0.0.0"
FASTAPI_PORT = 8000
STREAMLIT_PORT = 8501

# Local Server URLs
FASTAPI_URL = f"http://localhost:{FASTAPI_PORT}"
STREAMLIT_URL = f"http://localhost:{STREAMLIT_PORT}"
FASTAPI_DOCS_URL = f"{FASTAPI_URL}/docs"

# API Endpoints
ENDPOINT_DATA_CLEAR = f"{FASTAPI_URL}/data/clear"
ENDPOINT_SYSTEM_SHUTDOWN = f"{FASTAPI_URL}/system/shutdown"

# Rate Limiting Configuration
RATE_LIMIT_MIN_INTERVAL = 15  # seconds between API calls
RATE_LIMIT_CACHE_DURATION = 30  # seconds to cache API responses
RATE_LIMIT_MAX_CALLS_PER_MINUTE = 4

# Scheduler Configuration
DEFAULT_COLLECTION_INTERVAL = 60  # seconds between price collections
SCHEDULER_SLEEP_INTERVAL = 1  # seconds to sleep in scheduler loop

# GUI Configuration
AUTO_REFRESH_INTERVAL = 60  # seconds between GUI auto-refreshes
AUTO_REFRESH_MAX_SLEEP = 5  # maximum seconds to sleep during refresh countdown
GUI_REFRESH_LABEL = f"Auto Refresh ({AUTO_REFRESH_INTERVAL}s)"

# Data Limits
DEFAULT_DB_QUERY_LIMIT = 1000
DEFAULT_API_LIMIT = 100
DEFAULT_SERIES_LIMIT = 50
RECENT_ENTRIES_DISPLAY_LIMIT = 10
RECENT_DATA_TAIL_LIMIT = 10

# Time Ranges for GUI
TIME_RANGE_OPTIONS = {
    "Last 100 points": 100,
    "Last 500 points": 500,
    "Last 1000 points": 1000,
    "All data": None
}

# Timeout Configuration
API_REQUEST_TIMEOUT = 10  # seconds
SHUTDOWN_REQUEST_TIMEOUT = 5  # seconds
PROCESS_TERMINATION_TIMEOUT = 5  # seconds

# Startup Delays
FASTAPI_STARTUP_DELAY = 3  # seconds to wait for FastAPI to start
STREAMLIT_STARTUP_DELAY = 5  # seconds to wait before starting Streamlit
INITIAL_SETUP_DELAY = 2  # seconds for initial setup

# HTTP Status Codes
HTTP_OK = 200
HTTP_NOT_FOUND = 404
HTTP_RATE_LIMIT = 429
HTTP_SERVICE_UNAVAILABLE = 503
HTTP_INTERNAL_ERROR = 500

# API Parameters
COINGECKO_PARAMS = {
    'ids': 'bitcoin',
    'vs_currencies': 'usd',
    'include_market_cap': 'true',
    'include_24hr_vol': 'true',
    'include_last_updated_at': 'true'
}

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

# Timezone Configuration
DEFAULT_TIMEZONE = 'UTC'

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
    'fastapi_starting': f"FastAPI server starting on {FASTAPI_URL}",
    'streamlit_starting': f"Starting Streamlit GUI on {STREAMLIT_URL}",
    'stopping_app': "Stopping Crypto Analyser...",
    'no_historical_data': "No historical data available. Start the data collection service first!",
    'start_collection': "Run `python run.py` to start collecting crypto price data.",
    'data_source_footer': f"**Data Source:** CoinGecko API | **Collection Rate:** {DEFAULT_COLLECTION_INTERVAL} seconds | **Auto-refresh:** {AUTO_REFRESH_INTERVAL} seconds (when enabled)"
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
    'recent_data_title': "Recent Price Data ({timezone})",
    'time_axis': "Time",
    'price_axis': "Price (USD)",
    'volume_axis': "Volume (USD)",
    'volume_name': "24h Volume"
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