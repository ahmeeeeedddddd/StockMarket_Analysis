# ingestion/main.py
"""
Ingestion service entry point — Person 1.

What this does
--------------
1. Validates that API keys are present in the environment.
2. Starts a Polygon.io WebSocket listener in a background daemon thread.
3. Starts an Alpha Vantage REST poller in a second background daemon thread.
4. Both sources share a single TickKafkaProducer and call its .send() method.
5. Runs until SIGINT / SIGTERM, then shuts down cleanly (flush + close).

How to run
----------
    export POLYGON_API_KEY="your_key"
    export ALPHA_VANTAGE_API_KEY="your_key"
    python -m ingestion.main          # from repo root

Environment variables
---------------------
POLYGON_API_KEY       — required: Polygon.io API key
ALPHA_VANTAGE_API_KEY — required: Alpha Vantage API key
LOG_LEVEL             — optional: DEBUG | INFO (default) | WARNING | ERROR
"""

import logging
import signal
import sys
import threading
from pathlib import Path

from dotenv import load_dotenv

# Load .env from repo root (D:\StockMarket_Analysis\.env)
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

from ingestion.config import (
    POLYGON_API_KEY,
    ALPHA_VANTAGE_API_KEY,
    LOG_LEVEL,
)
from ingestion.kafka_producer import TickKafkaProducer
from ingestion.polygon_ws import PolygonWebSocketClient
from ingestion.alpha_vantage import AlphaVantageClient

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Startup validation
# ---------------------------------------------------------------------------

def _validate_env() -> None:
    """Crash early with a clear message if API keys are missing."""
    missing = []
    if not POLYGON_API_KEY:
        missing.append("POLYGON_API_KEY")
    if not ALPHA_VANTAGE_API_KEY:
        missing.append("ALPHA_VANTAGE_API_KEY")
    if missing:
        logger.critical(
            "Missing required environment variable(s): %s. "
            "Set them and restart.",
            ", ".join(missing),
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# Graceful shutdown
# ---------------------------------------------------------------------------

_polygon_client: PolygonWebSocketClient | None = None
_av_client: AlphaVantageClient | None = None
_producer: TickKafkaProducer | None = None


def _shutdown(signum, frame) -> None:  # noqa: ANN001
    """SIGINT / SIGTERM handler — stop clients and flush Kafka."""
    logger.info("Shutdown signal received (sig=%d). Stopping …", signum)

    if _polygon_client:
        _polygon_client.stop()
    if _av_client:
        _av_client.stop()
    if _producer:
        _producer.close()

    logger.info("Ingestion service stopped cleanly.")
    sys.exit(0)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    global _polygon_client, _av_client, _producer  # noqa: PLW0603

    _validate_env()

    # Register shutdown handlers
    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    # Shared Kafka producer
    _producer = TickKafkaProducer()

    # ---- Polygon WebSocket thread ----------------------------------------
    _polygon_client = PolygonWebSocketClient(on_tick=_producer.send)
    polygon_thread = threading.Thread(
        target=_polygon_client.run_forever,
        name="polygon-ws",
        daemon=True,
    )
    polygon_thread.start()
    logger.info("Polygon WebSocket thread started.")

    # ---- Alpha Vantage poller thread -------------------------------------
    _av_client = AlphaVantageClient(on_tick=_producer.send)
    av_thread = threading.Thread(
        target=_av_client.run_forever,
        name="alpha-vantage-poller",
        daemon=True,
    )
    av_thread.start()
    logger.info("Alpha Vantage poller thread started.")

    # ---- Keep the main thread alive --------------------------------------
    logger.info("Ingestion service running. Press Ctrl+C to stop.")
    polygon_thread.join()
    av_thread.join()


if __name__ == "__main__":
    main()
