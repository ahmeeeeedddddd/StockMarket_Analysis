# shared/constants.py

from enum import Enum

# ---------------------------------------------------------------------------
# Tracked symbols
# ---------------------------------------------------------------------------
SYMBOLS: list[str] = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "TSLA", "META", "JPM", "SPY", "QQQ",
]

# ---------------------------------------------------------------------------
# Kafka topic names
# ---------------------------------------------------------------------------
class Topics(str, Enum):
    TICKS       = "ticks"
    AGGREGATES  = "aggregates"
    ALERTS      = "alerts"

# ---------------------------------------------------------------------------
# Consumer group IDs  (one per service so offsets are tracked independently)
# ---------------------------------------------------------------------------
class ConsumerGroups(str, Enum):
    PROCESSING        = "processing-group"
    ANOMALY_DETECTION = "anomaly-detection-group"
    ALERTS            = "alerts-group"

# ---------------------------------------------------------------------------
# Stream-processing window sizes (seconds)
# ---------------------------------------------------------------------------
class WindowSizes(int, Enum):
    ONE_MIN    = 60
    FIVE_MIN   = 300
    FIFTEEN_MIN = 900

# ---------------------------------------------------------------------------
# Anomaly-detection thresholds
# ---------------------------------------------------------------------------
ZSCORE_VOLUME_THRESHOLD: float  = 3.0   # std-devs above mean volume
PRICE_JUMP_STD_THRESHOLD: float = 3.0   # std-devs for sudden price move
BOLLINGER_PERIOD: int           = 20    # candles for Bollinger Band calc
BOLLINGER_STD_MULT: float       = 2.0   # band width multiplier

# ---------------------------------------------------------------------------
# TimescaleDB chunk interval  (used when creating hypertables)
# ---------------------------------------------------------------------------
TIMESCALE_CHUNK_INTERVAL: str = "1 day"

# ---------------------------------------------------------------------------
# Alert severity levels
# ---------------------------------------------------------------------------
class AlertSeverity(str, Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"

# ---------------------------------------------------------------------------
# Alert type identifiers  (used in schema.py AlertEvent)
# ---------------------------------------------------------------------------
class AlertType(str, Enum):
    BOLLINGER_BREACH   = "bollinger_breach"
    ZSCORE_VOLUME_SPIKE = "zscore_volume_spike"
    PRICE_JUMP         = "price_jump"