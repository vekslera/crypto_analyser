"""
Data operations module for GUI dashboard (DIP compliant)
Handles data retrieval via API endpoints using dependency injection
"""

import sys
import os
import pandas as pd
import requests
from datetime import datetime
from typing import Optional, Dict, Any

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from core.config import DEFAULT_DB_QUERY_LIMIT, FASTAPI_URL


def get_price_data_from_db(time_params=None) -> pd.DataFrame:
    """Get price data via API endpoint (DIP compliant) with optional time filtering"""
    try:
        if time_params and 'start_time' in time_params and 'end_time' in time_params:
            # Use time-range endpoint
            api_url = f"{FASTAPI_URL}/price/history/range"
            params = time_params
        else:
            # Use limit-based endpoint for backwards compatibility
            api_url = f"{FASTAPI_URL}/price/history"
            params = {"limit": DEFAULT_DB_QUERY_LIMIT}
            
        response = requests.get(api_url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                df = pd.DataFrame(data)
                # Convert timestamp strings to datetime objects (handle mixed formats)
                if 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'], format='mixed', utc=True)
                return df
        return pd.DataFrame()
        
    except Exception as e:
        print(f"Error fetching price data from API: {e}")
        return pd.DataFrame()


def get_current_price_from_api() -> Optional[Dict[str, Any]]:
    """Fetch current price via API endpoint (DIP compliant)"""
    try:
        api_url = f"{FASTAPI_URL}/price/current"
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # Convert to expected format
            return {
                'price': data['price'],
                'timestamp': datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00')),
                'volume_24h': data.get('volume_24h'),
                'volume_velocity': data.get('volume_velocity'),
                'market_cap': data.get('market_cap')
            }
        return None
        
    except Exception as e:
        print(f"Error fetching current price from API: {e}")
        return None


def clear_all_data() -> bool:
    """Clear all data via API endpoint (DIP compliant)"""
    try:
        api_url = f"{FASTAPI_URL}/data/clear"
        response = requests.delete(api_url, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Error clearing data: {e}")
        return False


def shutdown_application() -> bool:
    """Shutdown application via API endpoint (DIP compliant)"""
    try:
        api_url = f"{FASTAPI_URL}/system/shutdown"
        response = requests.post(api_url, timeout=5)
        return response.status_code == 200
    except requests.exceptions.Timeout:
        # Connection timeout is expected during shutdown
        return True
    except Exception as e:
        print(f"Error shutting down application: {e}")
        return False


def get_statistics() -> Optional[Dict[str, Any]]:
    """Get price statistics via API endpoint (DIP compliant)"""
    try:
        api_url = f"{FASTAPI_URL}/stats"
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        return None
        
    except Exception as e:
        print(f"Error fetching statistics: {e}")
        return None


def trigger_price_collection() -> bool:
    """Trigger manual price collection via API endpoint (DIP compliant)"""
    try:
        api_url = f"{FASTAPI_URL}/price/collect"
        response = requests.post(api_url, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Error triggering price collection: {e}")
        return False


def fill_data_gaps() -> Optional[Dict[str, Any]]:
    """Fill data gaps via API endpoint (DIP compliant)"""
    try:
        api_url = f"{FASTAPI_URL}/data/fill-gaps"
        response = requests.post(api_url, timeout=60)  # Longer timeout for gap filling
        
        if response.status_code == 200:
            return response.json()
        return None
        
    except Exception as e:
        print(f"Error filling data gaps: {e}")
        return None


def detect_data_gaps() -> Optional[Dict[str, Any]]:
    """Detect data gaps via API endpoint (DIP compliant)"""
    try:
        api_url = f"{FASTAPI_URL}/data/gaps"
        response = requests.get(api_url, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        return None
        
    except Exception as e:
        print(f"Error detecting data gaps: {e}")
        return None


def create_database_backup() -> Optional[Dict[str, Any]]:
    """Create database backup via API endpoint (DIP compliant)"""
    try:
        api_url = f"{FASTAPI_URL}/data/backup"
        response = requests.post(api_url, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        return None
        
    except Exception as e:
        print(f"Error creating backup: {e}")
        return None


def list_database_backups() -> Optional[Dict[str, Any]]:
    """List database backups via API endpoint (DIP compliant)"""
    try:
        api_url = f"{FASTAPI_URL}/data/backups"
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        return None
        
    except Exception as e:
        print(f"Error listing backups: {e}")
        return None


def recalculate_volatility(days_back: int = 35) -> Optional[Dict[str, Any]]:
    """Recalculate volatility for recent data via API endpoint (DIP compliant)"""
    try:
        api_url = f"{FASTAPI_URL}/data/recalculate-volatility"
        response = requests.post(api_url, params={"days_back": days_back}, timeout=60)
        
        if response.status_code == 200:
            return response.json()
        return None
        
    except Exception as e:
        print(f"Error recalculating volatility: {e}")
        return None