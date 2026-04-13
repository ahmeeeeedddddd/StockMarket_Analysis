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
        """Fetch latest bar for all tracked symbols and emit ticks."""
        for symbol in TRACKED_SYMBOLS:
            if not self._running:
                break
            try:
                df = yf.download(
                    tickers=symbol,
                    period="1d",
                    interval="1m",
                    progress=False,
                    auto_adjust=True,
                )

                if df.empty:
                    logger.debug("YFinanceClient skipping %s: empty dataframe", symbol)
                    continue

                # Take the most recent completed bar
                latest = df.iloc[-1]

                price  = float(latest["Close"].iloc[0] if hasattr(latest["Close"], "iloc") else latest["Close"])
                volume = int(latest["Volume"].iloc[0]  if hasattr(latest["Volume"], "iloc") else latest["Volume"])

                if price > 0:
                    event = TickEvent(
                        event_id=str(uuid.uuid4()),
                        timestamp=time.time(),
                        symbol=symbol,
                        price=price,
                        volume=volume,
                        source="yfinance",
                    )
                    self._on_tick(event)
                    logger.info("Sent tick: symbol=%s price=%.4f", event.symbol, event.price)
                else:
                    logger.debug("YFinanceClient skipping %s: invalid price %s", symbol, price)

            except Exception as e:
                logger.error("YFinanceClient failed to fetch data for %s: %s", symbol, e)
