#!/usr/bin/env python3
"""
Investigate suspicious volume velocity peaks
Analyze the data to understand why we're seeing extreme 1-minute spikes
"""

import sqlite3
import os
from datetime import datetime

def investigate_volume_peaks():
    """Investigate extreme volume velocity values"""
    
    db_path = "data/crypto_analyser.db"
    
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return
    
    print("Investigating Volume Velocity Peaks")
    print("=" * 40)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Find extreme volume velocity values
        print("\n1. EXTREME VELOCITY VALUES:")
        cursor.execute("""
            SELECT timestamp, price, volume_24h, volume_velocity
            FROM bitcoin_prices 
            WHERE ABS(volume_velocity) > 1000000000  -- Greater than 1B/min
            ORDER BY ABS(volume_velocity) DESC
            LIMIT 10
        """)
        
        extreme_values = cursor.fetchall()
        
        if extreme_values:
            print("Top 10 extreme velocity values:")
            for record in extreme_values:
                timestamp, price, volume_24h, velocity = record
                print(f"  {timestamp}: Volume=${volume_24h:,.0f}, Velocity=${velocity:,.0f}/min")
        else:
            print("No extreme velocity values found")
        
        # Analyze patterns around peaks
        print("\n2. ANALYZING PEAK PATTERNS:")
        if extreme_values:
            # Get context around the most extreme peak
            extreme_timestamp = extreme_values[0][0]
            
            cursor.execute("""
                SELECT timestamp, volume_24h, volume_velocity
                FROM bitcoin_prices 
                WHERE timestamp BETWEEN 
                    datetime(?, '-5 minutes') AND datetime(?, '+5 minutes')
                ORDER BY timestamp ASC
            """, (extreme_timestamp, extreme_timestamp))
            
            context_records = cursor.fetchall()
            
            print(f"Context around peak at {extreme_timestamp}:")
            for i, (ts, vol, vel) in enumerate(context_records):
                marker = " <-- PEAK" if ts == extreme_timestamp else ""
                vel_str = f"{vel:,.0f}" if vel is not None else "None"
                print(f"  {ts}: Volume=${vol:,.0f}, Velocity=${vel_str}/min{marker}")
        
        # Check for data quality issues
        print("\n3. DATA QUALITY ANALYSIS:")
        
        # Check for duplicate volume values
        cursor.execute("""
            SELECT volume_24h, COUNT(*) as count
            FROM bitcoin_prices 
            WHERE volume_24h IS NOT NULL
            GROUP BY volume_24h 
            HAVING COUNT(*) > 5
            ORDER BY COUNT(*) DESC
            LIMIT 5
        """)
        
        duplicate_volumes = cursor.fetchall()
        if duplicate_volumes:
            print("Most common volume values (potential duplicates):")
            for volume, count in duplicate_volumes:
                print(f"  Volume ${volume:,.0f}: appears {count} times")
        
        # Check time intervals between records
        cursor.execute("""
            SELECT 
                timestamp,
                LAG(timestamp) OVER (ORDER BY timestamp) as prev_timestamp,
                volume_24h,
                volume_velocity,
                (JULIANDAY(timestamp) - JULIANDAY(LAG(timestamp) OVER (ORDER BY timestamp))) * 24 * 60 as time_diff_minutes
            FROM bitcoin_prices 
            WHERE volume_velocity IS NOT NULL
            ORDER BY timestamp DESC
            LIMIT 20
        """)
        
        timing_data = cursor.fetchall()
        print("\nRecent timing intervals:")
        for record in timing_data:
            ts, prev_ts, vol, vel, time_diff = record
            if prev_ts and time_diff:
                vel_str = f"{vel:,.0f}" if vel is not None else "None"
                print(f"  {ts}: {time_diff:.2f}min gap, Velocity=${vel_str}/min")
        
        # Check for sudden volume jumps (simplified query)
        print("\n4. SUDDEN VOLUME CHANGES:")
        cursor.execute("""
            SELECT 
                a.timestamp,
                a.volume_24h as current_volume,
                b.volume_24h as prev_volume,
                (a.volume_24h - b.volume_24h) as volume_change,
                a.volume_velocity
            FROM bitcoin_prices a
            JOIN bitcoin_prices b ON a.id = b.id + 1
            WHERE ABS(a.volume_24h - b.volume_24h) > 2000000000  -- 2B change
            ORDER BY ABS(a.volume_24h - b.volume_24h) DESC
            LIMIT 10
        """)
        
        big_changes = cursor.fetchall()
        if big_changes:
            print("Largest volume changes:")
            for ts, vol, prev_vol, change, velocity in big_changes:
                if prev_vol is not None:
                    change_str = f"{change:+,.0f}"
                    vel_str = f"{velocity:,.0f}" if velocity is not None else "None"
                    print(f"  {ts}: {prev_vol:,.0f} -> {vol:,.0f} ({change_str}), Velocity=${vel_str}/min")
        
        # Statistical overview
        print("\n5. STATISTICAL OVERVIEW:")
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                AVG(volume_velocity) as avg_velocity,
                MIN(volume_velocity) as min_velocity,
                MAX(volume_velocity) as max_velocity,
                AVG(ABS(volume_velocity)) as avg_abs_velocity
            FROM bitcoin_prices 
            WHERE volume_velocity IS NOT NULL
        """)
        
        stats = cursor.fetchone()
        if stats:
            total, avg, min_vel, max_vel, avg_abs = stats
            print(f"  Total records: {total}")
            print(f"  Average velocity: ${avg:,.0f}/min")
            print(f"  Min velocity: ${min_vel:,.0f}/min")
            print(f"  Max velocity: ${max_vel:,.0f}/min")
            print(f"  Average absolute velocity: ${avg_abs:,.0f}/min")
        
        conn.close()
        
    except Exception as e:
        print(f"Error during investigation: {e}")
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    investigate_volume_peaks()