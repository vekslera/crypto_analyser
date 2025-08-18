#!/usr/bin/env python3
"""
Fast 24-hour volatility recalculation for mixed-interval data
Optimized for performance with vectorized operations
"""

import sys
import os
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def fast_recalculate_volatility():
    """Fast recalculation using vectorized operations"""
    
    print("FAST VOLATILITY RECALCULATION FOR MIXED-INTERVAL DATA")
    print("=" * 55)
    
    # Connect to database
    db_path = os.path.join(project_root, 'data', 'crypto_analyser.db')
    conn = sqlite3.connect(db_path)
    
    # Load all data for calculation, but identify records that need updates
    print("Loading data...")
    query = '''
    SELECT id, timestamp, price, volatility
    FROM bitcoin_prices 
    ORDER BY timestamp ASC
    '''
    
    df = pd.read_sql_query(query, conn)
    print(f"Loaded {len(df)} records")
    
    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='mixed', utc=True)
    
    # Identify records that need volatility updates (newest records with NULL volatility)
    # Sort by timestamp descending to find newest records
    df_newest = df.sort_values('timestamp', ascending=False).head(10)
    
    # Find records in positions 1-9 that have NULL volatility (expanded range)
    records_to_update = []
    for i, (idx, row) in enumerate(df_newest.iterrows()):
        if i >= 1 and i <= 9 and pd.isna(row['volatility']):
            records_to_update.append(idx)  # Store the original dataframe index
    
    print(f"\nFound {len(records_to_update)} newest records that need volatility updates")
    if records_to_update:
        for idx in records_to_update:
            record = df.loc[idx]
            print(f"  ID {record['id']}: {record['timestamp']}")
    else:
        print("No records need updates!")
        conn.close()
        return
    
    # Calculate price returns (simple approach for mixed intervals)
    df['returns'] = df['price'].pct_change()
    df['time_diff_hours'] = df['timestamp'].diff().dt.total_seconds() / 3600
    
    print("Calculating 24-hour rolling volatility...")
    
    # Use a simplified approach: calculate 24-hour rolling standard deviation of returns
    # This will work reasonably well for mixed intervals
    window_size = '24h'  # 24-hour rolling window (using lowercase 'h')
    
    # Set timestamp as index for rolling operations
    df_indexed = df.set_index('timestamp')
    
    # Calculate rolling volatility (24-hour window) for ALL records to ensure proper calculation
    df_indexed['volatility_24h'] = df_indexed['returns'].rolling(window_size, min_periods=2).std() * 100 * np.sqrt(24*12)  # Scale to daily % volatility
    
    # Reset index and handle NaN values
    df = df_indexed.reset_index()
    
    # Only update the specific records we identified
    update_count = 0
    for idx in records_to_update:
        if pd.notna(df.loc[idx, 'volatility_24h']):
            update_count += 1
    
    print(f"Calculated volatility for {update_count} of {len(records_to_update)} target records")
    
    # Update database for specific records only
    print("Updating database...")
    cursor = conn.cursor()
    
    updated_total = 0
    batch_updates = []
    
    # Only update the records we identified as needing updates
    for idx in records_to_update:
        row = df.loc[idx]
        if pd.notna(row['volatility_24h']):
            batch_updates.append((float(row['volatility_24h']), int(row['id'])))
            print(f"  Will update ID {row['id']}: {row['volatility_24h']:.4f}%")
    
    if batch_updates:
        cursor.executemany(
            "UPDATE bitcoin_prices SET volatility = ? WHERE id = ?",
            batch_updates
        )
        updated_total = len(batch_updates)
        print(f"  Updated {updated_total} specific records")
    else:
        print("  No records to update")
    
    conn.commit()
    print(f"\nDatabase update complete: {updated_total} records updated")
    
    # Show statistics for updated records
    if updated_total > 0:
        print(f"\nUpdated Records:")
        for idx in records_to_update:
            row = df.loc[idx]
            if pd.notna(row['volatility_24h']):
                print(f"  ID {row['id']}: {row['timestamp']} -> {row['volatility_24h']:.4f}%")
    
    # Verify the updates in database
    print(f"\nVerification - checking database:")
    if updated_total > 0:
        verify_ids = [int(df.loc[idx]['id']) for idx in records_to_update if pd.notna(df.loc[idx]['volatility_24h'])]
        if verify_ids:
            verify_query = f"SELECT id, timestamp, volatility FROM bitcoin_prices WHERE id IN ({','.join(map(str, verify_ids))}) ORDER BY timestamp DESC"
            verify_df = pd.read_sql_query(verify_query, conn)
            for _, row in verify_df.iterrows():
                vol_status = f'{row["volatility"]:.4f}%' if pd.notna(row['volatility']) else 'NULL'
                print(f"  ID {row['id']}: {vol_status}")
    
    conn.close()
    print("\nTargeted volatility fill complete!")

if __name__ == "__main__":
    try:
        fast_recalculate_volatility()
    except Exception as e:
        print(f"Error during recalculation: {e}")
        import traceback
        traceback.print_exc()