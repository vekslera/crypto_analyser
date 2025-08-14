#!/usr/bin/env python3
"""
Add the missing "Observed vs Predicted" plot for piecewise linear model
"""

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress

def load_data():
    """Load data with 1-hour lag"""
    conn = sqlite3.connect('data/crypto_analyser.db')
    
    query = '''
    SELECT timestamp, price, volume_24h, volatility
    FROM bitcoin_prices 
    WHERE volume_24h IS NOT NULL AND volatility IS NOT NULL
    ORDER BY timestamp ASC
    '''
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['btc_volume'] = df['volume_24h'] / df['price']
    
    # Apply 1-hour lag
    lag_periods = 12  # 1 hour = 12 periods (5-minute intervals)
    df_lagged = df.copy()
    df_lagged['volatility_future'] = df['volatility'].shift(-lag_periods)
    df_lagged = df_lagged.dropna(subset=['volatility_future'])
    
    return df_lagged['btc_volume'].values, df_lagged['volatility_future'].values

def fit_piecewise_linear(btc_volumes, volatilities):
    """Fit piecewise linear model"""
    median_vol = np.median(btc_volumes)
    low_mask = btc_volumes <= median_vol
    high_mask = btc_volumes > median_vol
    
    # Fit separate linear models
    slope_low, intercept_low, r_low, p_low, se_low = linregress(btc_volumes[low_mask], volatilities[low_mask])
    slope_high, intercept_high, r_high, p_high, se_high = linregress(btc_volumes[high_mask], volatilities[high_mask])
    
    # Create predictions
    pred_piecewise = np.zeros_like(volatilities)
    pred_piecewise[low_mask] = slope_low * btc_volumes[low_mask] + intercept_low
    pred_piecewise[high_mask] = slope_high * btc_volumes[high_mask] + intercept_high
    
    # Calculate overall R²
    r2_overall = 1 - np.sum((volatilities - pred_piecewise)**2) / np.sum((volatilities - np.mean(volatilities))**2)
    
    params = {
        'median_volume': median_vol,
        'low_slope': slope_low,
        'low_intercept': intercept_low,
        'low_r': r_low,
        'high_slope': slope_high,
        'high_intercept': intercept_high,
        'high_r': r_high,
        'overall_r2': r2_overall
    }
    
    return params, pred_piecewise, low_mask, high_mask

def create_comprehensive_piecewise_plot(btc_volumes, volatilities, params, predictions, low_mask, high_mask):
    """Create comprehensive 5-panel plot including observed vs predicted"""
    
    fig = plt.figure(figsize=(20, 12))
    
    # Plot 1: Overall fit with breakpoint
    ax1 = plt.subplot(2, 3, 1)
    ax1.scatter(btc_volumes[low_mask], volatilities[low_mask], alpha=0.6, s=20, color='blue', label='Low Volume Data')
    ax1.scatter(btc_volumes[high_mask], volatilities[high_mask], alpha=0.6, s=20, color='red', label='High Volume Data')
    
    # Plot fitted lines
    vol_low_range = np.linspace(btc_volumes[low_mask].min(), params['median_volume'], 100)
    vol_high_range = np.linspace(params['median_volume'], btc_volumes[high_mask].max(), 100)
    
    line_low = params['low_slope'] * vol_low_range + params['low_intercept']
    line_high = params['high_slope'] * vol_high_range + params['high_intercept']
    
    ax1.plot(vol_low_range, line_low, 'b-', linewidth=3, label=f'Low: σ = {params["low_slope"]:.2e}×V + {params["low_intercept"]:.3f}')
    ax1.plot(vol_high_range, line_high, 'r-', linewidth=3, label=f'High: σ = {params["high_slope"]:.2e}×V + {params["high_intercept"]:.3f}')
    
    # Mark breakpoint
    breakpoint_y = params['low_slope'] * params['median_volume'] + params['low_intercept']
    ax1.axvline(params['median_volume'], color='black', linestyle='--', alpha=0.7, label=f'Breakpoint: {params["median_volume"]:.0f} BTC')
    ax1.plot(params['median_volume'], breakpoint_y, 'ko', markersize=8, label='Transition Point')
    
    ax1.set_xlabel('BTC Volume (24h)')
    ax1.set_ylabel('Volatility (%)')
    ax1.set_title(f'Piecewise Linear Model (R² = {params["overall_r2"]:.4f})')
    ax1.legend(fontsize=8)
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: OBSERVED vs PREDICTED - The missing plot!
    ax2 = plt.subplot(2, 3, 2)
    ax2.scatter(volatilities[low_mask], predictions[low_mask], alpha=0.7, s=25, color='blue', label='Low Volume')
    ax2.scatter(volatilities[high_mask], predictions[high_mask], alpha=0.7, s=25, color='red', label='High Volume')
    
    # Perfect fit line
    min_val = min(volatilities.min(), predictions.min())
    max_val = max(volatilities.max(), predictions.max())
    ax2.plot([min_val, max_val], [min_val, max_val], 'k--', linewidth=2, label='Perfect Fit')
    
    # Calculate correlation
    correlation = np.corrcoef(volatilities, predictions)[0, 1]
    ax2.set_xlabel('Observed Volatility (%)')
    ax2.set_ylabel('Predicted Volatility (%)')
    ax2.set_title(f'Observed vs Predicted (r = {correlation:.4f})')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Residuals
    ax3 = plt.subplot(2, 3, 3)
    residuals = volatilities - predictions
    ax3.scatter(btc_volumes, residuals, alpha=0.6, s=15, color='purple')
    ax3.axhline(y=0, color='black', linestyle='-', alpha=0.5)
    ax3.axhline(y=np.std(residuals), color='red', linestyle='--', alpha=0.7, label=f'±1σ = ±{np.std(residuals):.4f}')
    ax3.axhline(y=-np.std(residuals), color='red', linestyle='--', alpha=0.7)
    ax3.set_xlabel('BTC Volume (24h)')
    ax3.set_ylabel('Residuals (Observed - Predicted)')
    ax3.set_title('Residual Analysis')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Low volume regime detail
    ax4 = plt.subplot(2, 3, 4)
    ax4.scatter(btc_volumes[low_mask], volatilities[low_mask], alpha=0.7, s=25, color='blue')
    ax4.plot(vol_low_range, line_low, 'b-', linewidth=2)
    ax4.set_xlabel('BTC Volume (24h)')
    ax4.set_ylabel('Volatility (%)')
    ax4.set_title(f'Low Volume Regime (r = {params["low_r"]:.3f})')
    ax4.grid(True, alpha=0.3)
    
    # Plot 5: High volume regime detail
    ax5 = plt.subplot(2, 3, 5)
    ax5.scatter(btc_volumes[high_mask], volatilities[high_mask], alpha=0.7, s=25, color='red')
    ax5.plot(vol_high_range, line_high, 'r-', linewidth=2)
    ax5.set_xlabel('BTC Volume (24h)')
    ax5.set_ylabel('Volatility (%)')
    ax5.set_title(f'High Volume Regime (r = {params["high_r"]:.3f})')
    ax5.grid(True, alpha=0.3)
    
    # Plot 6: Regime comparison in observed vs predicted space
    ax6 = plt.subplot(2, 3, 6)
    ax6.scatter(volatilities[low_mask], predictions[low_mask], alpha=0.7, s=25, color='blue', label=f'Low Vol (r={np.corrcoef(volatilities[low_mask], predictions[low_mask])[0,1]:.3f})')
    ax6.scatter(volatilities[high_mask], predictions[high_mask], alpha=0.7, s=25, color='red', label=f'High Vol (r={np.corrcoef(volatilities[high_mask], predictions[high_mask])[0,1]:.3f})')
    ax6.plot([min_val, max_val], [min_val, max_val], 'k--', linewidth=2, alpha=0.5)
    ax6.set_xlabel('Observed Volatility (%)')
    ax6.set_ylabel('Predicted Volatility (%)')
    ax6.set_title('Regime-Specific Prediction Quality')
    ax6.legend()
    ax6.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('scripts/complete_piecewise_linear_model.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Complete piecewise linear plot saved to: scripts/complete_piecewise_linear_model.png")
    
    # Print detailed statistics
    print(f"\nDETAILED PREDICTION STATISTICS:")
    print(f"Overall correlation: {correlation:.4f}")
    print(f"Low volume correlation: {np.corrcoef(volatilities[low_mask], predictions[low_mask])[0,1]:.4f}")
    print(f"High volume correlation: {np.corrcoef(volatilities[high_mask], predictions[high_mask])[0,1]:.4f}")
    print(f"RMSE: {np.sqrt(np.mean((volatilities - predictions)**2)):.6f}")

def main():
    """Create the complete piecewise linear plot with observed vs predicted"""
    
    print("CREATING COMPLETE PIECEWISE LINEAR MODEL PLOT")
    print("=" * 50)
    
    # Load data
    btc_volumes, volatilities = load_data()
    print(f"Data loaded: {len(btc_volumes)} points with 1h lag")
    
    # Fit model
    params, predictions, low_mask, high_mask = fit_piecewise_linear(btc_volumes, volatilities)
    
    # Create comprehensive plot
    create_comprehensive_piecewise_plot(btc_volumes, volatilities, params, predictions, low_mask, high_mask)

if __name__ == "__main__":
    main()