# Bitcoin Price Tracker

A FastAPI application that fetches real-time Bitcoin-USD exchange rates, processes them with pandas, and stores them in a SQLite database.

## Features

- Real-time Bitcoin price fetching from CoinGecko API
- Pandas data series for time series analysis
- SQLite database storage
- REST API endpoints for data access
- Background scheduler for automatic data collection
- Statistical analysis of price data

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Start with GUI Dashboard (Recommended):
```bash
python run_with_gui.py
```
This starts:
- FastAPI server on `http://localhost:8000`
- Streamlit GUI on `http://localhost:8501`
- Background price collection every 60 seconds
- Automatically opens both in your browser

### Alternative - Start API only:
```bash
python run.py
```

### Alternative - Run GUI only (requires API running):
```bash
streamlit run gui_dashboard.py
```

### Alternative - Run FastAPI only:
```bash
python main.py
```

### Alternative - Run scheduler only:
```bash
python scheduler.py
```

## GUI Features

The Streamlit dashboard includes:
- **Real-time Bitcoin price display** with current price, market cap, and 24h volume
- **Interactive price chart** similar to CoinMarketCap with hover details
- **24h trading volume chart** (when data available)
- **Auto-refresh option** (60-second intervals)
- **Time range selector** (100, 500, 1000 points, or all data)
- **Statistics panel** with average, min, max prices
- **Recent data table** showing latest price entries
- **Data management** with clear data option

## API Endpoints

- `GET /` - API status
- `GET /price/current` - Get current Bitcoin price
- `POST /price/collect` - Manually trigger price collection
- `GET /price/history?limit=100` - Get price history from database
- `GET /stats` - Get statistical analysis of collected data
- `GET /series/recent?limit=50` - Get recent data from pandas series
- `DELETE /data/clear` - Clear all stored data

## Example Usage

```python
import requests

# Get current price
response = requests.get("http://localhost:8000/price/current")
print(response.json())

# Get statistics
response = requests.get("http://localhost:8000/stats")
print(response.json())

# Get price history
response = requests.get("http://localhost:8000/price/history?limit=10")
print(response.json())
```

## Data Storage

- SQLite database: `bitcoin_data.db`
- Pandas series: In-memory for fast analysis
- Automatic data collection every 60 seconds (configurable)

## API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.