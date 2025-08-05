# Crypto Analyser

A professional cryptocurrency price tracking application built with FastAPI and Streamlit. Features real-time price fetching, advanced rate limiting, timezone support, and comprehensive user configuration management.

## 🚀 Features

- **Real-time cryptocurrency price fetching** from CoinGecko API with intelligent rate limiting
- **Professional GUI dashboard** with Streamlit featuring auto-refresh and timezone conversion
- **Comprehensive configuration management** with centralized user parameters
- **SQLite database storage** with organized data folder structure
- **REST API endpoints** for data access and configuration management
- **Background scheduler** for automatic data collection
- **Statistical analysis** of price data with pandas
- **Multi-timezone support** including Israel Standard/Daylight Time
- **Rate limiting protection** to prevent API quota exhaustion

## 📁 Project Structure

```
crypto_analyser/
├── client/              # Frontend GUI components
│   └── gui_dashboard.py # Streamlit dashboard
├── server/              # Backend API and services
│   ├── api_server.py   # FastAPI application orchestrator
│   ├── bitcoin_service.py
│   ├── database.py
│   ├── scheduler.py
│   └── rate_limiter.py
├── core/               # Core configuration and utilities
│   ├── config.py       # Centralized configuration
│   └── timezone_utils.py
├── scripts/            # Application entry points
│   ├── run_with_gui.py
│   ├── run.py
│   └── stop_app.py
├── data/               # Database files
│   └── crypto_analyser.db
├── tests/              # Test files
└── docs/               # Documentation
```

## 🛠️ Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd crypto_analyser
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## 🎯 Usage

### Start with GUI Dashboard (Recommended):
```bash
python scripts/run_with_gui.py
```
This starts:
- FastAPI server on `http://localhost:8000`
- Streamlit GUI on `http://localhost:8501`
- Background price collection every 60 seconds
- Automatically opens both in your browser

### Alternative Entry Points:

#### API Server Only:
```bash
python scripts/run.py
```

#### GUI Only (requires API running):
```bash
streamlit run client/gui_dashboard.py
```

#### Server Entry Point:
```bash
python main.py
# or
python run_server.py
```

## 🖥️ GUI Features

The Streamlit dashboard includes:
- **Real-time cryptocurrency price display** with current price, market cap, and 24h volume
- **Interactive price chart** similar to CoinMarketCap with hover details and timezone conversion
- **24h trading volume chart** with timezone-aware time axis
- **Auto-refresh option** with configurable 60-second intervals
- **Multi-timezone support** with 30+ timezone options including Israel Standard/Daylight Time
- **Time range selector** (100, 500, 1000 points, or all data)
- **Statistics panel** with average, min, max prices and data point counts
- **Recent data table** showing latest price entries with timezone conversion
- **User settings panel** displaying all current configuration parameters
- **Data management** with clear data and application stop functionality
- **Settings reset** option to restore default configuration

## 🔧 User Configuration

The application features comprehensive user parameter management:

### Configurable Parameters:
- **Auto-refresh settings** (enabled/disabled, interval)
- **Timezone preferences** (30+ options including IST/IDT)
- **Data display limits** (query limits, series limits)
- **Rate limiting settings** (intervals, cache duration)
- **Server configuration** (ports, timeouts)
- **Collection intervals** (data fetching frequency)

### Settings Management:
- View all current settings in the GUI sidebar
- Reset to defaults with one click
- API endpoints for programmatic configuration
- Persistent parameter storage across sessions

## 🌐 API Endpoints

### Core Data Endpoints:
- `GET /` - API status and information
- `GET /price/current` - Get current cryptocurrency price
- `POST /price/collect` - Manually trigger price collection
- `GET /price/history?limit=100` - Get price history from database
- `GET /stats` - Get statistical analysis of collected data
- `GET /series/recent?limit=50` - Get recent data from pandas series
- `DELETE /data/clear` - Clear all stored data

### Configuration Management:
- `GET /config/user-parameters` - Get current user parameters
- `POST /config/user-parameters` - Update user parameters
- `POST /config/reset-parameters` - Reset parameters to defaults

### System Management:
- `POST /system/shutdown` - Gracefully shutdown the application
- `GET /debug/rate-limiter` - Check rate limiter status

## 📘 Example Usage

### Basic API Usage:
```python
import requests

# Get current crypto price
response = requests.get("http://localhost:8000/price/current")
print(response.json())

# Get statistics
response = requests.get("http://localhost:8000/stats")
print(response.json())

# Get price history
response = requests.get("http://localhost:8000/price/history?limit=10")
print(response.json())
```

### Configuration Management:
```python
import requests

# Get current user parameters
response = requests.get("http://localhost:8000/config/user-parameters")
config = response.json()["user_parameters"]
print(f"Current timezone: {config['selected_timezone']}")

# Update user parameters
update_data = {
    "selected_timezone": "Europe/London",
    "auto_refresh_interval": 30
}
response = requests.post("http://localhost:8000/config/user-parameters", json=update_data)
print(response.json())

# Reset to defaults
response = requests.post("http://localhost:8000/config/reset-parameters")
print(response.json())
```

## 💾 Data Storage

- **SQLite database**: `data/crypto_analyser.db` (organized in dedicated data folder)
- **Pandas series**: In-memory for fast analysis and real-time operations
- **Automatic data collection**: Every 60 seconds (user-configurable via USER_PARAMETERS)
- **Rate limiting**: 15-second minimum intervals with 30-second caching to prevent API abuse
- **Backup database**: `data/bitcoin_data.db` (legacy data preservation)

## 🏗️ Architecture

### Core Components:
- **FastAPI Server** (`server/api_server.py`): RESTful API with comprehensive endpoints
- **Streamlit GUI** (`client/gui_dashboard.py`): Interactive dashboard with real-time updates
- **Bitcoin Service** (`server/bitcoin_service.py`): CoinGecko API integration with rate limiting
- **Database Layer** (`server/database.py`): SQLAlchemy ORM with SQLite backend
- **Configuration Management** (`core/config.py`): Centralized parameter system
- **Timezone Utilities** (`core/timezone_utils.py`): Multi-timezone support

### Key Features:
- **Modular Design**: Clean separation of concerns across logical folders
- **Rate Limiting**: Global rate limiter prevents API quota exhaustion
- **Error Handling**: Comprehensive exception handling and graceful degradation
- **User Configuration**: Complete parameter management system
- **Professional Structure**: Industry-standard folder organization

## 📚 API Documentation

Visit `http://localhost:8000/docs` for interactive Swagger/OpenAPI documentation.

## 🚦 Rate Limiting

The application implements intelligent rate limiting to respect CoinGecko's API limits:
- **Minimum interval**: 15 seconds between API calls
- **Caching**: 30-second response caching
- **Global coordination**: Shared rate limiter across all components
- **Graceful handling**: Falls back to cached data when rate limited

## 🌍 Timezone Support

Supports 30+ timezones including:
- UTC (default)
- US timezones (Eastern, Central, Mountain, Pacific)
- European timezones (London, Paris, Berlin, Rome)
- Asian timezones (Tokyo, Shanghai, Kolkata, Jerusalem)
- Australian and American regional timezones

## 🛑 Stopping the Application

Multiple ways to stop the application:
- **GUI Stop Button**: Graceful shutdown via Streamlit interface
- **API Endpoint**: `POST /system/shutdown`
- **Script**: `python scripts/stop_app.py`
- **Keyboard**: Ctrl+C in terminal

## 🔄 Version History

- **v1.0.0**: Initial release with basic functionality
- **Current**: Professional refactoring with folder structure, user parameters, and enhanced features