#!/usr/bin/env python3
"""
Comprehensive 24-hour volatility recalculation for ALL records in database
Uses frequency-independent calculation method to ensure consistency
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

def recalculate_all_volatility():
    """Recalculate 24-hour volatility for ALL records in the database"""
    
    print("COMPREHENSIVE 24-HOUR VOLATILITY RECALCULATION")
    print("=" * 50)
    print("Using frequency-independent calculation method")
    print()
    
    # Connect to database
    db_path = os.path.join(project_root, 'data', 'crypto_analyser.db')
    print(f"Database path: {db_path}")
    
    if not os.path.exists(db_path):
        print("ERROR: Database file not found!")
        return
    
    conn = sqlite3.connect(db_path)
    
    # Load ALL data for comprehensive recalculation
    print("Loading all price data...")
    query = '''
    SELECT id, timestamp, price
    FROM bitcoin_prices 
    ORDER BY timestamp ASC
    '''
    
    df = pd.read_sql_query(query, conn)
    print(f"Loaded {len(df):,} records")
    
    if len(df) < 25:
        print("ERROR: Insufficient data for volatility calculation (need at least 25 records)")
        conn.close()
        return
    
    # Convert timestamp to datetime
    print("Processing timestamps...")
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='mixed', utc=True)
    
    # Calculate price returns
    print("Calculating price returns...")
    df['returns'] = df['price'].pct_change()
    
    # Detect data frequency by examining time differences
    print("Detecting data frequency...")
    df['time_diff_hours'] = df['timestamp'].diff().dt.total_seconds() / 3600
    median_interval_hours = df['time_diff_hours'].median()
    
    if pd.isna(median_interval_hours) or median_interval_hours <= 0:
        # Fallback: assume 5-minute intervals
        median_interval_hours = 5/60  # 5 minutes = 0.0833 hours
        print(f"WARNING: Using fallback interval: {median_interval_hours:.4f} hours (5 minutes)")
    else:
        print(f"Detected median interval: {median_interval_hours:.4f} hours ({median_interval_hours*60:.1f} minutes)")
    
    # Calculate periods per year for annualization
    periods_per_year = 365 * (24 / median_interval_hours)
    annualization_factor = np.sqrt(periods_per_year)
    
    print(f"Periods per year: {periods_per_year:,.0f}")
    print(f"Annualization factor: sqrt({periods_per_year:.0f}) = {annualization_factor:.2f}")
    print()
    
    # Set timestamp as index for time-based rolling operations
    print("Calculating frequency-independent 24-hour rolling volatility...")
    df_indexed = df.set_index('timestamp')
    
    # Use time-based rolling window (24 hours) for frequency independence
    df_indexed['volatility_raw'] = df_indexed['returns'].rolling('24H', min_periods=2).std()
    
    # Annualize the volatility: convert to daily percentage volatility
    df_indexed['volatility'] = df_indexed['volatility_raw'] * annualization_factor * 100
    
    # Reset index back to regular DataFrame
    df = df_indexed.reset_index()
    
    # Count valid volatility calculations
    valid_volatility = df['volatility'].notna()
    valid_count = valid_volatility.sum()
    
    print(f"SUCCESS: Calculated volatility for {valid_count:,} records ({valid_count/len(df)*100:.1f}%)")
    
    if valid_count == 0:
        print("ERROR: No valid volatility calculations!")
        conn.close()
        return
    
    # Show sample statistics
    vol_stats = df['volatility'].describe()
    print(f"\nVolatility Statistics:")
    print(f"   Mean: {vol_stats['mean']:.4f}%")
    print(f"   Std:  {vol_stats['std']:.4f}%") 
    print(f"   Min:  {vol_stats['min']:.4f}%")
    print(f"   Max:  {vol_stats['max']:.4f}%")
    print(f"   25%:  {vol_stats['25%']:.4f}%")
    print(f"   50%:  {vol_stats['50%']:.4f}%")
    print(f"   75%:  {vol_stats['75%']:.4f}%")
    print()
    
    # Update database with ALL calculated volatilities
    print("Updating database with new volatility values...")
    cursor = conn.cursor()
    
    # Prepare batch updates for all records with valid volatility
    batch_updates = []
    for _, row in df.iterrows():
        if pd.notna(row['volatility']):
            batch_updates.append((float(row['volatility']), int(row['id'])))
    
    print(f"Preparing {len(batch_updates):,} updates...")
    
    # Execute batch update
    if batch_updates:
        # Update in chunks to avoid memory issues
        chunk_size = 1000
        total_updated = 0
        
        for i in range(0, len(batch_updates), chunk_size):
            chunk = batch_updates[i:i + chunk_size]
            cursor.executemany(
                "UPDATE bitcoin_prices SET volatility = ? WHERE id = ?",
                chunk
            )
            total_updated += len(chunk)
            
            # Show progress
            if i % (chunk_size * 10) == 0:
                progress = (i + len(chunk)) / len(batch_updates) * 100
                print(f"   Progress: {progress:.1f}% ({i + len(chunk):,}/{len(batch_updates):,})")
        
        conn.commit()
        print(f"SUCCESS: Updated {total_updated:,} records")
    else:
        print("ERROR: No records to update")
    
    # Verification: Check a sample of updated records
    print("\nVerification - checking sample of updated records:")
    verify_query = """
    SELECT id, timestamp, volatility, 
           LAG(volatility) OVER (ORDER BY timestamp) as prev_volatility
    FROM bitcoin_prices 
    WHERE volatility IS NOT NULL 
    ORDER BY timestamp DESC 
    LIMIT 10
    """
    
    verify_df = pd.read_sql_query(verify_query, conn)
    for i, row in verify_df.iterrows():
        timestamp = pd.to_datetime(row['timestamp']).strftime('%Y-%m-%d %H:%M')
        volatility = row['volatility']
        print(f"   ID {row['id']}: {timestamp} -> {volatility:.4f}%")
    
    # Final statistics
    print(f"\nFinal Database Statistics:")
    stats_query = """
    SELECT 
        COUNT(*) as total_records,
        COUNT(volatility) as records_with_volatility,
        AVG(volatility) as avg_volatility,
        MIN(volatility) as min_volatility,
        MAX(volatility) as max_volatility
    FROM bitcoin_prices
    """
    
    stats_df = pd.read_sql_query(stats_query, conn)
    stats = stats_df.iloc[0]
    
    print(f"   Total records: {stats['total_records']:,}")
    print(f"   Records with volatility: {stats['records_with_volatility']:,}")
    print(f"   Coverage: {stats['records_with_volatility']/stats['total_records']*100:.1f}%")
    print(f"   Average volatility: {stats['avg_volatility']:.4f}%")
    print(f"   Min volatility: {stats['min_volatility']:.4f}%")
    print(f"   Max volatility: {stats['max_volatility']:.4f}%")
    
    conn.close()
    print(f"\nCOMPLETE: Comprehensive volatility recalculation finished!")
    print(f"   Updated {total_updated:,} records with frequency-independent volatility")

if __name__ == "__main__":
    try:
        recalculate_all_volatility()
    except Exception as e:
        print(f"ERROR: Error during recalculation: {e}")
        import traceback
        traceback.print_exc()