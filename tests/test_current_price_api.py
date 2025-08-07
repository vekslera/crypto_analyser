#!/usr/bin/env python3
"""
Test script for current price API endpoint fix
Tests that /price/current returns real-time series data vs database data
"""

import sys
import os
import requests
import time
from datetime import datetime

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from core.config import FASTAPI_URL

def test_current_price_endpoint():
    """Test that /price/current returns real-time data"""
    
    print("Testing /price/current endpoint for real-time updates...")
    print("=" * 50)
    
    # Test multiple calls over time to see price updates
    for i in range(3):
        try:
            response = requests.get(f"{FASTAPI_URL}/price/current", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                price = data['price']
                timestamp = data['timestamp']
                volume = data.get('volume_24h', 'N/A')
                
                print(f"Call {i+1}: ${price:,.2f} at {timestamp}")
                print(f"  Volume: ${volume:,.0f}" if volume != 'N/A' else "  Volume: N/A")
                print()
                
                # Wait to see if price changes (should update every 60s)
                if i < 2:
                    print("Waiting 10 seconds for next call...")
                    time.sleep(10)
            else:
                print(f"Error: HTTP {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"Error calling API: {e}")
    
    print("Test completed!")

def test_series_vs_database():
    """Compare series endpoint vs current price endpoint"""
    
    print("\nComparing series vs current price endpoints...")
    print("=" * 50)
    
    try:
        # Get from series endpoint
        series_response = requests.get(f"{FASTAPI_URL}/series/recent?limit=1", timeout=10)
        
        # Get from current price endpoint  
        current_response = requests.get(f"{FASTAPI_URL}/price/current", timeout=10)
        
        if series_response.status_code == 200 and current_response.status_code == 200:
            series_data = series_response.json()
            current_data = current_response.json()
            
            print("Series endpoint (real-time 60s updates):")
            if series_data['data']:
                series_items = list(series_data['data'].items())
                if series_items:
                    timestamp, price = series_items[-1]
                    print(f"  Price: ${price:,.2f} at {timestamp}")
            
            print(f"\nCurrent price endpoint (should match series):")
            print(f"  Price: ${current_data['price']:,.2f} at {current_data['timestamp']}")
            
            print(f"\nVolume (from database, 5min updates):")
            print(f"  Volume: ${current_data.get('volume_24h', 0):,.0f}")
            
        else:
            print("Error getting data from endpoints")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_current_price_endpoint()
    test_series_vs_database()