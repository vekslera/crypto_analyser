#!/usr/bin/env python3
"""
Improved calibration incorporating insights from model investigation
- Wider parameter bounds
- Time lag consideration
- Alternative functional forms
- Better data preprocessing
"""

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize, curve_fit
from datetime import datetime, timedelta

def load_lagged_data(lag_hours=1):
    """Load data with time lag between volume and volatility"""
    
    conn = sqlite3.connect('data/crypto_analyser.db')
    
    # Load all data
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
    
    # Apply time lag: volume at time t predicts volatility at time t+lag
    lag_periods = lag_hours * 12  # 12 periods per hour (5-minute intervals)
    
    if lag_periods > 0:
        # Shift volatility forward by lag_periods
        df_lagged = df.copy()
        df_lagged['volatility_future'] = df['volatility'].shift(-lag_periods)
        
        # Remove rows where future volatility is NaN
        df_lagged = df_lagged.dropna(subset=['volatility_future'])
        
        print(f"Applied {lag_hours}h lag: volume at time t predicts volatility at time t+{lag_hours}h")
        print(f"Usable records after lag: {len(df_lagged)}")
        
        return df_lagged['btc_volume'].values, df_lagged['volatility_future'].values
    else:
        return df['btc_volume'].values, df['volatility'].values

def improved_power_law_calibration(btc_volumes, volatilities):
    """Calibrate power law with wider bounds and better optimization"""
    
    print("IMPROVED POWER LAW CALIBRATION")
    print("=" * 35)
    
    # Clean data
    valid_mask = (btc_volumes > 0) & (volatilities > 0) & np.isfinite(btc_volumes) & np.isfinite(volatilities)
    btc_volumes = btc_volumes[valid_mask]
    volatilities = volatilities[valid_mask]
    
    print(f"Valid data points: {len(btc_volumes)}")
    
    def power_law(V, k, beta):
        return k * (V ** beta)
    
    # Try multiple optimization strategies
    best_r2 = -np.inf
    best_params = None
    best_predictions = None
    
    # Strategy 1: Wide bounds
    try:
        print("\nStrategy 1: Wide parameter bounds")
        popt1, _ = curve_fit(power_law, btc_volumes, volatilities, 
                           bounds=([1e-12, -1.0], [1e-1, 3.0]), 
                           maxfev=10000)
        pred1 = power_law(btc_volumes, *popt1)
        r2_1 = 1 - np.sum((volatilities - pred1)**2) / np.sum((volatilities - np.mean(volatilities))**2)
        print(f"Result: k={popt1[0]:.2e}, beta={popt1[1]:.4f}, R²={r2_1:.4f}")
        
        if r2_1 > best_r2:
            best_r2 = r2_1
            best_params = popt1
            best_predictions = pred1
    except Exception as e:
        print(f"Strategy 1 failed: {e}")
    
    # Strategy 2: Log-space fitting (more stable for power laws)
    try:
        print("\nStrategy 2: Log-space fitting")
        log_V = np.log(btc_volumes)
        log_vol = np.log(volatilities + 1e-8)  # Add small constant to avoid log(0)
        
        # Fit log(sigma) = log(k) + beta * log(V)
        poly_coeffs = np.polyfit(log_V, log_vol, 1)
        beta_2 = poly_coeffs[0]
        k_2 = np.exp(poly_coeffs[1])
        
        pred2 = power_law(btc_volumes, k_2, beta_2)
        r2_2 = 1 - np.sum((volatilities - pred2)**2) / np.sum((volatilities - np.mean(volatilities))**2)
        print(f"Result: k={k_2:.2e}, beta={beta_2:.4f}, R²={r2_2:.4f}")
        
        if r2_2 > best_r2:
            best_r2 = r2_2
            best_params = (k_2, beta_2)
            best_predictions = pred2
    except Exception as e:
        print(f"Strategy 2 failed: {e}")
    
    # Strategy 3: Multiple initial guesses
    try:
        print("\nStrategy 3: Multiple initial guesses")
        initial_guesses = [
            (1e-6, 0.5),
            (1e-4, 0.2),
            (1e-8, 1.0),
            (1e-3, 0.1),
            (1e-10, 2.0)
        ]
        
        for i, (k0, beta0) in enumerate(initial_guesses):
            try:
                popt3, _ = curve_fit(power_law, btc_volumes, volatilities,
                                   p0=[k0, beta0],
                                   bounds=([1e-12, -1.0], [1e-1, 3.0]),
                                   maxfev=10000)
                pred3 = power_law(btc_volumes, *popt3)
                r2_3 = 1 - np.sum((volatilities - pred3)**2) / np.sum((volatilities - np.mean(volatilities))**2)
                
                print(f"  Guess {i+1}: k={popt3[0]:.2e}, beta={popt3[1]:.4f}, R²={r2_3:.4f}")
                
                if r2_3 > best_r2:
                    best_r2 = r2_3
                    best_params = popt3
                    best_predictions = pred3
            except:
                continue
    except Exception as e:
        print(f"Strategy 3 failed: {e}")
    
    if best_params is not None:
        print(f"\nBEST POWER LAW FIT:")
        print(f"k = {best_params[0]:.6e}")
        print(f"beta = {best_params[1]:.6f}")
        print(f"R² = {best_r2:.6f}")
        
        return best_params, best_r2, best_predictions
    else:
        print("All power law fitting strategies failed!")
        return None, None, None

def test_alternative_approaches(btc_volumes, volatilities):
    """Test completely different approaches"""
    
    print("\nALTERNATIVE APPROACHES")
    print("=" * 25)
    
    results = {}
    
    # 1. Square root relationship (from investigation)
    try:
        def sqrt_model(V, a, b):
            return a * np.sqrt(V) + b
        
        popt_sqrt, _ = curve_fit(sqrt_model, btc_volumes, volatilities, maxfev=5000)
        pred_sqrt = sqrt_model(btc_volumes, *popt_sqrt)
        r2_sqrt = 1 - np.sum((volatilities - pred_sqrt)**2) / np.sum((volatilities - np.mean(volatilities))**2)
        results['Square Root'] = (popt_sqrt, r2_sqrt, pred_sqrt)
        print(f"Square Root: sigma = {popt_sqrt[0]:.2e} * sqrt(V) + {popt_sqrt[1]:.2e}, R²={r2_sqrt:.4f}")
    except Exception as e:
        print(f"Square root failed: {e}")
    
    # 2. Piecewise linear (different regimes)
    try:
        # Split at median volume
        median_vol = np.median(btc_volumes)
        low_mask = btc_volumes <= median_vol
        high_mask = btc_volumes > median_vol
        
        if np.sum(low_mask) > 10 and np.sum(high_mask) > 10:
            # Fit separate linear models
            from scipy.stats import linregress
            
            slope_low, intercept_low, r_low, _, _ = linregress(btc_volumes[low_mask], volatilities[low_mask])
            slope_high, intercept_high, r_high, _, _ = linregress(btc_volumes[high_mask], volatilities[high_mask])
            
            # Create predictions
            pred_piecewise = np.zeros_like(volatilities)
            pred_piecewise[low_mask] = slope_low * btc_volumes[low_mask] + intercept_low
            pred_piecewise[high_mask] = slope_high * btc_volumes[high_mask] + intercept_high
            
            r2_piecewise = 1 - np.sum((volatilities - pred_piecewise)**2) / np.sum((volatilities - np.mean(volatilities))**2)
            results['Piecewise Linear'] = ((slope_low, intercept_low, slope_high, intercept_high), r2_piecewise, pred_piecewise)
            print(f"Piecewise Linear: R²={r2_piecewise:.4f}")
            print(f"  Low volume: {slope_low:.2e}*V + {intercept_low:.2e}")
            print(f"  High volume: {slope_high:.2e}*V + {intercept_high:.2e}")
    except Exception as e:
        print(f"Piecewise linear failed: {e}")
    
    return results

def create_comprehensive_plots(btc_volumes, volatilities, power_params, alternative_results):
    """Create plots showing all model fits"""
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten()
    
    # Plot 1: Raw data
    axes[0].scatter(btc_volumes, volatilities, alpha=0.6, s=15)
    axes[0].set_xlabel('BTC Volume')
    axes[0].set_ylabel('Volatility (%)')
    axes[0].set_title('Raw Data')
    axes[0].grid(True, alpha=0.3)
    
    # Plot 2: Power law fit
    if power_params is not None:
        axes[1].scatter(btc_volumes, volatilities, alpha=0.4, s=15, label='Data')
        
        # Create smooth curve
        vol_range = np.linspace(btc_volumes.min(), btc_volumes.max(), 100)
        power_curve = power_params[0] * (vol_range ** power_params[1])
        axes[1].plot(vol_range, power_curve, 'r-', linewidth=2, 
                    label=f'sigma = {power_params[0]:.2e} * V^{power_params[1]:.3f}')
        
        axes[1].set_xlabel('BTC Volume')
        axes[1].set_ylabel('Volatility (%)')
        axes[1].set_title('Improved Power Law Fit')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
    
    # Plot 3: Log-log view
    axes[2].scatter(btc_volumes, volatilities, alpha=0.6, s=15)
    if power_params is not None:
        vol_range = np.linspace(btc_volumes.min(), btc_volumes.max(), 100)
        power_curve = power_params[0] * (vol_range ** power_params[1])
        axes[2].plot(vol_range, power_curve, 'r-', linewidth=2)
    axes[2].set_xscale('log')
    axes[2].set_yscale('log')
    axes[2].set_xlabel('BTC Volume [log]')
    axes[2].set_ylabel('Volatility [log]')
    axes[2].set_title('Log-Log Scale')
    axes[2].grid(True, alpha=0.3)
    
    # Plots 4-6: Alternative models
    plot_idx = 3
    for model_name, (params, r2, predictions) in alternative_results.items():
        if plot_idx < 6:
            axes[plot_idx].scatter(btc_volumes, volatilities, alpha=0.4, s=15, label='Data')
            
            # Sort for smooth line
            sort_idx = np.argsort(btc_volumes)
            axes[plot_idx].plot(btc_volumes[sort_idx], predictions[sort_idx], 'r-', 
                              linewidth=2, label=f'R² = {r2:.4f}')
            
            axes[plot_idx].set_xlabel('BTC Volume')
            axes[plot_idx].set_ylabel('Volatility (%)')
            axes[plot_idx].set_title(f'{model_name}')
            axes[plot_idx].legend()
            axes[plot_idx].grid(True, alpha=0.3)
            plot_idx += 1
    
    plt.tight_layout()
    
    # Save plots
    plot_file = "scripts/improved_calibration_results.png"
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    print(f"\nImproved calibration plots saved to: {plot_file}")
    
    return plot_file

def main():
    """Main improved calibration function"""
    
    print("IMPROVED VOLATILITY-VOLUME CALIBRATION")
    print("=" * 45)
    
    # Test different time lags
    for lag_hours in [0, 1, 2]:
        print(f"\n--- TESTING {lag_hours}H TIME LAG ---")
        
        btc_volumes, volatilities = load_lagged_data(lag_hours)
        
        # Improved power law calibration
        power_params, power_r2, power_pred = improved_power_law_calibration(btc_volumes, volatilities)
        
        # Test alternatives
        alternative_results = test_alternative_approaches(btc_volumes, volatilities)
        
        # Find best overall model
        all_models = {}
        if power_params is not None:
            all_models['Power Law'] = (power_params, power_r2, power_pred)
        all_models.update(alternative_results)
        
        if all_models:
            best_model = max(all_models.items(), key=lambda x: x[1][1])
            print(f"\nBest model for {lag_hours}h lag: {best_model[0]} (R² = {best_model[1][1]:.4f})")
        
        # Create plots for best lag
        if lag_hours == 1:  # Based on investigation results
            plot_file = create_comprehensive_plots(btc_volumes, volatilities, power_params, alternative_results)
            
            # Save results
            if power_params is not None:
                results_file = "scripts/improved_calibration_results.txt"
                with open(results_file, 'w') as f:
                    f.write("IMPROVED VOLATILITY-VOLUME CALIBRATION RESULTS\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(f"Time lag applied: 1 hour\n")
                    f.write(f"Data points used: {len(btc_volumes)}\n\n")
                    f.write("IMPROVED POWER LAW PARAMETERS:\n")
                    f.write("-" * 32 + "\n")
                    f.write(f"k = {power_params[0]:.6e}\n")
                    f.write(f"beta = {power_params[1]:.6f}\n")
                    f.write(f"R² = {power_r2:.6f}\n\n")
                    f.write("MODEL: sigma = k * V^beta\n")
                    f.write("Where V is BTC volume at time t, sigma is volatility at time t+1h\n")
                
                print(f"Results saved to: {results_file}")

if __name__ == "__main__":
    main()