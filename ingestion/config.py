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
# API credentials
# ---------------------------------------------------------------------------
# `yfinance` does not require API keys for its public endpoints.


# ---------------------------------------------------------------------------
# Symbols to track
# ---------------------------------------------------------------------------

TRACKED_SYMBOLS: List[str] = SYMBOLS   # defined once in shared/constants.py


# ---------------------------------------------------------------------------
# YFinance
# ---------------------------------------------------------------------------

# Polling interval in seconds between data fetches
YFINANCE_POLL_INTERVAL: float = 5.0


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
