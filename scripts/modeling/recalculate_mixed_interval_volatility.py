#!/usr/bin/env python3
"""
Recalculate 24-hour volatility for mixed-interval data
Handles both hourly historical data and 5-minute live data properly
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

def recalculate_mixed_interval_volatility():
    """Recalculate 24-hour volatility accounting for mixed data intervals"""
    
    print("RECALCULATING 24-HOUR VOLATILITY FOR MIXED-INTERVAL DATA")
    print("=" * 60)
    print("Handles both hourly backfilled data and 5-minute live data")
    
    # Connect to database
    db_path = os.path.join(project_root, 'data', 'crypto_analyser.db')
    conn = sqlite3.connect(db_path)
    
    # Load all data ordered by timestamp
    query = '''
    SELECT id, timestamp, price
    FROM bitcoin_prices 
    ORDER BY timestamp ASC
    '''
    
    df = pd.read_sql_query(query, conn)
    print(f"Loaded {len(df)} records for volatility recalculation")
    
    # Convert timestamp to datetime (handle mixed formats, normalize to UTC)
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='mixed', utc=True)
    
    # Calculate time differences to understand data intervals
    df['time_diff'] = df['timestamp'].diff()
    
    # Analyze data intervals
    time_diffs_minutes = df['time_diff'].dt.total_seconds() / 60
    print(f"\nData interval analysis:")
    print(f"  Median interval: {time_diffs_minutes.median():.1f} minutes")
    print(f"  Most common intervals: {time_diffs_minutes.value_counts().head(3).to_dict()}")
    
    # Initialize new volatility column
    df['volatility_24h'] = None
    
    updated_count = 0
    skipped_count = 0
    
    print("\nProcessing records...")
    print("Progress: [", end="", flush=True)
    progress_interval = max(1, len(df) // 50)  # Show 50 progress markers
    
    for i in range(len(df)):
        current_record = df.iloc[i]
        current_time = current_record['timestamp']
        
        # Show progress
        if i % progress_interval == 0:
            print(".", end="", flush=True)
        
        # Get 24-hour window of data (24 hours before current record)
        twenty_four_hours_ago = current_time - timedelta(hours=24)
        
        # Filter data within 24-hour window (including current record)
        window_mask = (df['timestamp'] >= twenty_four_hours_ago) & (df['timestamp'] <= current_time)
        window_data = df[window_mask].copy().reset_index(drop=True)
        
        if len(window_data) >= 3:  # Need at least 3 data points for meaningful volatility
            # Calculate time-weighted returns for mixed intervals
            prices = window_data['price'].values
            timestamps = window_data['timestamp']  # Keep as pandas datetime series
            
            # Calculate returns with time normalization
            returns = []
            for j in range(1, len(prices)):
                # Standard return calculation
                price_return = (prices[j] - prices[j-1]) / prices[j-1]
                
                # Calculate time interval in hours
                time_diff = timestamps.iloc[j] - timestamps.iloc[j-1]
                time_interval_hours = time_diff.total_seconds() / 3600
                
                # Normalize return to hourly basis for consistent volatility calculation
                # For intervals != 1 hour, scale the return appropriately
                if time_interval_hours > 0:
                    # Convert to effective hourly return rate
                    hourly_return = price_return / time_interval_hours
                    returns.append(hourly_return)
            
            if len(returns) >= 2:  # Need at least 2 returns for variance
                # Calculate 24-hour volatility using proper statistical formula
                n = len(returns)
                mean_return = np.mean(returns)
                # Proper variance: Σ(x - μ)² / (n-1) 
                variance = np.sum([(r - mean_return)**2 for r in returns]) / (n - 1)
                
                # Scale volatility back to 24-hour basis
                # Since we normalized to hourly returns, multiply by sqrt(24) for daily volatility
                volatility = np.sqrt(variance) * np.sqrt(24) * 100  # Convert to percentage
                
                df.at[i, 'volatility_24h'] = volatility
                updated_count += 1
            else:
                skipped_count += 1
        else:
            skipped_count += 1
    
    print("]")
    print(f"\nVolatility calculation completed:")
    print(f"  • Updated records: {updated_count}")
    print(f"  • Skipped records: {skipped_count} (insufficient 24h data)")
    
    # Update database with new volatility values
    print("\nUpdating database...")
    cursor = conn.cursor()
    
    update_count = 0
    for i in range(len(df)):
        if pd.notna(df.iloc[i]['volatility_24h']):
            cursor.execute(
                "UPDATE bitcoin_prices SET volatility = ? WHERE id = ?",
                (df.iloc[i]['volatility_24h'], df.iloc[i]['id'])
            )
            update_count += 1
    
    conn.commit()
    print(f"Database updated: {update_count} records with new 24-hour volatility")
    
    # Show statistics
    valid_volatilities = df['volatility_24h'].dropna()
    if len(valid_volatilities) > 0:
        print(f"\nVolatility Statistics:")
        print(f"  • Mean: {valid_volatilities.mean():.4f}%")
        print(f"  • Std: {valid_volatilities.std():.4f}%")
        print(f"  • Min: {valid_volatilities.min():.4f}%")
        print(f"  • Max: {valid_volatilities.max():.4f}%")
        print(f"  • Median: {valid_volatilities.median():.4f}%")
    
    # Show sample of updated records
    print(f"\nSample of updated records:")
    sample_data = df[df['volatility_24h'].notna()].tail(10)
    for _, row in sample_data.iterrows():
        print(f"  {row['timestamp']}: {row['volatility_24h']:.4f}%")
    
    conn.close()
    print("\nMixed-interval volatility recalculation complete!")

if __name__ == "__main__":
    try:
        recalculate_mixed_interval_volatility()
    except Exception as e:
        print(f"Error during recalculation: {e}")
        import traceback
        traceback.print_exc()