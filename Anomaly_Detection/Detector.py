import logging
from collections import defaultdict, deque
from datetime import datetime, timezone

from bollinger import BB_WINDOW, check_bollinger_breach
from zscore import JUMP_WINDOW, VOL_WINDOW, check_price_jump, check_volume_spike
from kafka_consumer import make_consumer, poll_tick
from alert_publisher import build_alert, flush, make_producer, publish_alert


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("anomaly_detector")




class TickerState:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.prices = deque(maxlen=max(BB_WINDOW, JUMP_WINDOW))
        self.volumes = deque(maxlen=VOL_WINDOW)

    def update(self, price: float, volume: float):
        self.prices.append(price)
        self.volumes.append(volume)




def run():
    log.info("Anomaly detection service starting...")

    consumer = make_consumer()
    producer = make_producer()

    state: dict[str, TickerState] = defaultdict(lambda: TickerState("unknown"))

    try:
        while True:
            tick = poll_tick(consumer)
            if tick is None:
                continue

            ticker    = tick["ticker"]
            price     = float(tick["price"])
            volume    = float(tick["volume"])
            timestamp = tick.get("timestamp", datetime.now(timezone.utc).isoformat())

            if ticker not in state:
                state[ticker] = TickerState(ticker)
            ts = state[ticker]
            ts.update(price, volume)

            detections = [
                check_bollinger_breach(ts.prices, price),
                check_volume_spike(ts.volumes, volume),
                check_price_jump(ts.prices, price),
            ]

            for detection in detections:
                if detection is None:
                    continue

                alert = build_alert(ticker, timestamp, detection)

                log.info(
                    "ALERT  %s | %s | severity=%s",
                    ticker,
                    detection["type"],
                    detection["severity"],
                )

                publish_alert(producer, alert)

    except KeyboardInterrupt:
        log.info("Shutting down gracefully...")
    finally:
        consumer.close()
        flush(producer)
        log.info("Shutdown complete.")


if __name__ == "__main__":
    run()