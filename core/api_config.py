"""
API configuration and settings
External API settings, rate limiting, and data collection parameters
"""
import os

# API Configuration
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
COINGECKO_PING_URL = f"{COINGECKO_BASE_URL}/ping"

# API Endpoints
from .app_config import FASTAPI_URL
ENDPOINT_DATA_CLEAR = f"{FASTAPI_URL}/data/clear"
ENDPOINT_SYSTEM_SHUTDOWN = f"{FASTAPI_URL}/system/shutdown"

# Rate Limiting Configuration
RATE_LIMIT_MIN_INTERVAL = 15  # seconds between API calls
RATE_LIMIT_CACHE_DURATION = 30  # seconds to cache API responses
RATE_LIMIT_MAX_CALLS_PER_MINUTE = 4

# Scheduler Configuration
DEFAULT_COLLECTION_INTERVAL = 300  # seconds between collections (CoinGecko - 5 minutes)
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

# Time Ranges for GUI (now using time periods instead of point counts)
TIME_RANGE_OPTIONS = {
    "Last 24 hours": {"hours": 24},
    "Last 7 days": {"days": 7},
    "Last 30 days": {"days": 30},
    "Last 1 year": {"days": 365},
    "Last 5 years": {"days": 1825},
    "All data": None
}

# HTTP Status Codes
HTTP_OK = 200
HTTP_NOT_FOUND = 404
HTTP_RATE_LIMIT = 429
HTTP_SERVICE_UNAVAILABLE = 503
HTTP_INTERNAL_ERROR = 500

# CoinMarketCap API Key filename
CMC_API_KEY = os.environ.get("CMC_API_KEY")
CG_API_KEY = os.environ.get("CG_API_KEY")

# API Parameters
COINGECKO_PARAMS = {

    'ids': 'bitcoin',
    'vs_currencies': 'usd',
    'include_market_cap': 'true',
    'include_24hr_vol': 'true',
    'include_last_updated_at': 'true',
    'x_cg_demo_api_key': CG_API_KEY
}

