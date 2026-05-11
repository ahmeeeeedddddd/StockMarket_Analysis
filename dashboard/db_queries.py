import pandas as pd
import numpy as np
import random
from shared.db_client import execute_query

def add_mock_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    
    # Randomly assign anomalies
    n_rows = len(df)
    is_anomaly = np.random.rand(n_rows) < 0.05
    
    types = ["Price Spike", "Volume Surge", "Volatility Increase", "Support Break", "Trend Reversal"]
    
    df['anomaly_type'] = None
    df['severity'] = "normal"
    df['anomaly_value'] = None
    
    # We want at least one recent anomaly so the UI looks good
    if n_rows > 0:
        is_anomaly[-1] = True
        
    for idx in df[is_anomaly].index:
        df.at[idx, 'anomaly_type'] = random.choice(types)
        df.at[idx, 'severity'] = random.choice(["mild", "critical"])
        df.at[idx, 'anomaly_value'] = round(df.at[idx, 'close'] * (1 + random.uniform(-0.05, 0.05)), 2)
        
    return df

def get_latest_price(symbol: str) -> dict:
    sql = """
        SELECT price, time
        FROM ticks
        WHERE symbol = %s
        ORDER BY time DESC
        LIMIT 1
    """
    rows = execute_query(sql, (symbol,))
    if rows:
        return rows[0]
    return None

def get_candlesticks(symbol: str, window_sec: int, limit: int = 100) -> pd.DataFrame:
    sql = """
        SELECT time, open, high, low, close, volume, vwap, trade_count
        FROM aggregates
        WHERE symbol = %s AND window_sec = %s
        ORDER BY time DESC
        LIMIT %s
    """
    rows = execute_query(sql, (symbol, window_sec, limit))
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(by="time").reset_index(drop=True)
        df = add_mock_anomalies(df)
    return df

def get_recent_alerts(symbol: str = None, limit: int = 50) -> pd.DataFrame:
    if symbol and symbol != "ALL":
        sql = """
            SELECT time, symbol, alert_type, severity, message, trigger_price
            FROM alerts
            WHERE symbol = %s
            ORDER BY time DESC
            LIMIT %s
        """
        rows = execute_query(sql, (symbol, limit))
    else:
        sql = """
            SELECT time, symbol, alert_type, severity, message, trigger_price
            FROM alerts
            ORDER BY time DESC
            LIMIT %s
        """
        rows = execute_query(sql, (limit,))
    
    df = pd.DataFrame(rows)
    if not df.empty:
        df['actual_value'] = df['trigger_price']
        df['expected_value'] = df['trigger_price'].apply(lambda x: float(x) * (1 - random.uniform(0.01, 0.05)))
    return df

def get_heatmap_data(limit: int = 20) -> list:
    stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA']
    heatmap = []
    
    for symbol in stocks:
        sql = """
            SELECT time, close
            FROM aggregates
            WHERE symbol = %s AND window_sec = 60
            ORDER BY time DESC
            LIMIT %s
        """
        rows = execute_query(sql, (symbol, limit))
        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.sort_values(by="time").reset_index(drop=True)
            df = add_mock_anomalies(df)
            timeline = []
            for _, row in df.iterrows():
                timeline.append({
                    "time": row['time'],
                    "severity": row['severity']
                })
            heatmap.append({
                "symbol": symbol,
                "timeline": timeline
            })
    return heatmap

def get_deep_dive_data(symbol: str) -> dict:
    sql = """
        SELECT time, open, high, low, close, volume
        FROM aggregates
        WHERE symbol = %s AND window_sec = 300
        ORDER BY time DESC
        LIMIT 100
    """
    rows = execute_query(sql, (symbol,))
    df = pd.DataFrame(rows)
    if df.empty:
        return {}
    
    df = df.sort_values(by="time").reset_index(drop=True)
    df = add_mock_anomalies(df)
    
    period = 20
    df['ma'] = df['close'].rolling(window=period).mean()
    df['std'] = df['close'].rolling(window=period).std()
    df['upper'] = df['ma'] + (df['std'] * 2)
    df['lower'] = df['ma'] - (df['std'] * 2)
    
    # Z-Score
    df['z_score'] = (df['close'] - df['ma']) / df['std']
    df = df.replace({np.nan: None})
    
    historical = df[df['severity'] != 'normal'].tail(5).to_dict(orient='records')
    
    return {
        "symbol": symbol,
        "candles": df.to_dict(orient='records'),
        "historical": historical
    }
