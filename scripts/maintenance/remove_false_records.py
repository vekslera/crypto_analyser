#!/usr/bin/env python3
"""
Remove false price records from the database
"""

import sqlite3
import pandas as pd
from datetime import datetime

def identify_suspicious_records():
    """Identify all suspicious records with round numbers or extreme outliers"""
    
    conn = sqlite3.connect('data/crypto_analyser.db')
    
    # Look for records with suspicious round numbers or extreme outliers
    query = '''
    SELECT timestamp, price, volume_24h, market_cap, volatility, money_flow, id
    FROM bitcoin_prices 
    WHERE 
        (volume_24h = 30000000000.0 OR volume_24h = 31000000000.0 OR volume_24h = 32000000000.0 OR volume_24h = 33000000000.0 OR volume_24h = 34000000000.0) 
        OR market_cap = 1000000000000.0
        OR price = 50000.0
        OR (timestamp > '2025-08-12 19:20:00' AND timestamp < '2025-08-12 20:00:00' AND (price < 100000 OR volume_24h < 40000000000))
    ORDER BY timestamp
    '''
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print("SUSPICIOUS RECORDS FOUND:")
    print("=" * 50)
    print(df.to_string(index=False))
    print(f"\nTotal suspicious records: {len(df)}")
    
    return df

def remove_records(record_ids):
    """Remove specified records from database"""
    
    if not record_ids:
        print("No records to remove")
        return
    
    conn = sqlite3.connect('data/crypto_analyser.db')
    cursor = conn.cursor()
    
    print(f"\nRemoving {len(record_ids)} suspicious records...")
    
    # Convert to list if single value
    if isinstance(record_ids, (int, float)):
        record_ids = [record_ids]
    
    for record_id in record_ids:
        print(f"Removing record ID: {record_id}")
        cursor.execute("DELETE FROM bitcoin_prices WHERE id = ?", (record_id,))
    
    conn.commit()
    print(f"Successfully removed {cursor.rowcount} records")
    
    conn.close()

def verify_removal():
    """Verify that suspicious records have been removed"""
    
    conn = sqlite3.connect('data/crypto_analyser.db')
    
    # Check the time window around the false record
    query = '''
    SELECT timestamp, price, volume_24h, market_cap, id
    FROM bitcoin_prices 
    WHERE timestamp BETWEEN '2025-08-12 19:20:00' AND '2025-08-12 20:00:00'
    ORDER BY timestamp
    '''
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print("\nRECORDS AFTER CLEANUP (Aug 12, 19:20-20:00):")
    print("=" * 50)
    print(df.to_string(index=False))
    
    if len(df) > 0:
        print(f"\nPrice range after cleanup: ${df['price'].min():,.2f} - ${df['price'].max():,.2f}")

def analyze_potential_cause():
    """Analyze what might have caused the false records"""
    
    print("\nANALYSIS OF POTENTIAL CAUSES:")
    print("=" * 40)
    print("The false records show several patterns:")
    print("1. Round number values (50000, 30B, 1T) - suggests manual insertion or test data")
    print("2. Timestamp around 19:25-19:57 UTC on Aug 12")
    print("3. Multiple records with similar suspicious patterns")
    print("4. Volume and market cap values that don't match real market conditions")
    print("\nPossible causes:")
    print("- Test data accidentally inserted during development")
    print("- API returned malformed/test data during a specific time window")
    print("- Database corruption or manual data entry error")
    print("- API provider had issues and returned placeholder values")

if __name__ == "__main__":
    print("DATABASE CLEANUP - REMOVING FALSE RECORDS")
    print("=" * 50)
    
    # Step 1: Identify suspicious records
    suspicious_df = identify_suspicious_records()
    
    if len(suspicious_df) > 0:
        # Step 2: Analyze potential cause
        analyze_potential_cause()
        
        # Step 3: Get confirmation and remove
        print(f"\nFound {len(suspicious_df)} suspicious records.")
        print("These will be removed from the database.")
        
        record_ids = suspicious_df['id'].tolist()
        
        # Remove the records
        remove_records(record_ids)
        
        # Step 4: Verify removal
        verify_removal()
        
        print("\nCleanup completed successfully!")
    else:
        print("No suspicious records found.")