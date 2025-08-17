#!/usr/bin/env python3
"""
Deep analysis of Bitcoin pricing mechanism to understand the relationship 
between market cap changes and actual trading volumes.

Key Questions:
1. How does BTC price formation work across exchanges?
2. What is the relationship between order book depth and price impact?
3. Can we estimate trading volume from price movements?
4. How do market makers, arbitrageurs, and sentiment affect the relationship?
"""

import sys
import os
import requests
import sqlite3
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import math

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def analyze_price_formation_theory():
    """Analyze theoretical Bitcoin price formation mechanism"""
    
    print("BITCOIN PRICE FORMATION MECHANISM ANALYSIS")
    print("=" * 55)
    
    print("1. PRICE DISCOVERY FUNDAMENTALS:")
    print("-" * 35)
    print("Bitcoin price is determined by:")
    print("+ Order book matching on exchanges")
    print("+ Arbitrage between exchanges")
    print("+ Market maker algorithms")
    print("+ Supply/demand imbalances")
    print()
    print("Key Formula: Price Impact = Volume / Market Depth")
    print("Where Market Depth = Available liquidity at current price levels")
    print()
    
    print("2. MARKET CAP vs TRADING VOLUME RELATIONSHIP:")
    print("-" * 50)
    print("Market Cap Change = Price Change × Circulating Supply")
    print("Trading Volume = Actual BTC traded × Average Price")
    print()
    print("CRITICAL INSIGHT:")
    print("Price impact depends on ORDER BOOK DEPTH, not total supply!")
    print()
    print("Example Scenarios:")
    print("Scenario A - Deep Market (High Liquidity):")
    print("  - $100M trading volume might move price by $10")
    print("  - Market cap change: $10 × 19.9M = $199M")
    print("  - Volume to Market Cap ratio: 1:2")
    print()
    print("Scenario B - Shallow Market (Low Liquidity):")
    print("  - $10M trading volume might move price by $100")
    print("  - Market cap change: $100 × 19.9M = $1.99B")
    print("  - Volume to Market Cap ratio: 1:199")
    print()
    print("This explains the variable ratio we observed!")

def analyze_liquidity_impact_model():
    """Analyze how liquidity affects price impact"""
    
    print(f"\n3. LIQUIDITY IMPACT MODEL:")
    print("-" * 30)
    print("Theoretical Models for Price Impact:")
    print()
    print("A. LINEAR MODEL (unrealistic):")
    print("   Price Impact = k × Volume")
    print("   Where k is constant")
    print("   Problem: Assumes infinite liquidity")
    print()
    print("B. SQUARE ROOT MODEL (more realistic):")
    print("   Price Impact = k × sqrt(Volume / Average Daily Volume)")
    print("   Used by institutional traders")
    print("   Better for large orders")
    print()
    print("C. LOGARITHMIC MODEL (for extreme cases):")
    print("   Price Impact = k × log(Volume / Market Depth)")
    print("   Accounts for depleting order book")
    print("   Best for understanding market dynamics")
    print()
    print("IMPLICATION FOR MARKET CAP:")
    print("Market Cap Change = sqrt(Trading Volume) × Supply × Liquidity Factor")
    print("This is why the relationship is non-linear and variable!")

def estimate_bitcoin_market_depth():
    """Estimate Bitcoin market depth from available data"""
    
    print(f"\n4. BITCOIN MARKET DEPTH ESTIMATION:")
    print("-" * 40)
    
    # Use our historical data to estimate market behavior
    db_path = os.path.join(project_root, "data", "crypto_analyser.db")
    
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            
            # Get recent data with both price and volume changes
            query = """
            SELECT 
                datetime(timestamp, '+2 hours') as israel_time,
                price,
                volume_24h,
                volume_velocity,
                market_cap,
                LAG(price) OVER (ORDER BY timestamp) as prev_price,
                LAG(market_cap) OVER (ORDER BY timestamp) as prev_market_cap,
                LAG(volume_24h) OVER (ORDER BY timestamp) as prev_volume_24h
            FROM bitcoin_prices 
            WHERE timestamp >= datetime('now', '-24 hours')
                AND market_cap IS NOT NULL 
                AND volume_24h IS NOT NULL
                AND price IS NOT NULL
            ORDER BY timestamp ASC
            """
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if len(df) > 1:
                # Calculate actual changes
                df['price_change'] = df['price'] - df['prev_price']
                df['price_change_pct'] = (df['price_change'] / df['prev_price']) * 100
                df['market_cap_change'] = df['market_cap'] - df['prev_market_cap']
                df['volume_change_24h'] = df['volume_24h'] - df['prev_volume_24h']
                
                # Remove NaN and extreme outliers
                analysis_df = df.dropna()
                analysis_df = analysis_df[abs(analysis_df['price_change_pct']) < 5]  # Remove >5% price changes
                
                if len(analysis_df) > 10:
                    print("EMPIRICAL MARKET DEPTH ANALYSIS:")
                    print("-" * 35)
                    print(f"Sample size: {len(analysis_df)} 5-minute intervals")
                    
                    # Calculate effective volume (proxy from volume velocity)
                    # Volume velocity represents net volume change per minute
                    # So 5-minute effective volume ≈ |volume_velocity| × 5
                    analysis_df['effective_volume_5min'] = abs(analysis_df['volume_velocity']) * 5
                    
                    # Calculate price impact per unit volume
                    # Price Impact per $1B volume
                    analysis_df['price_impact_per_billion'] = analysis_df['price_change'] / (analysis_df['effective_volume_5min'] / 1e9)
                    
                    # Remove infinite and extreme values
                    valid_impacts = analysis_df['price_impact_per_billion'].replace([np.inf, -np.inf], np.nan).dropna()
                    valid_impacts = valid_impacts[abs(valid_impacts) < 1000]  # Remove extreme outliers
                    
                    if len(valid_impacts) > 5:
                        print(f"Price impact per $1B trading volume:")
                        print(f"  Mean: ${valid_impacts.mean():.2f}")
                        print(f"  Median: ${valid_impacts.median():.2f}")
                        print(f"  Std Dev: ${valid_impacts.std():.2f}")
                        print(f"  Range: ${valid_impacts.min():.2f} to ${valid_impacts.max():.2f}")
                        
                        # Estimate market depth
                        median_impact = valid_impacts.median()
                        if median_impact != 0:
                            estimated_depth = 1e9 / abs(median_impact)  # Volume needed for $1 price change
                            print(f"\nESTIMATED MARKET DEPTH:")
                            print(f"  Volume for $1 price impact: ${estimated_depth:,.0f}")
                            print(f"  Volume for $10 price impact: ${estimated_depth * 10:,.0f}")
                            print(f"  Volume for $100 price impact: ${estimated_depth * 100:,.0f}")
                            
                            # This tells us about liquidity
                            if estimated_depth > 100e6:  # > $100M
                                print("  Assessment: HIGH liquidity market")
                            elif estimated_depth > 10e6:  # > $10M
                                print("  Assessment: MEDIUM liquidity market")
                            else:
                                print("  Assessment: LOW liquidity market")
                    
                    # Analyze the relationship shape
                    print(f"\nRELATIONSHIP SHAPE ANALYSIS:")
                    print("-" * 30)
                    
                    # Test different models
                    valid_data = analysis_df[(analysis_df['effective_volume_5min'] > 0) & 
                                           (abs(analysis_df['price_change']) > 0)].copy()
                    
                    if len(valid_data) > 5:
                        # Linear model: price_change = k * volume
                        linear_corr = valid_data['price_change'].corr(valid_data['effective_volume_5min'])
                        
                        # Square root model: price_change = k * sqrt(volume)
                        valid_data['sqrt_volume'] = np.sqrt(valid_data['effective_volume_5min'])
                        sqrt_corr = valid_data['price_change'].corr(valid_data['sqrt_volume'])
                        
                        # Log model: price_change = k * log(volume)
                        valid_data['log_volume'] = np.log(valid_data['effective_volume_5min'] + 1)
                        log_corr = valid_data['price_change'].corr(valid_data['log_volume'])
                        
                        print(f"Model correlations with price change:")
                        print(f"  Linear model (price proportional to volume): {linear_corr:.4f}")
                        print(f"  Square root model (price proportional to sqrt(volume)): {sqrt_corr:.4f}")
                        print(f"  Logarithmic model (price proportional to log(volume)): {log_corr:.4f}")
                        
                        # Find best model
                        models = [
                            ('Linear', abs(linear_corr)),
                            ('Square Root', abs(sqrt_corr)),
                            ('Logarithmic', abs(log_corr))
                        ]
                        
                        best_model = max(models, key=lambda x: x[1])
                        print(f"\n  BEST FIT: {best_model[0]} model (correlation: {best_model[1]:.4f})")
                        
                        return {
                            'estimated_depth': estimated_depth if 'estimated_depth' in locals() else None,
                            'best_model': best_model[0],
                            'correlations': {
                                'linear': linear_corr,
                                'sqrt': sqrt_corr,
                                'log': log_corr
                            }
                        }
        
        except Exception as e:
            print(f"Error in market depth analysis: {e}")
            import traceback
            traceback.print_exc()
    
    return None

def develop_volume_estimation_formula():
    """Develop formula to estimate trading volume from market cap changes"""
    
    print(f"\n5. TRADING VOLUME ESTIMATION FORMULA:")
    print("-" * 45)
    
    print("Based on pricing mechanism analysis:")
    print()
    print("THEORETICAL FRAMEWORK:")
    print("If Price Impact is proportional to Volume^alpha / Market Depth")
    print("Then: Trading Volume is proportional to (Price Impact × Market Depth)^(1/alpha)")
    print()
    print("Since Market Cap Change = Price Impact × Supply:")
    print("Trading Volume is proportional to (Market Cap Change / Supply × Market Depth)^(1/alpha)")
    print()
    print("PROPOSED ESTIMATION FORMULA:")
    print("Estimated Volume = K × (|Market Cap Change| / Supply)^(1/alpha) × Depth Factor")
    print()
    print("Where:")
    print("- K = Calibration constant (from historical data)")
    print("- alpha = Price impact exponent (0.5 for sqrt model, 1.0 for linear)")
    print("- Supply = Current circulating supply (19.9M BTC)")
    print("- Depth Factor = Market liquidity adjustment")
    print()
    print("PRACTICAL IMPLEMENTATION:")
    print("1. Use alpha = 0.5 (square root model is most realistic)")
    print("2. Calibrate K using periods where we have reliable volume data")
    print("3. Adjust Depth Factor based on market conditions (volatility, time of day)")
    print("4. Apply smoothing to reduce noise")

def validate_estimation_approach():
    """Validate the volume estimation approach against known data"""
    
    print(f"\n6. VALIDATION AGAINST KNOWN DATA:")
    print("-" * 40)
    
    db_path = os.path.join(project_root, "data", "crypto_analyser.db")
    
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            
            # Get data where we have both market cap and volume changes
            query = """
            SELECT 
                datetime(timestamp, '+2 hours') as israel_time,
                price,
                volume_24h,
                abs(volume_velocity) as abs_volume_velocity,
                market_cap,
                LAG(market_cap) OVER (ORDER BY timestamp) as prev_market_cap
            FROM bitcoin_prices 
            WHERE timestamp >= datetime('now', '-24 hours')
                AND market_cap IS NOT NULL 
                AND volume_24h IS NOT NULL
                AND volume_velocity IS NOT NULL
                AND abs(volume_velocity) < 1e12  -- Remove obvious artifacts
            ORDER BY timestamp ASC
            """
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if len(df) > 1:
                # Calculate market cap changes
                df['market_cap_change'] = df['market_cap'] - df['prev_market_cap']
                df['abs_market_cap_change'] = abs(df['market_cap_change'])
                
                # Remove NaN values
                validation_df = df.dropna()
                validation_df = validation_df[validation_df['abs_market_cap_change'] > 0]
                
                if len(validation_df) > 5:
                    print(f"Validation sample size: {len(validation_df)} intervals")
                    
                    # Test different estimation formulas
                    supply = 19.9e6  # Approximate BTC supply
                    
                    # Formula 1: Linear relationship
                    validation_df['estimated_vol_linear'] = validation_df['abs_market_cap_change'] / supply
                    
                    # Formula 2: Square root relationship  
                    validation_df['estimated_vol_sqrt'] = (validation_df['abs_market_cap_change'] / supply) ** 2
                    
                    # Formula 3: With depth adjustment (assume $50M depth for $1 price change)
                    estimated_depth = 50e6
                    validation_df['estimated_vol_depth'] = (validation_df['abs_market_cap_change'] / supply) * estimated_depth
                    
                    # Compare with actual volume velocity (our proxy for trading activity)
                    correlations = {}
                    
                    for formula in ['estimated_vol_linear', 'estimated_vol_sqrt', 'estimated_vol_depth']:
                        corr = validation_df['abs_volume_velocity'].corr(validation_df[formula])
                        correlations[formula] = corr
                        print(f"Correlation with actual volume velocity:")
                        print(f"  {formula.replace('_', ' ').title()}: {corr:.4f}")
                    
                    # Find best performing formula
                    best_formula = max(correlations, key=correlations.get)
                    best_corr = correlations[best_formula]
                    
                    print(f"\nBEST PERFORMING FORMULA: {best_formula.replace('_', ' ').title()}")
                    print(f"Correlation with actual data: {best_corr:.4f}")
                    
                    if best_corr > 0.3:
                        print("Assessment: PROMISING approach - market cap can estimate volume")
                        
                        # Calculate scaling factor for practical use
                        actual_volumes = validation_df['abs_volume_velocity']
                        estimated_volumes = validation_df[best_formula]
                        
                        # Remove extreme outliers for scaling calculation
                        ratio_data = actual_volumes / estimated_volumes
                        ratio_data = ratio_data.replace([np.inf, -np.inf], np.nan).dropna()
                        ratio_data = ratio_data[abs(ratio_data) < 100]  # Remove extreme ratios
                        
                        if len(ratio_data) > 0:
                            scaling_factor = ratio_data.median()
                            print(f"Recommended scaling factor: {scaling_factor:.4f}")
                            print(f"\nFINAL FORMULA:")
                            print(f"Estimated Trading Volume = {scaling_factor:.4f} × Market Cap Change Formula")
                            
                            return {
                                'best_formula': best_formula,
                                'correlation': best_corr,
                                'scaling_factor': scaling_factor,
                                'validation': True
                            }
                    
                    elif best_corr > 0.1:
                        print("Assessment: WEAK correlation - approach needs refinement")
                    else:
                        print("Assessment: POOR correlation - market cap cannot reliably estimate volume")
        
        except Exception as e:
            print(f"Error in validation: {e}")
            import traceback
            traceback.print_exc()
    
    return None

def provide_final_recommendations():
    """Provide final recommendations for volume estimation"""
    
    print(f"\n7. FINAL RECOMMENDATIONS:")
    print("-" * 30)
    
    print("BITCOIN PRICING MECHANISM INSIGHTS:")
    print("+ Price impact depends on order book depth, not total supply")
    print("+ Relationship between volume and price impact is non-linear (likely sqrt)")
    print("+ Market depth varies with time, volatility, and market conditions")
    print("+ Large dormant BTC movements cause disproportionate price impact")
    print()
    print("VOLUME ESTIMATION VIABILITY:")
    print("Market cap changes CAN provide trading volume estimates, but:")
    print("+ Requires calibration against known volume data")
    print("+ Needs adjustment for market liquidity conditions")
    print("+ Works better for detecting relative changes than absolute values")
    print("+ Should be combined with other indicators for accuracy")
    print()
    print("PROPOSED HYBRID APPROACH:")
    print("1. Use market cap velocity as primary metric (stable, artifact-free)")
    print("2. Convert to estimated trading volume using calibrated formula")
    print("3. Validate against actual volume data when available")
    print("4. Flag periods of unusual volume/market cap divergence")
    print("5. Adjust for market conditions (volatility, time of day)")

if __name__ == "__main__":
    analyze_price_formation_theory()
    analyze_liquidity_impact_model()
    
    # Run empirical analysis
    depth_analysis = estimate_bitcoin_market_depth()
    develop_volume_estimation_formula()
    validation_result = validate_estimation_approach()
    
    provide_final_recommendations()
    
    # Summary
    print(f"\nANALYSIS SUMMARY:")
    print("-" * 20)
    if depth_analysis and validation_result:
        print(f"Market depth estimated: ${depth_analysis.get('estimated_depth', 'N/A'):,.0f} for $1 price change")
        print(f"Best model: {depth_analysis.get('best_model', 'Unknown')}")
        print(f"Volume estimation correlation: {validation_result.get('correlation', 'N/A'):.4f}")
        
        if validation_result.get('validation', False):
            print("CONCLUSION: Market cap velocity CAN estimate trading volumes with proper calibration!")
        else:
            print("CONCLUSION: Market cap approach shows promise but needs refinement.")
    else:
        print("CONCLUSION: Analysis incomplete - need more data for validation.")