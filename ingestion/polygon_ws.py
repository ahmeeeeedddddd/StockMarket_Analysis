# ingestion/polygon_ws.py
"""
Polygon.io WebSocket client for real-time trade tick data.

Responsibilities
----------------
- Connect to the Polygon Stocks WebSocket feed.
- Authenticate with the API key.
- Subscribe to trade events (T.*) for every tracked symbol.
- Normalise raw Polygon messages into TickEvent objects.
- Handle disconnects with exponential back-off reconnect logic.
- Rate-limit awareness: Polygon free tier limits concurrent subscriptions.
- Call the provided on_tick callback for every valid tick received.
"""

import json
import logging
import time
import uuid
from typing import Callable, Optional

import websocket  # websocket-client

from shared.schema import TickEvent
from ingestion.config import (
    POLYGON_API_KEY,
    POLYGON_WS_URL,
    POLYGON_RECONNECT_DELAY,
    POLYGON_MAX_RECONNECTS,
    TRACKED_SYMBOLS,
)

logger = logging.getLogger(__name__)

# Polygon event type for trades
_TRADE_TYPE = "T"


class PolygonWebSocketClient:
    """
    Long-running WebSocket client that streams live trade ticks from Polygon.io.

    Parameters
    ----------
    on_tick : Callable[[TickEvent], None]
        Callback invoked for every validated tick received from Polygon.
    symbols : list[str] | None
        Override the symbols list from config (useful for testing).

    Usage
    -----
        def handle(tick: TickEvent):
            producer.send(tick)

        client = PolygonWebSocketClient(on_tick=handle)
        client.run_forever()   # blocking — run in a thread
    """

    def __init__(
        self,
        on_tick: Callable[[TickEvent], None],
        symbols: Optional[list] = None,
    ) -> None:
        self._on_tick = on_tick
        self._symbols = symbols or TRACKED_SYMBOLS
        self._ws: Optional[websocket.WebSocketApp] = None
        self._reconnect_count = 0
        self._running = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_forever(self) -> None:
        """
        Connect and keep reconnecting until stop() is called.
        Blocks the calling thread — run inside a daemon thread from main.py.
        """
        self._running = True
        while self._running:
            if POLYGON_MAX_RECONNECTS and self._reconnect_count >= POLYGON_MAX_RECONNECTS:
                logger.error(
                    "Reached max reconnects (%d). Stopping Polygon client.",
                    POLYGON_MAX_RECONNECTS,
                )
                break

            logger.info(
                "Connecting to Polygon WebSocket (attempt %d) …",
                self._reconnect_count + 1,
            )
            self._ws = websocket.WebSocketApp(
                POLYGON_WS_URL,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
            )
            self._ws.run_forever()

            if self._running:
                delay = POLYGON_RECONNECT_DELAY * (2 ** min(self._reconnect_count, 5))
                logger.info("Reconnecting in %.1f seconds …", delay)
                time.sleep(delay)
                self._reconnect_count += 1

    def stop(self) -> None:
        """Signal the client to stop reconnecting and close the socket."""
        self._running = False
        if self._ws:
            self._ws.close()
        logger.info("Polygon WebSocket client stopped.")

    # ------------------------------------------------------------------
    # WebSocketApp callbacks
    # ------------------------------------------------------------------

    def _on_open(self, ws: websocket.WebSocketApp) -> None:
        logger.info("Polygon WebSocket connection opened.")

    def _on_message(self, ws: websocket.WebSocketApp, raw: str) -> None:
        """Entry point for every message Polygon sends."""
        try:
            messages = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.warning("Could not parse Polygon message: %s — %s", raw[:200], exc)
            return

        for msg in messages:
            ev = msg.get("ev")

            if ev == "connected":
                logger.info("Polygon: connected — sending auth …")
                ws.send(json.dumps({"action": "auth", "params": POLYGON_API_KEY}))

            elif ev == "auth_success":
                logger.info("Polygon: authenticated — subscribing to symbols …")
                subscription_params = ",".join(f"T.{sym}" for sym in self._symbols)
                ws.send(json.dumps({"action": "subscribe", "params": subscription_params}))
                self._reconnect_count = 0   # reset counter on successful auth

            elif ev == "auth_failed":
                logger.error("Polygon authentication failed. Check POLYGON_API_KEY.")
                ws.close()

            elif ev == _TRADE_TYPE:
                tick = self._normalise_trade(msg)
                if tick:
                    self._on_tick(tick)

            else:
                logger.debug("Polygon: unhandled event type '%s'", ev)

    def _on_error(self, ws: websocket.WebSocketApp, error: Exception) -> None:
        logger.error("Polygon WebSocket error: %s", error)

    def _on_close(
        self,
        ws: websocket.WebSocketApp,
        close_status_code: Optional[int],
        close_msg: Optional[str],
    ) -> None:
        logger.warning(
            "Polygon WebSocket closed (code=%s, msg=%s).",
            close_status_code,
            close_msg,
        )

    # ------------------------------------------------------------------
    # Normalisation
    # ------------------------------------------------------------------

    def _normalise_trade(self, msg: dict) -> Optional[TickEvent]:
        """
        Convert a raw Polygon trade message into a TickEvent.

        Polygon trade fields (relevant subset)
        ---------------------------------------
        sym  — ticker symbol
        p    — trade price
        s    — trade size (volume)
        t    — SIP timestamp (nanoseconds epoch)
        """
        try:
            symbol: str  = msg["sym"]
            price: float = float(msg["p"])
            volume: int  = int(msg["s"])
            # Polygon sends nanoseconds; convert to seconds
            timestamp: float = msg["t"] / 1_000_000_000

            return TickEvent(
                event_id=str(uuid.uuid4()),
                timestamp=timestamp,
                symbol=symbol,
                price=price,
                volume=volume,
                source="polygon",
                bid=None,
                ask=None,
            )
        except (KeyError, ValueError, TypeError) as exc:
            logger.warning("Could not normalise Polygon trade: %s — %s", msg, exc)
            return None
