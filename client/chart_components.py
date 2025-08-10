"""
Chart components module for GUI dashboard
Handles creation of Plotly charts and visualizations
"""

import sys
import os
import pandas as pd
import plotly.graph_objects as go
import pytz

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from core.config import COLORS, CHART_CONFIG, CHART_LABELS


def _convert_timestamps_to_timezone(df, timezone_name=None):
    """Helper function to convert DataFrame timestamps to specified timezone"""
    if df.empty or timezone_name is None:
        return df
    
    df_local = df.copy()
    try:
        if timezone_name and timezone_name != 'UTC':
            # Ensure timestamps are timezone-aware (assume UTC if naive)
            df_local['timestamp'] = pd.to_datetime(df_local['timestamp'], utc=True)
            # Convert to target timezone
            target_tz = pytz.timezone(timezone_name)
            df_local['timestamp'] = df_local['timestamp'].dt.tz_convert(target_tz)
        else:
            # Ensure UTC timezone is set
            df_local['timestamp'] = pd.to_datetime(df_local['timestamp'], utc=True)
    except Exception as e:
        print(f"Timezone conversion error: {e}")
        # Fallback to UTC if conversion fails
        df_local['timestamp'] = pd.to_datetime(df_local['timestamp'], utc=True)
    
    return df_local


def create_price_chart(df, timezone_name=None):
    """Create interactive price chart with timezone support"""
    if df.empty:
        return go.Figure()
    
    # Convert timestamps to local timezone
    df_local = _convert_timestamps_to_timezone(df, timezone_name)
    
    fig = go.Figure()
    
    # Add price line
    fig.add_trace(go.Scatter(
        x=df_local['timestamp'],
        y=df_local['price'],
        mode='lines',
        name='Bitcoin Price',
        line=dict(color=CHART_CONFIG['price_line_color'], width=2),
        hovertemplate='<b>Price: $%{y:,.2f}</b><br>Time: %{x}<extra></extra>'
    ))
    
    # Update layout to match CoinMarketCap style
    chart_title = CHART_LABELS['price_chart_title'].format(timezone=timezone_name if timezone_name else "UTC")
    fig.update_layout(
        title={
            'text': chart_title,
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'color': '#1f2937'}
        },
        xaxis=dict(
            title=CHART_LABELS['time_axis'],
            gridcolor=CHART_CONFIG['grid_color'],
            showgrid=True
        ),
        yaxis=dict(
            title=CHART_LABELS['price_axis'],
            gridcolor=CHART_CONFIG['grid_color'],
            showgrid=True,
            tickformat=CHART_CONFIG['tick_format_currency']
        ),
        plot_bgcolor=CHART_CONFIG['background_color'],
        paper_bgcolor=CHART_CONFIG['background_color'],
        hovermode=CHART_CONFIG['hover_mode'],
        height=500
    )
    
    return fig


def create_combined_price_volume_chart(df, timezone_name=None):
    """Create combined price and volume chart with dual y-axes"""
    if df.empty:
        return go.Figure()
    
    # Convert timestamps to local timezone
    df_local = _convert_timestamps_to_timezone(df, timezone_name)
    
    # Create figure with secondary y-axis
    fig = go.Figure()
    
    # Add price line (primary y-axis)
    fig.add_trace(go.Scatter(
        x=df_local['timestamp'],
        y=df_local['price'],
        mode='lines',
        name='Bitcoin Price',
        line=dict(color=CHART_CONFIG['price_line_color'], width=3),
        hovertemplate='<b>Price: $%{y:,.2f}</b><br>Time: %{x}<extra></extra>',
        yaxis='y'
    ))
    
    # Add volume velocity line (secondary y-axis) - only if volume velocity data exists
    if 'volume_velocity' in df_local.columns and df_local['volume_velocity'].notna().any():
        fig.add_trace(go.Scatter(
            x=df_local['timestamp'],
            y=df_local['volume_velocity'],
            mode='lines',
            name='Volume Velocity',
            line=dict(color=CHART_CONFIG['volume_bar_color'], width=2),
            hovertemplate='<b>Volume Velocity: $%{y:,.0f}/min</b><br>Time: %{x}<extra></extra>',
            yaxis='y2'
        ))
    
    # Update layout with dual y-axes
    chart_title = CHART_LABELS['price_chart_title'].format(timezone=timezone_name if timezone_name else "UTC")
    fig.update_layout(
        title={
            'text': f"{chart_title} with Volume Velocity",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'color': '#1f2937'}
        },
        xaxis=dict(
            title=CHART_LABELS['time_axis'],
            gridcolor=CHART_CONFIG['grid_color'],
            showgrid=True,
            domain=[0, 1]
        ),
        # Primary y-axis (left) - Price
        yaxis=dict(
            title=CHART_LABELS['price_axis'],
            gridcolor=CHART_CONFIG['grid_color'],
            showgrid=True,
            tickformat=CHART_CONFIG['tick_format_currency'],
            side='left'
        ),
        # Secondary y-axis (right) - Volume
        yaxis2=dict(
            title=dict(
                text='Volume Velocity (USD/min)',
                font=dict(color=CHART_CONFIG['volume_bar_color'])
            ),
            tickformat='$,.0f',
            side='right',
            overlaying='y',
            showgrid=False,
            tickfont=dict(color=CHART_CONFIG['volume_bar_color'])
        ),
        plot_bgcolor=CHART_CONFIG['background_color'],
        paper_bgcolor=CHART_CONFIG['background_color'],
        hovermode='x unified',
        height=600,  # Slightly taller to accommodate dual axes
        showlegend=True,
        legend=dict(
            x=0.02,
            y=0.98,
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='rgba(0, 0, 0, 0.2)',
            borderwidth=1
        )
    )
    
    return fig


def create_volume_chart(df, timezone_name=None):
    """Create interactive volume chart with timezone support"""
    if df.empty or 'volume_24h' not in df.columns:
        return go.Figure()
    
    # Convert timestamps to local timezone
    df_local = _convert_timestamps_to_timezone(df, timezone_name)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df_local['timestamp'],
        y=df_local['volume_24h'],
        name=CHART_LABELS['volume_name'],
        marker_color=CHART_CONFIG['volume_bar_color'],
        hovertemplate='<b>Volume: $%{y:,.0f}</b><br>Time: %{x}<extra></extra>'
    ))
    
    volume_title = CHART_LABELS['volume_chart_title'].format(timezone=timezone_name if timezone_name else "UTC")
    fig.update_layout(
        title={
            'text': volume_title,
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'color': '#1f2937'}
        },
        xaxis=dict(title=CHART_LABELS['time_axis'], gridcolor=CHART_CONFIG['grid_color']),
        yaxis=dict(title=CHART_LABELS['volume_axis'], gridcolor=CHART_CONFIG['grid_color'], tickformat=CHART_CONFIG['tick_format_currency']),
        plot_bgcolor=CHART_CONFIG['background_color'],
        paper_bgcolor=CHART_CONFIG['background_color'],
        height=300
    )
    
    return fig


def create_statistics_display(df):
    """Create statistics metrics for display"""
    if df.empty:
        return {
            'data_points': 0,
            'average_price': 0,
            'min_price': 0,
            'max_price': 0
        }
    
    return {
        'data_points': len(df),
        'average_price': df['price'].mean(),
        'min_price': df['price'].min(),
        'max_price': df['price'].max()
    }