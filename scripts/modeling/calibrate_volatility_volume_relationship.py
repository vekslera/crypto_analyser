#!/usr/bin/env python3
"""
Calibrate volatility-volume relationship using actual collected data

This script calibrates the power law relationship: sigma = k * V^beta
where:
- sigma = volatility (standard deviation of returns)
- V = BTC trading volume 
- k = calibration constant
- beta = power law exponent

Uses 24-hour rolling windows with 1-hour shifts from data start to present.
Both price and volume data have been collected consistently since the beginning.
"""

import sys
import os
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from scipy.optimize import minimize
import matplotlib.pyplot as plt

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def load_price_volume_data():
    """Load all price and volume data from database"""
    
    print("Loading price and volume data from database...")
    
    db_path = os.path.join(project_root, "data", "crypto_analyser.db")
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return None
    
    conn = sqlite3.connect(db_path)
    
    # Load all data with price and volume
    query = """
    SELECT timestamp, price, volume_24h 
    FROM bitcoin_prices 
    WHERE volume_24h IS NOT NULL 
    ORDER BY timestamp ASC
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        print("No data found in database")
        return None
    
    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    print(f"Loaded {len(df)} records")
    print(f"Time range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    
    return df

def calculate_24h_metrics(df, window_start, window_end):
    """
    Calculate 24h volatility and get corresponding BTC volume
    
    Logic:
    - Calculate volatility from price data over 24h window
    - Get volume_24h value at END of window (represents accumulation over that 24h)
    - This ensures we compare volatility vs actual volume for same time period
    
    Args:
        df: DataFrame with timestamp, price, volume_24h
        window_start: Start of 24h window (e.g., Aug 11 11:30)
        window_end: End of 24h window (window_start + 24h)
    
    Returns:
        dict with volatility, btc_volume_actual, window info
    """
    
    # Get price data for the 24h window to calculate volatility
    price_window = df[(df['timestamp'] >= window_start) & (df['timestamp'] < window_end)].copy()
    
    if len(price_window) < 10:  # Need minimum data points
        return None
    
    # Calculate returns and volatility from price movements in this window
    price_window = price_window.sort_values('timestamp')
    returns = price_window['price'].pct_change().dropna()
    
    if len(returns) < 5:
        return None
    
    volatility = returns.std()  # Standard deviation of returns over 24h window
    
    # Get volume_24h value at the END of the window
    # This represents the actual BTC volume traded during this 24h period
    end_records = df[(df['timestamp'] >= window_end - pd.Timedelta(minutes=30)) & 
                     (df['timestamp'] <= window_end + pd.Timedelta(minutes=30))]
    
    if len(end_records) == 0:
        return None
    
    # Use the closest record to window_end
    closest_idx = (end_records['timestamp'] - window_end).abs().idxmin()
    volume_24h_usd = end_records.loc[closest_idx, 'volume_24h']
    end_price = end_records.loc[closest_idx, 'price']
    
    if pd.isna(volume_24h_usd) or pd.isna(end_price):
        return None
    
    # Convert USD volume to BTC volume using end price
    btc_volume_actual = volume_24h_usd / end_price
    
    return {
        'window_start': window_start,
        'window_end': window_end,
        'volatility': volatility,
        'volume_24h_usd': volume_24h_usd,
        'btc_volume_actual': btc_volume_actual,
        'end_price': end_price,
        'price_data_points': len(price_window),
        'volume_timestamp': end_records.loc[closest_idx, 'timestamp']
    }

def generate_calibration_dataset(df):
    """
    Generate calibration dataset using 24h windows with 1h shifts
    
    Timeline logic:
    - Price/volatility calculations: Start from Aug 10 11:30 UTC to now
    - Volume data: Start from Aug 11 11:30 UTC to now (24h offset)
    
    This is because volume_24h at time T represents the accumulation 
    of the past 24 hours ending at time T.
    """
    
    print("Generating calibration dataset...")
    
    # Price data start: actual data start (Aug 10 11:30 UTC)
    price_start = df['timestamp'].min()
    print(f"Price data start: {price_start}")
    
    # Volume data start: 24h after price data start (Aug 11 11:30 UTC)
    volume_start = price_start + timedelta(hours=24)
    print(f"Volume data start: {volume_start}")
    
    # End time: latest data (now)
    end_date = df['timestamp'].max()
    print(f"Data end: {end_date}")
    
    # Calibration starts when we have both price windows AND volume data
    # First 24h price window: Aug 10 11:30 to Aug 11 11:30
    # Corresponding volume data: at Aug 11 11:30 (represents Aug 10 11:30 to Aug 11 11:30)
    calibration_start = volume_start
    
    print(f"Calibration period: {calibration_start} to {end_date}")
    
    calibration_data = []
    current_time = calibration_start
    
    while current_time <= end_date:
        # Price window: 24h ending at current_time
        price_window_start = current_time - timedelta(hours=24)
        price_window_end = current_time
        
        metrics = calculate_24h_metrics(df, price_window_start, price_window_end)
        
        if metrics is not None:
            calibration_data.append(metrics)
        
        # Move to next 1-hour shift
        current_time += timedelta(hours=1)
    
    print(f"Generated {len(calibration_data)} calibration windows")
    
    return calibration_data

def power_law_model(btc_volume, k, beta):
    """Power law model: sigma = k * V^beta"""
    return k * (btc_volume ** beta)

def objective_function(params, btc_volumes, observed_volatilities):
    """
    Objective function for optimization (minimize sum of squared residuals)
    
    Args:
        params: [k, beta] - parameters to optimize
        btc_volumes: Array of BTC volumes
        observed_volatilities: Array of observed volatilities
    """
    k, beta = params
    
    # Prevent invalid parameter values
    if k <= 0 or beta <= 0 or beta > 1:
        return 1e10  # Large penalty for invalid parameters
    
    predicted_volatilities = power_law_model(btc_volumes, k, beta)
    
    # Sum of squared residuals
    residuals = observed_volatilities - predicted_volatilities
    return np.sum(residuals ** 2)

def calibrate_parameters(calibration_data):
    """
    Calibrate k and beta parameters using least squares optimization
    """
    
    print("Calibrating volatility-volume relationship parameters...")
    
    # Extract data for calibration
    btc_volumes = np.array([d['btc_volume_actual'] for d in calibration_data])
    volatilities = np.array([d['volatility'] for d in calibration_data])
    
    # Remove any invalid data points
    valid_mask = (btc_volumes > 0) & (volatilities > 0) & np.isfinite(btc_volumes) & np.isfinite(volatilities)
    btc_volumes = btc_volumes[valid_mask]
    volatilities = volatilities[valid_mask]
    
    print(f"Using {len(btc_volumes)} valid data points for calibration")
    
    if len(btc_volumes) < 10:
        print("Error: Insufficient valid data points for calibration")
        return None, None, None
    
    # Initial parameter guess
    initial_k = 1e-4  # Based on literature
    initial_beta = 0.2  # Based on literature
    
    # Optimization bounds
    bounds = [(1e-8, 1e-1), (0.01, 0.8)]  # (k_min, k_max), (beta_min, beta_max)
    
    # Optimize parameters
    result = minimize(
        objective_function,
        x0=[initial_k, initial_beta],
        args=(btc_volumes, volatilities),
        bounds=bounds,
        method='L-BFGS-B'
    )
    
    if result.success:
        k_opt, beta_opt = result.x
        final_error = result.fun
        
        print(f"Optimization successful!")
        print(f"Calibrated parameters:")
        print(f"  k = {k_opt:.2e}")
        print(f"  beta = {beta_opt:.4f}")
        print(f"  Sum of squared residuals: {final_error:.2e}")
        
        return k_opt, beta_opt, (btc_volumes, volatilities)
    else:
        print(f"Optimization failed: {result.message}")
        return None, None, None

def validate_calibration(k, beta, btc_volumes, volatilities):
    """Validate the calibrated model and generate statistics"""
    
    print("\nValidating calibrated model...")
    
    # Calculate predictions
    predicted_volatilities = power_law_model(btc_volumes, k, beta)
    
    # Calculate R-squared
    ss_res = np.sum((volatilities - predicted_volatilities) ** 2)
    ss_tot = np.sum((volatilities - np.mean(volatilities)) ** 2)
    r_squared = 1 - (ss_res / ss_tot)
    
    # Calculate mean absolute percentage error
    mape = np.mean(np.abs((volatilities - predicted_volatilities) / volatilities)) * 100
    
    # Calculate correlation coefficient
    correlation = np.corrcoef(volatilities, predicted_volatilities)[0, 1]
    
    print(f"Model validation statistics:")
    print(f"  R-squared: {r_squared:.4f}")
    print(f"  Correlation: {correlation:.4f}")
    print(f"  Mean Absolute Percentage Error: {mape:.2f}%")
    
    # Show sample predictions
    print(f"\nSample predictions:")
    for i in [0, len(btc_volumes)//4, len(btc_volumes)//2, -1]:
        if i < len(btc_volumes):
            vol = btc_volumes[i]
            obs = volatilities[i]
            pred = predicted_volatilities[i]
            error = abs(obs - pred) / obs * 100
            print(f"  Volume: {vol:,.0f} BTC | Observed: {obs:.6f} | Predicted: {pred:.6f} | Error: {error:.1f}%")
    
    return r_squared, mape, correlation

def create_visualizations(k, beta, btc_volumes, volatilities, calibration_data):
    """Create visualization plots for the calibration results"""
    
    print("\nCreating visualization plots...")
    
    predicted_volatilities = power_law_model(btc_volumes, k, beta)
    
    # Create figure with subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # Plot 1: Scatter plot of volume vs volatility with fitted curve (log-log scale for better visualization)
    ax1.scatter(btc_volumes, volatilities, alpha=0.7, s=30, color='blue', label='Observed Data')
    
    # Generate smooth curve for fitted line with more points for smoothness
    vol_range = np.logspace(np.log10(btc_volumes.min()), np.log10(btc_volumes.max()), 200)
    fitted_curve = power_law_model(vol_range, k, beta)
    ax1.plot(vol_range, fitted_curve, 'r-', linewidth=3, label=f'Calibrated: sigma = {k:.2e} * V^{beta:.3f}')
    
    # Use log scale to better see the power law relationship
    ax1.set_xscale('log')
    ax1.set_yscale('log')
    ax1.set_xlabel('BTC Trading Volume (24h) [log scale]')
    ax1.set_ylabel('Volatility (sigma) [log scale]')
    ax1.set_title('Volatility vs BTC Trading Volume (Log-Log Scale)')
    ax1.legend()
    ax1.grid(True, alpha=0.3, which='both')
    
    # Plot 2: Observed vs Predicted with correlation info
    correlation = np.corrcoef(volatilities, predicted_volatilities)[0, 1]
    ax2.scatter(volatilities, predicted_volatilities, alpha=0.7, s=30, color='green')
    min_val = min(volatilities.min(), predicted_volatilities.min())
    max_val = max(volatilities.max(), predicted_volatilities.max())
    ax2.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='Perfect Fit')
    ax2.set_xlabel('Observed Volatility')
    ax2.set_ylabel('Predicted Volatility')
    ax2.set_title(f'Observed vs Predicted Volatility (r = {correlation:.3f})')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Time series of volatility
    timestamps = [d['window_start'] for d in calibration_data]
    ax3.plot(timestamps, volatilities, 'b-', linewidth=1, alpha=0.7, label='Observed')
    ax3.plot(timestamps, predicted_volatilities, 'r-', linewidth=1, alpha=0.7, label='Predicted')
    ax3.set_xlabel('Time')
    ax3.set_ylabel('Volatility')
    ax3.set_title('Volatility Time Series')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.tick_params(axis='x', rotation=45)
    
    # Plot 4: Residuals over time
    residuals = volatilities - predicted_volatilities
    ax4.plot(timestamps, residuals, 'g-', linewidth=1, alpha=0.7)
    ax4.axhline(y=0, color='k', linestyle='--', alpha=0.5)
    ax4.set_xlabel('Time')
    ax4.set_ylabel('Residuals (Observed - Predicted)')
    ax4.set_title('Model Residuals Over Time')
    ax4.grid(True, alpha=0.3)
    ax4.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    
    # Save plots
    plot_file = os.path.join(project_root, "scripts", "volatility_volume_calibration_results.png")
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    print(f"Plots saved to: {plot_file}")
    
    return plot_file

def save_calibration_results(k, beta, calibration_data, r_squared, mape, correlation):
    """Save calibration results to file"""
    
    print("\nSaving calibration results...")
    
    results_file = os.path.join(project_root, "scripts", "volatility_volume_calibration_results.txt")
    
    with open(results_file, 'w') as f:
        f.write("VOLATILITY-VOLUME RELATIONSHIP CALIBRATION RESULTS\n")
        f.write("=" * 55 + "\n\n")
        
        f.write(f"Calibration Date: {datetime.now()}\n")
        f.write(f"Data Points Used: {len(calibration_data)}\n\n")
        
        f.write("CALIBRATED PARAMETERS:\n")
        f.write("-" * 22 + "\n")
        f.write(f"k (calibration constant): {k:.6e}\n")
        f.write(f"beta (power law exponent): {beta:.6f}\n\n")
        
        f.write("POWER LAW MODEL:\n")
        f.write("-" * 17 + "\n")
        f.write(f"sigma = {k:.2e} * V^{beta:.3f}\n")
        f.write("Where:\n")
        f.write("  sigma = volatility (standard deviation of returns)\n")
        f.write("  V = BTC trading volume (24h)\n\n")
        
        f.write("MODEL VALIDATION:\n")
        f.write("-" * 18 + "\n")
        f.write(f"R-squared: {r_squared:.6f}\n")
        f.write(f"Correlation: {correlation:.6f}\n")
        f.write(f"Mean Absolute Percentage Error: {mape:.2f}%\n\n")
        
        f.write("USAGE IN APPLICATION:\n")
        f.write("-" * 22 + "\n")
        f.write("Update server/services/crypto_service.py:\n")
        f.write(f"k = {k:.6e}\n")
        f.write(f"beta = {beta:.6f}\n\n")
        
        f.write("MONEY FLOW CALCULATION:\n")
        f.write("-" * 24 + "\n")
        f.write("1. Calculate volatility: sigma = std(price_returns)\n")
        f.write(f"2. Estimate BTC volume: V = (sigma / {k:.2e})^(1/{beta:.3f})\n")
        f.write("3. Calculate money flow: X = V * delta_P\n")
        f.write("   Where delta_P = price change\n")
    
    print(f"Results saved to: {results_file}")
    return results_file

def main():
    """Main calibration process"""
    
    print("VOLATILITY-VOLUME RELATIONSHIP CALIBRATION")
    print("=" * 45)
    print()
    
    # Load data
    df = load_price_volume_data()
    if df is None:
        return
    
    # Generate calibration dataset
    calibration_data = generate_calibration_dataset(df)
    if not calibration_data:
        print("Error: No calibration data generated")
        return
    
    # Calibrate parameters
    k, beta, data_arrays = calibrate_parameters(calibration_data)
    if k is None:
        return
    
    btc_volumes, volatilities = data_arrays
    
    # Validate model
    r_squared, mape, correlation = validate_calibration(k, beta, btc_volumes, volatilities)
    
    # Create visualizations
    plot_file = create_visualizations(k, beta, btc_volumes, volatilities, calibration_data)
    
    # Save results
    results_file = save_calibration_results(k, beta, calibration_data, r_squared, mape, correlation)
    
    print("\n" + "=" * 45)
    print("CALIBRATION COMPLETE!")
    print("=" * 45)
    print(f"Calibrated k = {k:.6e}")
    print(f"Calibrated beta = {beta:.6f}")
    print(f"Model R^2 = {r_squared:.4f}")
    print()
    print("Files generated:")
    print(f"  - Results: {results_file}")
    print(f"  - Plots: {plot_file}")
    print()
    print("Next steps:")
    print("1. Review the calibration results and plots")
    print("2. Update the constants in server/services/crypto_service.py")
    print("3. Test the updated money flow calculations")

if __name__ == "__main__":
    main()