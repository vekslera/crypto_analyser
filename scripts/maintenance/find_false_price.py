#!/usr/bin/env python3
"""
Find and analyze the false price record around Aug 12, 19:25 UTC
"""

import sqlite3
import pandas as pd
from datetime import datetime, timezone

def find_false_price():
    """Find the problematic price record"""
    
    # Connect to database
    conn = sqlite3.connect('data/crypto_analyser.db')
    
    # Search for records around Aug 12, 19:25 UTC
    query = '''
    SELECT timestamp, price, volume_24h, market_cap, volatility, money_flow, id
    FROM bitcoin_prices 
    WHERE timestamp BETWEEN '2025-08-12 19:00:00' AND '2025-08-12 20:00:00'
    ORDER BY timestamp
    '''
    
    df = pd.read_sql_query(query, conn)
    
    print('Records around Aug 12, 19:25 UTC:')
    print(df.to_string(index=False))
    print(f'\nTotal records: {len(df)}')
    
    if len(df) > 0:
        print(f'Price range: ${df["price"].min():,.2f} - ${df["price"].max():,.2f}')
        
        # Look for outliers (prices significantly different from median)
        median_price = df['price'].median()
        print(f'Median price: ${median_price:,.2f}')
        
        # Find records that are more than 50% away from median
        outliers = df[abs(df['price'] - median_price) / median_price > 0.5]
        
        if len(outliers) > 0:
            print('\nOUTLIER RECORDS (>50% from median):')
            print(outliers.to_string(index=False))
            
            return outliers
        else:
            print('\nNo obvious outliers found in this time window')
    
    # Also search for any records with price around $50,000
    query_50k = '''
    SELECT timestamp, price, volume_24h, market_cap, volatility, money_flow, id
    FROM bitcoin_prices 
    WHERE price BETWEEN 45000 AND 55000
    AND timestamp > '2025-08-12 19:00:00'
    ORDER BY timestamp
    '''
    
    df_50k = pd.read_sql_query(query_50k, conn)
    
    if len(df_50k) > 0:
        print('\nRECORDS WITH PRICE AROUND $50,000:')
        print(df_50k.to_string(index=False))
    
    conn.close()
    return df_50k if len(df_50k) > 0 else None

def analyze_surrounding_records(record_id):
    """Analyze records before and after the problematic one"""
    
    conn = sqlite3.connect('data/crypto_analyser.db')
    
    # Get records around the problematic one
    query = '''
    SELECT timestamp, price, volume_24h, market_cap, volatility, money_flow, id
    FROM bitcoin_prices 
    WHERE id BETWEEN ? - 5 AND ? + 5
    ORDER BY timestamp
    '''
    
    df = pd.read_sql_query(query, conn, params=(record_id, record_id))
    conn.close()
    
    print(f'\nRECORDS AROUND ID {record_id}:')
    print(df.to_string(index=False))
    
    return df

if __name__ == "__main__":
    print("SEARCHING FOR FALSE PRICE RECORD")
    print("=" * 40)
    
    outliers = find_false_price()
    
    if outliers is not None and len(outliers) > 0:
        for _, row in outliers.iterrows():
            print(f"\nAnalyzing surrounding records for ID {row['id']}:")
            analyze_surrounding_records(row['id'])