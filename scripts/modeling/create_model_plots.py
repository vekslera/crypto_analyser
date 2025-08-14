#!/usr/bin/env python3
"""
Create separate, detailed plots for piecewise linear and square root models
"""

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import linregress

def load_lagged_data(lag_hours=1):
    """Load data with 1-hour time lag"""
    
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
    lag_periods = lag_hours * 12  # 12 periods per hour (5-minute intervals)
    df_lagged = df.copy()
    df_lagged['volatility_future'] = df['volatility'].shift(-lag_periods)
    df_lagged = df_lagged.dropna(subset=['volatility_future'])
    
    return df_lagged['btc_volume'].values, df_lagged['volatility_future'].values

def fit_piecewise_linear(btc_volumes, volatilities):
    """Fit piecewise linear model"""
    
    # Split at median volume
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
        'low_p': p_low,
        'high_slope': slope_high,
        'high_intercept': intercept_high,
        'high_r': r_high,
        'high_p': p_high,
        'overall_r2': r2_overall
    }
    
    return params, pred_piecewise, low_mask, high_mask

def fit_square_root(btc_volumes, volatilities):
    """Fit square root model"""
    
    def sqrt_model(V, a, b):
        return a * np.sqrt(V) + b
    
    popt, pcov = curve_fit(sqrt_model, btc_volumes, volatilities, maxfev=5000)
    predictions = sqrt_model(btc_volumes, *popt)
    
    # Calculate R² and parameter uncertainties
    r2 = 1 - np.sum((volatilities - predictions)**2) / np.sum((volatilities - np.mean(volatilities))**2)
    param_errors = np.sqrt(np.diag(pcov))
    
    params = {
        'a': popt[0],
        'b': popt[1],
        'a_error': param_errors[0],
        'b_error': param_errors[1],
        'r2': r2
    }
    
    return params, predictions

def create_piecewise_linear_plot(btc_volumes, volatilities, params, predictions, low_mask, high_mask):
    """Create detailed plot for piecewise linear model"""
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # Plot 1: Overall fit with breakpoint
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
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Residuals
    residuals = volatilities - predictions
    ax2.scatter(btc_volumes, residuals, alpha=0.6, s=15, color='purple')
    ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5)
    ax2.axhline(y=np.std(residuals), color='red', linestyle='--', alpha=0.7, label=f'±1σ = ±{np.std(residuals):.4f}')
    ax2.axhline(y=-np.std(residuals), color='red', linestyle='--', alpha=0.7)
    ax2.set_xlabel('BTC Volume (24h)')
    ax2.set_ylabel('Residuals (Observed - Predicted)')
    ax2.set_title('Residual Analysis')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Low volume regime detail
    ax3.scatter(btc_volumes[low_mask], volatilities[low_mask], alpha=0.7, s=25, color='blue')
    ax3.plot(vol_low_range, line_low, 'b-', linewidth=2)
    ax3.set_xlabel('BTC Volume (24h)')
    ax3.set_ylabel('Volatility (%)')
    ax3.set_title(f'Low Volume Regime (r = {params["low_r"]:.3f}, p = {params["low_p"]:.3e})')
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: High volume regime detail
    ax4.scatter(btc_volumes[high_mask], volatilities[high_mask], alpha=0.7, s=25, color='red')
    ax4.plot(vol_high_range, line_high, 'r-', linewidth=2)
    ax4.set_xlabel('BTC Volume (24h)')
    ax4.set_ylabel('Volatility (%)')
    ax4.set_title(f'High Volume Regime (r = {params["high_r"]:.3f}, p = {params["high_p"]:.3e})')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('scripts/piecewise_linear_model.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Piecewise linear plot saved to: scripts/piecewise_linear_model.png")

def create_square_root_plot(btc_volumes, volatilities, params, predictions):
    """Create detailed plot for square root model"""
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # Plot 1: Main fit
    ax1.scatter(btc_volumes, volatilities, alpha=0.6, s=20, color='green', label='Data')
    
    # Create smooth curve
    vol_range = np.linspace(btc_volumes.min(), btc_volumes.max(), 200)
    curve_smooth = params['a'] * np.sqrt(vol_range) + params['b']
    ax1.plot(vol_range, curve_smooth, 'orange', linewidth=3, 
            label=f'σ = {params["a"]:.2e}×√V + {params["b"]:.3f}')
    
    ax1.set_xlabel('BTC Volume (24h)')
    ax1.set_ylabel('Volatility (%)')
    ax1.set_title(f'Square Root Model (R² = {params["r2"]:.4f})')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Observed vs Predicted
    ax2.scatter(volatilities, predictions, alpha=0.6, s=20, color='green')
    min_val = min(volatilities.min(), predictions.min())
    max_val = max(volatilities.max(), predictions.max())
    ax2.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='Perfect Fit')
    
    # Add correlation info
    correlation = np.corrcoef(volatilities, predictions)[0, 1]
    ax2.set_xlabel('Observed Volatility (%)')
    ax2.set_ylabel('Predicted Volatility (%)')
    ax2.set_title(f'Observed vs Predicted (r = {correlation:.4f})')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Residuals vs Volume
    residuals = volatilities - predictions
    ax3.scatter(btc_volumes, residuals, alpha=0.6, s=15, color='purple')
    ax3.axhline(y=0, color='black', linestyle='-', alpha=0.5)
    ax3.axhline(y=np.std(residuals), color='red', linestyle='--', alpha=0.7, label=f'±1σ = ±{np.std(residuals):.4f}')
    ax3.axhline(y=-np.std(residuals), color='red', linestyle='--', alpha=0.7)
    ax3.set_xlabel('BTC Volume (24h)')
    ax3.set_ylabel('Residuals (Observed - Predicted)')
    ax3.set_title('Residuals vs Volume')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Square root transformation view
    sqrt_volumes = np.sqrt(btc_volumes)
    ax4.scatter(sqrt_volumes, volatilities, alpha=0.6, s=20, color='green', label='Data')
    
    # Linear fit in sqrt space
    sqrt_range = np.linspace(sqrt_volumes.min(), sqrt_volumes.max(), 100)
    linear_fit = params['a'] * sqrt_range + params['b']
    ax4.plot(sqrt_range, linear_fit, 'orange', linewidth=3, 
            label=f'Linear in √V space')
    
    ax4.set_xlabel('√(BTC Volume)')
    ax4.set_ylabel('Volatility (%)')
    ax4.set_title('Square Root Transformation View')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('scripts/square_root_model.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Square root plot saved to: scripts/square_root_model.png")

def create_model_comparison_plot(btc_volumes, volatilities, pw_params, pw_predictions, sqrt_params, sqrt_predictions):
    """Create side-by-side comparison of both models"""
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Piecewise linear
    low_mask = btc_volumes <= pw_params['median_volume']
    high_mask = btc_volumes > pw_params['median_volume']
    
    ax1.scatter(btc_volumes[low_mask], volatilities[low_mask], alpha=0.6, s=15, color='blue', label='Low Volume')
    ax1.scatter(btc_volumes[high_mask], volatilities[high_mask], alpha=0.6, s=15, color='red', label='High Volume')
    
    # Sort for smooth lines
    sort_idx = np.argsort(btc_volumes)
    ax1.plot(btc_volumes[sort_idx], pw_predictions[sort_idx], 'black', linewidth=3, 
            label=f'Piecewise Linear (R² = {pw_params["overall_r2"]:.4f})')
    ax1.axvline(pw_params['median_volume'], color='gray', linestyle='--', alpha=0.7)
    
    ax1.set_xlabel('BTC Volume (24h)')
    ax1.set_ylabel('Volatility (%)')
    ax1.set_title('Piecewise Linear Model')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Square root
    ax2.scatter(btc_volumes, volatilities, alpha=0.6, s=15, color='green', label='Data')
    vol_range = np.linspace(btc_volumes.min(), btc_volumes.max(), 200)
    sqrt_curve = sqrt_params['a'] * np.sqrt(vol_range) + sqrt_params['b']
    ax2.plot(vol_range, sqrt_curve, 'orange', linewidth=3, 
            label=f'Square Root (R² = {sqrt_params["r2"]:.4f})')
    
    ax2.set_xlabel('BTC Volume (24h)')
    ax2.set_ylabel('Volatility (%)')
    ax2.set_title('Square Root Model')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('scripts/model_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Model comparison plot saved to: scripts/model_comparison.png")

def save_model_results(pw_params, sqrt_params):
    """Save detailed results for both models"""
    
    with open('scripts/detailed_model_results.txt', 'w') as f:
        f.write("DETAILED VOLATILITY-VOLUME MODEL RESULTS\n")
        f.write("=" * 45 + "\n\n")
        f.write("Time lag applied: 1 hour (volume at t predicts volatility at t+1h)\n\n")
        
        f.write("PIECEWISE LINEAR MODEL RESULTS:\n")
        f.write("-" * 35 + "\n")
        f.write(f"Overall R^2 = {pw_params['overall_r2']:.6f}\n")
        f.write(f"Breakpoint volume = {pw_params['median_volume']:.0f} BTC\n\n")
        
        f.write("Low Volume Regime (V <= {:.0f} BTC):\n".format(pw_params['median_volume']))
        f.write(f"  sigma = {pw_params['low_slope']:.6e} * V + {pw_params['low_intercept']:.6f}\n")
        f.write(f"  Correlation: r = {pw_params['low_r']:.4f} (p = {pw_params['low_p']:.2e})\n\n")
        
        f.write("High Volume Regime (V > {:.0f} BTC):\n".format(pw_params['median_volume']))
        f.write(f"  sigma = {pw_params['high_slope']:.6e} * V + {pw_params['high_intercept']:.6f}\n")
        f.write(f"  Correlation: r = {pw_params['high_r']:.4f} (p = {pw_params['high_p']:.2e})\n\n")
        
        f.write("SQUARE ROOT MODEL RESULTS:\n")
        f.write("-" * 30 + "\n")
        f.write(f"sigma = {sqrt_params['a']:.6e} * sqrt(V) + {sqrt_params['b']:.6f}\n")
        f.write(f"R^2 = {sqrt_params['r2']:.6f}\n")
        f.write(f"Parameter uncertainties:\n")
        f.write(f"  a = {sqrt_params['a']:.2e} +/- {sqrt_params['a_error']:.2e}\n")
        f.write(f"  b = {sqrt_params['b']:.4f} +/- {sqrt_params['b_error']:.4f}\n\n")
        
        f.write("MODEL COMPARISON:\n")
        f.write("-" * 17 + "\n")
        if pw_params['overall_r2'] > sqrt_params['r2']:
            f.write("Piecewise Linear model shows better fit\n")
            f.write("Suggests different volatility regimes at different volume levels\n")
        else:
            f.write("Square Root model shows better fit\n")
            f.write("Suggests smooth non-linear relationship\n")
    
    print("Detailed results saved to: scripts/detailed_model_results.txt")

def main():
    """Create all plots for both models"""
    
    print("CREATING DETAILED MODEL PLOTS")
    print("=" * 35)
    
    # Load data with 1-hour lag
    btc_volumes, volatilities = load_lagged_data(lag_hours=1)
    print(f"Data loaded: {len(btc_volumes)} points with 1h lag")
    
    # Fit piecewise linear model
    print("\nFitting piecewise linear model...")
    pw_params, pw_predictions, low_mask, high_mask = fit_piecewise_linear(btc_volumes, volatilities)
    
    # Fit square root model
    print("Fitting square root model...")
    sqrt_params, sqrt_predictions = fit_square_root(btc_volumes, volatilities)
    
    # Create plots
    print("\nCreating plots...")
    create_piecewise_linear_plot(btc_volumes, volatilities, pw_params, pw_predictions, low_mask, high_mask)
    create_square_root_plot(btc_volumes, volatilities, sqrt_params, sqrt_predictions)
    create_model_comparison_plot(btc_volumes, volatilities, pw_params, pw_predictions, sqrt_params, sqrt_predictions)
    
    # Save detailed results
    save_model_results(pw_params, sqrt_params)
    
    print("\nSUMMARY:")
    print(f"Piecewise Linear R² = {pw_params['overall_r2']:.4f}")
    print(f"Square Root R² = {sqrt_params['r2']:.4f}")
    print(f"Best model: {'Piecewise Linear' if pw_params['overall_r2'] > sqrt_params['r2'] else 'Square Root'}")

if __name__ == "__main__":
    main()