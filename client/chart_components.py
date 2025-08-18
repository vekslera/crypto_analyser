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


def create_unified_chart(df, selected_charts, timezone_name=None):
    """Create unified chart with configurable line plots and multiple y-axes"""
    if df.empty:
        return go.Figure()
    
    # Convert timestamps to local timezone
    df_local = _convert_timestamps_to_timezone(df, timezone_name)
    
    # Create figure with multiple y-axes
    fig = go.Figure()
    
    # Add price line (primary y-axis - left) if selected
    if "price" in selected_charts:
        fig.add_trace(go.Scatter(
            x=df_local['timestamp'],
            y=df_local['price'],
            mode='lines',
            name='Bitcoin Price',
            line=dict(color='#2E86AB', width=3),  # Blue
            hovertemplate='<b>Price: $%{y:,.2f}</b><br>Time: %{x}<extra></extra>',
            yaxis='y'
        ))
    
    # Add volatility line (secondary y-axis - right) if selected and available
    if "volatility" in selected_charts and 'volatility' in df_local.columns:
        valid_volatility = df_local['volatility'].notna()
        if valid_volatility.any():
            fig.add_trace(go.Scatter(
                x=df_local.loc[valid_volatility, 'timestamp'],
                y=df_local.loc[valid_volatility, 'volatility'],
                mode='lines',
                name='24h Volatility (%)',
                line=dict(color='#A23B72', width=2),  # Purple/Magenta
                hovertemplate='<b>Volatility: %{y:.3f}%</b><br>Time: %{x}<extra></extra>',
                yaxis='y2'
            ))
    
    # Add volume line (third y-axis - far right) if selected and available
    if "volume" in selected_charts and 'volume_24h' in df_local.columns:
        valid_volume = df_local['volume_24h'].notna()
        if valid_volume.any():
            fig.add_trace(go.Scatter(
                x=df_local.loc[valid_volume, 'timestamp'],
                y=df_local.loc[valid_volume, 'volume_24h'],
                mode='lines',
                name='24h Volume (USD)',
                line=dict(color='#34D399', width=2),  # Green
                hovertemplate='<b>Volume: $%{y:,.0f}</b><br>Time: %{x}<extra></extra>',
                yaxis='y3'
            ))
    
    # Build dynamic chart title based on selected data
    title_parts = []
    if "price" in selected_charts:
        title_parts.append("Price")
    if "volatility" in selected_charts:
        title_parts.append("Volatility")  
    if "volume" in selected_charts:
        title_parts.append("Volume")
    
    chart_title = CHART_LABELS['price_chart_title'].format(timezone=timezone_name if timezone_name else "UTC")
    if title_parts:
        chart_title = f"{chart_title} - {' & '.join(title_parts)}"
    
    # Update layout with three separate y-axes
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
            showgrid=True,
            domain=[0, 1]
        ),
        # Primary y-axis (left) - Price
        yaxis=dict(
            title=dict(
                text='Price (USD)',
                font=dict(color='#2E86AB')
            ),
            gridcolor=CHART_CONFIG['grid_color'],
            showgrid=True,
            tickformat=CHART_CONFIG['tick_format_currency'],
            side='left',
            tickfont=dict(color='#2E86AB')
        ),
        # Secondary y-axis (right) - Volatility
        yaxis2=dict(
            title=dict(
                text='Volatility (%)',
                font=dict(color='#A23B72')
            ),
            side='right',
            overlaying='y',
            showgrid=False,
            tickfont=dict(color='#A23B72'),
            tickformat='.3f',
            anchor='free',
            position=0.90  # Moved further right
        ),
        # Third y-axis (far right) - Volume
        yaxis3=dict(
            title=dict(
                text='Volume (USD)',
                font=dict(color='#34D399')
            ),
            side='right',
            overlaying='y',
            showgrid=False,
            tickfont=dict(color='#34D399'),
            tickformat='$,.0s',  # Format as currency with SI suffix (K, M, B)
            anchor='free',
            position=0.97  # Moved further right
        ),
        plot_bgcolor=CHART_CONFIG['background_color'],
        paper_bgcolor=CHART_CONFIG['background_color'],
        hovermode='x unified',
        height=600,
        showlegend=True,
        legend=dict(
            x=0.02,
            y=1.02,  # Moved higher above the chart
            bgcolor='rgba(255, 255, 255, 0.9)',
            bordercolor='rgba(0, 0, 0, 0.2)',
            borderwidth=1,
            orientation='h'  # Make legend horizontal for better space usage
        ),
        margin=dict(r=140, t=60)  # Extra right margin for axes and top margin for legend
    )
    
    return fig


# MONEY FLOW CHART TEMPORARILY COMMENTED OUT - TO BE REPLACED SOON
# def create_money_flow_chart(df, timezone_name=None):
#     """Create money flow chart based on volatility analysis"""
#     if df.empty:
#         return go.Figure()
#     
#     # Convert timestamps to local timezone
#     df_local = _convert_timestamps_to_timezone(df, timezone_name)
#     
#     if len(df_local) <= 1:
#         return go.Figure()
#     
#     # Calculate price returns and volatility
#     df_local['returns'] = df_local['price'].pct_change()
#     df_local['volatility'] = df_local['returns'].rolling(window=5, min_periods=2).std()
#     
#     # Calculate BTC volume from volatility using power law: sigma = k * V^beta
#     # Solving for V: V = (sigma / k)^(1/beta)
#     k = 1.0e-4  # calibration constant
#     beta = 0.2  # power law exponent
#     
#     # Calculate estimated BTC volume (in BTC units)
#     df_local['btc_volume'] = (df_local['volatility'] / k) ** (1 / beta)
#     
#     # Calculate money flow: X = V * price_change (in USD) with direction
#     df_local['price_change'] = df_local['price'].diff()
#     df_local['money_flow'] = df_local['btc_volume'] * df_local['price_change']
#     
#     fig = go.Figure()
#     
#     # Only plot where we have valid money flow data
#     valid_data = df_local['money_flow'].notna()
#     if valid_data.any():
#         fig.add_trace(go.Scatter(
#             x=df_local.loc[valid_data, 'timestamp'],
#             y=df_local.loc[valid_data, 'money_flow'],
#             mode='lines',
#             name='Money Flow',
#             line=dict(color='#e74c3c', width=2),
#             hovertemplate='<b>Money Flow: $%{y:+,.0f}</b><br>Time: %{x}<extra></extra>'
#         ))
#     
#     flow_title = f"Bitcoin Money Flow Analysis ({timezone_name if timezone_name else 'UTC'})"
#     fig.update_layout(
#         title={
#             'text': flow_title,
#             'x': 0.5,
#             'xanchor': 'center',
#             'font': {'size': 20, 'color': '#1f2937'}
#         },
#         xaxis=dict(title=CHART_LABELS['time_axis'], gridcolor=CHART_CONFIG['grid_color']),
#         yaxis=dict(title='Money Flow (USD)', gridcolor=CHART_CONFIG['grid_color'], tickformat='$+,.0f'),
#         plot_bgcolor=CHART_CONFIG['background_color'],
#         paper_bgcolor=CHART_CONFIG['background_color'],
#         height=400
#     )
#     
#     return fig


def create_volume_chart(df, timezone_name=None):
    """Create 24h trading volume chart"""
    if df.empty:
        return go.Figure()
    
    # Convert timestamps to local timezone
    df_local = _convert_timestamps_to_timezone(df, timezone_name)
    
    # Check if volume data is available
    if 'volume_24h' not in df_local.columns:
        return go.Figure()
    
    # Filter out records with no volume data
    valid_volume = df_local['volume_24h'].notna()
    if not valid_volume.any():
        return go.Figure()
    
    fig = go.Figure()
    
    # Add volume bars
    fig.add_trace(go.Bar(
        x=df_local.loc[valid_volume, 'timestamp'],
        y=df_local.loc[valid_volume, 'volume_24h'],
        name='24h Volume',
        marker_color='#34D399',  # Green
        hovertemplate='<b>Volume: $%{y:,.0f}</b><br>Time: %{x}<extra></extra>'
    ))
    
    # Update layout
    chart_title = f"Bitcoin 24h Trading Volume ({timezone_name if timezone_name else 'UTC'})"
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
            title='Volume (USD)',
            gridcolor=CHART_CONFIG['grid_color'],
            showgrid=True,
            tickformat='$,.0s'  # Format as currency with SI suffix (K, M, B)
        ),
        plot_bgcolor=CHART_CONFIG['background_color'],
        paper_bgcolor=CHART_CONFIG['background_color'],
        hovermode=CHART_CONFIG['hover_mode'],
        height=500
    )
    
    return fig


def create_volatility_chart(df, timezone_name=None):
    """Create 24h volatility chart"""
    if df.empty:
        return go.Figure()
    
    # Convert timestamps to local timezone
    df_local = _convert_timestamps_to_timezone(df, timezone_name)
    
    # Check if volatility data is available
    if 'volatility' not in df_local.columns:
        return go.Figure()
    
    # Filter out records with no volatility data
    valid_volatility = df_local['volatility'].notna()
    if not valid_volatility.any():
        return go.Figure()
    
    fig = go.Figure()
    
    # Add volatility line
    fig.add_trace(go.Scatter(
        x=df_local.loc[valid_volatility, 'timestamp'],
        y=df_local.loc[valid_volatility, 'volatility'],
        mode='lines',
        name='24h Volatility',
        line=dict(color='#A23B72', width=2),  # Purple/Magenta
        hovertemplate='<b>Volatility: %{y:.3f}%</b><br>Time: %{x}<extra></extra>'
    ))
    
    # Update layout
    chart_title = f"Bitcoin 24h Volatility ({timezone_name if timezone_name else 'UTC'})"
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
            title='Volatility (%)',
            gridcolor=CHART_CONFIG['grid_color'],
            showgrid=True,
            tickformat='.3f'
        ),
        plot_bgcolor=CHART_CONFIG['background_color'],
        paper_bgcolor=CHART_CONFIG['background_color'],
        hovermode=CHART_CONFIG['hover_mode'],
        height=500
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