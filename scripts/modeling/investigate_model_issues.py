#!/usr/bin/env python3
"""
Investigate fundamental issues with the volatility-volume relationship model
"""

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize, curve_fit
from scipy.stats import pearsonr, spearmanr
from datetime import datetime, timedelta

def load_and_analyze_data():
    """Load data and perform basic analysis"""
    
    conn = sqlite3.connect('data/crypto_analyser.db')
    
    # Load all data with volume and volatility
    query = '''
    SELECT timestamp, price, volume_24h, volatility
    FROM bitcoin_prices 
    WHERE volume_24h IS NOT NULL AND volatility IS NOT NULL
    ORDER BY timestamp ASC
    '''
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['btc_volume'] = df['volume_24h'] / df['price']  # Convert USD volume to BTC volume
    
    print(f"Data range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"Records: {len(df)}")
    print(f"\nVolatility statistics:")
    print(f"  Range: {df['volatility'].min():.6f}% to {df['volatility'].max():.6f}%")
    print(f"  Mean: {df['volatility'].mean():.6f}%")
    print(f"  Std: {df['volatility'].std():.6f}%")
    
    print(f"\nBTC Volume statistics:")
    print(f"  Range: {df['btc_volume'].min():,.0f} to {df['btc_volume'].max():,.0f} BTC")
    print(f"  Mean: {df['btc_volume'].mean():,.0f} BTC")
    print(f"  Std: {df['btc_volume'].std():,.0f} BTC")
    
    return df

def test_correlations(df):
    """Test various correlation patterns"""
    
    print("\nCORRELATION ANALYSIS:")
    print("=" * 25)
    
    vol = df['volatility'].values
    btc_vol = df['btc_volume'].values
    
    # Basic correlation
    corr_linear, p_linear = pearsonr(btc_vol, vol)
    corr_rank, p_rank = spearmanr(btc_vol, vol)
    
    print(f"Linear correlation (Pearson): {corr_linear:.4f} (p={p_linear:.4f})")
    print(f"Rank correlation (Spearman): {corr_rank:.4f} (p={p_rank:.4f})")
    
    # Log-log correlation (power law test)
    log_vol = np.log(vol + 1e-8)  # Add small constant to avoid log(0)
    log_btc_vol = np.log(btc_vol)
    
    corr_log, p_log = pearsonr(log_btc_vol, log_vol)
    print(f"Log-log correlation: {corr_log:.4f} (p={p_log:.4f})")
    
    # Test different transformations
    sqrt_vol = np.sqrt(vol)
    corr_sqrt, p_sqrt = pearsonr(btc_vol, sqrt_vol)
    print(f"Volume vs sqrt(volatility): {corr_sqrt:.4f} (p={p_sqrt:.4f})")
    
    return corr_linear, corr_log, corr_sqrt

def test_time_lags(df):
    """Test if there are time lag effects"""
    
    print("\nTIME LAG ANALYSIS:")
    print("=" * 20)
    
    # Test different time shifts (0 to 24 hours)
    max_lag_hours = 24
    lag_correlations = []
    
    for lag_hours in range(0, max_lag_hours + 1):
        lag_minutes = lag_hours * 60 // 5  # Convert to 5-minute intervals
        
        if lag_minutes < len(df) - 1:
            # Shift volatility forward by lag_minutes
            vol_shifted = df['volatility'].iloc[lag_minutes:].values
            btc_vol_base = df['btc_volume'].iloc[:-lag_minutes if lag_minutes > 0 else None].values
            
            if len(vol_shifted) == len(btc_vol_base) and len(vol_shifted) > 10:
                corr, p_val = pearsonr(btc_vol_base, vol_shifted)
                lag_correlations.append((lag_hours, corr, p_val))
    
    # Find best lag
    best_lag = max(lag_correlations, key=lambda x: abs(x[1]))
    print(f"Best lag: {best_lag[0]} hours, correlation: {best_lag[1]:.4f} (p={best_lag[2]:.4f})")
    
    # Show top 5 lags
    sorted_lags = sorted(lag_correlations, key=lambda x: abs(x[1]), reverse=True)[:5]
    print("\nTop 5 time lags:")
    for lag, corr, p_val in sorted_lags:
        print(f"  {lag:2d}h: {corr:+.4f} (p={p_val:.4f})")
    
    return lag_correlations, best_lag

def test_alternative_models(df):
    """Test different functional forms"""
    
    print("\nALTERNATIVE MODEL TESTING:")
    print("=" * 30)
    
    vol = df['volatility'].values
    btc_vol = df['btc_volume'].values
    
    # Remove any invalid data
    valid_mask = (vol > 0) & (btc_vol > 0) & np.isfinite(vol) & np.isfinite(btc_vol)
    vol = vol[valid_mask]
    btc_vol = btc_vol[valid_mask]
    
    models = {}
    
    try:
        # 1. Power law: sigma = k * V^beta
        def power_law(V, k, beta):
            return k * (V ** beta)
        
        popt_power, _ = curve_fit(power_law, btc_vol, vol, 
                                bounds=([1e-10, -2], [1e-1, 2]), 
                                maxfev=5000)
        pred_power = power_law(btc_vol, *popt_power)
        r2_power = 1 - np.sum((vol - pred_power)**2) / np.sum((vol - np.mean(vol))**2)
        models['Power Law'] = (popt_power, r2_power, pred_power)
        print(f"Power Law: sigma = {popt_power[0]:.2e} * V^{popt_power[1]:.3f}, R²={r2_power:.4f}")
        
    except Exception as e:
        print(f"Power law fitting failed: {e}")
    
    try:
        # 2. Exponential: sigma = a * exp(b * V)
        def exponential(V, a, b):
            return a * np.exp(b * V)
        
        popt_exp, _ = curve_fit(exponential, btc_vol, vol, 
                              bounds=([1e-10, -1e-3], [1e-1, 1e-3]),
                              maxfev=5000)
        pred_exp = exponential(btc_vol, *popt_exp)
        r2_exp = 1 - np.sum((vol - pred_exp)**2) / np.sum((vol - np.mean(vol))**2)
        models['Exponential'] = (popt_exp, r2_exp, pred_exp)
        print(f"Exponential: sigma = {popt_exp[0]:.2e} * exp({popt_exp[1]:.2e} * V), R²={r2_exp:.4f}")
        
    except Exception as e:
        print(f"Exponential fitting failed: {e}")
    
    try:
        # 3. Logarithmic: sigma = a * log(V) + b
        def logarithmic(V, a, b):
            return a * np.log(V + 1) + b
        
        popt_log, _ = curve_fit(logarithmic, btc_vol, vol, maxfev=5000)
        pred_log = logarithmic(btc_vol, *popt_log)
        r2_log = 1 - np.sum((vol - pred_log)**2) / np.sum((vol - np.mean(vol))**2)
        models['Logarithmic'] = (popt_log, r2_log, pred_log)
        print(f"Logarithmic: sigma = {popt_log[0]:.2e} * log(V+1) + {popt_log[1]:.2e}, R²={r2_log:.4f}")
        
    except Exception as e:
        print(f"Logarithmic fitting failed: {e}")
    
    try:
        # 4. Linear: sigma = a * V + b
        def linear(V, a, b):
            return a * V + b
        
        popt_linear, _ = curve_fit(linear, btc_vol, vol, maxfev=5000)
        pred_linear = linear(btc_vol, *popt_linear)
        r2_linear = 1 - np.sum((vol - pred_linear)**2) / np.sum((vol - np.mean(vol))**2)
        models['Linear'] = (popt_linear, r2_linear, pred_linear)
        print(f"Linear: sigma = {popt_linear[0]:.2e} * V + {popt_linear[1]:.2e}, R²={r2_linear:.4f}")
        
    except Exception as e:
        print(f"Linear fitting failed: {e}")
    
    try:
        # 5. Square root: sigma = a * sqrt(V) + b
        def sqrt_model(V, a, b):
            return a * np.sqrt(V) + b
        
        popt_sqrt, _ = curve_fit(sqrt_model, btc_vol, vol, maxfev=5000)
        pred_sqrt = sqrt_model(btc_vol, *popt_sqrt)
        r2_sqrt = 1 - np.sum((vol - pred_sqrt)**2) / np.sum((vol - np.mean(vol))**2)
        models['Square Root'] = (popt_sqrt, r2_sqrt, pred_sqrt)
        print(f"Square Root: sigma = {popt_sqrt[0]:.2e} * sqrt(V) + {popt_sqrt[1]:.2e}, R²={r2_sqrt:.4f}")
        
    except Exception as e:
        print(f"Square root fitting failed: {e}")
    
    # Find best model
    if models:
        best_model = max(models.items(), key=lambda x: x[1][1])
        print(f"\nBest model: {best_model[0]} with R² = {best_model[1][1]:.4f}")
    
    return models

def create_diagnostic_plots(df, models=None, lag_correlations=None):
    """Create comprehensive diagnostic plots"""
    
    vol = df['volatility'].values
    btc_vol = df['btc_volume'].values
    timestamps = df['timestamp'].values
    
    # Remove invalid data
    valid_mask = (vol > 0) & (btc_vol > 0) & np.isfinite(vol) & np.isfinite(btc_vol)
    vol = vol[valid_mask]
    btc_vol = btc_vol[valid_mask]
    timestamps = timestamps[valid_mask]
    
    fig = plt.figure(figsize=(20, 15))
    
    # Plot 1: Raw scatter plot
    ax1 = plt.subplot(3, 3, 1)
    plt.scatter(btc_vol, vol, alpha=0.6, s=20)
    plt.xlabel('BTC Volume (24h)')
    plt.ylabel('Volatility (%)')
    plt.title('Raw Data: Volatility vs BTC Volume')
    plt.grid(True, alpha=0.3)
    
    # Plot 2: Log-log scatter
    ax2 = plt.subplot(3, 3, 2)
    plt.scatter(btc_vol, vol, alpha=0.6, s=20)
    plt.xscale('log')
    plt.yscale('log')
    plt.xlabel('BTC Volume (24h) [log]')
    plt.ylabel('Volatility (%) [log]')
    plt.title('Log-Log Scale')
    plt.grid(True, alpha=0.3)
    
    # Plot 3: Time series of both variables
    ax3 = plt.subplot(3, 3, 3)
    ax3_twin = ax3.twinx()
    ax3.plot(timestamps, vol, 'b-', alpha=0.7, label='Volatility')
    ax3_twin.plot(timestamps, btc_vol, 'r-', alpha=0.7, label='BTC Volume')
    ax3.set_xlabel('Time')
    ax3.set_ylabel('Volatility (%)', color='b')
    ax3_twin.set_ylabel('BTC Volume', color='r')
    ax3.set_title('Time Series')
    plt.xticks(rotation=45)
    
    # Plot 4: Lag correlation analysis
    if lag_correlations:
        ax4 = plt.subplot(3, 3, 4)
        lags, corrs, _ = zip(*lag_correlations)
        plt.plot(lags, corrs, 'o-')
        plt.xlabel('Lag (hours)')
        plt.ylabel('Correlation')
        plt.title('Time Lag Analysis')
        plt.grid(True, alpha=0.3)
    
    # Plot 5-9: Model fits
    if models:
        plot_idx = 5
        for model_name, (params, r2, predictions) in models.items():
            if plot_idx <= 9:
                ax = plt.subplot(3, 3, plot_idx)
                plt.scatter(btc_vol, vol, alpha=0.4, s=15, label='Data')
                
                # Sort for smooth line
                sort_idx = np.argsort(btc_vol)
                plt.plot(btc_vol[sort_idx], predictions[sort_idx], 'r-', linewidth=2, 
                        label=f'{model_name}\nR² = {r2:.4f}')
                
                plt.xlabel('BTC Volume')
                plt.ylabel('Volatility (%)')
                plt.title(f'{model_name} Fit')
                plt.legend()
                plt.grid(True, alpha=0.3)
                plot_idx += 1
    
    plt.tight_layout()
    
    # Save plots
    plot_file = "scripts/model_investigation_plots.png"
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    print(f"\nDiagnostic plots saved to: {plot_file}")
    
    return plot_file

def main():
    """Main investigation function"""
    
    print("INVESTIGATING VOLATILITY-VOLUME MODEL ISSUES")
    print("=" * 50)
    
    # Load and analyze data
    df = load_and_analyze_data()
    
    # Test correlations
    corr_linear, corr_log, corr_sqrt = test_correlations(df)
    
    # Test time lags
    lag_correlations, best_lag = test_time_lags(df)
    
    # Test alternative models
    models = test_alternative_models(df)
    
    # Create diagnostic plots
    plot_file = create_diagnostic_plots(df, models, lag_correlations)
    
    print("\nSUMMARY AND RECOMMENDATIONS:")
    print("=" * 35)
    
    if abs(corr_linear) < 0.1:
        print("- Very weak linear correlation suggests non-linear relationship or no relationship")
    
    if abs(corr_log) > abs(corr_linear):
        print("- Log-log correlation stronger than linear suggests power law might be appropriate")
    else:
        print("- Log-log correlation weaker than linear suggests power law may not be appropriate")
    
    if best_lag[0] > 0:
        print(f"- Best correlation at {best_lag[0]}h lag suggests time delay effects")
    
    if models:
        best_model = max(models.items(), key=lambda x: x[1][1])
        if best_model[1][1] > 0.1:
            print(f"- {best_model[0]} model shows best fit (R² = {best_model[1][1]:.4f})")
        else:
            print("- All models show poor fit (R² < 0.1) - relationship may be very weak or non-existent")
    
    print(f"\nNext steps:")
    print("1. Review diagnostic plots in {plot_file}")
    print("2. Consider if the relationship exists at all")
    print("3. Try different data preprocessing (smoothing, filtering)")
    print("4. Consider market regime analysis (bull/bear markets)")
    print("5. Investigate other volatility measures")

if __name__ == "__main__":
    main()