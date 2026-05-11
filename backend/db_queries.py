import pandas as pd
import numpy as np
from shared.db_client import execute_query
from shared.constants import SYMBOLS

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
    return {}

def get_candlesticks(symbol: str, window_sec: int, limit: int = 100) -> pd.DataFrame:
    # Left join with alerts to get any anomalies that triggered during this candlestick window
    sql = """
        SELECT a.time, a.open, a.high, a.low, a.close, a.volume, a.vwap, a.trade_count,
               al.alert_type as anomaly_type, al.severity, al.trigger_price as anomaly_value
        FROM aggregates a
        LEFT JOIN alerts al 
          ON a.symbol = al.symbol 
         AND al.time >= a.time 
         AND al.time < a.time + (INTERVAL '1 second' * %s)
        WHERE a.symbol = %s AND a.window_sec = %s
        ORDER BY a.time DESC
        LIMIT %s
    """
    rows = execute_query(sql, (window_sec, symbol, window_sec, limit))
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(by="time").reset_index(drop=True)
        if 'severity' in df.columns:
            df['severity'] = df['severity'].fillna('normal')
        else:
            df['severity'] = 'normal'
            df['anomaly_type'] = None
            df['anomaly_value'] = None
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
    return df

def get_heatmap_data(limit: int = 20) -> list:
    # Top 6 stocks for heatmap
    stocks = SYMBOLS[:6] if len(SYMBOLS) >= 6 else SYMBOLS
    heatmap = []
    
    for symbol in stocks:
        sql = """
            SELECT a.time, a.close, al.severity
            FROM aggregates a
            LEFT JOIN alerts al 
              ON a.symbol = al.symbol 
             AND al.time >= a.time 
             AND al.time < a.time + INTERVAL '1 minute'
            WHERE a.symbol = %s AND a.window_sec = 60
            ORDER BY a.time DESC
            LIMIT %s
        """
        rows = execute_query(sql, (symbol, limit))
        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.sort_values(by="time").reset_index(drop=True)
            if 'severity' in df.columns:
                df['severity'] = df['severity'].fillna('normal')
            else:
                df['severity'] = 'normal'
            
            timeline = [{"time": str(row['time']), "severity": row['severity']} for _, row in df.iterrows()]
            heatmap.append({
                "symbol": symbol,
                "timeline": timeline
            })
    return heatmap

def get_deep_dive_data(symbol: str) -> dict:
    # Similar to candlesticks but hardcoded to 5m windows and calculates Z-scores for the UI chart
    sql = """
        SELECT a.time, a.open, a.high, a.low, a.close, a.volume,
               al.alert_type as anomaly_type, al.severity
        FROM aggregates a
        LEFT JOIN alerts al 
          ON a.symbol = al.symbol 
         AND al.time >= a.time 
         AND al.time < a.time + INTERVAL '5 minutes'
        WHERE a.symbol = %s AND a.window_sec = 300
        ORDER BY a.time DESC
        LIMIT 100
    """
    rows = execute_query(sql, (symbol,))
    df = pd.DataFrame(rows)
    if df.empty:
        return {}
    
    df = df.sort_values(by="time").reset_index(drop=True)
    if 'severity' in df.columns:
        df['severity'] = df['severity'].fillna('normal')
    else:
        df['severity'] = 'normal'
    
    period = 20
    df['ma'] = df['close'].rolling(window=period).mean()
    df['std'] = df['close'].rolling(window=period).std()
    df['upper'] = df['ma'] + (df['std'] * 2)
    df['lower'] = df['ma'] - (df['std'] * 2)
    
    df['z_score'] = (df['close'] - df['ma']) / df['std']
    df = df.replace({np.nan: None})
    
    historical = df[df['severity'] != 'normal'].tail(5).to_dict(orient='records')
    
    return {
        "symbol": symbol,
        "candles": df.to_dict(orient='records'),
        "historical": historical
    }
