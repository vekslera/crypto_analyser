"""
UI components module for GUI dashboard
Reusable UI components and styling
"""

import sys
import os
import streamlit as st
import pandas as pd
import pytz

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from core.config import COLORS, CSS_SIZES, METRIC_LABELS, CHART_LABELS, RECENT_ENTRIES_DISPLAY_LIMIT


def apply_custom_css():
    """Apply custom CSS styling"""
    st.markdown("""
    <style>
        .main-header {
            font-size: 3rem;
            font-weight: bold;
            color: #F7931A;
            text-align: center;
            margin-bottom: 2rem;
        }
        .price-card {
            background: linear-gradient(90deg, #F7931A 0%, #FFB84D 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin: 10px 0;
        }
        .metric-card {
            background: #f0f2f6;
            padding: 15px;
            border-radius: 8px;
            margin: 5px 0;
        }
    </style>
    """, unsafe_allow_html=True)



def display_price_cards(current_price_data):
    """Display current price information in card format"""
    if not current_price_data:
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="price-card">
            <h2>${current_price_data['price']:,.2f}</h2>
            <p>{METRIC_LABELS['current_price']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if current_price_data.get('market_cap'):
            st.markdown(f"""
            <div class="price-card">
                <h2>${current_price_data['market_cap']:,.0f}</h2>
                <p>{METRIC_LABELS['market_cap']}</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        if current_price_data.get('volume_24h'):
            st.markdown(f"""
            <div class="price-card">
                <h2>${current_price_data['volume_24h']:,.0f}</h2>
                <p>{METRIC_LABELS['volume_24h']}</p>
            </div>
            """, unsafe_allow_html=True)


def display_statistics_metrics(stats):
    """Display statistics in metric format"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(METRIC_LABELS['data_points'], stats['data_points'])
    with col2:
        st.metric(METRIC_LABELS['average_price'], f"${stats['average_price']:,.2f}")
    with col3:
        st.metric(METRIC_LABELS['min_price'], f"${stats['min_price']:,.2f}")
    with col4:
        st.metric(METRIC_LABELS['max_price'], f"${stats['max_price']:,.2f}")


def display_recent_data_table(df, selected_timezone):
    """Display recent data table with timezone conversion including volatility and money flow"""
    st.subheader(CHART_LABELS['recent_data_title'].format(timezone=selected_timezone))
    
    # Take recent entries from the dataset (volatility and money_flow are pre-calculated in DB)
    recent_df = df.tail(RECENT_ENTRIES_DISPLAY_LIMIT).copy()
    
    if selected_timezone != 'UTC':
        try:
            # First ensure timestamps are timezone-aware (assume UTC if naive)
            recent_df['timestamp'] = pd.to_datetime(recent_df['timestamp'], utc=True)
            # Then convert to selected timezone
            target_tz = pytz.timezone(selected_timezone)
            recent_df['timestamp'] = recent_df['timestamp'].dt.tz_convert(target_tz)
        except Exception as e:
            print(f"Timezone conversion error for table: {e}")
            # Keep original timestamps if conversion fails
            pass
    
    # Format for display
    recent_df['Price'] = recent_df['price'].apply(lambda x: f"${x:,.2f}")
    recent_df['Timestamp'] = recent_df['timestamp']
    
    # Handle volatility column (might not exist in older data)
    if 'volatility' in recent_df.columns:
        recent_df['Volatility'] = recent_df['volatility'].apply(lambda x: f'{x:.3f}%' if pd.notna(x) else 'N/A')
    else:
        recent_df['Volatility'] = 'N/A'
    
    # Handle money_flow column (might not exist in older data)
    if 'money_flow' in recent_df.columns:
        recent_df['Money Flow'] = recent_df['money_flow'].apply(lambda x: f'${x:+,.0f}' if pd.notna(x) else 'N/A')
    else:
        recent_df['Money Flow'] = 'N/A'
    
    # Display the relevant columns
    display_df = recent_df[['Timestamp', 'Price', 'Volatility', 'Money Flow']].copy()
    st.dataframe(display_df.iloc[::-1], use_container_width=True)


def display_no_data_message():
    """Display message when no data is available"""
    st.warning("No historical data available. Start the data collection service first!")
    st.info("Run `python run.py` to start collecting crypto price data.")


def display_footer():
    """Display footer information"""
    st.markdown("---")
    st.markdown("**Data Source:** CoinGecko API | **Collection Rate:** 300 seconds | **Auto-refresh:** 60 seconds (when enabled)")


def show_main_header():
    """Display the main application header"""
    st.markdown(f'<div class="main-header">{CHART_LABELS["main_title"]}</div>', unsafe_allow_html=True)