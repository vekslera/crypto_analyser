#!/usr/bin/env python3
"""
Backfill historical Bitcoin data from CoinGecko API
Fetches 30 days of hourly Bitcoin price data and adds it to existing bitcoin_prices table
"""

import sys
import os
import sqlite3
import requests
import time
from datetime import datetime, timedelta, timezone
import json

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def fetch_coingecko_historical_data(days=30):
    """Fetch historical Bitcoin data from CoinGecko API"""
    
    print(f"FETCHING {days}-DAY BITCOIN HISTORICAL DATA FROM COINGECKO")
    print("=" * 65)
    
    # CoinGecko API endpoint for historical market chart data
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    
    params = {
        'vs_currency': 'usd',
        'days': str(days)  # 30 days will auto-give us hourly data (free tier rule)
    }
    
    print(f"API URL: {url}")
    print(f"Parameters: {params}")
    print(f"Expected data points: ~{days * 24} hourly records")
    
    try:
        print("\nMaking API request...")
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("SUCCESS: API request successful")
            
            # Parse the response
            prices = data.get('prices', [])
            market_caps = data.get('market_caps', [])
            total_volumes = data.get('total_volumes', [])
            
            print(f"SUCCESS: Received {len(prices)} price data points")
            print(f"SUCCESS: Received {len(market_caps)} market cap data points")
            print(f"SUCCESS: Received {len(total_volumes)} volume data points")
            
            if not prices:
                print("ERROR: No price data received from API")
                return None
            
            # Process the data into records
            records = []
            for i in range(len(prices)):
                timestamp_ms = prices[i][0]
                price = prices[i][1]
                
                # Convert timestamp from milliseconds to datetime
                timestamp = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
                
                # Get corresponding market cap and volume (if available)
                market_cap = market_caps[i][1] if i < len(market_caps) else None
                volume_24h = total_volumes[i][1] if i < len(total_volumes) else None
                
                record = {
                    'timestamp': timestamp,
                    'price': price,
                    'volume_24h': volume_24h,
                    'market_cap': market_cap,
                    'volume_velocity': None,  # Will be calculated later
                    'volatility': None,       # Will be calculated later  
                    'money_flow': None        # Will be calculated later
                }
                
                records.append(record)
            
            print(f"SUCCESS: Processed {len(records)} historical records")
            
            # Show sample of data
            if records:
                print(f"\nSample data (first 3 records):")
                for i, record in enumerate(records[:3]):
                    print(f"  {i+1}. {record['timestamp']}: ${record['price']:,.2f}")
                    print(f"     Volume: ${record['volume_24h']:,.0f}" if record['volume_24h'] else "     Volume: N/A")
                    print(f"     Market Cap: ${record['market_cap']:,.0f}" if record['market_cap'] else "     Market Cap: N/A")
                
                print(f"\nLast record: {records[-1]['timestamp']}")
                print(f"First record: {records[0]['timestamp']}")
            
            return records
            
        else:
            print(f"ERROR: API request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Network error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"ERROR: JSON parsing error: {e}")
        return None
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        return None

def check_database_gaps():
    """Check existing database for gaps that need to be filled"""
    
    print("\nCHECKING DATABASE FOR GAPS")
    print("=" * 30)
    
    db_path = os.path.join(project_root, 'data', 'crypto_analyser.db')
    conn = sqlite3.connect(db_path)
    
    # Get earliest and latest records
    query = '''
    SELECT 
        MIN(timestamp) as earliest,
        MAX(timestamp) as latest,
        COUNT(*) as total_records
    FROM bitcoin_prices
    '''
    
    result = conn.execute(query).fetchone()
    earliest_str, latest_str, total = result
    
    if earliest_str:
        earliest = datetime.fromisoformat(earliest_str)
        latest = datetime.fromisoformat(latest_str)
        
        print(f"Current data range: {earliest.date()} to {latest.date()}")
        print(f"Total existing records: {total}")
        
        # Calculate gap
        thirty_days_ago = latest - timedelta(days=30)
        
        if earliest > thirty_days_ago:
            gap_days = (earliest - thirty_days_ago).days
            print(f"Gap identified: {gap_days} days missing before {earliest.date()}")
            print(f"Need to backfill: {thirty_days_ago.date()} to {earliest.date()}")
            
            conn.close()
            return thirty_days_ago, earliest
        else:
            print("No significant gap found - database has 30+ days of data")
            conn.close()
            return None, None
    else:
        print("No existing data found in database")
        conn.close()
        return None, None

def insert_historical_data(records):
    """Insert historical records into the existing bitcoin_prices table"""
    
    print(f"\nINSERTING {len(records)} HISTORICAL RECORDS")
    print("=" * 45)
    
    db_path = os.path.join(project_root, 'data', 'crypto_analyser.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check for duplicates before inserting
    print("Checking for duplicate timestamps...")
    
    inserted_count = 0
    duplicate_count = 0
    error_count = 0
    
    for i, record in enumerate(records):
        try:
            # Check if this timestamp already exists
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
            
            # Show progress every 100 records
            if (i + 1) % 100 == 0:
                print(f"Progress: {i + 1}/{len(records)} processed...")
                
        except Exception as e:
            print(f"Error inserting record {i+1}: {e}")
            error_count += 1
            continue
    
    # Commit all changes
    conn.commit()
    conn.close()
    
    print(f"\nINSERTION RESULTS:")
    print(f"SUCCESS: Inserted: {inserted_count} records")
    print(f"WARNING: Duplicates skipped: {duplicate_count} records")
    print(f"ERROR: Errors: {error_count} records")
    
    return inserted_count

def verify_data_integrity():
    """Verify the inserted data integrity"""
    
    print(f"\nVERIFYING DATA INTEGRITY")
    print("=" * 25)
    
    db_path = os.path.join(project_root, 'data', 'crypto_analyser.db')
    conn = sqlite3.connect(db_path)
    
    # Get updated statistics
    query = '''
    SELECT 
        MIN(timestamp) as earliest,
        MAX(timestamp) as latest,
        COUNT(*) as total_records,
        COUNT(CASE WHEN volume_24h IS NOT NULL THEN 1 END) as records_with_volume,
        COUNT(CASE WHEN market_cap IS NOT NULL THEN 1 END) as records_with_market_cap
    FROM bitcoin_prices
    '''
    
    result = conn.execute(query).fetchone()
    earliest_str, latest_str, total, with_volume, with_market_cap = result
    
    earliest = datetime.fromisoformat(earliest_str)
    latest = datetime.fromisoformat(latest_str)
    
    # Handle timezone awareness
    if earliest.tzinfo is None:
        earliest = earliest.replace(tzinfo=timezone.utc)
    if latest.tzinfo is None:
        latest = latest.replace(tzinfo=timezone.utc)
    
    print(f"Updated data range: {earliest.date()} to {latest.date()}")
    print(f"Total records: {total}")
    print(f"Records with volume: {with_volume}")
    print(f"Records with market cap: {with_market_cap}")
    print(f"Data coverage: {(latest - earliest).days} days")
    
    # Check for reasonable price ranges
    price_query = '''
    SELECT MIN(price), MAX(price), AVG(price)
    FROM bitcoin_prices
    WHERE timestamp >= ?
    '''
    
    week_ago = latest - timedelta(days=7)
    price_result = conn.execute(price_query, (week_ago,)).fetchone()
    min_price, max_price, avg_price = price_result
    
    print(f"\nPrice validation (last 7 days):")
    print(f"Min price: ${min_price:,.2f}")
    print(f"Max price: ${max_price:,.2f}")
    print(f"Avg price: ${avg_price:,.2f}")
    
    # Sanity check
    if min_price > 50000 and max_price < 200000:
        print("SUCCESS: Price ranges look reasonable for Bitcoin")
    else:
        print("WARNING: Price ranges may need verification")
    
    conn.close()

def main():
    """Main function to orchestrate the historical data backfill"""
    
    print("BITCOIN HISTORICAL DATA BACKFILL")
    print("=" * 35)
    print("This script fetches 30 days of Bitcoin historical data from CoinGecko")
    print("and adds it to the existing bitcoin_prices table.\n")
    
    try:
        # Step 1: Check what data we need
        gap_start, gap_end = check_database_gaps()
        
        if gap_start is None:
            print("No historical data backfill needed.")
            return
        
        # Step 2: Fetch historical data from CoinGecko
        historical_records = fetch_coingecko_historical_data(days=30)
        
        if not historical_records:
            print("Failed to fetch historical data. Exiting.")
            return
        
        # Step 3: Filter records to only fill the gap
        print(f"\nFiltering records for gap period...")
        gap_records = []
        
        # Make gap_start and gap_end timezone-aware to match API data
        if gap_start.tzinfo is None:
            gap_start = gap_start.replace(tzinfo=timezone.utc)
        if gap_end.tzinfo is None:
            gap_end = gap_end.replace(tzinfo=timezone.utc)
            
        for record in historical_records:
            if gap_start <= record['timestamp'] < gap_end:
                gap_records.append(record)
        
        print(f"Found {len(gap_records)} records to fill the gap")
        
        if not gap_records:
            print("No records needed for the identified gap period.")
            return
        
        # Step 4: Insert the records
        inserted_count = insert_historical_data(gap_records)
        
        if inserted_count > 0:
            print(f"\nSUCCESS: Successfully backfilled {inserted_count} historical records")
            
            # Step 5: Verify data integrity
            verify_data_integrity()
            
            print(f"\nBACKFILL COMPLETE!")
            print("Next steps:")
            print("1. Run the volatility recalculation script to update historical volatility")
            print("2. Check the GUI to see extended historical charts")
            
        else:
            print("No records were inserted.")
            
    except Exception as e:
        print(f"ERROR: Error during backfill process: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()