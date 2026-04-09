# shared/schema.py

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Optional


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BaseEvent:
    """All Kafka events inherit from this. frozen=True makes them immutable."""

    event_id:  str    # UUID4 — set by the publisher
    timestamp: float  # Unix epoch seconds (UTC)
    symbol:    str    # Ticker, e.g. "AAPL"

    def __post_init__(self):
        if not self.event_id or not isinstance(self.event_id, str):
            raise ValueError("event_id must be a non-empty string")
        if self.timestamp <= 0:
            raise ValueError("timestamp must be a positive Unix epoch value")
        if not self.symbol or not isinstance(self.symbol, str):
            raise ValueError("symbol must be a non-empty string")
        # frozen=True blocks normal assignment, so we use object.__setattr__
        object.__setattr__(self, "symbol", self.symbol.strip().upper())


# ---------------------------------------------------------------------------
# Topic: ticks
# Published by:  Person 1 (ingestion/)
# Consumed by:   Person 3 (processing/), Person 4 (anomaly_detection/)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TickEvent(BaseEvent):
    """
    A single raw trade tick from Alpha Vantage or Polygon.io.

    JSON example
    ------------
    {
        "event_id":  "3f2a1b4c-...",
        "timestamp": 1710000000.123,
        "symbol":    "AAPL",
        "price":     182.45,
        "volume":    1200,
        "bid":       182.44,
        "ask":       182.46,
        "source":    "polygon"
    }
    """

    price:  float           = 0.0
    volume: int             = 0
    source: str             = ""
    bid:    Optional[float] = None
    ask:    Optional[float] = None

    def __post_init__(self):
        super().__post_init__()
        if self.price <= 0:
            raise ValueError(f"price must be > 0, got {self.price}")
        if self.volume < 0:
            raise ValueError(f"volume must be >= 0, got {self.volume}")
        if not self.source:
            raise ValueError("source must be a non-empty string")
        if self.bid is not None and self.bid <= 0:
            raise ValueError(f"bid must be > 0, got {self.bid}")
        if self.ask is not None and self.ask <= 0:
            raise ValueError(f"ask must be > 0, got {self.ask}")
        if self.bid is not None and self.ask is not None:
            if self.bid > self.ask:
                raise ValueError(f"bid ({self.bid}) cannot exceed ask ({self.ask})")


# ---------------------------------------------------------------------------
# Topic: aggregates
# Published by:  Person 3 (processing/)
# Consumed by:   Person 4 (anomaly_detection/), Person 6 (dashboard/)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AggregateEvent(BaseEvent):
    """
    A completed OHLCV candlestick or VWAP aggregate for a given window.

    JSON example
    ------------
    {
        "event_id":      "7a9c2d1e-...",
        "timestamp":     1710000060.0,
        "symbol":        "AAPL",
        "window_sec":    60,
        "open":          182.10,
        "high":          182.80,
        "low":           181.90,
        "close":         182.45,
        "volume":        48200,
        "vwap":          182.38,
        "trade_count":   312,
        "window_start":  1710000000.0,
        "window_end":    1710000060.0
    }
    """

    window_sec:   int   = 0
    open:         float = 0.0
    high:         float = 0.0
    low:          float = 0.0
    close:        float = 0.0
    volume:       int   = 0
    vwap:         float = 0.0
    trade_count:  int   = 0
    window_start: float = 0.0
    window_end:   float = 0.0

    def __post_init__(self):
        super().__post_init__()
        for name, val in [("open", self.open), ("high", self.high),
                          ("low", self.low),   ("close", self.close),
                          ("vwap", self.vwap)]:
            if val <= 0:
                raise ValueError(f"{name} must be > 0, got {val}")
        if self.volume < 0:
            raise ValueError(f"volume must be >= 0, got {self.volume}")
        if self.trade_count < 0:
            raise ValueError(f"trade_count must be >= 0, got {self.trade_count}")
        if self.window_sec <= 0:
            raise ValueError(f"window_sec must be > 0, got {self.window_sec}")
        if self.low > self.high:
            raise ValueError(f"low ({self.low}) cannot exceed high ({self.high})")
        if not (self.low <= self.open <= self.high):
            raise ValueError("open must be between low and high")
        if not (self.low <= self.close <= self.high):
            raise ValueError("close must be between low and high")
        if self.window_start >= self.window_end:
            raise ValueError("window_start must be before window_end")


# ---------------------------------------------------------------------------
# Topic: alerts
# Published by:  Person 4 (anomaly_detection/)
# Consumed by:   Person 5 (alerts/), Person 6 (dashboard/)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AlertEvent(BaseEvent):
    """
    An anomaly alert fired by the detection engine.

    JSON example
    ------------
    {
        "event_id":        "c1d2e3f4-...",
        "timestamp":       1710000300.0,
        "symbol":          "AAPL",
        "alert_type":      "bollinger_breach",
        "severity":        "high",
        "message":         "Price closed above upper Bollinger Band",
        "trigger_price":   185.20,
        "trigger_volume":  null,
        "zscore":          null,
        "reference_value": 183.90,
        "window_sec":      300
    }
    """

    alert_type:      str            = ""
    severity:        str            = ""
    message:         str            = ""
    trigger_price:   Optional[float] = None
    trigger_volume:  Optional[int]   = None
    zscore:          Optional[float] = None
    reference_value: Optional[float] = None
    window_sec:      Optional[int]   = None

    def __post_init__(self):
        super().__post_init__()
        if not self.alert_type:
            raise ValueError("alert_type must be a non-empty string")
        if not self.severity:
            raise ValueError("severity must be a non-empty string")
        if not self.message:
            raise ValueError("message must be a non-empty string")
        if self.trigger_price is not None and self.trigger_price <= 0:
            raise ValueError(f"trigger_price must be > 0, got {self.trigger_price}")
        if self.trigger_volume is not None and self.trigger_volume < 0:
            raise ValueError(f"trigger_volume must be >= 0, got {self.trigger_volume}")
        if self.window_sec is not None and self.window_sec <= 0:
            raise ValueError(f"window_sec must be > 0, got {self.window_sec}")


# ---------------------------------------------------------------------------
# Serialisation helpers — used by every module's Kafka producer/consumer
# ---------------------------------------------------------------------------

def serialize(event: BaseEvent) -> bytes:
    """Serialize any event dataclass to UTF-8 JSON bytes for Kafka."""
    return json.dumps(asdict(event)).encode("utf-8")


def _deserialize_raw(raw: bytes) -> dict:
    return json.loads(raw.decode("utf-8"))


def deserialize_tick(raw: bytes) -> TickEvent:
    return TickEvent(**_deserialize_raw(raw))


def deserialize_aggregate(raw: bytes) -> AggregateEvent:
    return AggregateEvent(**_deserialize_raw(raw))


def deserialize_alert(raw: bytes) -> AlertEvent:
    return AlertEvent(**_deserialize_raw(raw))