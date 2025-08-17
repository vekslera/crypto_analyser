#!/usr/bin/env python3
"""
Analyze existing CoinGecko volume data for velocity spikes
"""

import sys
import os
import sqlite3
import statistics
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas as pd

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


def analyze_volume_velocity():
    """Analyze volume velocity from existing CoinGecko data"""
    
    print("CoinGecko Volume Velocity Analysis")
    print("=" * 50)
    
    # Connect to database
    db_path = os.path.join(project_root, "data", "bitcoin_data.db")
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get recent volume data (last 7 days)
    query = """
    SELECT timestamp, volume_24h, volume_velocity
    FROM bitcoin_prices 
    WHERE volume_24h IS NOT NULL 
    ORDER BY timestamp DESC 
    LIMIT 1000
    """
    
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        
        if len(rows) < 2:
            print("Insufficient volume data in database")
            return
        
        print(f"Analyzing {len(rows)} volume records...")
        
        # Convert to list of tuples (timestamp, volume, velocity)
        data = []
        existing_velocities = []
        for row in rows:
            timestamp_str, volume, existing_velocity = row
            try:
                # Parse timestamp
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                data.append((timestamp, volume))
                if existing_velocity is not None:
                    existing_velocities.append(existing_velocity)
            except:
                continue
        
        # Sort by timestamp (oldest first)
        data.sort(key=lambda x: x[0])
        
        if len(data) < 2:
            print("Could not parse timestamp data")
            return
        
        print(f"Successfully parsed {len(data)} records")
        print(f"Time range: {data[0][0]} to {data[-1][0]}")
        print(f"Existing velocity values: {len(existing_velocities)}")
        
        # Analyze existing velocities first (if available)
        if existing_velocities:
            print(f"\nExisting Volume Velocity Analysis:")
            abs_existing = [abs(v) for v in existing_velocities if v is not None]
            
            if abs_existing:
                print(f"  Mean absolute velocity: ${statistics.mean(abs_existing):,.0f}/min")
                print(f"  Max existing velocity: ${max(abs_existing):,.0f}/min")
                
                if len(abs_existing) > 1:
                    std_dev = statistics.stdev(abs_existing)
                    mean_vel = statistics.mean(abs_existing)
                    threshold = mean_vel + (2 * std_dev)
                    
                    spikes = [v for v in abs_existing if v > threshold]
                    print(f"  Standard deviation: ${std_dev:,.0f}/min")
                    print(f"  Spikes (>2σ): {len(spikes)}/{len(abs_existing)} ({len(spikes)/len(abs_existing)*100:.2f}%)")
        
        # Calculate volume velocities from raw data
        velocities = []
        timestamps = []
        volumes = []
        
        for i in range(1, len(data)):
            prev_time, prev_volume = data[i-1]
            curr_time, curr_volume = data[i]
            
            # Time difference in minutes
            time_diff = (curr_time - prev_time).total_seconds() / 60
            
            if time_diff > 0:
                # Volume velocity = volume change per minute
                velocity = (curr_volume - prev_volume) / time_diff
                velocities.append(velocity)
                timestamps.append(curr_time)
                volumes.append(curr_volume)
        
        if not velocities:
            print("Could not calculate velocities")
            return
        
        print(f"Calculated {len(velocities)} velocity values")
        
        # Statistical analysis
        abs_velocities = [abs(v) for v in velocities]
        
        print(f"\nVolume Velocity Statistics:")
        print(f"  Mean absolute velocity: ${statistics.mean(abs_velocities):,.0f}/min")
        print(f"  Median absolute velocity: ${statistics.median(abs_velocities):,.0f}/min")
        print(f"  Max velocity: ${max(abs_velocities):,.0f}/min")
        print(f"  Min velocity: ${min(abs_velocities):,.0f}/min")
        
        if len(abs_velocities) > 1:
            std_dev = statistics.stdev(abs_velocities)
            print(f"  Standard deviation: ${std_dev:,.0f}/min")
            
            # Identify spikes (values above mean + 2 standard deviations)
            mean_vel = statistics.mean(abs_velocities)
            threshold = mean_vel + (2 * std_dev)
            
            spikes = [(i, v) for i, v in enumerate(abs_velocities) if v > threshold]
            
            print(f"\nSpike Analysis:")
            print(f"  Spike threshold (mean + 2*std): ${threshold:,.0f}/min")
            print(f"  Spikes detected: {len(spikes)}/{len(velocities)} ({len(spikes)/len(velocities)*100:.2f}%)")
            
            if spikes:
                print(f"  Top 5 spikes:")
                sorted_spikes = sorted(spikes, key=lambda x: x[1], reverse=True)
                for i, (idx, velocity) in enumerate(sorted_spikes[:5]):
                    timestamp = timestamps[idx]
                    print(f"    {i+1}. ${velocity:,.0f}/min at {timestamp}")
            
            # Show distribution
            percentiles = [50, 75, 90, 95, 99]
            print(f"\nVelocity Percentiles:")
            for p in percentiles:
                value = sorted(abs_velocities)[int(len(abs_velocities) * p / 100)]
                print(f"  {p}th percentile: ${value:,.0f}/min")
        
        # Save results for later comparison
        results = {
            'source': 'coingecko',
            'total_samples': len(velocities),
            'mean_velocity': statistics.mean(abs_velocities),
            'std_dev': statistics.stdev(abs_velocities) if len(abs_velocities) > 1 else 0,
            'max_velocity': max(abs_velocities),
            'spike_count': len(spikes) if 'spikes' in locals() else 0,
            'spike_percentage': (len(spikes) / len(velocities) * 100) if 'spikes' in locals() else 0
        }
        
        # Write summary to file
        summary_file = "data/coingecko_velocity_analysis.txt"
        os.makedirs(os.path.dirname(summary_file), exist_ok=True)
        
        with open(summary_file, 'w') as f:
            f.write(f"CoinGecko Volume Velocity Analysis - {datetime.now()}\n")
            f.write("=" * 50 + "\n")
            f.write(f"Total samples: {results['total_samples']}\n")
            f.write(f"Mean absolute velocity: ${results['mean_velocity']:,.0f}/min\n")
            f.write(f"Standard deviation: ${results['std_dev']:,.0f}/min\n")
            f.write(f"Maximum velocity: ${results['max_velocity']:,.0f}/min\n")
            f.write(f"Spikes detected: {results['spike_count']} ({results['spike_percentage']:.2f}%)\n")
        
        print(f"\nAnalysis saved to: {summary_file}")
        
    except Exception as e:
        print(f"Error analyzing data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == "__main__":
    analyze_volume_velocity()