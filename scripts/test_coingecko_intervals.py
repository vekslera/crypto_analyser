#!/usr/bin/env python3
"""
Test CoinGecko API endpoints for Bitcoin volume data in shorter intervals
Check what's actually available on the free tier vs documentation claims
"""

import sys
import os
import requests
import json
from datetime import datetime, timedelta

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_coingecko_endpoints():
    """Test various CoinGecko endpoints for interval volume data"""
    
    print("TESTING COINGECKO API ENDPOINTS FOR BITCOIN VOLUME")
    print("=" * 60)
    
    base_url = "https://api.coingecko.com/api/v3"
    
    endpoints = [
        {
            'name': 'Market Chart (1 day - should give 5min intervals)',
            'url': f'{base_url}/coins/bitcoin/market_chart',
            'params': {'vs_currency': 'usd', 'days': '1'},
            'description': 'Price, market cap, and total volume over 1 day'
        },
        {
            'name': 'Market Chart (2 days - should give hourly intervals)',
            'url': f'{base_url}/coins/bitcoin/market_chart',
            'params': {'vs_currency': 'usd', 'days': '2'},
            'description': 'Price, market cap, and total volume over 2 days'
        },
        {
            'name': 'OHLC (1 day - should give 30min candles)',
            'url': f'{base_url}/coins/bitcoin/ohlc',
            'params': {'vs_currency': 'usd', 'days': '1'},
            'description': 'OHLC data for 1 day'
        },
        {
            'name': 'OHLC (7 days - should give 4hr candles)',
            'url': f'{base_url}/coins/bitcoin/ohlc',
            'params': {'vs_currency': 'usd', 'days': '7'},
            'description': 'OHLC data for 7 days'
        }
    ]
    
    results = {}
    
    for endpoint in endpoints:
        print(f"\n{endpoint['name']}:")
        print(f"URL: {endpoint['url']}")
        print(f"Description: {endpoint['description']}")
        
        try:
            response = requests.get(endpoint['url'], params=endpoint['params'], timeout=15)
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Analyze the structure
                print("SUCCESS: Data retrieved")
                
                if 'prices' in data:
                    # Market chart format
                    price_count = len(data['prices'])
                    volume_count = len(data.get('total_volumes', []))
                    market_cap_count = len(data.get('market_caps', []))
                    
                    print(f"  Data points: {price_count} prices, {volume_count} volumes, {market_cap_count} market_caps")
                    
                    if price_count > 1:
                        # Calculate time intervals
                        first_timestamp = data['prices'][0][0] / 1000
                        second_timestamp = data['prices'][1][0] / 1000
                        interval_seconds = second_timestamp - first_timestamp
                        interval_minutes = interval_seconds / 60
                        
                        print(f"  Time interval: {interval_minutes:.1f} minutes")
                        
                        # Show sample data
                        print(f"  Sample volume data:")
                        for i in range(min(3, volume_count)):
                            timestamp = data['total_volumes'][i][0] / 1000
                            volume = data['total_volumes'][i][1]
                            time_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                            print(f"    {time_str}: ${volume:,.0f}")
                        
                        # Check if volume data changes between intervals
                        if volume_count > 1:
                            vol1 = data['total_volumes'][0][1]
                            vol2 = data['total_volumes'][1][1]
                            vol_diff = abs(vol1 - vol2)
                            
                            print(f"  Volume difference between first two points: ${vol_diff:,.0f}")
                            
                            if vol_diff > 0:
                                print(f"  GOOD: Volume data changes between intervals")
                                results[endpoint['name']] = {
                                    'interval_minutes': interval_minutes,
                                    'data_points': volume_count,
                                    'volume_changes': True
                                }
                            else:
                                print(f"  WARNING: Volume data appears static")
                                results[endpoint['name']] = {
                                    'interval_minutes': interval_minutes,
                                    'data_points': volume_count,
                                    'volume_changes': False
                                }
                
                elif isinstance(data, list) and len(data) > 0:
                    # OHLC format
                    data_points = len(data)
                    print(f"  OHLC data points: {data_points}")
                    
                    if data_points > 1:
                        # OHLC format: [timestamp, open, high, low, close]
                        first_timestamp = data[0][0] / 1000
                        second_timestamp = data[1][0] / 1000
                        interval_seconds = second_timestamp - first_timestamp
                        interval_minutes = interval_seconds / 60
                        
                        print(f"  Time interval: {interval_minutes:.1f} minutes")
                        
                        # Show sample data
                        print(f"  Sample OHLC data (no volume in free OHLC):")
                        for i in range(min(3, data_points)):
                            timestamp = data[i][0] / 1000
                            time_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                            ohlc = data[i][1:5]
                            print(f"    {time_str}: O:{ohlc[0]:.0f} H:{ohlc[1]:.0f} L:{ohlc[2]:.0f} C:{ohlc[3]:.0f}")
                        
                        results[endpoint['name']] = {
                            'interval_minutes': interval_minutes,
                            'data_points': data_points,
                            'has_volume': False
                        }
                
            elif response.status_code == 429:
                print("Rate limited")
            else:
                print(f"Error: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"  Message: {error_data.get('error', 'Unknown error')}")
                except:
                    print(f"  Response: {response.text[:200]}")
                    
        except Exception as e:
            print(f"Request failed: {e}")
    
    # Summary
    print(f"\n\nSUMMARY OF COINGECKO CAPABILITIES:")
    print("=" * 45)
    
    for endpoint_name, result in results.items():
        print(f"\n{endpoint_name}:")
        print(f"  Interval: {result.get('interval_minutes', 'N/A'):.1f} minutes")
        print(f"  Data points: {result.get('data_points', 'N/A')}")
        
        if 'volume_changes' in result:
            if result['volume_changes']:
                print(f"  Volume data: AVAILABLE and changes between intervals")
                print(f"  POTENTIAL SOLUTION: Can calculate volume velocity for {result['interval_minutes']:.0f}min periods!")
            else:
                print(f"  Volume data: Available but static (likely 24h cumulative)")
        elif 'has_volume' in result:
            if result['has_volume']:
                print(f"  Volume data: Available in OHLCV format")
            else:
                print(f"  Volume data: NOT available (free tier OHLC limitation)")
    
    # Recommendations
    print(f"\nRECOMMENDATIONS:")
    print("-" * 20)
    
    viable_endpoints = [name for name, result in results.items() 
                       if result.get('volume_changes', False)]
    
    if viable_endpoints:
        print("VIABLE SOLUTIONS FOUND:")
        for endpoint in viable_endpoints:
            result = results[endpoint]
            print(f"+ {endpoint}")
            print(f"  - {result['interval_minutes']:.0f}min intervals eliminate sliding window artifacts")
            print(f"  - {result['data_points']} data points per day")
            print(f"  - Can calculate true volume velocity")
    else:
        print("NO VIABLE SOLUTIONS: All volume data appears to be 24h cumulative")
        print("Market cap velocity remains the best approach for artifact-free money flow measurement")

if __name__ == "__main__":
    test_coingecko_endpoints()