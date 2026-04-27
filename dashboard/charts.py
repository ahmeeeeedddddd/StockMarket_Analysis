import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

def create_main_chart(df: pd.DataFrame, symbol: str) -> go.Figure:
    """
    Creates a premium dark-themed candlestick chart with a VWAP overlay
    and volume bars in a subplot.
    """
    if df.empty:
        # Return an empty figure with a message if no data
        fig = go.Figure()
        fig.update_layout(
            template="plotly_dark",
            title=f"No data available for {symbol}",
            plot_bgcolor='rgba(17,17,17,1)',
            paper_bgcolor='rgba(17,17,17,1)'
        )
        return fig

    # Create subplots: Candlestick (top) and Volume (bottom)
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.03, 
        subplot_titles=(f"{symbol} Price & VWAP", "Volume"),
        row_width=[0.2, 0.7] # 20% volume, 70% price (remaining 10% spacing)
    )

    # 1. Candlestick Trace
    fig.add_trace(
        go.Candlestick(
            x=df['time'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='Price',
            increasing_line_color='#26a69a', # Premium Teal
            decreasing_line_color='#ef5350'  # Premium Red
        ),
        row=1, col=1
    )

    # 2. VWAP Trace
    fig.add_trace(
        go.Scatter(
            x=df['time'],
            y=df['vwap'],
            mode='lines',
            name='VWAP',
            line=dict(color='#ffca28', width=2) # Premium Amber
        ),
        row=1, col=1
    )

    # 3. Volume Trace (Color-coded based on close vs open)
    colors = ['#26a69a' if row['close'] >= row['open'] else '#ef5350' for index, row in df.iterrows()]
    fig.add_trace(
        go.Bar(
            x=df['time'],
            y=df['volume'],
            name='Volume',
            marker_color=colors,
            opacity=0.8
        ),
        row=2, col=1
    )

    # Apply Premium Dark Layout
    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor='#111111',  # Deep dark gray
        paper_bgcolor='#111111',
        margin=dict(l=40, r=40, t=40, b=40),
        xaxis_rangeslider_visible=False,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode="x unified"
    )
    
    # Grid styling
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#333333')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#333333')

    return fig
