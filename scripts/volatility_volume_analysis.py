#!/usr/bin/env python3
"""
Volatility analysis to estimate trading volume (V) independently
Uses established financial relationships between volatility and trading volume
"""

import sys
import os
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def analyze_volatility_volume_theory():
    """Analyze theoretical relationship between volatility and trading volume"""
    
    print("VOLATILITY-VOLUME RELATIONSHIP THEORY")
    print("=" * 40)
    
    print("\nESTABLISHED FINANCIAL RELATIONSHIPS:")
    print("-" * 35)
    print("1. MIXTURE OF DISTRIBUTIONS HYPOTHESIS:")
    print("   Volatility = f(Trading Volume, Information Flow)")
    print("   Higher volume → Higher volatility")
    print()
    
    print("2. EMPIRICAL POWER LAW:")
    print("   σ ∝ V^β")
    print("   Where σ = volatility, V = volume, β ≈ 0.1-0.3")
    print()
    
    print("3. INTRADAY VOLATILITY MODEL:")
    print("   σ(t) = σ₀ × √(V(t) / V_avg)")
    print("   Where σ₀ = baseline volatility, V_avg = average volume")
    print()
    
    print("4. GARCH-VOLUME MODEL:")
    print("   σₜ² = ω + α×(εₜ₋₁² / Vₜ₋₁) + β×σₜ₋₁²")
    print("   Volume normalizes volatility shocks")
    print()

def calculate_bitcoin_volatility():
    """Calculate different volatility measures from our Bitcoin data"""
    
    print("\nBITCOIN VOLATILITY ANALYSIS")
    print("=" * 30)
    
    db_path = os.path.join(project_root, "data", "crypto_analyser.db")
    
    if not os.path.exists(db_path):
        print("Database not found. Run the data collection first.")
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Get recent price data
        query = """
        SELECT 
            datetime(timestamp) as time,
            price,
            volume_24h,
            volume_velocity,
            market_cap
        FROM bitcoin_prices 
        WHERE timestamp >= datetime('now', '-24 hours')
            AND price IS NOT NULL
        ORDER BY timestamp ASC
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if len(df) < 10:
            print("Not enough data for volatility analysis")
            return None
        
        # Calculate returns (price changes)
        df['returns'] = df['price'].pct_change()
        df['log_returns'] = np.log(df['price'] / df['price'].shift(1))
        
        # Remove NaN values
        df = df.dropna()
        
        if len(df) < 5:
            print("Insufficient data after cleaning")
            return None
        
        print(f"Analyzing {len(df)} data points over last 24 hours")
        print()
        
        # Calculate different volatility measures
        volatility_measures = {}
        
        # 1. Standard deviation of returns (annualized)
        returns_std = df['returns'].std()
        # Convert 5-minute intervals to annual (assuming 288 intervals per day, 365 days)
        annual_periods = 288 * 365
        volatility_measures['returns_annualized'] = returns_std * np.sqrt(annual_periods)
        
        # 2. Realized volatility (sum of squared returns)
        realized_vol = np.sqrt(np.sum(df['returns']**2))
        volatility_measures['realized'] = realized_vol
        
        # 3. GARCH-like measure (rolling volatility)
        window = min(12, len(df)//2)  # 1-hour window or half the data
        df['rolling_vol'] = df['returns'].rolling(window=window).std()
        volatility_measures['rolling_avg'] = df['rolling_vol'].mean()
        
        # 4. Log return volatility
        log_vol = df['log_returns'].std()
        volatility_measures['log_returns'] = log_vol * np.sqrt(annual_periods)
        
        print("VOLATILITY MEASURES:")
        print("-" * 20)
        for measure, value in volatility_measures.items():
            if not np.isnan(value):
                print(f"{measure}: {value:.6f}")
        
        return df, volatility_measures
        
    except Exception as e:
        print(f"Error in volatility calculation: {e}")
        return None

def estimate_volume_from_volatility(df, volatility_measures):
    """Estimate trading volume using volatility-volume relationships"""
    
    print("\nVOLUME ESTIMATION FROM VOLATILITY")
    print("=" * 35)
    
    if df is None or volatility_measures is None:
        print("No volatility data available")
        return
    
    # Get current market data
    latest_price = df['price'].iloc[-1]
    latest_market_cap = df['market_cap'].iloc[-1] if df['market_cap'].iloc[-1] else latest_price * 19.9e6
    
    print(f"Current price: ${latest_price:,.2f}")
    print(f"Current market cap: ${latest_market_cap:,.0f}")
    print()
    
    # Method 1: Use power law relationship σ ∝ V^β
    print("METHOD 1: POWER LAW ESTIMATION")
    print("-" * 30)
    
    # Estimate baseline parameters from literature
    # For Bitcoin: β typically 0.15-0.25
    beta_values = [0.15, 0.2, 0.25]
    
    # Use realized volatility as our σ
    current_vol = volatility_measures.get('realized', 0)
    
    if current_vol > 0:
        print(f"Current volatility (σ): {current_vol:.6f}")
        
        # Estimate baseline volume (calibration needed with historical data)
        # Assume typical Bitcoin daily volume is ~$30B, for 5-min periods: ~$100M
        baseline_vol_usd = 100e6  # $100M baseline for 5-min period
        baseline_volatility = 0.001  # 0.1% baseline volatility
        
        for beta in beta_values:
            # σ ∝ V^β → V = (σ/σ₀)^(1/β) × V₀
            estimated_vol_usd = baseline_vol_usd * (current_vol / baseline_volatility)**(1/beta)
            estimated_vol_btc = estimated_vol_usd / latest_price
            
            print(f"  β = {beta}: Estimated volume = {estimated_vol_btc:,.0f} BTC (${estimated_vol_usd:,.0f})")
    
    # Method 2: Square root relationship
    print("\nMETHOD 2: SQUARE ROOT RELATIONSHIP")
    print("-" * 35)
    
    # σ ∝ √V → V = (σ/k)²
    # Calibrate k using typical values
    k_values = [0.0001, 0.0005, 0.001]  # Calibration constants
    
    for k in k_values:
        estimated_vol_btc = (current_vol / k)**2
        estimated_vol_usd = estimated_vol_btc * latest_price
        
        if estimated_vol_usd < 1e12:  # Sanity check: less than $1T
            print(f"  k = {k}: Estimated volume = {estimated_vol_btc:,.0f} BTC (${estimated_vol_usd:,.0f})")
    
    # Method 3: Use market cap changes and price volatility
    print("\nMETHOD 3: MARKET CAP VOLATILITY APPROACH")
    print("-" * 40)
    
    if len(df) >= 2:
        # Calculate market cap changes
        df['market_cap_change'] = df['market_cap'].diff()
        df['price_change'] = df['price'].diff()
        
        # Get valid data
        valid_data = df.dropna()
        
        if len(valid_data) >= 2:
            # Use our relationship: S = Q × ΔP and X = V × ΔP
            # If we assume typical amplification factors
            
            recent_data = valid_data.tail(5)  # Last 5 data points
            
            print("Recent market dynamics:")
            for i, (_, row) in enumerate(recent_data.iterrows()):
                price_change = row['price_change']
                mcap_change = row['market_cap_change']
                
                if abs(price_change) > 0.01:  # Meaningful price change
                    # Calculate implied volume using volatility
                    vol_estimate = abs(mcap_change) / (19.9e6 * abs(price_change)) * abs(price_change)
                    vol_btc = vol_estimate / latest_price if latest_price > 0 else 0
                    
                    print(f"  Point {i+1}: Price Δ=${price_change:+,.2f}, Volume est.={vol_btc:,.0f} BTC")

def compare_with_reported_volumes(df):
    """Compare our estimates with reported 24h volumes"""
    
    print("\nCOMPARISON WITH REPORTED VOLUMES")
    print("=" * 35)
    
    if df is None or len(df) == 0:
        print("No data for comparison")
        return
    
    # Get reported 24h volumes
    reported_volumes = df['volume_24h'].dropna()
    
    if len(reported_volumes) == 0:
        print("No reported volume data available")
        return
    
    latest_24h_volume = reported_volumes.iloc[-1]
    avg_24h_volume = reported_volumes.mean()
    
    print(f"Reported 24h volume (latest): ${latest_24h_volume:,.0f}")
    print(f"Reported 24h volume (average): ${avg_24h_volume:,.0f}")
    print()
    
    # Convert to 5-minute equivalent
    # 24h = 288 five-minute periods
    equivalent_5min_volume = latest_24h_volume / 288
    
    print(f"Equivalent 5-min volume: ${equivalent_5min_volume:,.0f}")
    print("(This assumes uniform distribution over 24h)")
    print()
    
    print("COMPARISON WITH VOLATILITY ESTIMATES:")
    print("Compare the volatility-based estimates above with:")
    print(f"Reported 5-min equivalent: ${equivalent_5min_volume:,.0f}")

if __name__ == "__main__":
    analyze_volatility_volume_theory()
    
    result = calculate_bitcoin_volatility()
    if result:
        df, vol_measures = result
        estimate_volume_from_volatility(df, vol_measures)
        compare_with_reported_volumes(df)
    
    print("\nCONCLUSION:")
    print("-" * 11)
    print("• Volatility analysis can provide independent volume estimates")
    print("• Multiple models available (power law, square root, market cap)")
    print("• Calibration with historical data needed for accuracy")
    print("• Can be combined with market cap analysis for better X and V separation")