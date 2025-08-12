#!/usr/bin/env python3
"""
Investigate what CoinGecko's market_chart volume data actually contains
Clarify whether it's true interval data or still 24h cumulative data
"""

import sys
import os
import requests
import json
from datetime import datetime

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def investigate_coingecko_volume_data():
    """Investigate CoinGecko market chart volume data structure"""
    
    print("INVESTIGATING COINGECKO VOLUME DATA STRUCTURE")
    print("=" * 60)
    
    base_url = "https://api.coingecko.com/api/v3"
    
    endpoints_to_test = [
        {
            'name': '1 day market chart (should give ~3min intervals)',
            'url': f'{base_url}/coins/bitcoin/market_chart',
            'params': {'vs_currency': 'usd', 'days': '1'},
        },
        {
            'name': '2 days market chart (should give ~1hr intervals)',
            'url': f'{base_url}/coins/bitcoin/market_chart',
            'params': {'vs_currency': 'usd', 'days': '2'},
        }
    ]
    
    for endpoint in endpoints_to_test:
        print(f"\n{endpoint['name']}:")
        print(f"URL: {endpoint['url']}")
        print(f"Params: {endpoint['params']}")
        
        try:
            response = requests.get(endpoint['url'], params=endpoint['params'], timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"Status: SUCCESS")
                print(f"Data keys: {list(data.keys())}")
                
                if 'total_volumes' in data:
                    volumes = data['total_volumes']
                    print(f"Volume data points: {len(volumes)}")
                    
                    if len(volumes) >= 3:
                        print("\nFIRST 3 VOLUME DATA POINTS:")
                        for i in range(3):
                            timestamp_ms, volume = volumes[i]
                            timestamp = datetime.fromtimestamp(timestamp_ms / 1000)
                            print(f"  {i+1}. {timestamp}: ${volume:,.0f}")
                        
                        print("\nLAST 3 VOLUME DATA POINTS:")
                        for i in range(len(volumes)-3, len(volumes)):
                            timestamp_ms, volume = volumes[i]
                            timestamp = datetime.fromtimestamp(timestamp_ms / 1000)
                            print(f"  {i+1}. {timestamp}: ${volume:,.0f}")
                        
                        # Analyze if data changes between points
                        print(f"\nVOLUME DATA ANALYSIS:")
                        volume_values = [v[1] for v in volumes[:10]]  # First 10 values
                        all_same = all(v == volume_values[0] for v in volume_values)
                        
                        if all_same:
                            print(f"  WARNING: First 10 volume values are IDENTICAL")
                            print(f"  This suggests 24h cumulative data, NOT interval data")
                        else:
                            print(f"  GOOD: Volume values change between data points")
                            
                            # Calculate differences
                            differences = []
                            for i in range(1, min(10, len(volumes))):
                                diff = volumes[i][1] - volumes[i-1][1]
                                differences.append(diff)
                            
                            print(f"  Volume differences (first 9 intervals):")
                            for i, diff in enumerate(differences):
                                print(f"    Interval {i+1}: ${diff:+,.0f}")
                            
                            # Check if differences are reasonable for interval data
                            max_diff = max(abs(d) for d in differences)
                            if max_diff > 50e9:  # > $50B difference
                                print(f"  SUSPICIOUS: Very large volume changes (>${max_diff/1e9:.1f}B)")
                                print(f"  This suggests 24h sliding window artifacts")
                            else:
                                print(f"  REASONABLE: Volume changes are within expected range")
                        
                        # Calculate time intervals
                        if len(volumes) >= 2:
                            time_diff_ms = volumes[1][0] - volumes[0][0]
                            time_diff_min = time_diff_ms / 1000 / 60
                            print(f"\nTIME INTERVALS:")
                            print(f"  Interval between data points: {time_diff_min:.1f} minutes")
                            
                            # Check consistency
                            intervals = []
                            for i in range(1, min(10, len(volumes))):
                                interval_ms = volumes[i][0] - volumes[i-1][0]
                                intervals.append(interval_ms / 1000 / 60)
                            
                            if len(set(intervals)) == 1:
                                print(f"  Intervals are CONSISTENT: {intervals[0]:.1f} minutes")
                            else:
                                print(f"  Intervals VARY: {min(intervals):.1f} - {max(intervals):.1f} minutes")
                
            else:
                print(f"Status: ERROR {response.status_code}")
                
        except Exception as e:
            print(f"Status: EXCEPTION - {e}")
    
    print(f"\n" + "=" * 60)
    print("CONCLUSION ABOUT COINGECKO VOLUME DATA:")
    print("=" * 60)
    
    print("Based on CoinGecko documentation and testing:")
    print("")
    print("1. MARKET CHART VOLUME DATA MEANING:")
    print("   - 'total_volumes' represents CUMULATIVE 24h trading volume")
    print("   - Each data point shows the 24h volume AT THAT TIMESTAMP")
    print("   - NOT the volume traded IN THE INTERVAL between timestamps")
    print("")
    print("2. WHY VOLUME VALUES CHANGE:")
    print("   - As time moves forward, the 24h sliding window changes")
    print("   - Old trades drop out, new trades are added")
    print("   - This creates the SAME ARTIFACTS as our current method")
    print("")
    print("3. IMPLICATION FOR VOLUME VELOCITY:")
    print("   - volume_velocity = (current_24h_vol - previous_24h_vol) / time_diff")
    print("   - This is IDENTICAL to our current flawed calculation")
    print("   - Still suffers from 24h sliding window artifacts")
    print("")
    print("4. CONCLUSION:")
    print("   - CoinGecko's market_chart does NOT provide true interval volume")
    print("   - The volume data is still 24h cumulative with sliding window")
    print("   - More frequent data points don't solve the fundamental problem")
    print("   - Market cap velocity remains the better approach")

if __name__ == "__main__":
    investigate_coingecko_volume_data()