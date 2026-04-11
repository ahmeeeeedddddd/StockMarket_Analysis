# ingestion/main.py
"""
Ingestion service entry point — Person 1.

What this does
--------------
1. Starts a YFinance poller in a background daemon thread.
2. The source uses a single TickKafkaProducer and calls its .send() method.
3. Runs until SIGINT / SIGTERM, then shuts down cleanly (flush + close).

How to run
----------
    python -m ingestion.main          # from repo root

Environment variables
---------------------
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

from ingestion.config import LOG_LEVEL
from ingestion.kafka_producer import TickKafkaProducer
from ingestion.yfinance_client import YFinanceClient

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
# Graceful shutdown
# ---------------------------------------------------------------------------

_yf_client: YFinanceClient | None = None
_producer: TickKafkaProducer | None = None


def _shutdown(signum, frame) -> None:  # noqa: ANN001
    """SIGINT / SIGTERM handler — stop clients and flush Kafka."""
    logger.info("Shutdown signal received (sig=%d). Stopping …", signum)

    if _yf_client:
        _yf_client.stop()
    if _producer:
        _producer.close()

    logger.info("Ingestion service stopped cleanly.")
    sys.exit(0)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    global _yf_client, _producer  # noqa: PLW0603

    # Register shutdown handlers
    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    # Shared Kafka producer
    _producer = TickKafkaProducer()

    # ---- YFinance poller thread ------------------------------------------
    _yf_client = YFinanceClient(on_tick=_producer.send)
    yf_thread = threading.Thread(
        target=_yf_client.run_forever,
        name="yfinance-poller",
        daemon=True,
    )
    yf_thread.start()
    logger.info("YFinance poller thread started.")

    # ---- Keep the main thread alive --------------------------------------
    logger.info("Ingestion service running. Press Ctrl+C to stop.")
    yf_thread.join()


if __name__ == "__main__":
    main()
