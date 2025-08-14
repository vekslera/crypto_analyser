#!/usr/bin/env python3
"""
Debug script to check series data vs current price endpoint
"""

import sys
import os
import requests
import pandas as pd

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from core.config import FASTAPI_URL

def debug_series_data():
    """Debug what's in the series vs what current endpoint returns"""
    
    print("DEBUGGING SERIES DATA")
    print("=" * 40)
    
    try:
        # Get series data
        print("1. Fetching series data...")
        series_response = requests.get(f"{FASTAPI_URL}/series/recent?limit=5", timeout=10)
        
        if series_response.status_code == 200:
            series_data = series_response.json()
            print(f"   Series count: {series_data['count']}")
            print(f"   Latest timestamp: {series_data['latest_timestamp']}")
            print(f"   Data items: {len(series_data['data'])}")
            
            if series_data['data']:
                print("\n   Recent series data:")
                series_items = list(series_data['data'].items())
                for i, (timestamp, price) in enumerate(series_items[-3:]):  # Last 3
                    print(f"     {i+1}. {timestamp}: ${price:,.2f}")
        else:
            print(f"   Error: HTTP {series_response.status_code}")
        
        # Get current price endpoint
        print(f"\n2. Fetching current price endpoint...")
        current_response = requests.get(f"{FASTAPI_URL}/price/current", timeout=10)
        
        if current_response.status_code == 200:
            current_data = current_response.json()
            print(f"   Current price: ${current_data['price']:,.2f}")
            print(f"   Current timestamp: {current_data['timestamp']}")
            print(f"   Volume: ${current_data.get('volume_24h', 0):,.0f}")
        else:
            print(f"   Error: HTTP {current_response.status_code}")
            print(f"   Response: {current_response.text}")
        
        # Get database data for comparison
        print(f"\n3. Fetching recent database data...")
        db_response = requests.get(f"{FASTAPI_URL}/price/history?limit=2", timeout=10)
        
        if db_response.status_code == 200:
            db_data = db_response.json()
            print(f"   DB records: {len(db_data)}")
            if db_data:
                latest_db = db_data[0]  # Most recent
                print(f"   Latest DB price: ${latest_db['price']:,.2f}")
                print(f"   Latest DB timestamp: {latest_db['timestamp']}")
        else:
            print(f"   Error: HTTP {db_response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_series_data()