import sys
import os
# Add the parent directory (project root) to the python path so we can import 'shared'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import time
from datetime import datetime

# Import dashboard components
from db_queries import get_candlesticks, get_recent_alerts, get_latest_price
from charts import create_main_chart
from alert_panel import render_alert_panel

# Must be the first Streamlit command
st.set_page_config(
    page_title="Stock Market Live Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for overall theme
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #0e1117;
    }
    /* Metric styling */
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
        color: #00e676; /* Bright green for positive vibe, adjust dynamically if needed */
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar Configuration
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Dashboard Controls")
    
    # Constants from shared/constants.py (could be imported dynamically)
    SYMBOLS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "JPM", "SPY", "QQQ"]
    selected_symbol = st.selectbox("Select Symbol", options=["ALL"] + SYMBOLS, index=1)
    
    window_options = {
        "1 Minute": 60,
        "5 Minutes": 300,
        "15 Minutes": 900
    }
    selected_window_label = st.selectbox("Time Window", options=list(window_options.keys()))
    selected_window_sec = window_options[selected_window_label]
    
    st.markdown("---")
    auto_refresh = st.checkbox("Auto-Refresh", value=True)
    refresh_rate = st.slider("Refresh Interval (seconds)", min_value=1, max_value=60, value=5)
    
    st.markdown("---")
    st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

# ---------------------------------------------------------------------------
# Main Layout
# ---------------------------------------------------------------------------
st.title(f"📈 Real-Time Market Analysis: {selected_symbol if selected_symbol != 'ALL' else 'Market Overview'}")

# Top Row: Latest Price / Stats (Only if a specific symbol is selected)
if selected_symbol != "ALL":
    try:
        latest_tick = get_latest_price(selected_symbol)
        if latest_tick:
            st.metric(
                label=f"{selected_symbol} Last Price",
                value=f"${latest_tick['price']:.2f}",
                delta="Live"
            )
    except Exception as e:
        st.error(f"Error fetching price: {e}")

# Main Content: Split into 2 columns (Charts 70%, Alerts 30%)
col_chart, col_alerts = st.columns([7, 3])

with col_chart:
    if selected_symbol == "ALL":
        st.info("Please select a specific symbol from the sidebar to view the candlestick and VWAP charts.")
    else:
        try:
            # Fetch data and render chart
            df_candles = get_candlesticks(selected_symbol, selected_window_sec, limit=100)
            fig = create_main_chart(df_candles, selected_symbol)
            # Use use_container_width to fill the column
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        except Exception as e:
            st.error(f"Error generating chart: {e}")

with col_alerts:
    try:
        # Fetch and render alerts
        df_alerts = get_recent_alerts(symbol=None if selected_symbol == "ALL" else selected_symbol, limit=20)
        render_alert_panel(df_alerts)
    except Exception as e:
        st.error(f"Error fetching alerts: {e}")

# ---------------------------------------------------------------------------
# Auto-Refresh Logic
# ---------------------------------------------------------------------------
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()
