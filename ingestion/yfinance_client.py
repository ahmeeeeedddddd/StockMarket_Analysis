import logging
import time
import uuid
from typing import Callable

import yfinance as yf

from shared.schema import TickEvent
from ingestion.config import TRACKED_SYMBOLS, YFINANCE_POLL_INTERVAL

logger = logging.getLogger(__name__)


class YFinanceClient:
    """
    Polls Yahoo Finance at a fixed interval to emit simulated 'real-time' TickEvents.
    """

    def __init__(self, on_tick: Callable[[TickEvent], None]) -> None:
        self._on_tick = on_tick
        self._running = False

    def run_forever(self) -> None:
        """Main polling loop. Blocks until stop() is called."""
        logger.info("YFinanceClient starting with polling interval %.1fs", YFINANCE_POLL_INTERVAL)
        self._running = True

        while self._running:
            self._poll_all()
            # Sleep in short bursts so stop() is responsive
            end_time = time.time() + YFINANCE_POLL_INTERVAL
            while self._running and time.time() < end_time:
                time.sleep(0.5)

        logger.info("YFinanceClient stopped.")

    def stop(self) -> None:
        """Signal the polling loop to exit gracefully."""
        self._running = False

    def _poll_all(self) -> None:
        """Fetch fast_info for all tracked symbols and emit ticks."""
        for symbol in TRACKED_SYMBOLS:
            if not self._running:
                break
            try:
                ticker = yf.Ticker(symbol)
                fast_info = ticker.fast_info
                
                # fast_info might be missing some fields for some symbols/times.
                # using last_price as price and last_volume as volume.
                price = getattr(fast_info, "last_price", None)
                volume = getattr(fast_info, "last_volume", 0)

                # Ensure volume is an int, default to 0 if None
                if volume is None:
                    volume = 0
                else:
                    volume = int(volume)

                if price is not None and price > 0:
                    event = TickEvent(
                        event_id=str(uuid.uuid4()),
                        timestamp=time.time(),
                        symbol=symbol,
                        price=float(price),
                        volume=volume,
                        source="yfinance",
                    )
                    self._on_tick(event)
                else:
                    logger.debug("YFinanceClient skipping %s: invalid price %s", symbol, price)

            except Exception as e:
                logger.error("YFinanceClient failed to fetch data for %s: %s", symbol, e)
