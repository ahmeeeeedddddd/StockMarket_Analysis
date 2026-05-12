import json
import logging
import uuid
from datetime import datetime, timezone, timedelta
import time
from confluent_kafka import Consumer, KafkaError
from shared.db_client import execute_write
from shared.health_check import report_health

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("market_processor")

class StreamProcessor:
    def __init__(self, bootstrap_servers="127.0.0.1:9092"):
        self.consumer = Consumer({
            "bootstrap.servers": bootstrap_servers,
            "group.id": "market-processor-group",
            "auto.offset.reset": "latest"
        })
        self.windows = [60, 300, 900]  # 1m, 5m, 15m
        self.state = {}
        self.msg_count = 0
        self.last_report = time.time()
        
    def get_bucket_start(self, ts, window_sec):
        bucket_ts = int(ts) - (int(ts) % window_sec)
        return datetime.fromtimestamp(bucket_ts, tz=timezone.utc)

    def process_tick(self, tick):
        symbol = tick.get("symbol")
        price = float(tick.get("price", 0))
        volume = int(tick.get("volume", 0))
        ts = tick.get("timestamp")
        
        if not symbol or not ts: return

        for window in self.windows:
            bucket_start = self.get_bucket_start(ts, window)
            key = (symbol, window, bucket_start)
            
            if key not in self.state:
                self.state[key] = {
                    "open": price,
                    "high": price,
                    "low": price,
                    "close": price,
                    "volume": volume,
                    "vw_sum": price * volume,
                    "trade_count": 1
                }
            else:
                s = self.state[key]
                s["high"] = max(s["high"], price)
                s["low"] = min(s["low"], price)
                s["close"] = price
                s["volume"] += volume
                s["vw_sum"] += (price * volume)
                s["trade_count"] += 1
                
            self.upsert_to_db(key, self.state[key])
            
        self.cleanup_state(ts)

    def upsert_to_db(self, key, s):
        bucket_start, symbol, window_sec = key[2], key[0], key[1]
        vwap = s["vw_sum"] / s["volume"] if s["volume"] > 0 else s["open"]
        window_end = bucket_start + timedelta(seconds=window_sec)
        
        sql = """
            INSERT INTO aggregates (
                time, symbol, window_sec, 
                open, high, low, close, 
                volume, vwap, trade_count, 
                event_id, window_end
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (time, symbol, window_sec) DO UPDATE SET
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                volume = EXCLUDED.volume,
                vwap = EXCLUDED.vwap,
                trade_count = EXCLUDED.trade_count,
                window_end = EXCLUDED.window_end
        """
        
        try:
            execute_write(sql, (
                bucket_start, symbol, window_sec,
                s["open"], s["high"], s["low"], s["close"],
                s["volume"], vwap, s["trade_count"],
                str(uuid.uuid4()), window_end
            ))
        except Exception as e:
            pass

    def cleanup_state(self, current_ts):
        cutoff = current_ts - 3600 # Keep 1 hour
        keys_to_del = [k for k in self.state.keys() if k[2].timestamp() < cutoff]
        for k in keys_to_del:
            del self.state[k]

    def run(self):
        self.consumer.subscribe(["ticks"])
        log.info("Market Processor (Python) started - monitoring 'ticks'")
        
        try:
            while True:
                # Report health every 10s even if no messages
                now = time.time()
                if now - self.last_report > 10:
                    mps = self.msg_count / (now - self.last_report) if (now - self.last_report) > 0 else 0
                    report_health("processor", "running", {
                        "mps": round(mps, 2),
                        "total_processed": self.msg_count
                    })
                    self.last_report = now
                    self.msg_count = 0

                msg = self.consumer.poll(1.0)
                if msg is None: continue

        except KeyboardInterrupt:
            pass
        finally:
            self.consumer.close()

if __name__ == "__main__":
    processor = StreamProcessor()
    processor.run()
