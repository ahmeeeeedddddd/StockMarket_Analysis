import streamlit as st
import pandas as pd

def render_alert_panel(alerts_df: pd.DataFrame):
    """
    Renders the recent alerts feed in the Streamlit app.
    """
    st.subheader("🚨 Live Alerts Feed")
    
    if alerts_df.empty:
        st.info("No recent alerts.")
        return

    # Custom CSS for styling the alerts
    st.markdown("""
    <style>
    .alert-card {
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
        border-left: 5px solid;
        background-color: #1e1e1e;
        color: #ffffff;
    }
    .alert-high { border-color: #ff4b4b; }
    .alert-medium { border-color: #ffa421; }
    .alert-low { border-color: #29b5e8; }
    
    .alert-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 8px;
        font-size: 0.9em;
        color: #aaaaaa;
    }
    .alert-symbol {
        font-weight: bold;
        color: #ffffff;
        font-size: 1.1em;
    }
    .alert-type {
        font-family: monospace;
        background: #333333;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.8em;
    }
    .alert-message {
        font-size: 1em;
    }
    .alert-price {
        font-weight: bold;
        color: #ffca28;
    }
    </style>
    """, unsafe_allow_html=True)

    for _, row in alerts_df.iterrows():
        severity = row['severity'].lower()
        
        # Determine CSS class based on severity
        if severity == 'high':
            css_class = 'alert-high'
            icon = '🔴'
        elif severity == 'medium':
            css_class = 'alert-medium'
            icon = '🟡'
        else:
            css_class = 'alert-low'
            icon = '🔵'

        # Format time safely
        time_str = row['time'].strftime('%H:%M:%S') if pd.notnull(row['time']) else 'Unknown Time'
        
        # Price formatting
        price_str = f"@ ${row['trigger_price']:.2f}" if pd.notnull(row['trigger_price']) else ""

        html = f"""
        <div class="alert-card {css_class}">
            <div class="alert-header">
                <span>{icon} <span class="alert-symbol">{row['symbol']}</span> {price_str}</span>
                <span>{time_str}</span>
            </div>
            <div>
                <span class="alert-type">{row['alert_type']}</span>
            </div>
            <div class="alert-message" style="margin-top: 8px;">
                {row['message']}
            </div>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)
