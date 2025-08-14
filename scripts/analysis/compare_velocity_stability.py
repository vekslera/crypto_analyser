#!/usr/bin/env python3
"""
Compare volume velocity stability between CoinGecko and CoinMarketCap
"""

import sys
import os
import sqlite3
import statistics
from datetime import datetime

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def analyze_velocity_stability():
    """Compare volume velocity stability between CoinGecko and CoinMarketCap"""
    
    print("Volume Velocity Stability Comparison")
    print("=" * 50)
    
    # Connect to database
    db_path = os.path.join(project_root, "data", "bitcoin_data.db")
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    results = {}
    
    # Analyze CoinGecko data (from bitcoin_prices table)
    print("Analyzing CoinGecko data...")
    try:
        cursor.execute("""
            SELECT timestamp, volume_24h 
            FROM bitcoin_prices 
            WHERE volume_24h IS NOT NULL 
            ORDER BY timestamp ASC
            LIMIT 500
        """)
        
        cg_rows = cursor.fetchall()
        if len(cg_rows) > 1:
            cg_velocities = calculate_velocities(cg_rows)
            results['coingecko'] = analyze_velocities('CoinGecko', cg_velocities)
        else:
            print("  Insufficient CoinGecko data")
    except Exception as e:
        print(f"  Error analyzing CoinGecko: {e}")
    
    # Analyze CoinMarketCap data (from cmc_data table)
    print("\nAnalyzing CoinMarketCap data...")
    try:
        cursor.execute("""
            SELECT timestamp, volume_24h 
            FROM cmc_data 
            WHERE volume_24h IS NOT NULL 
            ORDER BY timestamp ASC
        """)
        
        cmc_rows = cursor.fetchall()
        if len(cmc_rows) > 1:
            cmc_velocities = calculate_velocities(cmc_rows)
            results['coinmarketcap'] = analyze_velocities('CoinMarketCap', cmc_velocities)
        else:
            print("  Insufficient CoinMarketCap data")
    except Exception as e:
        print(f"  Error analyzing CoinMarketCap: {e}")
    
    conn.close()
    
    # Comparison
    if 'coingecko' in results and 'coinmarketcap' in results:
        print(f"\n" + "=" * 50)
        print("DETAILED COMPARISON")
        print("=" * 50)
        
        cg = results['coingecko']
        cmc = results['coinmarketcap']
        
        print(f"\nStability Metrics:")
        print(f"{'Metric':<25} {'CoinGecko':<20} {'CoinMarketCap':<20} {'Winner'}")
        print("-" * 75)
        
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
        print(f"{'Spike Percentage':<25} {cg_spikes:.2f}%{'':<12} {cmc_spikes:.2f}%{'':<12} {spike_winner}")
        
        # Overall winner
        cmc_wins = sum([
            cmc_mean < cg_mean,
            cmc_std < cg_std, 
            cmc_max < cg_max,
            cmc_spikes < cg_spikes
        ])
        
        print(f"\n" + "=" * 50)
        print("FINAL RECOMMENDATION")
        print("=" * 50)
        
        if cmc_wins >= 3:
            print("🏆 WINNER: CoinMarketCap")
            print("CoinMarketCap provides significantly more stable volume data")
            
            # Calculate improvement percentages
            if cg_std > 0:
                std_improvement = ((cg_std - cmc_std) / cg_std) * 100
                print(f"   - {std_improvement:.1f}% reduction in velocity variance")
            
            if cg_spikes > 0:
                spike_reduction = ((cg_spikes - cmc_spikes) / cg_spikes) * 100
                print(f"   - {spike_reduction:.1f}% fewer velocity spikes")
                
            print(f"   - Maximum spike: ${cmc_max:,.0f}/min vs ${cg_max:,.0f}/min")
            
        else:
            print("🏆 WINNER: CoinGecko")
            print("CoinGecko shows better stability metrics")
        
        print(f"\nRECOMMENDATION:")
        if cmc_wins >= 3:
            print("Switch to CoinMarketCap as your primary data source")
            print("This should eliminate the volume velocity spikes you observed")
        else:
            print("Consider additional testing or data smoothing techniques")
            
    # Save comparison results
    save_comparison_results(results)


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
        except:
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


def save_comparison_results(results):
    """Save comparison results to file"""
    timestamp_str = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    results_file = f"data/velocity_comparison_{timestamp_str}.txt"
    
    try:
        os.makedirs(os.path.dirname(results_file), exist_ok=True)
        
        with open(results_file, 'w') as f:
            f.write("Volume Velocity Stability Comparison\n")
            f.write("=" * 40 + "\n")
            f.write(f"Analysis time: {datetime.utcnow()}\n\n")
            
            for source, data in results.items():
                if data:
                    f.write(f"{data['source']} Results:\n")
                    f.write(f"  Samples: {data['sample_count']}\n")
                    f.write(f"  Mean velocity: ${data['mean_abs_velocity']:,.0f}/min\n")
                    f.write(f"  Max velocity: ${data['max_velocity']:,.0f}/min\n") 
                    f.write(f"  Std deviation: ${data['std_deviation']:,.0f}/min\n")
                    f.write(f"  Spike percentage: {data['spike_percentage']:.2f}%\n")
                    f.write("\n")
        
        print(f"\nDetailed results saved to: {results_file}")
    except Exception as e:
        print(f"Could not save results: {e}")


if __name__ == "__main__":
    analyze_velocity_stability()