#!/usr/bin/env python3
"""
Test volume velocity calculation for different data sources
Compare stability and identify peaks/spikes
"""

import sys
import os
import asyncio
import json
import statistics
from datetime import datetime, timedelta
import time

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from server.implementations.multi_source_provider import MultiSourceProvider


async def test_volume_velocity():
    """Test volume velocity calculation for stability"""
    
    print("Volume Velocity Stability Test")
    print("=" * 50)
    print("Testing volume velocity spikes across data sources")
    print("Sampling every 30 seconds for better velocity calculation")
    
    provider = MultiSourceProvider()
    
    # Test parameters
    num_samples = 10
    interval_seconds = 30
    
    results = {
        'coingecko': {'timestamps': [], 'volumes': [], 'velocities': []},
        'coinmarketcap': {'timestamps': [], 'volumes': [], 'velocities': []}
    }
    
    print(f"\nCollecting {num_samples} samples (every {interval_seconds}s)...")
    print("This will take about {:.1f} minutes".format(num_samples * interval_seconds / 60))
    
    for i in range(num_samples):
        print(f"\nSample {i+1}/{num_samples}:")
        timestamp = datetime.utcnow()
        
        # Get CoinGecko data
        cg_data = await provider._fetch_coingecko('bitcoin')
        if cg_data and cg_data.volume_24h:
            results['coingecko']['timestamps'].append(timestamp)
            results['coingecko']['volumes'].append(cg_data.volume_24h)
            print(f"  CoinGecko: ${cg_data.volume_24h:,.0f}")
        else:
            print("  CoinGecko: Failed")
        
        # Get CoinMarketCap data
        cmc_data = await provider._fetch_coinmarketcap('bitcoin')
        if cmc_data and cmc_data.volume_24h:
            results['coinmarketcap']['timestamps'].append(timestamp)
            results['coinmarketcap']['volumes'].append(cmc_data.volume_24h)
            print(f"  CoinMarketCap: ${cmc_data.volume_24h:,.0f}")
        else:
            print("  CoinMarketCap: Failed")
        
        # Calculate velocities if we have at least 2 data points
        for source in ['coingecko', 'coinmarketcap']:
            volumes = results[source]['volumes']
            timestamps = results[source]['timestamps']
            
            if len(volumes) >= 2:
                # Calculate velocity: (volume_change) / (time_diff_in_minutes)
                vol_diff = volumes[-1] - volumes[-2]
                time_diff = (timestamps[-1] - timestamps[-2]).total_seconds() / 60  # minutes
                velocity = vol_diff / time_diff if time_diff > 0 else 0
                results[source]['velocities'].append(velocity)
                
                # Show velocity for this sample
                if len(results[source]['velocities']) == 1:
                    print(f"    {source} velocity: ${velocity:,.0f}/min")
        
        # Wait before next sample (except last)
        if i < num_samples - 1:
            await asyncio.sleep(interval_seconds)
    
    # Analysis
    print(f"\n" + "=" * 50)
    print("VOLUME VELOCITY ANALYSIS")
    print("=" * 50)
    
    for source in ['coingecko', 'coinmarketcap']:
        velocities = results[source]['velocities']
        volumes = results[source]['volumes']
        
        if not velocities:
            print(f"\n{source.upper()}: No velocity data collected")
            continue
        
        print(f"\n{source.upper()} Results:")
        print(f"  Samples collected: {len(volumes)}")
        print(f"  Velocity calculations: {len(velocities)}")
        
        if len(velocities) > 0:
            abs_velocities = [abs(v) for v in velocities]
            
            print(f"  Average volume velocity: ${statistics.mean(abs_velocities):,.0f}/min")
            print(f"  Max velocity: ${max(abs_velocities):,.0f}/min")
            print(f"  Std deviation: ${statistics.stdev(abs_velocities) if len(abs_velocities) > 1 else 0:,.0f}/min")
            
            # Identify peaks (velocities above 2 standard deviations)
            if len(abs_velocities) > 2:
                mean_vel = statistics.mean(abs_velocities)
                std_vel = statistics.stdev(abs_velocities)
                threshold = mean_vel + (2 * std_vel)
                
                peaks = [v for v in abs_velocities if v > threshold]
                peak_count = len(peaks)
                
                print(f"  Peak threshold (mean + 2σ): ${threshold:,.0f}/min")
                print(f"  Peaks detected: {peak_count}/{len(velocities)} ({peak_count/len(velocities)*100:.1f}%)")
                
                if peak_count > 0:
                    print(f"  Peak values: {[f'${p:,.0f}' for p in peaks]}")
                else:
                    print("  EXCELLENT: No significant peaks detected!")
            
            # Show raw velocity data for inspection
            print(f"  Raw velocities: {[f'${v:,.0f}' for v in velocities[-5:]]}")  # Show last 5
    
    # Comparison
    print(f"\n" + "=" * 50)
    print("COMPARISON & RECOMMENDATIONS")
    print("=" * 50)
    
    cg_velocities = [abs(v) for v in results['coingecko']['velocities']]
    cmc_velocities = [abs(v) for v in results['coinmarketcap']['velocities']]
    
    if cg_velocities and cmc_velocities:
        cg_std = statistics.stdev(cg_velocities) if len(cg_velocities) > 1 else 0
        cmc_std = statistics.stdev(cmc_velocities) if len(cmc_velocities) > 1 else 0
        
        cg_mean = statistics.mean(cg_velocities)
        cmc_mean = statistics.mean(cmc_velocities)
        
        print(f"CoinGecko velocity stability (std dev): ${cg_std:,.0f}/min")
        print(f"CoinMarketCap velocity stability (std dev): ${cmc_std:,.0f}/min")
        
        if cmc_std < cg_std:
            improvement = ((cg_std - cmc_std) / cg_std) * 100
            print(f"\nCoinMarketCap is {improvement:.1f}% more stable for volume velocity!")
            print("RECOMMENDATION: Switch to CoinMarketCap for more reliable volume analytics")
        elif cg_std < cmc_std:
            improvement = ((cmc_std - cg_std) / cmc_std) * 100
            print(f"\nCoinGecko is {improvement:.1f}% more stable for volume velocity")
            print("RECOMMENDATION: Keep CoinGecko if velocity stability is priority")
        else:
            print("\nBoth sources show similar velocity stability")
    
    # Save results for further analysis
    timestamp_str = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    results_file = f"data/velocity_test_results_{timestamp_str}.json"
    
    try:
        # Convert datetime objects to strings for JSON serialization
        json_results = {}
        for source, data in results.items():
            json_results[source] = {
                'timestamps': [t.isoformat() for t in data['timestamps']],
                'volumes': data['volumes'],
                'velocities': data['velocities']
            }
        
        os.makedirs(os.path.dirname(results_file), exist_ok=True)
        with open(results_file, 'w') as f:
            json.dump(json_results, f, indent=2)
        print(f"\nDetailed results saved to: {results_file}")
    except Exception as e:
        print(f"\nCould not save results: {e}")


if __name__ == "__main__":
    asyncio.run(test_volume_velocity())