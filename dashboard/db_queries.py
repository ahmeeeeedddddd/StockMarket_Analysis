import pandas as pd
from shared.db_client import execute_query

def get_latest_price(symbol: str) -> dict:
    """
    Fetch the most recent tick for the given symbol to get the current price.
    """
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
    """
    Fetch the latest candlestick aggregates for a symbol and window size.
    Returns a pandas DataFrame sorted by time ascending (for plotting).
    """
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
        # Sort by time ascending for charts
        df = df.sort_values(by="time").reset_index(drop=True)
    return df

def get_recent_alerts(symbol: str = None, limit: int = 50) -> pd.DataFrame:
    """
    Fetch recent alerts. If symbol is provided, filters by symbol.
    Returns a pandas DataFrame.
    """
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
    
    return pd.DataFrame(rows)
