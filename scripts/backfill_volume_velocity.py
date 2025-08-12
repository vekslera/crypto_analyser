#!/usr/bin/env python3
"""
Backfill volume velocity for all existing historical data
Calculates volume velocity for all existing 24h volume records in chronological order
"""

import sqlite3
import sys
import os
from datetime import datetime

def backfill_volume_velocity():
    """Calculate and update volume velocity for all existing records"""
    
    db_path = "data/crypto_analyser.db"
    
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return False
    
    print("Starting volume velocity backfill...")
    print(f"Database: {db_path}")
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all records ordered chronologically (oldest first)
        print("\nFetching all records in chronological order...")
        cursor.execute("""
            SELECT id, price, timestamp, volume_24h, volume_velocity, market_cap 
            FROM bitcoin_prices 
            WHERE volume_24h IS NOT NULL 
            ORDER BY timestamp ASC
        """)
        
        records = cursor.fetchall()
        total_records = len(records)
        
        if total_records == 0:
            print("No records with volume data found.")
            return True
        
        print(f"Found {total_records} records with volume data")
        
        # Process records to calculate volume velocity
        updates = []
        processed = 0
        calculated = 0
        
        print("\nCalculating volume velocities...")
        
        for i, record in enumerate(records):
            record_id, price, timestamp_str, volume_24h, current_velocity, market_cap = record
            
            # Parse timestamp
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            
            # Skip first record (no previous data to compare)
            if i == 0:
                # Set first record velocity to None (no previous data)
                if current_velocity is not None:
                    updates.append((None, record_id))
                processed += 1
                continue
            
            # Get previous record for calculation
            prev_record = records[i-1]
            prev_timestamp_str = prev_record[2]
            prev_volume_24h = prev_record[3]
            
            # Parse previous timestamp
            prev_timestamp = datetime.fromisoformat(prev_timestamp_str.replace('Z', '+00:00'))
            
            # Calculate time difference in minutes
            time_diff_seconds = (timestamp - prev_timestamp).total_seconds()
            time_diff_minutes = time_diff_seconds / 60.0
            
            if time_diff_minutes > 0 and prev_volume_24h is not None:
                # Calculate volume velocity (USD per minute)
                volume_change = volume_24h - prev_volume_24h
                volume_velocity = volume_change / time_diff_minutes
                
                # Add to updates if different from current value
                if abs((current_velocity or 0) - volume_velocity) > 0.01:  # Only update if significantly different
                    updates.append((volume_velocity, record_id))
                    calculated += 1
            else:
                # Set to None if we can't calculate
                if current_velocity is not None:
                    updates.append((None, record_id))
            
            processed += 1
            
            # Progress indicator
            if processed % 100 == 0:
                print(f"  Processed {processed}/{total_records} records... ({calculated} calculations)")
        
        print(f"\nProcessing complete:")
        print(f"  Total records processed: {processed}")
        print(f"  Volume velocities calculated: {calculated}")
        print(f"  Database updates needed: {len(updates)}")
        
        # Apply updates to database
        if updates:
            print(f"\nApplying {len(updates)} updates to database...")
            
            cursor.executemany(
                "UPDATE bitcoin_prices SET volume_velocity = ? WHERE id = ?",
                updates
            )
            
            # Commit changes
            conn.commit()
            print("Database updates committed successfully!")
            
            # Show some sample results
            print(f"\nSample backfilled data (last 5 records):")
            cursor.execute("""
                SELECT timestamp, price, volume_24h, volume_velocity 
                FROM bitcoin_prices 
                WHERE volume_velocity IS NOT NULL 
                ORDER BY timestamp DESC 
                LIMIT 5
            """)
            
            sample_records = cursor.fetchall()
            for record in reversed(sample_records):  # Show chronologically
                timestamp, price, volume_24h, velocity = record
                velocity_str = f"${velocity:,.0f}/min" if velocity is not None else "None"
                print(f"  {timestamp}: Price=${price:,.0f}, Volume=${volume_24h:,.0f}, Velocity={velocity_str}")
        else:
            print("No updates needed - all volume velocities are already correct!")
        
        conn.close()
        print(f"\nBackfill completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error during backfill: {e}")
        if 'conn' in locals():
            conn.close()
        return False

def verify_backfill():
    """Verify the backfill results"""
    db_path = "data/crypto_analyser.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get statistics
        cursor.execute("SELECT COUNT(*) FROM bitcoin_prices WHERE volume_24h IS NOT NULL")
        total_with_volume = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM bitcoin_prices WHERE volume_velocity IS NOT NULL")
        total_with_velocity = cursor.fetchone()[0]
        
        print(f"\nBackfill verification:")
        print(f"  Records with volume data: {total_with_volume}")
        print(f"  Records with velocity data: {total_with_velocity}")
        print(f"  Coverage: {(total_with_velocity/total_with_volume*100):.1f}%" if total_with_volume > 0 else "  Coverage: N/A")
        
        # Show date range
        cursor.execute("""
            SELECT MIN(timestamp), MAX(timestamp) 
            FROM bitcoin_prices 
            WHERE volume_velocity IS NOT NULL
        """)
        date_range = cursor.fetchone()
        if date_range[0]:
            print(f"  Date range: {date_range[0]} to {date_range[1]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error during verification: {e}")
        return False

if __name__ == "__main__":
    print("Volume Velocity Backfill Script")
    print("=" * 40)
    
    # Run backfill
    success = backfill_volume_velocity()
    
    if success:
        # Verify results
        verify_backfill()
        print(f"\nAll historical volume velocity data has been calculated!")
        print(f"You can now view volume velocity charts for the entire database history.")
    else:
        print(f"\nBackfill failed. Please check the error messages above.")
        sys.exit(1)