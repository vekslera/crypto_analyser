#!/usr/bin/env python3
"""
Analyze recent CMC volume peaks mentioned by user
Check the negative peak at 19:11:35 and positive at 19:16:25 Israel time
"""

import sys
import os
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def analyze_recent_peaks():
    """Analyze the specific peaks mentioned by user"""
    
    print("ANALYZING RECENT CMC VOLUME VELOCITY PEAKS")
    print("=" * 50)
    
    db_path = os.path.join(project_root, "data", "crypto_analyser.db")
    
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Get recent data around the mentioned times (Israel time is UTC+2)
        # Looking for 19:11-19:16 Israel time = 17:11-17:16 UTC
        query = """
        SELECT 
            datetime(timestamp, '+2 hours') as israel_time,
            datetime(timestamp) as utc_time,
            price,
            volume_24h,
            volume_velocity,
            market_cap
        FROM bitcoin_prices 
        WHERE timestamp >= datetime('now', '-6 hours')
        ORDER BY timestamp DESC
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            print("No recent data found")
            return
        
        print(f"Found {len(df)} recent records")
        print()
        
        # Show all records with their velocity values
        print("Recent CMC Volume Data:")
        print("-" * 100)
        print(f"{'Israel Time':<20} {'Price ($)':<15} {'Volume 24h ($)':<20} {'Velocity ($/min)':<20} {'Market Cap ($)':<20}")
        print("-" * 100)
        
        for _, row in df.iterrows():
            israel_time = row['israel_time']
            price = f"{row['price']:,.2f}" if row['price'] else "N/A"
            volume = f"{row['volume_24h']:,.0f}" if row['volume_24h'] else "N/A"
            velocity = f"{row['volume_velocity']:,.0f}" if row['volume_velocity'] else "N/A"
            market_cap = f"{row['market_cap']:,.0f}" if row['market_cap'] else "N/A"
            
            print(f"{israel_time:<20} {price:<15} {volume:<20} {velocity:<20} {market_cap:<20}")
        
        print()
        
        # Analyze velocity patterns
        print("VELOCITY ANALYSIS:")
        print("-" * 30)
        
        velocities = df['volume_velocity'].dropna()
        if len(velocities) > 0:
            print(f"Max positive velocity: ${velocities.max():,.0f}/min")
            print(f"Max negative velocity: ${velocities.min():,.0f}/min")
            print(f"Average velocity: ${velocities.mean():,.0f}/min")
            print(f"Velocity std dev: ${velocities.std():,.0f}/min")
            
            # Find extreme values
            extreme_threshold = 1_000_000_000  # 1B/min
            extreme_velocities = velocities[abs(velocities) > extreme_threshold]
            
            if len(extreme_velocities) > 0:
                print(f"\nExtreme velocities (>1B/min): {len(extreme_velocities)} records")
                for i, (idx, vel) in enumerate(extreme_velocities.items()):
                    time_str = df.iloc[idx]['israel_time']
                    print(f"  {i+1}. {time_str}: ${vel:,.0f}/min")
        
        print()
        
        # Calculate 24h volume differences to show the methodology issue
        print("24H VOLUME METHODOLOGY ANALYSIS:")
        print("-" * 40)
        
        df_sorted = df.sort_values('utc_time')
        for i in range(1, min(len(df_sorted), 6)):
            prev_row = df_sorted.iloc[i-1]
            curr_row = df_sorted.iloc[i]
            
            if prev_row['volume_24h'] and curr_row['volume_24h']:
                vol_diff = curr_row['volume_24h'] - prev_row['volume_24h']
                time_diff = (pd.to_datetime(curr_row['utc_time']) - pd.to_datetime(prev_row['utc_time'])).total_seconds() / 60
                calculated_velocity = vol_diff / time_diff if time_diff > 0 else 0
                stored_velocity = curr_row['volume_velocity']
                
                print(f"Time: {curr_row['israel_time']}")
                print(f"  Volume change: ${vol_diff:,.0f}")
                print(f"  Time diff: {time_diff:.1f} min")
                print(f"  Calculated velocity: ${calculated_velocity:,.0f}/min")
                print(f"  Stored velocity: ${stored_velocity:,.0f}/min" if stored_velocity else "  Stored velocity: N/A")
                print()

    except Exception as e:
        print(f"Error analyzing peaks: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_recent_peaks()