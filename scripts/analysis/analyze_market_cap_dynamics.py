#!/usr/bin/env python3
"""
Analyze market cap dynamics as alternative to volume velocity
Market Cap = Price × Circulating Supply
Market Cap Change ≈ Money Flow (assuming supply is relatively constant)
"""

import sys
import os
import sqlite3
import pandas as pd
import numpy as np

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def analyze_market_cap_dynamics():
    """Analyze market cap changes as proxy for money flow"""
    
    print("ANALYZING MARKET CAP DYNAMICS AS MONEY FLOW PROXY")
    print("=" * 60)
    
    db_path = os.path.join(project_root, "data", "crypto_analyser.db")
    
    try:
        conn = sqlite3.connect(db_path)
        
        query = """
        SELECT 
            datetime(timestamp, '+2 hours') as israel_time,
            price,
            volume_24h,
            volume_velocity,
            market_cap
        FROM bitcoin_prices 
        WHERE timestamp >= datetime('now', '-6 hours')
        ORDER BY timestamp ASC
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if len(df) < 2:
            print("Not enough data for analysis")
            return
        
        # Calculate market cap velocity (change per minute)
        df['prev_market_cap'] = df['market_cap'].shift(1)
        df['prev_israel_time'] = df['israel_time'].shift(1)
        df['price_change'] = df['price'] - df['price'].shift(1)
        
        # Calculate time differences
        df['time_diff_min'] = pd.to_datetime(df['israel_time']) - pd.to_datetime(df['prev_israel_time'])
        df['time_diff_min'] = df['time_diff_min'].dt.total_seconds() / 60
        
        # Calculate market cap velocity
        df['market_cap_change'] = df['market_cap'] - df['prev_market_cap']
        df['market_cap_velocity'] = df['market_cap_change'] / df['time_diff_min']
        
        # Show comparison during problematic period
        print("COMPARISON: Volume Velocity vs Market Cap Velocity")
        print("-" * 80)
        print(f"{'Time':<20} {'Price':<12} {'Vol Vel (B/min)':<15} {'MCap Vel (B/min)':<18} {'MCap Change (B)':<18}")
        print("-" * 80)
        
        for _, row in df.iterrows():
            if pd.isna(row['market_cap_velocity']):
                continue
                
            time_str = row['israel_time']
            price = f"{row['price']:,.0f}"
            vol_vel = f"{row['volume_velocity']/1e9:.1f}" if row['volume_velocity'] else "N/A"
            mcap_vel = f"{row['market_cap_velocity']/1e9:.1f}"
            mcap_change = f"{row['market_cap_change']/1e9:.1f}"
            
            print(f"{time_str:<20} ${price:<11} {vol_vel:<15} {mcap_vel:<18} {mcap_change:<18}")
        
        print()
        
        # Statistical analysis
        valid_data = df.dropna()
        if len(valid_data) > 0:
            print("STATISTICAL COMPARISON:")
            print("-" * 30)
            
            vol_velocities = valid_data['volume_velocity'].dropna()
            mcap_velocities = valid_data['market_cap_velocity'].dropna()
            
            print(f"Volume Velocity Stats ($/min):")
            print(f"  Max: ${vol_velocities.max():,.0f}")
            print(f"  Min: ${vol_velocities.min():,.0f}")
            print(f"  Std: ${vol_velocities.std():,.0f}")
            print(f"  Mean: ${vol_velocities.mean():,.0f}")
            
            print(f"\nMarket Cap Velocity Stats ($/min):")
            print(f"  Max: ${mcap_velocities.max():,.0f}")
            print(f"  Min: ${mcap_velocities.min():,.0f}")
            print(f"  Std: ${mcap_velocities.std():,.0f}")
            print(f"  Mean: ${mcap_velocities.mean():,.0f}")
            
            # Check stability - market cap should be more stable
            vol_cv = abs(vol_velocities.std() / vol_velocities.mean()) if vol_velocities.mean() != 0 else float('inf')
            mcap_cv = abs(mcap_velocities.std() / mcap_velocities.mean()) if mcap_velocities.mean() != 0 else float('inf')
            
            print(f"\nCoefficient of Variation (lower = more stable):")
            print(f"  Volume velocity CV: {vol_cv:.2f}")
            print(f"  Market cap velocity CV: {mcap_cv:.2f}")
            
            if mcap_cv < vol_cv:
                print("  RESULT: Market cap velocity is MORE STABLE than volume velocity")
            else:
                print("  RESULT: Volume velocity is more stable than market cap velocity")
        
        print()
        
        # Theoretical analysis
        print("THEORETICAL MONEY FLOW ANALYSIS:")
        print("-" * 40)
        print("Market Cap = Price × Circulating Supply")
        print("If supply is constant, then:")
        print("Market Cap Change ≈ Price Change × Supply")
        print("Market Cap Velocity ≈ Price Velocity × Supply")
        print()
        print("Advantages of Market Cap Velocity:")
        print("+ No 24h sliding window artifacts")
        print("+ Reflects actual price changes")
        print("+ More stable and meaningful")
        print("+ Available in real-time")
        print()
        print("Disadvantages:")
        print("- Doesn't capture actual trading volume")
        print("- Supply changes (mining, burning) introduce noise")
        print("- Reflects market valuation, not trading activity")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_market_cap_dynamics()