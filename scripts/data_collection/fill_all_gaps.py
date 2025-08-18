#!/usr/bin/env python3
"""
Fill all gaps > 1 hour in Bitcoin price data using CoinGecko API
Comprehensive gap detection and filling for continuous data coverage
"""

import sys
import os
import sqlite3
import requests
import time
import pandas as pd
from datetime import datetime, timedelta, timezone
import json

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def detect_all_gaps(min_gap_hours=1):
    """Detect all gaps > specified hours in the database"""
    
    print(f"DETECTING ALL GAPS > {min_gap_hours} HOUR(S)")
    print("=" * 45)
    
    db_path = os.path.join(project_root, 'data', 'crypto_analyser.db')
    conn = sqlite3.connect(db_path)
    
    # Get all timestamps ordered
    query = '''
    SELECT timestamp 
    FROM bitcoin_prices 
    ORDER BY timestamp ASC
    '''
    
    df = pd.read_sql_query(query, conn)
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='mixed', utc=True)
    
    print(f"Analyzing {len(df)} records...")
    print(f"Date range: {df['timestamp'].iloc[0].date()} to {df['timestamp'].iloc[-1].date()}")
    
    # Find gaps
    gaps = []
    for i in range(1, len(df)):
        prev_time = df.iloc[i-1]['timestamp']
        curr_time = df.iloc[i]['timestamp']
        gap_hours = (curr_time - prev_time).total_seconds() / 3600
        
        if gap_hours > min_gap_hours:
            gaps.append({
                'start': prev_time,
                'end': curr_time,
                'duration_hours': gap_hours
            })
    
    conn.close()
    
    print(f"Found {len(gaps)} gaps > {min_gap_hours} hour(s)")
    
    if gaps:
        total_gap_hours = sum(gap['duration_hours'] for gap in gaps)
        print(f"Total gap time: {total_gap_hours:.1f} hours ({total_gap_hours/24:.1f} days)")
        
        # Show largest gaps
        sorted_gaps = sorted(gaps, key=lambda x: x['duration_hours'], reverse=True)
        print(f"\\nLargest gaps:")
        for i, gap in enumerate(sorted_gaps[:10], 1):
            print(f"{i:2}. {gap['duration_hours']:5.1f}h: {gap['start'].strftime('%Y-%m-%d %H:%M')} to {gap['end'].strftime('%Y-%m-%d %H:%M')}")
    
    return gaps

def fetch_coingecko_data_for_range(start_time, end_time):
    """Fetch CoinGecko data for a specific time range"""
    
    # Calculate days difference
    duration = (end_time - start_time).total_seconds() / (24 * 3600)
    
    print(f"  Fetching {duration:.1f} days of data from CoinGecko...")
    
    # For ranges > 90 days, CoinGecko gives daily data
    # For 1-90 days, it gives hourly data  
    # For < 1 day, it gives ~5min data
    
    if duration > 90:
        print(f"  WARNING: {duration:.1f} days > 90, will get daily data only")
    
    # CoinGecko market_chart/range endpoint
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart/range"
    
    # Convert to Unix timestamps (seconds)
    from_timestamp = int(start_time.timestamp())
    to_timestamp = int(end_time.timestamp())
    
    params = {
        'vs_currency': 'usd',
        'from': from_timestamp,
        'to': to_timestamp
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            prices = data.get('prices', [])
            market_caps = data.get('market_caps', [])
            total_volumes = data.get('total_volumes', [])
            
            print(f"  SUCCESS: Got {len(prices)} data points")
            
            # Process into records
            records = []
            for i in range(len(prices)):
                timestamp_ms = prices[i][0]
                price = prices[i][1]
                
                # Convert timestamp from milliseconds to datetime
                timestamp = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
                
                # Get corresponding data
                market_cap = market_caps[i][1] if i < len(market_caps) else None
                volume_24h = total_volumes[i][1] if i < len(total_volumes) else None
                
                record = {
                    'timestamp': timestamp,
                    'price': price,
                    'volume_24h': volume_24h,
                    'market_cap': market_cap,
                    'volume_velocity': None,
                    'volatility': None,
                    'money_flow': None
                }
                
                records.append(record)
            
            return records
            
        else:
            print(f"  ERROR: API failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return []
            
    except Exception as e:
        print(f"  ERROR: {e}")
        return []

def fill_gap(gap):
    """Fill a single gap with CoinGecko data"""
    
    gap_start = gap['start']
    gap_end = gap['end']
    duration_hours = gap['duration_hours']
    
    print(f"\\nFilling gap: {gap_start.strftime('%Y-%m-%d %H:%M')} to {gap_end.strftime('%Y-%m-%d %H:%M')} ({duration_hours:.1f}h)")
    
    # Fetch data for this range (extend slightly to ensure coverage)
    fetch_start = gap_start - timedelta(minutes=30)
    fetch_end = gap_end + timedelta(minutes=30)
    
    records = fetch_coingecko_data_for_range(fetch_start, fetch_end)
    
    if not records:
        print(f"  FAILED: No data received for this gap")
        return 0
    
    # Filter records to only include the gap period (avoid duplicates)
    gap_records = []
    for record in records:
        if gap_start < record['timestamp'] < gap_end:
            gap_records.append(record)
    
    print(f"  Filtered to {len(gap_records)} records for gap period")
    
    if not gap_records:
        print(f"  WARNING: No records in gap period after filtering")
        return 0
    
    # Insert into database
    return insert_gap_records(gap_records)

def insert_gap_records(records):
    """Insert gap records into database"""
    
    db_path = os.path.join(project_root, 'data', 'crypto_analyser.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    inserted_count = 0
    duplicate_count = 0
    
    for record in records:
        try:
            # Check if timestamp already exists
            check_query = "SELECT COUNT(*) FROM bitcoin_prices WHERE timestamp = ?"
            existing = cursor.execute(check_query, (record['timestamp'],)).fetchone()[0]
            
            if existing > 0:
                duplicate_count += 1
                continue
            
            # Insert the record
            insert_query = '''
            INSERT INTO bitcoin_prices 
            (price, timestamp, volume_24h, market_cap, volume_velocity, volatility, money_flow)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            '''
            
            cursor.execute(insert_query, (
                record['price'],
                record['timestamp'],
                record['volume_24h'],
                record['market_cap'],
                record['volume_velocity'],
                record['volatility'],
                record['money_flow']
            ))
            
            inserted_count += 1
            
        except Exception as e:
            print(f"    ERROR inserting record: {e}")
            continue
    
    conn.commit()
    conn.close()
    
    print(f"  RESULT: Inserted {inserted_count} records, {duplicate_count} duplicates skipped")
    return inserted_count

def main():
    """Main function to fill all gaps"""
    
    print("COMPREHENSIVE GAP FILLING FOR BITCOIN PRICE DATA")
    print("=" * 50)
    print("This script finds and fills all gaps > 1 hour using CoinGecko API\\n")
    
    try:
        # Step 1: Detect all gaps
        gaps = detect_all_gaps(min_gap_hours=1)
        
        if not gaps:
            print("No gaps found! Database has continuous coverage.")
            return
        
        # Step 2: Sort gaps by size (fill largest first for efficiency)
        gaps_sorted = sorted(gaps, key=lambda x: x['duration_hours'], reverse=True)
        
        print(f"\\nFILLING {len(gaps_sorted)} GAPS...")
        print("=" * 35)
        
        total_inserted = 0
        successful_fills = 0
        
        for i, gap in enumerate(gaps_sorted, 1):
            print(f"\\nGap {i}/{len(gaps_sorted)}: {gap['duration_hours']:.1f} hours")
            
            # Add delay between API calls to respect rate limits
            if i > 1:
                print("  Waiting 2 seconds for rate limiting...")
                time.sleep(2)
            
            inserted = fill_gap(gap)
            total_inserted += inserted
            
            if inserted > 0:
                successful_fills += 1
            
            # Add longer delay for large gaps
            if gap['duration_hours'] > 24:
                print("  Waiting 5 seconds after large gap...")
                time.sleep(5)
        
        print(f"\\nGAP FILLING COMPLETE!")
        print("=" * 25)
        print(f"Gaps processed: {len(gaps_sorted)}")
        print(f"Successful fills: {successful_fills}")
        print(f"Total records inserted: {total_inserted}")
        
        if total_inserted > 0:
            # Get updated statistics
            print(f"\\nUpdated database statistics:")
            db_path = os.path.join(project_root, 'data', 'crypto_analyser.db')
            conn = sqlite3.connect(db_path)
            
            count_query = "SELECT COUNT(*) FROM bitcoin_prices"
            total_records = conn.execute(count_query).fetchone()[0]
            
            range_query = '''
            SELECT MIN(timestamp), MAX(timestamp) 
            FROM bitcoin_prices
            '''
            earliest, latest = conn.execute(range_query).fetchone()
            
            conn.close()
            
            print(f"  Total records: {total_records:,}")
            print(f"  Date range: {earliest[:10]} to {latest[:10]}")
            
            print(f"\\nNext steps:")
            print(f"1. Run volatility recalculation script")
            print(f"2. Check GUI for improved data coverage")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()