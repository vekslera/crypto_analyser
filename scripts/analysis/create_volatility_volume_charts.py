#!/usr/bin/env python3
"""
Create visualizations for volatility-volume relationship analysis
Generates scatter plots, power-law fits, and time-series comparisons
"""

import sys
import os
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def create_volatility_volume_charts():
    """Create comprehensive charts showing volatility-volume relationship"""
    
    print("CREATING VOLATILITY-VOLUME RELATIONSHIP CHARTS")
    print("=" * 50)
    print()
    
    # Connect to database and load data
    db_path = os.path.join(project_root, 'data', 'crypto_analyser.db')
    conn = sqlite3.connect(db_path)
    
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
    
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='mixed', utc=True)
    
    print(f"Loaded {len(df):,} data points for visualization")
    
    # Calculate power-law parameters
    df['log_volatility'] = np.log(df['volatility'])
    df['log_volume'] = np.log(df['volume_24h'])
    
    # Linear regression on log-log data
    coeffs = np.polyfit(df['log_volatility'], df['log_volume'], 1)
    beta = coeffs[0]  # Power exponent
    log_k = coeffs[1]  # Log of scaling constant
    k = np.exp(log_k)
    
    print(f"Power-law parameters: Volume = {k:.2e} * (Volatility)^{beta:.4f}")
    print()
    
    # Create output directory
    charts_dir = os.path.join(project_root, 'charts')
    os.makedirs(charts_dir, exist_ok=True)
    
    # Set up matplotlib parameters for better-looking plots
    plt.style.use('default')
    plt.rcParams['figure.figsize'] = (12, 8)
    plt.rcParams['font.size'] = 10
    plt.rcParams['axes.grid'] = True
    plt.rcParams['grid.alpha'] = 0.3
    
    # Chart 1: Linear Scale Scatter Plot with Power-Law Fit
    print("Creating Chart 1: Linear Scale Scatter Plot with Power-Law Fit...")
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Scatter plot - use sample for better performance
    sample_size = min(2000, len(df))
    df_sample = df.sample(n=sample_size, random_state=42)
    
    scatter = ax.scatter(df_sample['volatility'], df_sample['volume_24h'] / 1e9, 
                        alpha=0.6, s=20, c='blue', label='Data Points')
    
    # Generate power-law curve
    vol_range = np.linspace(df['volatility'].min(), df['volatility'].max(), 100)
    volume_fit = k * (vol_range ** beta) / 1e9
    
    ax.plot(vol_range, volume_fit, 'r-', linewidth=2, 
            label=f'Power-Law Fit: V = {k:.2e} * σ^{beta:.3f}')
    
    ax.set_xlabel('24h Volatility (%)')
    ax.set_ylabel('24h Trading Volume (Billions USD)')
    ax.set_title('Bitcoin: 24h Volatility vs Trading Volume\n(Linear Scale with Power-Law Fit)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Add correlation info
    pearson_corr = df['volatility'].corr(df['volume_24h'])
    ax.text(0.05, 0.95, f'Pearson r = {pearson_corr:.3f}\nPower β = {beta:.3f}', 
            transform=ax.transAxes, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    chart1_path = os.path.join(charts_dir, 'volatility_volume_linear.png')
    plt.savefig(chart1_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {chart1_path}")
    
    # Chart 2: Log-Log Plot (Shows Power-Law as Straight Line)
    print("Creating Chart 2: Log-Log Plot (Power-Law Relationship)...")
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Log-log scatter plot
    ax.scatter(df_sample['volatility'], df_sample['volume_24h'], 
               alpha=0.6, s=20, c='green', label='Data Points')
    
    # Power-law appears as straight line in log-log space
    ax.plot(vol_range, k * (vol_range ** beta), 'r-', linewidth=2,
            label=f'Power-Law: β = {beta:.3f}')
    
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('24h Volatility (%) [Log Scale]')
    ax.set_ylabel('24h Trading Volume (USD) [Log Scale]')
    ax.set_title('Bitcoin: 24h Volatility vs Trading Volume\n(Log-Log Scale - Power-Law as Straight Line)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Add log-log correlation info
    log_corr = df['log_volatility'].corr(df['log_volume'])
    ax.text(0.05, 0.95, f'Log-Log r = {log_corr:.3f}\nPower β = {beta:.3f}', 
            transform=ax.transAxes, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    chart2_path = os.path.join(charts_dir, 'volatility_volume_loglog.png')
    plt.savefig(chart2_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {chart2_path}")
    
    # Chart 3: Time Series Comparison (Dual Y-Axis)
    print("Creating Chart 3: Time Series Comparison...")
    
    fig, ax1 = plt.subplots(figsize=(14, 8))
    
    # Sample data for better performance (every 10th point)
    df_time_sample = df[::10].copy()
    
    # Volatility on left axis
    color1 = 'tab:red'
    ax1.set_xlabel('Date')
    ax1.set_ylabel('24h Volatility (%)', color=color1)
    line1 = ax1.plot(df_time_sample['timestamp'], df_time_sample['volatility'], 
                     color=color1, linewidth=1, alpha=0.8, label='Volatility')
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.grid(True, alpha=0.3)
    
    # Volume on right axis
    ax2 = ax1.twinx()
    color2 = 'tab:blue'
    ax2.set_ylabel('24h Trading Volume (Billions USD)', color=color2)
    line2 = ax2.plot(df_time_sample['timestamp'], df_time_sample['volume_24h'] / 1e9, 
                     color=color2, linewidth=1, alpha=0.8, label='Volume')
    ax2.tick_params(axis='y', labelcolor=color2)
    
    ax1.set_title('Bitcoin: 24h Volatility and Trading Volume Over Time\n(Dual Y-Axis Time Series)')
    
    # Add legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    # Rotate x-axis labels for better readability
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    chart3_path = os.path.join(charts_dir, 'volatility_volume_timeseries.png')
    plt.savefig(chart3_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {chart3_path}")
    
    # Chart 4: Residuals Plot (How Well Power-Law Fits)
    print("Creating Chart 4: Power-Law Fit Quality (Residuals)...")
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Calculate predicted values and residuals
    df_sample['volume_predicted'] = k * (df_sample['volatility'] ** beta)
    df_sample['residuals'] = df_sample['volume_24h'] - df_sample['volume_predicted']
    df_sample['residuals_percent'] = (df_sample['residuals'] / df_sample['volume_24h']) * 100
    
    # Residuals vs Fitted
    ax1.scatter(df_sample['volume_predicted'] / 1e9, df_sample['residuals_percent'], 
                alpha=0.6, s=20, c='purple')
    ax1.axhline(y=0, color='red', linestyle='--', alpha=0.8)
    ax1.set_xlabel('Predicted Volume (Billions USD)')
    ax1.set_ylabel('Residuals (% Error)')
    ax1.set_title('Residuals vs Predicted Values\n(Power-Law Fit Quality)')
    ax1.grid(True, alpha=0.3)
    
    # Histogram of residuals
    ax2.hist(df_sample['residuals_percent'], bins=50, alpha=0.7, color='orange', edgecolor='black')
    ax2.axvline(x=0, color='red', linestyle='--', alpha=0.8)
    ax2.set_xlabel('Residuals (% Error)')
    ax2.set_ylabel('Frequency')
    ax2.set_title('Distribution of Residuals\n(Should be Normal if Good Fit)')
    ax2.grid(True, alpha=0.3)
    
    # Add fit quality metrics
    rmse = np.sqrt(np.mean(df_sample['residuals']**2)) / 1e9
    mae_percent = np.mean(np.abs(df_sample['residuals_percent']))
    
    fig.suptitle(f'Power-Law Fit Quality Assessment\nRMSE: ${rmse:.2f}B, MAE: {mae_percent:.1f}%', 
                 fontsize=14)
    
    plt.tight_layout()
    chart4_path = os.path.join(charts_dir, 'volatility_volume_residuals.png')
    plt.savefig(chart4_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {chart4_path}")
    
    # Chart 5: Correlation Heatmap by Time Period
    print("Creating Chart 5: Correlation Evolution Over Time...")
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Calculate rolling correlations (30-day windows)
    df['correlation_30d'] = df['volatility'].rolling(window=30*288, min_periods=100).corr(df['volume_24h'])  # 288 = 5-min intervals per day
    
    # Sample every 100th point for better performance
    df_corr_sample = df[::100].copy()
    df_corr_sample = df_corr_sample.dropna(subset=['correlation_30d'])
    
    # Create color-coded line plot
    scatter = ax.scatter(df_corr_sample['timestamp'], df_corr_sample['correlation_30d'], 
                        c=df_corr_sample['correlation_30d'], cmap='RdYlBu_r', 
                        s=30, alpha=0.7)
    
    # Add trend line
    valid_data = df_corr_sample.dropna(subset=['correlation_30d'])
    if len(valid_data) > 10:
        z = np.polyfit(range(len(valid_data)), valid_data['correlation_30d'], 1)
        p = np.poly1d(z)
        ax.plot(valid_data['timestamp'], p(range(len(valid_data))), 
                'k--', alpha=0.8, linewidth=2, label=f'Trend (slope: {z[0]:.4f}/day)')
    
    ax.set_xlabel('Date')
    ax.set_ylabel('30-Day Rolling Correlation')
    ax.set_title('Evolution of Volatility-Volume Correlation Over Time\n(30-Day Rolling Window)')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Add colorbar
    cbar = plt.colorbar(scatter)
    cbar.set_label('Correlation Coefficient')
    
    # Rotate x-axis labels
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    chart5_path = os.path.join(charts_dir, 'volatility_volume_correlation_evolution.png')
    plt.savefig(chart5_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {chart5_path}")
    
    print()
    print("CHARTS CREATED SUCCESSFULLY!")
    print("=" * 30)
    print(f"All charts saved in: {charts_dir}")
    print("Charts created:")
    print("1. volatility_volume_linear.png - Linear scale with power-law fit")
    print("2. volatility_volume_loglog.png - Log-log scale showing power-law")
    print("3. volatility_volume_timeseries.png - Time series comparison")
    print("4. volatility_volume_residuals.png - Fit quality assessment")
    print("5. volatility_volume_correlation_evolution.png - Correlation over time")
    
    return {
        'charts_directory': charts_dir,
        'power_exponent': beta,
        'scaling_constant': k,
        'sample_size': len(df),
        'charts_created': 5
    }

if __name__ == "__main__":
    try:
        result = create_volatility_volume_charts()
        print(f"\nChart generation complete!")
    except Exception as e:
        print(f"ERROR: Error during chart creation: {e}")
        import traceback
        traceback.print_exc()