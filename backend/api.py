import sys
import os
import math
import numpy as np

# Add the parent directory to path so we can import dashboard and shared
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from backend.db_queries import (
    get_latest_price,
    get_candlesticks,
    get_recent_alerts,
    get_heatmap_data,
    get_deep_dive_data,
    get_alert_rules,
    add_alert_rule,
    delete_alert_rule,
    get_system_health
)


app = FastAPI(title="StockPulse API")

# Setup CORS to allow the frontend to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def clean_dataframe(df):
    """Convert pandas DataFrame to a list of dicts, replacing NaN with None."""
    if df is None or df.empty:
        return []
    df = df.replace({np.nan: None})
    return df.to_dict(orient="records")

@app.get("/api/price/{symbol}")
def api_get_latest_price(symbol: str):
    try:
        data = get_latest_price(symbol)
        if not data:
            raise HTTPException(status_code=404, detail="Symbol not found or no data")
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/candlesticks")
def api_get_candlesticks(symbol: str, window_sec: int, limit: int = 100):
    try:
        df = get_candlesticks(symbol, window_sec, limit)
        return clean_dataframe(df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alerts")
def api_get_recent_alerts(symbol: Optional[str] = None, limit: int = 50):
    try:
        df = get_recent_alerts(symbol, limit)
        return clean_dataframe(df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/heatmap")
def api_get_heatmap():
    try:
        data = get_heatmap_data()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/deep-dive/{symbol}")
def api_get_deep_dive(symbol: str):
    try:
        data = get_deep_dive_data(symbol)
        if not data:
            raise HTTPException(status_code=404, detail="Symbol not found")
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/rules")
def api_get_rules():
    try:
        return get_alert_rules()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rules")
def api_add_rule(rule: dict):
    try:
        rule_id = add_alert_rule(
            rule['symbol'], 
            rule['rule_type'], 
            rule['threshold'], 
            rule.get('window_sec', 60)
        )
        return {"id": rule_id, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/rules/{rule_id}")
def api_delete_rule(rule_id: int):
    try:
        delete_alert_rule(rule_id)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
def api_get_health():
    try:
        data = get_system_health()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
