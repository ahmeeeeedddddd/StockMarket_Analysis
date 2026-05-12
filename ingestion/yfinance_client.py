import logging
import time
import uuid
from typing import Callable

import yfinance as yf

from shared.schema import TickEvent
from ingestion.config import TRACKED_SYMBOLS, YFINANCE_POLL_INTERVAL
from shared.health_check import report_health

logger = logging.getLogger(__name__)


class YFinanceClient:
    """
    Polls Yahoo Finance at a fixed interval to emit simulated 'real-time' TickEvents.
    """

    def __init__(self, on_tick: Callable[[TickEvent], None]) -> None:
        self._on_tick = on_tick
        self._running = False
        self._msg_count = 0
        self._last_report = time.time()

    def run_forever(self) -> None:
        """Main polling loop. Blocks until stop() is called."""
        logger.info("YFinanceClient starting with automatic 1-hour backfill...")
        self._running = True
        
        # 1. Perform initial backfill
        self._backfill()

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

    def _backfill(self) -> None:
        """Fetch last 60 1-minute bars to pre-populate charts."""
        for symbol in TRACKED_SYMBOLS:
            if not self._running: break
            try:
                logger.info("Backfilling 1h history for %s...", symbol)
                df = yf.download(
                    tickers=symbol,
                    period="1d",
                    interval="1m",
                    progress=False,
                    auto_adjust=True,
                )
                if df.empty: continue
                
                # Take last 60 bars
                recent_bars = df.tail(60)
                for ts, row in recent_bars.iterrows():
                    price = float(row['Close'])
                    volume = int(row['Volume'])
                    if price > 0:
                        # Convert pandas timestamp to unix seconds
                        unix_ts = ts.timestamp()
                        event = TickEvent(
                            event_id=str(uuid.uuid4()),
                            timestamp=unix_ts,
                            symbol=symbol,
                            price=price,
                            volume=volume,
                            source="yfinance-backfill",
                        )
                        self._on_tick(event)
            except Exception as e:
                logger.error("Backfill failed for %s: %s", symbol, e)
        logger.info("Backfill complete.")

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

                # Handle case where yfinance returns a MultiIndex or Series
                def get_val(col_name):
                    try:
                        val = latest[col_name]
                        if hasattr(val, "iloc"):
                            return float(val.iloc[0])
                        return float(val)
                    except (KeyError, IndexError, TypeError):
                        return 0.0

                price = get_val("Close")
                volume = int(get_val("Volume"))

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
                    self._msg_count += 1
                    logger.info("Sent tick: symbol=%s price=%.4f", event.symbol, event.price)
            except Exception as e:
                logger.error("YFinanceClient failed to fetch data for %s: %s", symbol, e)

        # Report health every 10s after processing all symbols
        now = time.time()
        if now - self._last_report > 10:
            mps = self._msg_count / (now - self._last_report) if (now - self._last_report) > 0 else 0
            status = "running" if self._msg_count > 0 else "idle"
            report_health("ingestion", status, {
                "mps": round(mps, 2),
                "total_processed": self._msg_count,
                "symbols_tracked": len(TRACKED_SYMBOLS)
            })
            self._last_report = now
            # Only reset msg_count if we successfully reported
            self._msg_count = 0
