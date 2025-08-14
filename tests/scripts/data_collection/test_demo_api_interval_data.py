#!/usr/bin/env python3
"""
Test CoinGecko Demo API to see if it provides true interval volume data
Check if Demo API gives us better data than free tier
"""

import sys
import os
import requests
from datetime import datetime

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from core.api_config import CG_API_KEY

def test_demo_api_capabilities():
    """Test CoinGecko Demo API capabilities for interval data"""
    
    print("TESTING COINGECKO DEMO API CAPABILITIES")
    print("=" * 45)
    
    if not CG_API_KEY:
        print("ERROR: CG_API_KEY not found in environment variables")
        print("Make sure you set the CG_API_KEY environment variable and restarted your terminal")
        return
    
    print(f"API Key found: {CG_API_KEY[:8]}..." if len(CG_API_KEY) > 8 else "API Key found")
    print()
    
    base_url = "https://api.coingecko.com/api/v3"
    headers = {'x-cg-demo-api-key': CG_API_KEY}
    
    # Test different endpoints with Demo API
    tests = [
        {
            'name': 'Simple Price (Demo API)',
            'url': f'{base_url}/simple/price',
            'params': {
                'ids': 'bitcoin',
                'vs_currencies': 'usd',
                'include_market_cap': 'true',
                'include_24hr_vol': 'true',
                'include_last_updated_at': 'true'
            }
        },
        {
            'name': 'Market Chart 1 day (Demo API)',
            'url': f'{base_url}/coins/bitcoin/market_chart',
            'params': {
                'vs_currency': 'usd',
                'days': '1'
            }
        },
        {
            'name': 'Market Chart 2 days (Demo API)', 
            'url': f'{base_url}/coins/bitcoin/market_chart',
            'params': {
                'vs_currency': 'usd',
                'days': '2'
            }
        },
        {
            'name': 'OHLC 1 day (Demo API)',
            'url': f'{base_url}/coins/bitcoin/ohlc',
            'params': {
                'vs_currency': 'usd',
                'days': '1'
            }
        }
    ]
    
    for test in tests:
        print(f"TESTING: {test['name']}")
        print("-" * 40)
        
        try:
            response = requests.get(test['url'], params=test['params'], headers=headers, timeout=15)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("SUCCESS: Data retrieved")
                
                # Check rate limit headers
                rate_headers = {k: v for k, v in response.headers.items() 
                              if 'rate' in k.lower() or 'limit' in k.lower() or 'remaining' in k.lower()}
                if rate_headers:
                    print(f"Rate limit headers: {rate_headers}")
                
                # Analyze data structure
                if 'total_volumes' in data:
                    volumes = data['total_volumes']
                    print(f"Volume data points: {len(volumes)}")
                    
                    if len(volumes) >= 3:
                        print("Sample volume data:")
                        for i in [0, 1, 2, -1]:
                            if i < len(volumes):
                                timestamp_ms, volume = volumes[i]
                                time_str = datetime.fromtimestamp(timestamp_ms / 1000).strftime('%Y-%m-%d %H:%M:%S')
                                print(f"  {time_str}: ${volume:,.0f}")
                        
                        # Check if this is different from free tier
                        if len(volumes) >= 2:
                            time_diff_ms = volumes[1][0] - volumes[0][0]
                            interval_min = time_diff_ms / 1000 / 60
                            print(f"Time interval: {interval_min:.1f} minutes")
                
                elif isinstance(data, dict) and 'bitcoin' in data:
                    # Simple price format
                    btc_data = data['bitcoin']
                    print(f"Price data keys: {list(btc_data.keys())}")
                    print(f"Price: ${btc_data.get('usd', 'N/A'):,.2f}")
                    print(f"Volume: ${btc_data.get('usd_24h_vol', 'N/A'):,.0f}")
                
                elif isinstance(data, list):
                    # OHLC format
                    print(f"OHLC data points: {len(data)}")
                    if len(data) >= 2:
                        time_diff_ms = data[1][0] - data[0][0]
                        interval_min = time_diff_ms / 1000 / 60
                        print(f"Time interval: {interval_min:.1f} minutes")
                        
                        # Check if there are volume columns (some OHLC has volume)
                        if len(data[0]) > 5:
                            print("OHLC includes volume data!")
                            sample = data[0]
                            print(f"Sample: timestamp={sample[0]}, OHLC={sample[1:5]}, volume={sample[5] if len(sample) > 5 else 'N/A'}")
            
            elif response.status_code == 401:
                print("UNAUTHORIZED: Check API key")
            elif response.status_code == 403:
                print("FORBIDDEN: API key may be invalid or rate limited")
            elif response.status_code == 429:
                print("RATE LIMITED: Too many requests")
            else:
                print(f"ERROR: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"EXCEPTION: {e}")
        
        print()
    
    # Test if Demo API provides better rate limits
    print("DEMO API BENEFITS ANALYSIS:")
    print("-" * 30)
    print("Expected Demo API improvements:")
    print("• Higher rate limits (30 calls/minute vs 5-15)")
    print("• More stable rate limiting")
    print("• Better data quality")
    print("• Access to premium endpoints")
    print("• But volume data structure likely same as free tier")

def test_simple_request():
    """Simple test to verify Demo API works"""
    
    print("\nSIMPLE DEMO API TEST:")
    print("-" * 25)
    
    if not CG_API_KEY:
        print("No API key available")
        return
    
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {'ids': 'bitcoin', 'vs_currencies': 'usd'}
        headers = {'x-cg-demo-api-key': CG_API_KEY}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            price = data['bitcoin']['usd']
            print(f"Bitcoin price: ${price:,.2f}")
            print("✅ Demo API is working!")
        else:
            print(f"❌ Demo API failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_demo_api_capabilities()
    test_simple_request()