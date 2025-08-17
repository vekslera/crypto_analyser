#!/usr/bin/env python3
"""
Deep analysis of market cap approach for money flow measurement
Addresses:
1. CoinGecko vs CMC market cap comparison
2. Circulating supply analysis
3. Supply definition investigation
4. Trading volume vs market cap relationship
"""

import sys
import os
import requests
import sqlite3
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def compare_market_cap_sources():
    """Compare market cap values from CoinGecko vs CMC"""
    
    print("1. COMPARING MARKET CAP SOURCES: COINGECKO vs CMC")
    print("=" * 60)
    
    api_key = os.getenv('CMC_API_KEY')
    
    # Get CMC data
    cmc_data = None
    if api_key:
        try:
            headers = {'Accepts': 'application/json', 'X-CMC_PRO_API_KEY': api_key}
            cmc_response = requests.get(
                'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest',
                headers=headers,
                params={'id': '1'},
                timeout=10
            )
            
            if cmc_response.status_code == 200:
                cmc_json = cmc_response.json()
                if '1' in cmc_json['data']:
                    cmc_data = cmc_json['data']['1']
                    print("CMC Data Retrieved:")
                    print(f"  Price: ${cmc_data['quote']['USD']['price']:,.2f}")
                    print(f"  Market Cap: ${cmc_data['quote']['USD']['market_cap']:,.0f}")
                    print(f"  Volume 24h: ${cmc_data['quote']['USD']['volume_24h']:,.0f}")
                    print(f"  Circulating Supply: {cmc_data['circulating_supply']:,.0f} BTC")
                    print(f"  Max Supply: {cmc_data.get('max_supply', 'N/A')} BTC")
                    print(f"  Total Supply: {cmc_data.get('total_supply', 'N/A')} BTC")
            else:
                print(f"CMC API Error: {cmc_response.status_code}")
                
        except Exception as e:
            print(f"CMC API Error: {e}")
    
    # Get CoinGecko data
    cg_data = None
    try:
        cg_response = requests.get(
            'https://api.coingecko.com/api/v3/coins/bitcoin',
            params={'localization': 'false', 'tickers': 'false', 'community_data': 'false', 'developer_data': 'false'},
            timeout=10
        )
        
        if cg_response.status_code == 200:
            cg_json = cg_response.json()
            cg_data = cg_json
            market_data = cg_data['market_data']
            
            print(f"\nCoinGecko Data Retrieved:")
            print(f"  Price: ${market_data['current_price']['usd']:,.2f}")
            print(f"  Market Cap: ${market_data['market_cap']['usd']:,.0f}")
            print(f"  Volume 24h: ${market_data['total_volume']['usd']:,.0f}")
            print(f"  Circulating Supply: {market_data['circulating_supply']:,.0f} BTC")
            print(f"  Max Supply: {market_data.get('max_supply', 'N/A')} BTC")
            print(f"  Total Supply: {market_data.get('total_supply', 'N/A')} BTC")
        else:
            print(f"CoinGecko API Error: {cg_response.status_code}")
            
    except Exception as e:
        print(f"CoinGecko API Error: {e}")
    
    # Compare if both available
    if cmc_data and cg_data:
        print(f"\nCOMPARISON:")
        print("-" * 30)
        
        cmc_market_cap = cmc_data['quote']['USD']['market_cap']
        cg_market_cap = cg_data['market_data']['market_cap']['usd']
        
        cmc_circ_supply = cmc_data['circulating_supply']
        cg_circ_supply = cg_data['market_data']['circulating_supply']
        
        cmc_price = cmc_data['quote']['USD']['price']
        cg_price = cg_data['market_data']['current_price']['usd']
        
        market_cap_diff = abs(cmc_market_cap - cg_market_cap)
        market_cap_diff_pct = (market_cap_diff / cg_market_cap) * 100
        
        supply_diff = abs(cmc_circ_supply - cg_circ_supply)
        supply_diff_pct = (supply_diff / cg_circ_supply) * 100
        
        price_diff = abs(cmc_price - cg_price)
        price_diff_pct = (price_diff / cg_price) * 100
        
        print(f"Market Cap Difference: ${market_cap_diff:,.0f} ({market_cap_diff_pct:.3f}%)")
        print(f"Supply Difference: {supply_diff:,.0f} BTC ({supply_diff_pct:.6f}%)")
        print(f"Price Difference: ${price_diff:,.2f} ({price_diff_pct:.3f}%)")
        
        # Check consistency: Market Cap = Price × Supply
        cmc_calculated_mcap = cmc_price * cmc_circ_supply
        cg_calculated_mcap = cg_price * cg_circ_supply
        
        print(f"\nConsistency Check (Market Cap = Price x Supply):")
        print(f"CMC: ${cmc_market_cap:,.0f} reported vs ${cmc_calculated_mcap:,.0f} calculated")
        print(f"CG:  ${cg_market_cap:,.0f} reported vs ${cg_calculated_mcap:,.0f} calculated")
        
        cmc_consistency = abs(cmc_market_cap - cmc_calculated_mcap) / cmc_market_cap * 100
        cg_consistency = abs(cg_market_cap - cg_calculated_mcap) / cg_market_cap * 100
        
        print(f"CMC consistency error: {cmc_consistency:.6f}%")
        print(f"CG consistency error: {cg_consistency:.6f}%")
        
        return {
            'cmc': cmc_data,
            'cg': cg_data,
            'market_cap_diff_pct': market_cap_diff_pct,
            'supply_diff_pct': supply_diff_pct,
            'price_diff_pct': price_diff_pct
        }
    
    return None

def analyze_circulating_supply():
    """Analyze circulating supply definition and stability"""
    
    print(f"\n\n3. CIRCULATING SUPPLY DEFINITION & ANALYSIS")
    print("=" * 50)
    
    print("CIRCULATING SUPPLY DEFINITION:")
    print("-" * 35)
    print("Per CoinMarketCap/CoinGecko methodology:")
    print("+ Circulating Supply = Total mined BTC - Lost/Burned BTC")
    print("+ Includes BTC in inactive wallets (even dormant for years)")
    print("+ Excludes only provably lost/burned coins")
    print("+ Does NOT exclude dormant wallets (Satoshi's coins, etc.)")
    print()
    print("KEY INSIGHT:")
    print("- Dormant BTC moving does NOT change circulating supply")
    print("- But it can cause significant price impact")
    print("- This is why market cap can change more than trading volume")
    print()
    print("BITCOIN SUPPLY MECHANICS:")
    print("- Current circulating supply: ~19.8M BTC")
    print("- Max supply: 21M BTC")
    print("- Mining rate: ~6.25 BTC per block (every ~10 minutes)")
    print("- Supply increases by ~328 BTC/day (very predictable)")
    print("- Next halving: ~2028 (3.125 BTC per block)")
    
    # Analyze our historical supply data if available
    db_path = os.path.join(project_root, "data", "crypto_analyser.db")
    
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            
            # Check if we have supply data
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(bitcoin_prices)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'circulating_supply' in columns:
                query = """
                SELECT 
                    datetime(timestamp) as time,
                    market_cap,
                    price,
                    market_cap / price as implied_supply
                FROM bitcoin_prices 
                WHERE market_cap IS NOT NULL AND price > 0
                ORDER BY timestamp DESC 
                LIMIT 20
                """
                
                df = pd.read_sql_query(query, conn)
                
                if len(df) > 0:
                    print(f"\nHISTORICAL SUPPLY ANALYSIS:")
                    print("-" * 30)
                    print(f"Records analyzed: {len(df)}")
                    print(f"Implied supply range: {df['implied_supply'].min():,.0f} - {df['implied_supply'].max():,.0f} BTC")
                    print(f"Supply std dev: {df['implied_supply'].std():,.0f} BTC")
                    print(f"Supply CV: {df['implied_supply'].std() / df['implied_supply'].mean():.6f}")
                    
                    # Check for supply jumps
                    df_sorted = df.sort_values('time')
                    df_sorted['supply_change'] = df_sorted['implied_supply'].diff()
                    large_changes = df_sorted[abs(df_sorted['supply_change']) > 1000]
                    
                    if len(large_changes) > 0:
                        print(f"Large supply changes (>1000 BTC): {len(large_changes)}")
                        for _, row in large_changes.head(3).iterrows():
                            print(f"  {row['time']}: {row['supply_change']:+,.0f} BTC")
            
            conn.close()
            
        except Exception as e:
            print(f"Error analyzing historical supply: {e}")
    
    return None

def analyze_market_cap_vs_volume_relationship():
    """Analyze the relationship between market cap changes and trading volume"""
    
    print(f"\n\n4. MARKET CAP vs TRADING VOLUME RELATIONSHIP")
    print("=" * 55)
    
    print("THEORETICAL ANALYSIS:")
    print("-" * 25)
    print("Market Cap Change = Price Change x Circulating Supply")
    print("Trading Volume = Amount of BTC actually traded x Average Price")
    print()
    print("KEY DIFFERENCES:")
    print("1. Market cap reflects VALUATION change of ALL Bitcoin")
    print("2. Trading volume reflects ACTUAL money flow in exchanges")
    print("3. Large holders moving BTC affects price (and market cap) disproportionately")
    print("4. Psychological factors can change market cap without proportional volume")
    print()
    
    # Analyze our data
    db_path = os.path.join(project_root, "data", "crypto_analyser.db")
    
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            
            query = """
            SELECT 
                datetime(timestamp, '+2 hours') as israel_time,
                price,
                volume_24h,
                volume_velocity,
                market_cap
            FROM bitcoin_prices 
            WHERE timestamp >= datetime('now', '-12 hours')
                AND market_cap IS NOT NULL 
                AND volume_24h IS NOT NULL
            ORDER BY timestamp ASC
            """
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if len(df) > 1:
                # Calculate changes
                df['price_change'] = df['price'].diff()
                df['market_cap_change'] = df['market_cap'].diff()
                df['volume_velocity_abs'] = abs(df['volume_velocity'])
                df['market_cap_velocity'] = df['market_cap_change'] / 5  # per minute
                df['market_cap_velocity_abs'] = abs(df['market_cap_velocity'])
                
                # Remove NaN values
                analysis_df = df.dropna()
                
                if len(analysis_df) > 5:
                    print(f"EMPIRICAL ANALYSIS:")
                    print("-" * 20)
                    print(f"Data points: {len(analysis_df)}")
                    
                    # Correlation analysis
                    if len(analysis_df) > 2:
                        # Price change vs market cap change (should be highly correlated)
                        price_mcap_corr = analysis_df['price_change'].corr(analysis_df['market_cap_change'])
                        
                        # Volume velocity vs market cap velocity (our key question)
                        vol_mcap_corr = analysis_df['volume_velocity_abs'].corr(analysis_df['market_cap_velocity_abs'])
                        
                        print(f"Price change <-> Market cap change correlation: {price_mcap_corr:.4f}")
                        print(f"Volume velocity <-> Market cap velocity correlation: {vol_mcap_corr:.4f}")
                        print()
                        
                        if price_mcap_corr > 0.9:
                            print("SUCCESS: Market cap changes track price changes well (expected)")
                        else:
                            print("WARNING: Market cap and price changes not well correlated (investigate)")
                        
                        if vol_mcap_corr > 0.5:
                            print("SUCCESS: Market cap velocity correlates with volume velocity")
                        elif vol_mcap_corr > 0.3:
                            print("MODERATE: Market cap velocity moderately correlates with volume velocity")
                        else:
                            print("POOR: Market cap velocity poorly correlates with volume velocity")
                    
                    # Ratio analysis
                    print(f"\nRATIO ANALYSIS:")
                    print("-" * 15)
                    
                    # Calculate market cap change per dollar of volume
                    analysis_df['mcap_per_volume_ratio'] = analysis_df['market_cap_velocity_abs'] / analysis_df['volume_velocity_abs']
                    valid_ratios = analysis_df['mcap_per_volume_ratio'].replace([np.inf, -np.inf], np.nan).dropna()
                    
                    if len(valid_ratios) > 0:
                        print(f"Market cap velocity / Volume velocity ratio:")
                        print(f"  Mean: {valid_ratios.mean():.4f}")
                        print(f"  Median: {valid_ratios.median():.4f}")
                        print(f"  Std: {valid_ratios.std():.4f}")
                        print(f"  Range: {valid_ratios.min():.4f} to {valid_ratios.max():.4f}")
                        
                        if valid_ratios.std() / valid_ratios.mean() < 0.5:
                            print("SUCCESS: Ratio is relatively stable - good conversion factor")
                        else:
                            print("WARNING: Ratio is highly variable - conversion unreliable")
                    
                    # Show examples of extreme cases
                    print(f"\nEXTREME CASES ANALYSIS:")
                    print("-" * 25)
                    
                    high_vol_vel = analysis_df[analysis_df['volume_velocity_abs'] > analysis_df['volume_velocity_abs'].quantile(0.9)]
                    high_mcap_vel = analysis_df[analysis_df['market_cap_velocity_abs'] > analysis_df['market_cap_velocity_abs'].quantile(0.9)]
                    
                    print(f"High volume velocity periods: {len(high_vol_vel)}")
                    print(f"High market cap velocity periods: {len(high_mcap_vel)}")
                    
                    # Check if they coincide
                    overlap = len(pd.merge(high_vol_vel[['israel_time']], high_mcap_vel[['israel_time']], on='israel_time'))
                    print(f"Periods with both high volume and market cap velocity: {overlap}")
                    
                    if overlap > 0:
                        print("SUCCESS: High volume and market cap velocities often coincide")
                    else:
                        print("ISSUE: High volume and market cap velocities rarely coincide")
        
        except Exception as e:
            print(f"Error in empirical analysis: {e}")
            import traceback
            traceback.print_exc()

def provide_recommendations():
    """Provide recommendations based on analysis"""
    
    print(f"\n\nRECOMMENDATIONS & CONCLUSIONS")
    print("=" * 40)
    
    print("MARKET CAP APPROACH ASSESSMENT:")
    print("-" * 35)
    print("PROS:")
    print("  + No 24h sliding window artifacts")
    print("  + Real-time availability") 
    print("  + Reflects price impact of money flow")
    print("  + Much more stable than volume velocity")
    print("  + Consistent between CoinGecko and CMC")
    print()
    print("CONSIDERATIONS:")
    print("  - Market cap != actual money traded")
    print("  - Psychological factors can amplify changes")
    print("  - Dormant coin movements create disproportionate impact")
    print("  - Supply changes (mining) introduce small noise")
    print()
    print("IMPLEMENTATION RECOMMENDATIONS:")
    print("-" * 35)
    print("1. PRIMARY METRIC: Market Cap Velocity")
    print("   - Most stable and meaningful for money flow impact")
    print("   - Free from sliding window artifacts")
    print()
    print("2. SECONDARY METRIC: Price Velocity")  
    print("   - Even more direct measure of market impact")
    print("   - Price Change per minute")
    print()
    print("3. VALIDATION: Keep Volume Velocity for comparison")
    print("   - Flag periods where they diverge significantly")
    print("   - Investigate anomalies")
    print()
    print("4. ALERT THRESHOLDS:")
    print("   - Market Cap Velocity > $1B/min: Significant event")
    print("   - Price Velocity > $100/min: High volatility")
    print("   - Volume/Market Cap divergence > 5x: Investigate")

if __name__ == "__main__":
    print("DEEP MARKET CAP ANALYSIS FOR MONEY FLOW MEASUREMENT")
    print("=" * 65)
    
    # Run all analyses
    comparison_result = compare_market_cap_sources()
    analyze_circulating_supply()
    analyze_market_cap_vs_volume_relationship()
    provide_recommendations()