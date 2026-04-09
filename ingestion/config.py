# ingestion/config.py
"""
Central configuration for the ingestion service.

All tuneable knobs live here so nothing is hardcoded in business logic.
Sensitive values (API keys) are read from environment variables so they
never appear in source control.
"""

import os
from dataclasses import dataclass, field
from typing import List

from shared.constants import SYMBOLS
from shared.kafka_config import KAFKA_CONFIG


# ---------------------------------------------------------------------------
# API credentials  (set these in your shell or .env before running)
# ---------------------------------------------------------------------------

POLYGON_API_KEY: str = os.getenv("POLYGON_API_KEY", "")
ALPHA_VANTAGE_API_KEY: str = os.getenv("ALPHA_VANTAGE_API_KEY", "")


# ---------------------------------------------------------------------------
# Symbols to track
# ---------------------------------------------------------------------------

TRACKED_SYMBOLS: List[str] = SYMBOLS   # defined once in shared/constants.py


# ---------------------------------------------------------------------------
# Polygon WebSocket
# ---------------------------------------------------------------------------

POLYGON_WS_URL: str = "wss://socket.polygon.io/stocks"

# How long to wait (seconds) before attempting a reconnect
POLYGON_RECONNECT_DELAY: float = 5.0

# Maximum number of reconnect attempts before giving up (0 = infinite)
POLYGON_MAX_RECONNECTS: int = 0


# ---------------------------------------------------------------------------
# Alpha Vantage REST
# ---------------------------------------------------------------------------

ALPHA_VANTAGE_BASE_URL: str = "https://www.alphavantage.co/query"

# Polling interval in seconds between REST calls (free tier: 5 req / min)
ALPHA_VANTAGE_POLL_INTERVAL: float = 15.0

# Number of retries on HTTP errors before skipping a cycle
ALPHA_VANTAGE_MAX_RETRIES: int = 3

# Seconds between retry attempts
ALPHA_VANTAGE_RETRY_DELAY: float = 2.0


# ---------------------------------------------------------------------------
# Kafka — re-exported from shared so ingestion only imports from this file
# ---------------------------------------------------------------------------

KAFKA_BOOTSTRAP_SERVERS: str = KAFKA_CONFIG.bootstrap_servers
KAFKA_TICKS_TOPIC: str       = KAFKA_CONFIG.topic_ticks

KAFKA_PRODUCER_ACKS: str     = KAFKA_CONFIG.producer_acks
KAFKA_PRODUCER_RETRIES: int  = KAFKA_CONFIG.producer_retries
KAFKA_LINGER_MS: int         = KAFKA_CONFIG.producer_linger_ms
KAFKA_BATCH_SIZE: int        = KAFKA_CONFIG.producer_batch_size


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
