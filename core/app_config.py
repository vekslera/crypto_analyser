"""
Core application configuration
Basic application settings and metadata
"""

# Application Information
APP_TITLE = "Crypto Analyser"
APP_VERSION = "1.0.0"
APP_ICON = "📊"

# Database Configuration
DATABASE_NAME = "crypto_analyser.db"
DATABASE_FOLDER = "data"
DATABASE_URL = f"sqlite:///./{DATABASE_FOLDER}/{DATABASE_NAME}"

# Server Configuration
FASTAPI_HOST = "0.0.0.0"
FASTAPI_PORT = 8000
STREAMLIT_PORT = 8501

# Local Server URLs
FASTAPI_URL = f"http://localhost:{FASTAPI_PORT}"
STREAMLIT_URL = f"http://localhost:{STREAMLIT_PORT}"
FASTAPI_DOCS_URL = f"{FASTAPI_URL}/docs"

# Timezone Configuration
DEFAULT_TIMEZONE = 'UTC'

# Timeout Configuration
API_REQUEST_TIMEOUT = 10  # seconds
SHUTDOWN_REQUEST_TIMEOUT = 5  # seconds
PROCESS_TERMINATION_TIMEOUT = 5  # seconds

# Startup Delays
FASTAPI_STARTUP_DELAY = 3  # seconds to wait for FastAPI to start
STREAMLIT_STARTUP_DELAY = 5  # seconds to wait before starting Streamlit
INITIAL_SETUP_DELAY = 2  # seconds for initial setup