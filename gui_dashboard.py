import streamlit as st
import plotly.graph_objects as go
#import plotly.express as px
import pandas as pd
import requests
import time
#from datetime import datetime, timedelta
from database import SessionLocal, BitcoinPrice
import asyncio
from bitcoin_service import BitcoinService
from timezone_utils import (
    get_available_timezones, 
    convert_utc_to_local, 
    #format_datetime_local,
    #get_system_timezone,
    set_default_timezone,
    get_default_timezone
)

st.set_page_config(
    page_title="Crypto Analyser",
    page_icon="📊",
    layout="wide"
)

# Initialize session state
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False
if 'selected_timezone' not in st.session_state:
    st.session_state.selected_timezone = get_default_timezone()
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()
if 'stop_confirmation' not in st.session_state:
    st.session_state.stop_confirmation = False

# Custom CSS for styling
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

def get_price_data_from_db(limit=1000):
    db = SessionLocal()
    try:
        # Get the most recent entries, then reverse for chronological order
        prices = db.query(BitcoinPrice).order_by(BitcoinPrice.timestamp.desc()).limit(limit).all()
        prices.reverse()  # Now oldest to newest for proper chart display
        if prices:
            df = pd.DataFrame([
                {
                    'timestamp': price.timestamp,
                    'price': price.price,
                    'volume_24h': price.volume_24h,
                    'market_cap': price.market_cap
                }
                for price in prices
            ])
            return df
        return pd.DataFrame()
    finally:
        db.close()

def get_current_price_from_api():
    try:
        bitcoin_service = BitcoinService()
        try:
            # Try to get existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, use asyncio.create_task() or run in thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, bitcoin_service.fetch_bitcoin_price())
                    price_data = future.result(timeout=10)
            else:
                price_data = loop.run_until_complete(bitcoin_service.fetch_bitcoin_price())
        except RuntimeError:
            # No event loop exists, create one
            price_data = asyncio.run(bitcoin_service.fetch_bitcoin_price())
        return price_data
    except Exception as e:
        print(f"Error fetching current price: {e}")
        return None

def create_price_chart(df, timezone_name=None):
    if df.empty:
        return go.Figure()
    
    # Convert timestamps to local timezone
    df_local = df.copy()
    try:
        if timezone_name and timezone_name != 'UTC':
            # Ensure timestamps are timezone-aware (assume UTC if naive)
            df_local['timestamp'] = pd.to_datetime(df_local['timestamp'], utc=True)
            # Convert to target timezone
            import pytz
            target_tz = pytz.timezone(timezone_name)
            df_local['timestamp'] = df_local['timestamp'].dt.tz_convert(target_tz)
        else:
            # Ensure UTC timezone is set
            df_local['timestamp'] = pd.to_datetime(df_local['timestamp'], utc=True)
    except Exception as e:
        print(f"Price chart timezone conversion error: {e}")
        # Fallback to UTC if conversion fails
        df_local['timestamp'] = pd.to_datetime(df_local['timestamp'], utc=True)
    
    fig = go.Figure()
    
    # Add price line
    fig.add_trace(go.Scatter(
        x=df_local['timestamp'],
        y=df_local['price'],
        mode='lines',
        name='Bitcoin Price',
        line=dict(color='#F7931A', width=2),
        hovertemplate='<b>Price: $%{y:,.2f}</b><br>Time: %{x}<extra></extra>'
    ))
    
    # Update layout to match CoinMarketCap style
    chart_title = f'Bitcoin Price Chart ({timezone_name if timezone_name else "UTC"})'
    fig.update_layout(
        title={
            'text': chart_title,
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'color': '#1f2937'}
        },
        xaxis=dict(
            title='Time',
            gridcolor='#e5e7eb',
            showgrid=True
        ),
        yaxis=dict(
            title='Price (USD)',
            gridcolor='#e5e7eb',
            showgrid=True,
            tickformat='$,.0f'
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='x unified',
        height=500
    )
    
    return fig

def create_volume_chart(df, timezone_name=None):
    if df.empty or 'volume_24h' not in df.columns:
        return go.Figure()
    
    # Convert timestamps to local timezone
    df_local = df.copy()
    try:
        if timezone_name and timezone_name != 'UTC':
            # Ensure timestamps are timezone-aware (assume UTC if naive)
            df_local['timestamp'] = pd.to_datetime(df_local['timestamp'], utc=True)
            # Convert to target timezone
            import pytz
            target_tz = pytz.timezone(timezone_name)
            df_local['timestamp'] = df_local['timestamp'].dt.tz_convert(target_tz)
        else:
            # Ensure UTC timezone is set
            df_local['timestamp'] = pd.to_datetime(df_local['timestamp'], utc=True)
    except Exception as e:
        print(f"Volume chart timezone conversion error: {e}")
        # Fallback to UTC if conversion fails
        df_local['timestamp'] = pd.to_datetime(df_local['timestamp'], utc=True)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df_local['timestamp'],
        y=df_local['volume_24h'],
        name='24h Volume',
        marker_color='#3b82f6',
        hovertemplate='<b>Volume: $%{y:,.0f}</b><br>Time: %{x}<extra></extra>'
    ))
    
    volume_title = f'24h Trading Volume ({timezone_name if timezone_name else "UTC"})'
    fig.update_layout(
        title={
            'text': volume_title,
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'color': '#1f2937'}
        },
        xaxis=dict(title='Time', gridcolor='#e5e7eb'),
        yaxis=dict(title='Volume (USD)', gridcolor='#e5e7eb', tickformat='$,.0f'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=300
    )
    
    return fig

# Main dashboard
st.markdown('<div class="main-header">📊 Crypto Analyser</div>', unsafe_allow_html=True)

# Sidebar controls
st.sidebar.header("Controls")
auto_refresh = st.sidebar.checkbox("Auto Refresh (60s)", value=st.session_state.auto_refresh)
st.session_state.auto_refresh = auto_refresh

refresh_button = st.sidebar.button("🔄 Refresh Now")
clear_data_button = st.sidebar.button("🗑️ Clear All Data", type="secondary")

st.sidebar.markdown("---")
stop_button = st.sidebar.button("🛑 Stop Application", type="primary", help="Gracefully shutdown the entire Bitcoin tracker application")

# Timezone selector
st.sidebar.header("🌍 Timezone Settings")
available_timezones = get_available_timezones()
try:
    current_index = available_timezones.index(st.session_state.selected_timezone)
except ValueError:
    current_index = 0

selected_timezone = st.sidebar.selectbox(
    "Select Timezone",
    available_timezones,
    index=current_index,
    help="Choose your local timezone for time display"
)

if selected_timezone != st.session_state.selected_timezone:
    st.session_state.selected_timezone = selected_timezone
    set_default_timezone(selected_timezone)
    st.rerun()

# Time range selector
st.sidebar.header("📊 Data Settings")
time_range = st.sidebar.selectbox(
    "Time Range",
    ["Last 100 points", "Last 500 points", "Last 1000 points", "All data"]
)

# Handle manual refresh
if refresh_button:
    st.session_state.last_refresh = time.time()  # Update timestamp to reset auto-refresh timer
    st.rerun()

# Handle clear data
if clear_data_button:
    try:
        response = requests.delete("http://localhost:8000/data/clear")
        if response.status_code == 200:
            st.sidebar.success("Data cleared successfully!")
        else:
            st.sidebar.error("Failed to clear data")
    except:
        st.sidebar.error("Could not connect to API")

# Handle stop application
if stop_button:
    st.session_state.stop_confirmation = True

if st.session_state.stop_confirmation:
    st.sidebar.warning("⚠️ Are you sure you want to stop the application?")
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("✅ Yes, Stop", key="confirm_stop"):
            try:
                st.sidebar.info("Shutting down application...")
                response = requests.post("http://localhost:8000/system/shutdown", timeout=5)
                if response.status_code == 200:
                    st.sidebar.success("Application stopped successfully!")
                    st.sidebar.info("You can close this browser tab now.")
                    st.stop()
                else:
                    st.sidebar.error("Failed to stop application")
            except requests.exceptions.Timeout:
                st.sidebar.success("Shutdown initiated (connection timed out as expected)")
                st.sidebar.info("You can close this browser tab now.")
                st.stop()
            except Exception as e:
                st.sidebar.error(f"Error stopping application: {e}")
    
    with col2:
        if st.button("❌ Cancel", key="cancel_stop"):
            st.session_state.stop_confirmation = False
            st.rerun()

# Set data limit based on selection
limit_map = {
    "Last 100 points": 100,
    "Last 500 points": 500,
    "Last 1000 points": 1000,
    "All data": None
}
data_limit = limit_map[time_range]

# Get current price (only when needed)
current_price_data = None
should_fetch_price = (
    refresh_button or 
    'current_price' not in st.session_state or
    (auto_refresh and time.time() - st.session_state.last_refresh >= 60)
)

if should_fetch_price:
    current_price_data = get_current_price_from_api()
    if current_price_data:
        st.session_state.current_price = current_price_data
else:
    current_price_data = st.session_state.get('current_price')

# Display current price card
if current_price_data:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="price-card">
            <h2>${current_price_data['price']:,.2f}</h2>
            <p>Current Bitcoin Price</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if current_price_data.get('market_cap'):
            st.markdown(f"""
            <div class="metric-card">
                <h3>${current_price_data['market_cap']:,.0f}</h3>
                <p>Market Cap</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        if current_price_data.get('volume_24h'):
            st.markdown(f"""
            <div class="metric-card">
                <h3>${current_price_data['volume_24h']:,.0f}</h3>
                <p>24h Volume</p>
            </div>
            """, unsafe_allow_html=True)

# Get historical data
df = get_price_data_from_db(data_limit)

if not df.empty:
    # Main price chart
    st.plotly_chart(create_price_chart(df, st.session_state.selected_timezone), use_container_width=True)
    
    # Statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Data Points", len(df))
    with col2:
        st.metric("Average Price", f"${df['price'].mean():,.2f}")
    with col3:
        st.metric("Min Price", f"${df['price'].min():,.2f}")
    with col4:
        st.metric("Max Price", f"${df['price'].max():,.2f}")
    
    # Volume chart (if available)
    if 'volume_24h' in df.columns and df['volume_24h'].notna().any():
        st.plotly_chart(create_volume_chart(df, st.session_state.selected_timezone), use_container_width=True)
    
    # Recent data table
    st.subheader(f"Recent Price Data ({st.session_state.selected_timezone})")
    recent_df = df.tail(10).copy()
    
    # Convert timestamps to local timezone for display
    if st.session_state.selected_timezone != 'UTC':
        try:
            # First ensure timestamps are timezone-aware (assume UTC if naive)
            recent_df['timestamp'] = pd.to_datetime(recent_df['timestamp'], utc=True)
            # Then convert to selected timezone
            import pytz
            target_tz = pytz.timezone(st.session_state.selected_timezone)
            recent_df['timestamp'] = recent_df['timestamp'].dt.tz_convert(target_tz)
        except Exception as e:
            print(f"Timezone conversion error: {e}")
            # Keep original timestamps if conversion fails
    
    recent_df['timestamp'] = recent_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    recent_df['price'] = recent_df['price'].apply(lambda x: f"${x:,.2f}")
    if 'volume_24h' in recent_df.columns:
        recent_df['volume_24h'] = recent_df['volume_24h'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A")
    st.dataframe(recent_df.iloc[::-1], use_container_width=True)

else:
    st.warning("No historical data available. Start the data collection service first!")
    st.info("Run `python run.py` to start collecting crypto price data.")

# Auto refresh with proper timing
if auto_refresh:
    current_time = time.time()
    time_since_last = current_time - st.session_state.last_refresh
    
    if time_since_last >= 60:  # 60 seconds interval
        st.session_state.last_refresh = current_time
        st.rerun()
    else:
        # Show countdown to next refresh
        time_remaining = 60 - time_since_last
        st.sidebar.info(f"Auto-refresh in: {int(time_remaining)} seconds")
        
        # Sleep for the remaining time, then refresh
        time.sleep(min(time_remaining, 5))  # Cap at 5 seconds to avoid long waits
        st.rerun()

# Footer
st.markdown("---")
st.markdown("**Data Source:** CoinGecko API | **Collection Rate:** 60 seconds | **Auto-refresh:** 60 seconds (when enabled)")