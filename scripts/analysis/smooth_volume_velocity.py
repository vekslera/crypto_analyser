#!/usr/bin/env python3
"""
Smooth volume velocity data to remove extreme API artifacts
Applies various smoothing techniques to make the data more meaningful
"""

import sqlite3
import os
import numpy as np
from datetime import datetime

def smooth_volume_velocity():
    """Apply smoothing to volume velocity data"""
    
    db_path = "data/crypto_analyser.db"
    
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return False
    
    print("Volume Velocity Smoothing Script")
    print("=" * 40)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all records with volume velocity in chronological order
        print("\nFetching volume velocity data...")
        cursor.execute("""
            SELECT id, timestamp, volume_velocity
            FROM bitcoin_prices 
            WHERE volume_velocity IS NOT NULL 
            ORDER BY timestamp ASC
        """)
        
        records = cursor.fetchall()
        total_records = len(records)
        print(f"Found {total_records} records with volume velocity data")
        
        if total_records < 10:
            print("Not enough data for smoothing")
            return False
        
        # Extract data for analysis
        ids = [r[0] for r in records]
        velocities = [r[2] for r in records]
        
        # Show current statistics
        print(f"\nCurrent statistics:")
        print(f"  Min velocity: ${min(velocities):,.0f}/min")
        print(f"  Max velocity: ${max(velocities):,.0f}/min")
        print(f"  Average: ${np.mean(velocities):,.0f}/min")
        print(f"  Std deviation: ${np.std(velocities):,.0f}/min")
        
        # Count extreme values (>1B/min)
        extreme_count = sum(1 for v in velocities if abs(v) > 1_000_000_000)
        print(f"  Extreme values (>1B/min): {extreme_count} ({extreme_count/total_records*100:.1f}%)")
        
        # Apply smoothing methods
        print(f"\nApplying smoothing methods...")
        
        # Method 1: Outlier capping (cap at ±500M/min)
        max_reasonable_velocity = 500_000_000  # $500M/min
        velocities_capped = []
        capped_count = 0
        
        for v in velocities:
            if v > max_reasonable_velocity:
                velocities_capped.append(max_reasonable_velocity)
                capped_count += 1
            elif v < -max_reasonable_velocity:
                velocities_capped.append(-max_reasonable_velocity)
                capped_count += 1
            else:
                velocities_capped.append(v)
        
        print(f"  Method 1 - Outlier capping: Capped {capped_count} extreme values")
        
        # Method 2: Moving average (5-point window)
        window_size = 5
        velocities_smoothed = []
        
        for i in range(len(velocities_capped)):
            # Calculate window bounds
            start = max(0, i - window_size // 2)
            end = min(len(velocities_capped), i + window_size // 2 + 1)
            
            # Calculate moving average
            window_values = velocities_capped[start:end]
            smoothed_value = np.mean(window_values)
            velocities_smoothed.append(smoothed_value)
        
        print(f"  Method 2 - Moving average: Applied {window_size}-point smoothing")
        
        # Show improved statistics
        print(f"\nSmoothed statistics:")
        print(f"  Min velocity: ${min(velocities_smoothed):,.0f}/min")
        print(f"  Max velocity: ${max(velocities_smoothed):,.0f}/min") 
        print(f"  Average: ${np.mean(velocities_smoothed):,.0f}/min")
        print(f"  Std deviation: ${np.std(velocities_smoothed):,.0f}/min")
        
        # Count remaining extreme values
        extreme_count_smoothed = sum(1 for v in velocities_smoothed if abs(v) > 1_000_000_000)
        print(f"  Extreme values (>1B/min): {extreme_count_smoothed} ({extreme_count_smoothed/total_records*100:.1f}%)")
        
        # Prepare updates
        updates = []
        significant_changes = 0
        
        for i, (record_id, old_velocity, new_velocity) in enumerate(zip(ids, velocities, velocities_smoothed)):
            # Only update if the change is significant (>1% or >1M)
            if abs(old_velocity - new_velocity) > max(abs(old_velocity) * 0.01, 1_000_000):
                updates.append((new_velocity, record_id))
                significant_changes += 1
        
        print(f"\nPrepared {len(updates)} database updates ({significant_changes} significant changes)")
        
        # Auto-apply smoothing (no confirmation needed)
        print(f"\nAuto-applying smoothing to {len(updates)} records...")
        
        if True:  # Always apply
            print(f"Applying smoothing updates...")
            
            # Create backup column first
            try:
                cursor.execute("ALTER TABLE bitcoin_prices ADD COLUMN volume_velocity_raw REAL")
                print("  Created backup column: volume_velocity_raw")
            except sqlite3.OperationalError:
                print("  Backup column already exists")
            
            # Backup original values
            cursor.execute("""
                UPDATE bitcoin_prices 
                SET volume_velocity_raw = volume_velocity 
                WHERE volume_velocity_raw IS NULL AND volume_velocity IS NOT NULL
            """)
            
            # Apply smoothed values
            cursor.executemany(
                "UPDATE bitcoin_prices SET volume_velocity = ? WHERE id = ?",
                updates
            )
            
            conn.commit()
            print("  Smoothing applied successfully!")
            
            # Show sample of changes
            print(f"\nSample of smoothing effects (first 5 significant changes):")
            cursor.execute("""
                SELECT timestamp, volume_velocity_raw, volume_velocity
                FROM bitcoin_prices 
                WHERE volume_velocity_raw IS NOT NULL 
                    AND ABS(volume_velocity_raw - volume_velocity) > 1000000
                ORDER BY ABS(volume_velocity_raw - volume_velocity) DESC
                LIMIT 5
            """)
            
            sample_changes = cursor.fetchall()
            for ts, raw_vel, smooth_vel in sample_changes:
                print(f"  {ts}: ${raw_vel:,.0f}/min -> ${smooth_vel:,.0f}/min")
                
        else:
            print("Smoothing cancelled by user")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error during smoothing: {e}")
        if 'conn' in locals():
            conn.close()
        return False

def restore_original_data():
    """Restore original volume velocity data from backup"""
    
    db_path = "data/crypto_analyser.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if backup exists
        cursor.execute("PRAGMA table_info(bitcoin_prices)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'volume_velocity_raw' not in columns:
            print("No backup data found")
            return False
        
        # Restore from backup
        cursor.execute("""
            UPDATE bitcoin_prices 
            SET volume_velocity = volume_velocity_raw 
            WHERE volume_velocity_raw IS NOT NULL
        """)
        
        restored_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        print(f"Restored {restored_count} original volume velocity values")
        return True
        
    except Exception as e:
        print(f"Error during restore: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--restore":
        print("Restoring original volume velocity data...")
        restore_original_data()
    else:
        smooth_volume_velocity()