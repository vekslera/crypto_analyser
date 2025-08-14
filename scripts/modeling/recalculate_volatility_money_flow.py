#!/usr/bin/env python3
"""
Recalculate volatility and money flow for all records after removing false data
This ensures all calculations are based on clean, accurate price data
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime

def recalculate_all_metrics():
    """Recalculate volatility and money flow for all records"""
    
    print("RECALCULATING VOLATILITY AND MONEY FLOW")
    print("=" * 45)
    
    # Connect to database
    conn = sqlite3.connect('data/crypto_analyser.db')
    
    # Load all data ordered by timestamp
    query = '''
    SELECT id, timestamp, price, volume_24h, market_cap
    FROM bitcoin_prices 
    ORDER BY timestamp ASC
    '''
    
    df = pd.read_sql_query(query, conn)
    print(f"Loaded {len(df)} records for recalculation")
    
    # Convert timestamp to datetime for easier manipulation
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Initialize new columns
    df['volatility_new'] = None
    df['money_flow_new'] = None
    
    # Recalculate for each record (starting from record with enough history)
    updated_count = 0
    
    for i in range(len(df)):
        if i >= 4:  # Need at least 4 previous points for 5-point rolling calculation
            # Get the current and 4 previous records for 5-point window
            window_start = max(0, i - 4)
            window_data = df.iloc[window_start:i+1]
            
            if len(window_data) >= 5:
                # Calculate returns from price changes
                prices = window_data['price'].values
                returns = []
                for j in range(1, len(prices)):
                    returns.append((prices[j] - prices[j-1]) / prices[j-1])
                
                if len(returns) >= 4:
                    # Calculate volatility (standard deviation of returns)
                    recent_returns = returns[-4:]  # Last 4 returns
                    mean_return = np.mean(recent_returns)
                    variance = np.var(recent_returns, ddof=1)  # Sample variance
                    volatility = np.sqrt(variance) * 100  # Convert to percentage
                    
                    # Calculate BTC volume from volatility using current parameters
                    k = 1.0e-2  # Will update with calibrated values later
                    beta = 0.2
                    btc_volume = (volatility / 100 / k) ** (1 / beta)
                    
                    # Calculate money flow with direction (current price vs 4 records ago)
                    current_price = df.iloc[i]['price']
                    reference_price = df.iloc[max(0, i-4)]['price']
                    price_change = current_price - reference_price
                    money_flow = btc_volume * price_change
                    
                    # Store calculated values
                    df.at[i, 'volatility_new'] = volatility
                    df.at[i, 'money_flow_new'] = money_flow
                    updated_count += 1
                    
                    if updated_count % 500 == 0:
                        print(f"Processed {updated_count} records...")
    
    print(f"Calculated new metrics for {updated_count} records")
    
    # Update database with new values
    cursor = conn.cursor()
    
    print("Updating database with recalculated values...")
    update_count = 0
    
    for i, row in df.iterrows():
        if pd.notna(row['volatility_new']) and pd.notna(row['money_flow_new']):
            cursor.execute("""
                UPDATE bitcoin_prices 
                SET volatility = ?, money_flow = ?
                WHERE id = ?
            """, (row['volatility_new'], row['money_flow_new'], row['id']))
            update_count += 1
    
    # Set volatility and money_flow to NULL for records without enough history
    cursor.execute("""
        UPDATE bitcoin_prices 
        SET volatility = NULL, money_flow = NULL
        WHERE id IN (
            SELECT id FROM bitcoin_prices 
            ORDER BY timestamp ASC 
            LIMIT 4
        )
    """)
    
    conn.commit()
    print(f"Updated {update_count} records in database")
    
    # Verify the updates
    verification_query = '''
    SELECT 
        COUNT(*) as total_records,
        COUNT(volatility) as records_with_volatility,
        COUNT(money_flow) as records_with_money_flow,
        AVG(volatility) as avg_volatility,
        MIN(volatility) as min_volatility,
        MAX(volatility) as max_volatility,
        AVG(money_flow) as avg_money_flow,
        MIN(money_flow) as min_money_flow,
        MAX(money_flow) as max_money_flow
    FROM bitcoin_prices
    '''
    
    verification = pd.read_sql_query(verification_query, conn)
    
    print("\nVERIFICATION RESULTS:")
    print("-" * 25)
    print(f"Total records: {verification['total_records'].iloc[0]}")
    print(f"Records with volatility: {verification['records_with_volatility'].iloc[0]}")
    print(f"Records with money flow: {verification['records_with_money_flow'].iloc[0]}")
    print(f"Average volatility: {verification['avg_volatility'].iloc[0]:.4f}%")
    print(f"Volatility range: {verification['min_volatility'].iloc[0]:.4f}% to {verification['max_volatility'].iloc[0]:.4f}%")
    print(f"Average money flow: ${verification['avg_money_flow'].iloc[0]:,.0f}")
    print(f"Money flow range: ${verification['min_money_flow'].iloc[0]:,.0f} to ${verification['max_money_flow'].iloc[0]:,.0f}")
    
    # Show sample of recalculated data around the area where false records were removed
    sample_query = '''
    SELECT timestamp, price, volatility, money_flow
    FROM bitcoin_prices 
    WHERE timestamp BETWEEN '2025-08-12 19:00:00' AND '2025-08-12 20:30:00'
    ORDER BY timestamp
    '''
    
    sample_data = pd.read_sql_query(sample_query, conn)
    
    print("\nSAMPLE DATA AROUND CLEANED AREA:")
    print("-" * 35)
    print(sample_data.to_string(index=False))
    
    conn.close()
    
    print(f"\nRecalculation completed successfully!")
    print(f"All volatility and money flow values have been recalculated based on clean price data.")

if __name__ == "__main__":
    recalculate_all_metrics()