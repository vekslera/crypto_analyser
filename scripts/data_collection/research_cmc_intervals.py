#!/usr/bin/env python3
"""
Research CoinMarketCap API capabilities for interval-based data
Check if CMC provides volume data in shorter time windows
"""

import sys
import os
import requests
import json

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def research_cmc_api():
    """Research CoinMarketCap API endpoints for interval data"""
    
    print("RESEARCHING COINMARKETCAP API CAPABILITIES")
    print("=" * 50)
    
    api_key = os.getenv('CMC_API_KEY')
    
    if not api_key:
        print("CMC_API_KEY not found in environment")
        return
    
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': api_key,
    }
    
    print("Available CoinMarketCap API endpoints for interval data:")
    print("-" * 60)
    
    # Test different endpoints
    endpoints = [
        {
            'name': 'Historical OHLCV (quotes/historical)',
            'url': 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/historical',
            'description': 'Historical price/volume data with time intervals',
            'params': {'id': '1', 'time_start': '2025-08-07T10:00:00Z', 'time_end': '2025-08-07T12:00:00Z', 'interval': '1h'},
            'test': True
        },
        {
            'name': 'OHLCV Latest',
            'url': 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/ohlcv/latest',
            'description': 'Latest OHLCV data',
            'params': {'id': '1'},
            'test': True
        },
        {
            'name': 'OHLCV Historical',
            'url': 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/ohlcv/historical',
            'description': 'Historical OHLCV with intervals: 1m,5m,10m,15m,30m,1h,2h,3h,4h,6h,8h,12h,1d,2d,3d,7d,14d,15d,30d,60d,90d',
            'params': {'id': '1', 'time_start': '2025-08-07T16:00:00Z', 'time_end': '2025-08-07T18:00:00Z', 'interval': '5m'},
            'test': True
        }
    ]
    
    for endpoint in endpoints:
        print(f"\n{endpoint['name']}:")
        print(f"URL: {endpoint['url']}")
        print(f"Description: {endpoint['description']}")
        
        if endpoint['test']:
            try:
                response = requests.get(endpoint['url'], headers=headers, params=endpoint['params'], timeout=10)
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print("SUCCESS: Endpoint available")
                    
                    # Show structure without printing massive data
                    if 'data' in data:
                        if isinstance(data['data'], dict):
                            if '1' in data['data']:
                                bitcoin_data = data['data']['1']
                                print(f"Data keys: {list(bitcoin_data.keys())}")
                                
                                if 'quotes' in bitcoin_data:
                                    print(f"Quotes count: {len(bitcoin_data['quotes'])}")
                                    if bitcoin_data['quotes']:
                                        sample_quote = bitcoin_data['quotes'][0]
                                        print(f"Sample quote keys: {list(sample_quote.keys())}")
                                        
                                        if 'USD' in sample_quote:
                                            usd_data = sample_quote['USD']
                                            print(f"USD data keys: {list(usd_data.keys())}")
                        elif isinstance(data['data'], list):
                            print(f"Data items: {len(data['data'])}")
                            if data['data']:
                                print(f"Sample item keys: {list(data['data'][0].keys())}")
                    
                elif response.status_code == 400:
                    error_data = response.json()
                    print(f"Bad Request: {error_data.get('status', {}).get('error_message', 'Unknown error')}")
                elif response.status_code == 401:
                    print("Unauthorized: Check API key")
                elif response.status_code == 403:
                    print("Forbidden: Plan limitations")
                else:
                    print(f"Error: {response.text[:200]}")
                    
            except Exception as e:
                print(f"Request failed: {e}")
    
    print("\n" + "=" * 60)
    print("SUMMARY OF CMC INTERVAL CAPABILITIES:")
    print("=" * 60)
    print("Based on CMC API documentation:")
    print("+ Historical OHLCV supports intervals: 1m, 5m, 10m, 15m, 30m, 1h, etc.")
    print("+ This could provide true volume data for specific time intervals")
    print("+ Would eliminate the 24h moving window problem")
    print("+ Free tier: 333 calls/day (vs our current 8,640 calls/month = 288/day)")
    print("+ Paid tiers: Much higher limits")
    print()
    print("POTENTIAL SOLUTION:")
    print("- Switch from /quotes/latest to /ohlcv/historical")
    print("- Use 5-minute intervals")
    print("- Get actual volume for each 5-minute period")
    print("- Calculate true money flow velocity")

def analyze_theoretical_improvement():
    """Analyze what improvement we'd get from interval data"""
    
    print("\n\nTHEORETICAL IMPROVEMENT ANALYSIS:")
    print("=" * 40)
    print("Current Method (24h Volume Difference):")
    print("- Volume Velocity CV: 15.17 (very unstable)")
    print("- Massive artifacts from sliding window")
    print("- False peaks of ±$10B+/min")
    print()
    print("Market Cap Method:")
    print("- Market Cap Velocity CV: 5.84 (much more stable)")
    print("- No sliding window artifacts") 
    print("- Reflects actual price changes")
    print("- Available in real-time")
    print()
    print("Interval Volume Method (if available):")
    print("+ True volume for specific time periods")
    print("+ No sliding window artifacts")
    print("+ Real money flow measurement")
    print("+ Can validate against market cap changes")
    print("- Requires different API endpoint")
    print("- May hit rate limits faster")
    print("- More complex implementation")

if __name__ == "__main__":
    research_cmc_api()
    analyze_theoretical_improvement()