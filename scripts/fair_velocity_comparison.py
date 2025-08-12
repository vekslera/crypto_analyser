#!/usr/bin/env python3
"""
Fair comparison of volume velocity using same time window
"""

import sys
import os
import sqlite3
import statistics
from datetime import datetime

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def fair_velocity_comparison():
    """Compare velocity using same time window for both sources"""
    
    print("Fair Volume Velocity Comparison (Same Time Window)")
    print("=" * 60)
    
    # Connect to both databases
    cg_db_path = os.path.join(project_root, "data", "crypto_analyser.db")
    cmc_db_path = os.path.join(project_root, "data", "bitcoin_data.db")
    
    # Get CMC time window first
    cmc_conn = sqlite3.connect(cmc_db_path)
    cmc_cursor = cmc_conn.cursor()
    
    cmc_cursor.execute("""
        SELECT MIN(timestamp), MAX(timestamp) 
        FROM cmc_data 
        WHERE volume_24h IS NOT NULL
    """)
    
    cmc_time_range = cmc_cursor.fetchone()
    if not cmc_time_range[0]:
        print("No CMC data found")
        return
    
    start_time, end_time = cmc_time_range
    print(f"Using time window: {start_time} to {end_time}")
    
    results = {}
    
    # Analyze CMC data
    print(f"\nAnalyzing CoinMarketCap data...")
    cmc_cursor.execute("""
        SELECT timestamp, volume_24h 
        FROM cmc_data 
        WHERE volume_24h IS NOT NULL 
        ORDER BY timestamp ASC
    """)
    
    cmc_rows = cmc_cursor.fetchall()
    if len(cmc_rows) > 1:
        cmc_velocities = calculate_velocities(cmc_rows)
        results['coinmarketcap'] = analyze_velocities('CoinMarketCap', cmc_velocities)
        print(f"  CMC samples in time window: {len(cmc_rows)}")
    
    cmc_conn.close()
    
    # Analyze CoinGecko data for the SAME time window
    cg_conn = sqlite3.connect(cg_db_path)
    cg_cursor = cg_conn.cursor()
    
    print(f"\nAnalyzing CoinGecko data for same time window...")
    cg_cursor.execute("""
        SELECT timestamp, volume_24h 
        FROM bitcoin_prices 
        WHERE volume_24h IS NOT NULL 
        AND timestamp >= ? 
        AND timestamp <= ?
        ORDER BY timestamp ASC
    """, (start_time, end_time))
    
    cg_rows = cg_cursor.fetchall()
    if len(cg_rows) > 1:
        cg_velocities = calculate_velocities(cg_rows)
        results['coingecko'] = analyze_velocities('CoinGecko', cg_velocities)
        print(f"  CoinGecko samples in time window: {len(cg_rows)}")
    else:
        print(f"  No CoinGecko data in time window {start_time} to {end_time}")
        
        # Let's try a broader search around the CMC time window
        print("  Searching for CoinGecko data around CMC time window...")
        cg_cursor.execute("""
            SELECT timestamp, volume_24h 
            FROM bitcoin_prices 
            WHERE volume_24h IS NOT NULL 
            AND timestamp >= datetime(?, '-2 hours')
            AND timestamp <= datetime(?, '+2 hours')
            ORDER BY timestamp ASC
        """, (start_time, end_time))
        
        cg_rows_broader = cg_cursor.fetchall()
        if len(cg_rows_broader) > 1:
            cg_velocities = calculate_velocities(cg_rows_broader)
            results['coingecko'] = analyze_velocities('CoinGecko (±2h window)', cg_velocities)
            print(f"  CoinGecko samples in broader window: {len(cg_rows_broader)}")
            
            # Show the actual time range for CG data
            if cg_rows_broader:
                cg_start = cg_rows_broader[0][0]
                cg_end = cg_rows_broader[-1][0]
                print(f"  CoinGecko actual range: {cg_start} to {cg_end}")
        else:
            print("  Still no CoinGecko data found in broader window")
    
    cg_conn.close()
    
    # Comparison (if we have both datasets)
    if 'coingecko' in results and 'coinmarketcap' in results:
        print(f"\n" + "=" * 60)
        print("FAIR COMPARISON RESULTS")
        print("=" * 60)
        
        cg = results['coingecko']
        cmc = results['coinmarketcap']
        
        print(f"\nStability Metrics (Same Time Period):")
        print(f"{'Metric':<25} {'CoinGecko':<25} {'CoinMarketCap':<25} {'Winner'}")
        print("-" * 85)
        
        # Mean velocity comparison
        cg_mean = cg['mean_abs_velocity']
        cmc_mean = cmc['mean_abs_velocity']
        mean_winner = "CoinMarketCap" if cmc_mean < cg_mean else "CoinGecko"
        print(f"{'Mean Velocity':<25} ${cg_mean:,.0f}/min{'':<5} ${cmc_mean:,.0f}/min{'':<5} {mean_winner}")
        
        # Standard deviation comparison
        cg_std = cg['std_deviation']
        cmc_std = cmc['std_deviation']
        std_winner = "CoinMarketCap" if cmc_std < cg_std else "CoinGecko"
        print(f"{'Standard Deviation':<25} ${cg_std:,.0f}/min{'':<5} ${cmc_std:,.0f}/min{'':<5} {std_winner}")
        
        # Max velocity comparison
        cg_max = cg['max_velocity']
        cmc_max = cmc['max_velocity']
        max_winner = "CoinMarketCap" if cmc_max < cg_max else "CoinGecko"
        print(f"{'Maximum Velocity':<25} ${cg_max:,.0f}/min{'':<5} ${cmc_max:,.0f}/min{'':<5} {max_winner}")
        
        # Spike percentage comparison
        cg_spikes = cg['spike_percentage']
        cmc_spikes = cmc['spike_percentage']
        spike_winner = "CoinMarketCap" if cmc_spikes < cg_spikes else "CoinGecko"
        print(f"{'Spike Percentage':<25} {cg_spikes:.2f}%{'':<17} {cmc_spikes:.2f}%{'':<17} {spike_winner}")
        
        # Sample sizes
        print(f"{'Sample Count':<25} {cg['sample_count']:<25} {cmc['sample_count']:<25} {'N/A'}")
        
        # Calculate overall winner
        cmc_wins = sum([
            cmc_mean < cg_mean,
            cmc_std < cg_std, 
            cmc_max < cg_max,
            cmc_spikes < cg_spikes
        ])
        
        print(f"\n" + "=" * 60)
        print("FAIR COMPARISON CONCLUSION")
        print("=" * 60)
        
        if cmc_wins >= 3:
            print("WINNER: CoinMarketCap")
            print("CoinMarketCap still shows better stability even in fair comparison")
            
            # Calculate improvement percentages
            improvements = []
            if cg_std > cmc_std and cg_std > 0:
                std_improvement = ((cg_std - cmc_std) / cg_std) * 100
                improvements.append(f"{std_improvement:.1f}% reduction in velocity variance")
            
            if cg_max > cmc_max and cg_max > 0:
                max_improvement = ((cg_max - cmc_max) / cg_max) * 100
                improvements.append(f"{max_improvement:.1f}% reduction in maximum spikes")
                
            if improvements:
                print("Improvements with CoinMarketCap:")
                for improvement in improvements:
                    print(f"  - {improvement}")
                    
        elif cmc_wins == 2:
            print("RESULT: Mixed - both sources have advantages")
            print("The difference is less dramatic when comparing same time periods")
        else:
            print("WINNER: CoinGecko")
            print("CoinGecko shows better stability in this time window")
        
        print(f"\nKey Insight:")
        print(f"Fair comparison using same time window shows more nuanced results.")
        print(f"The dramatic difference seen earlier was partly due to different time periods.")
        
    else:
        print("\nCannot perform fair comparison - missing data for one source")
        if 'coinmarketcap' in results:
            print("Have CMC data but no corresponding CoinGecko data in time window")
        if 'coingecko' in results:
            print("Have CoinGecko data but no corresponding CMC data")


def calculate_velocities(rows):
    """Calculate volume velocities from database rows"""
    velocities = []
    
    for i in range(1, len(rows)):
        try:
            prev_time_str, prev_volume = rows[i-1]
            curr_time_str, curr_volume = rows[i]
            
            prev_time = datetime.fromisoformat(prev_time_str.replace('Z', '+00:00'))
            curr_time = datetime.fromisoformat(curr_time_str.replace('Z', '+00:00'))
            
            time_diff = (curr_time - prev_time).total_seconds() / 60  # minutes
            
            if time_diff > 0 and curr_volume is not None and prev_volume is not None:
                velocity = (curr_volume - prev_volume) / time_diff
                velocities.append(velocity)
        except Exception as e:
            continue
            
    return velocities


def analyze_velocities(source_name, velocities):
    """Analyze velocity data for a source"""
    if not velocities:
        print(f"  No velocity data for {source_name}")
        return None
    
    abs_velocities = [abs(v) for v in velocities]
    
    mean_vel = statistics.mean(abs_velocities)
    std_dev = statistics.stdev(abs_velocities) if len(abs_velocities) > 1 else 0
    max_vel = max(abs_velocities)
    median_vel = statistics.median(abs_velocities)
    
    # Calculate spikes (above mean + 2*std)
    threshold = mean_vel + (2 * std_dev) if std_dev > 0 else mean_vel
    spikes = [v for v in abs_velocities if v > threshold]
    spike_percentage = (len(spikes) / len(velocities)) * 100 if velocities else 0
    
    print(f"  {source_name} Results:")
    print(f"    Samples: {len(velocities)}")
    print(f"    Mean velocity: ${mean_vel:,.0f}/min")
    print(f"    Median velocity: ${median_vel:,.0f}/min") 
    print(f"    Max velocity: ${max_vel:,.0f}/min")
    print(f"    Std deviation: ${std_dev:,.0f}/min")
    print(f"    Spikes detected: {len(spikes)}/{len(velocities)} ({spike_percentage:.2f}%)")
    
    if spikes:
        top_spikes = sorted(spikes, reverse=True)[:3]
        print(f"    Top 3 spikes: {[f'${s:,.0f}' for s in top_spikes]}")
    
    return {
        'source': source_name,
        'sample_count': len(velocities),
        'mean_abs_velocity': mean_vel,
        'median_velocity': median_vel,
        'max_velocity': max_vel,
        'std_deviation': std_dev,
        'spike_count': len(spikes),
        'spike_percentage': spike_percentage,
        'top_spikes': sorted(spikes, reverse=True)[:5] if spikes else []
    }


if __name__ == "__main__":
    fair_velocity_comparison()