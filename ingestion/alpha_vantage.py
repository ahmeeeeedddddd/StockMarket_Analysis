# ingestion/alpha_vantage.py
"""
Alpha Vantage REST client for real-time (polling) tick data.

Responsibilities
----------------
- Poll the Alpha Vantage GLOBAL_QUOTE endpoint for every tracked symbol.
- Respect the free-tier rate limit (5 requests / minute → 12 s gap per call).
- Handle HTTP errors and transient failures with configurable retries.
- Normalise the JSON response into a TickEvent.
- Call the provided on_tick callback for every valid quote received.
- Run continuously in a background thread via run_forever().
"""

import logging
import time
import uuid
from typing import Callable, List, Optional

import requests

from shared.schema import TickEvent
from ingestion.config import (
    ALPHA_VANTAGE_API_KEY,
    ALPHA_VANTAGE_BASE_URL,
    ALPHA_VANTAGE_POLL_INTERVAL,
    ALPHA_VANTAGE_MAX_RETRIES,
    ALPHA_VANTAGE_RETRY_DELAY,
    TRACKED_SYMBOLS,
)

logger = logging.getLogger(__name__)

# Alpha Vantage function name for current quote
_AV_FUNCTION = "GLOBAL_QUOTE"


class AlphaVantageClient:
    """
    Polling REST client that fetches live quotes from Alpha Vantage.

    Parameters
    ----------
    on_tick : Callable[[TickEvent], None]
        Callback invoked for every successfully fetched & validated quote.
    symbols : List[str] | None
        Override the symbol list from config (useful in tests).

    Usage
    -----
        def handle(tick: TickEvent):
            producer.send(tick)

        client = AlphaVantageClient(on_tick=handle)
        client.run_forever()   # blocking — run in a thread
    """

    def __init__(
        self,
        on_tick: Callable[[TickEvent], None],
        symbols: Optional[List[str]] = None,
    ) -> None:
        self._on_tick = on_tick
        self._symbols = symbols or TRACKED_SYMBOLS
        self._session = requests.Session()
        self._running = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_forever(self) -> None:
        """
        Poll all symbols in a round-robin loop until stop() is called.
        Blocks the calling thread — run inside a daemon thread from main.py.
        """
        self._running = True
        logger.info(
            "Alpha Vantage poller starting — %d symbol(s), interval=%.1fs",
            len(self._symbols),
            ALPHA_VANTAGE_POLL_INTERVAL,
        )

        while self._running:
            for symbol in self._symbols:
                if not self._running:
                    break
                tick = self._fetch_quote(symbol)
                if tick:
                    self._on_tick(tick)
                # Spread requests to stay within rate limit
                time.sleep(ALPHA_VANTAGE_POLL_INTERVAL)

    def stop(self) -> None:
        """Signal the poller to stop after the current cycle."""
        self._running = False
        self._session.close()
        logger.info("Alpha Vantage client stopped.")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fetch_quote(self, symbol: str) -> Optional[TickEvent]:
        """
        Fetch a single GLOBAL_QUOTE from Alpha Vantage with retry logic.

        Returns a TickEvent on success, None on unrecoverable failure.
        """
        params = {
            "function": _AV_FUNCTION,
            "symbol": symbol,
            "apikey": ALPHA_VANTAGE_API_KEY,
        }

        for attempt in range(1, ALPHA_VANTAGE_MAX_RETRIES + 1):
            try:
                response = self._session.get(
                    ALPHA_VANTAGE_BASE_URL,
                    params=params,
                    timeout=10,
                )
                response.raise_for_status()
                data = response.json()
                return self._normalise_quote(symbol, data)

            except requests.exceptions.HTTPError as exc:
                logger.warning(
                    "HTTP error fetching %s (attempt %d/%d): %s",
                    symbol, attempt, ALPHA_VANTAGE_MAX_RETRIES, exc,
                )
            except requests.exceptions.RequestException as exc:
                logger.warning(
                    "Request error fetching %s (attempt %d/%d): %s",
                    symbol, attempt, ALPHA_VANTAGE_MAX_RETRIES, exc,
                )

            if attempt < ALPHA_VANTAGE_MAX_RETRIES:
                time.sleep(ALPHA_VANTAGE_RETRY_DELAY)

        logger.error("All retries exhausted for symbol %s. Skipping.", symbol)
        return None

    def _normalise_quote(self, symbol: str, data: dict) -> Optional[TickEvent]:
        """
        Convert an Alpha Vantage GLOBAL_QUOTE response to a TickEvent.

        Alpha Vantage response structure
        ---------------------------------
        {
            "Global Quote": {
                "01. symbol":         "AAPL",
                "05. price":          "182.45",
                "06. volume":         "54321234",
                "07. latest trading day": "2024-03-10",
                ...
            }
        }
        """
        try:
            quote = data.get("Global Quote", {})

            if not quote:
                # API returns an empty object when rate-limited or symbol unknown
                note = data.get("Note") or data.get("Information") or "unknown reason"
                logger.warning("Empty Global Quote for %s: %s", symbol, note)
                return None

            price: float  = float(quote["05. price"])
            volume: int   = int(quote["06. volume"])
            timestamp: float = time.time()   # no tick-level timestamp from AV

            return TickEvent(
                event_id=str(uuid.uuid4()),
                timestamp=timestamp,
                symbol=symbol,
                price=price,
                volume=volume,
                source="alpha_vantage",
                bid=None,
                ask=None,
            )
        except (KeyError, ValueError, TypeError) as exc:
            logger.warning(
                "Could not normalise Alpha Vantage quote for %s: %s — %s",
                symbol, data, exc,
            )
            return None
