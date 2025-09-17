#!/usr/bin/env python3
"""
Simple Correlation Analysis between 24-hour Volatility and Trading Volume
Focus on Pearson correlation without requiring scipy dependencies
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

def analyze_simple_correlation():
    """Simple correlation analysis between 24h volatility and trading volume"""
    
    print("24-HOUR VOLATILITY vs TRADING VOLUME CORRELATION ANALYSIS")
    print("=" * 60)
    print()
    
    # Connect to database
    db_path = os.path.join(project_root, 'data', 'crypto_analyser.db')
    print(f"Database path: {db_path}")
    
    if not os.path.exists(db_path):
        print("ERROR: Database file not found!")
        return
    
    conn = sqlite3.connect(db_path)
    
    # Load data with both volatility and volume
    print("Loading volatility and volume data...")
    query = '''
    SELECT timestamp, price, volatility, volume_24h
    FROM bitcoin_prices 
    WHERE volatility IS NOT NULL 
    AND volume_24h IS NOT NULL 
    AND volume_24h > 0
    ORDER BY timestamp ASC
    '''
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print(f"Loaded {len(df):,} records with both volatility and volume data")
    
    if len(df) < 10:
        print("ERROR: Insufficient data for correlation analysis")
        return
    
    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='mixed', utc=True)
    
    # Basic statistics
    print(f"\nData Overview:")
    print(f"  Time range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"  Duration: {(df['timestamp'].max() - df['timestamp'].min()).days} days")
    
    vol_stats = df['volatility'].describe()
    volume_stats = df['volume_24h'].describe()
    
    print(f"\nVolatility Statistics:")
    print(f"  Mean: {vol_stats['mean']:.4f}%")
    print(f"  Std:  {vol_stats['std']:.4f}%")
    print(f"  Min:  {vol_stats['min']:.4f}%")
    print(f"  Max:  {vol_stats['max']:.4f}%")
    
    print(f"\nVolume Statistics (USD):")
    print(f"  Mean: ${volume_stats['mean']:,.0f}")
    print(f"  Std:  ${volume_stats['std']:,.0f}")
    print(f"  Min:  ${volume_stats['min']:,.0f}")
    print(f"  Max:  ${volume_stats['max']:,.0f}")
    
    # Calculate Pearson correlation (linear relationship)
    print(f"\nCORRELATION ANALYSIS:")
    print("=" * 30)
    
    pearson_corr = df['volatility'].corr(df['volume_24h'], method='pearson')
    print(f"Pearson Correlation (linear relationship):")
    print(f"  Coefficient: {pearson_corr:.6f}")
    
    # R-squared (coefficient of determination)
    r_squared = pearson_corr ** 2
    print(f"\nExplained Variance (R²):")
    print(f"  Linear model: {r_squared:.4f} ({r_squared*100:.2f}%)")
    
    # Logarithmic transformation analysis (power-law relationship)
    print(f"\nPOWER-LAW ANALYSIS:")
    print("=" * 20)
    
    # Check for positive values before log transformation
    if (df['volume_24h'] > 0).all() and (df['volatility'] > 0).all():
        df['log_volume'] = np.log(df['volume_24h'])
        df['log_volatility'] = np.log(df['volatility'])
        
        log_pearson_corr = df['log_volatility'].corr(df['log_volume'], method='pearson')
        log_r_squared = log_pearson_corr ** 2
        
        print(f"Log-Log Correlation:")
        print(f"  Coefficient: {log_pearson_corr:.6f}")
        print(f"  R²: {log_r_squared:.4f} ({log_r_squared*100:.2f}%)")
        
        # Determine which model fits better
        if log_r_squared > r_squared:
            print(f"  BETTER FIT: Power-law relationship explains more variance")
            best_model = "power-law"
            best_r2 = log_r_squared
        else:
            print(f"  BETTER FIT: Linear relationship explains more variance")
            best_model = "linear"
            best_r2 = r_squared
    else:
        log_pearson_corr = np.nan
        best_model = "linear"
        best_r2 = r_squared
        print(f"Log-Log Correlation: Cannot calculate (negative/zero values present)")
    
    # Time-based analysis (recent vs historical)
    print(f"\nTIME-BASED ANALYSIS:")
    print("=" * 22)
    
    recent_cutoff = df['timestamp'].max() - timedelta(days=7)
    recent_data = df[df['timestamp'] >= recent_cutoff]
    historical_data = df[df['timestamp'] < recent_cutoff]
    
    if len(recent_data) > 5 and len(historical_data) > 5:
        recent_corr = recent_data['volatility'].corr(recent_data['volume_24h'], method='pearson')
        historical_corr = historical_data['volatility'].corr(historical_data['volume_24h'], method='pearson')
        
        print(f"Recent (last 7 days): {recent_corr:.6f} (n={len(recent_data)})")
        print(f"Historical (older): {historical_corr:.6f} (n={len(historical_data)})")
        print(f"Difference: {abs(recent_corr - historical_corr):.6f}")
        
        if abs(recent_corr - historical_corr) < 0.1:
            print("STABLE: Correlation is consistent over time")
        else:
            print("VARIABLE: Correlation has changed significantly")
    
    # Interpretation
    print(f"\nINTERPRETATION:")
    print("=" * 20)
    
    def interpret_correlation(corr):
        abs_corr = abs(corr)
        if abs_corr >= 0.8:
            return "Very Strong"
        elif abs_corr >= 0.6:
            return "Strong"
        elif abs_corr >= 0.4:
            return "Moderate"
        elif abs_corr >= 0.2:
            return "Weak"
        else:
            return "Very Weak"
    
    strength = interpret_correlation(pearson_corr)
    print(f"Relationship Strength: {strength} ({pearson_corr:+.3f})")
    
    if pearson_corr > 0:
        print(f"\nPositive correlation indicates: Higher volatility -> Higher trading volume")
        print(f"This is consistent with financial theory:")
        print(f"- Uncertain markets drive more trading activity")
        print(f"- Increased volatility creates arbitrage opportunities")
        print(f"- Risk-averse investors adjust positions more frequently")
    else:
        print(f"\nNegative correlation indicates: Higher volatility -> Lower trading volume")
        print(f"This would be unusual and might indicate:")
        print(f"- Market freezing during extreme uncertainty")
        print(f"- Liquidity crises or exchange issues")
    
    # Financial significance
    print(f"\nFINANCIAL SIGNIFICANCE:")
    print("=" * 25)
    print(f"- Volatility explains {best_r2*100:.1f}% of volume variance ({best_model} model)")
    print(f"- {strength.lower()} correlation suggests:")
    
    if strength in ["Strong", "Very Strong"]:
        print(f"  * Highly efficient market mechanisms")
        print(f"  * Predictable volume-volatility relationship")
        print(f"  * Reliable for risk management models")
    elif strength == "Moderate":
        print(f"  * Moderately efficient market mechanisms")
        print(f"  * Other factors also influence trading volume")
        print(f"  * Useful but not sole predictor for models")
    else:
        print(f"  * Weak market efficiency or external factors")
        print(f"  * Volume driven by factors other than volatility")
        print(f"  * Limited predictive value")
    
    print(f"\nPRACTICAL APPLICATIONS:")
    print(f"- Risk management: Estimate trading costs during volatile periods")
    print(f"- Market making: Adjust spreads based on expected volume")
    print(f"- Portfolio rebalancing: Time trades to optimize liquidity")
    print(f"- Volatility forecasting: Use volume patterns as leading indicator")
    
    # Summary
    print(f"\nSUMMARY:")
    print("=" * 10)
    print(f"24h Volatility vs 24h Trading Volume: {pearson_corr:+.4f} correlation")
    print(f"Relationship: {strength} positive correlation")
    print(f"Explanation: Volatility explains {r_squared*100:.1f}% of volume variance")
    print(f"Financial Theory: {'Consistent' if pearson_corr > 0.3 else 'Weak consistency'}")
    
    return {
        'pearson_correlation': pearson_corr,
        'r_squared': r_squared,
        'log_correlation': log_pearson_corr if not np.isnan(log_pearson_corr) else None,
        'data_points': len(df),
        'interpretation': strength,
        'best_model': best_model
    }

if __name__ == "__main__":
    try:
        result = analyze_simple_correlation()
        print(f"\nAnalysis complete!")
    except Exception as e:
        print(f"ERROR: Error during analysis: {e}")
        import traceback
        traceback.print_exc()