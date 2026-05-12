import logging
import time
import json
import uuid
from collections import defaultdict, deque
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

from Anomaly_Detection.bollinger import BB_WINDOW, check_bollinger_breach
from Anomaly_Detection.zscore import JUMP_WINDOW, VOL_WINDOW, check_price_jump, check_volume_spike
from confluent_kafka import Consumer, KafkaError, Producer
from shared.kafka_config import KAFKA_CONFIG
from shared.db_client import execute_query
from shared.health_check import report_health

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

def fetch_rules():
    try:
        sql = "SELECT symbol, rule_type, threshold, window_sec FROM alert_rules"
        return execute_query(sql)
    except Exception as e:
        log.error("Failed to fetch rules: %s", e)
        return []

def run():
    log.info("Anomaly detection service (Confluent) starting...")

    consumer = Consumer({
        'bootstrap.servers': KAFKA_CONFIG.bootstrap_servers,
        'group.id': 'anomaly-detector-group',
        'auto.offset.reset': 'latest',
        'session.timeout.ms': 45000,
        'enable.auto.commit': True
    })
    consumer.subscribe(['ticks'])

    producer = Producer({'bootstrap.servers': KAFKA_CONFIG.bootstrap_servers})

    # Track when a specific symbol+rule was last triggered in memory to avoid spam
    rule_cooldowns = {}

    state: dict[str, TickerState] = defaultdict(lambda: TickerState("unknown"))
    rules: list = []
    last_rule_fetch = 0
    msg_count = 0
    last_report = time.time()

    try:
        while True:
            # Report health every 10s even if no ticks
            now = time.time()
            if now - last_report > 10:
                mps = msg_count / (now - last_report) if (now - last_report) > 0 else 0
                report_health("detector", "running", {
                    "mps": round(mps, 2),
                    "total_processed": msg_count
                })
                last_report = now
                msg_count = 0

            msg = consumer.poll(timeout=1.0)
            if msg is None:
                # Still check for rule refresh even if no tick
                if time.time() - last_rule_fetch > 5:
                    rules = fetch_rules()
                    last_rule_fetch = time.time()
                continue
            
            if msg.error():
                if msg.error().code() != KafkaError._PARTITION_EOF:
                    log.error("Kafka error: %s", msg.error())
                continue

            try:
                tick = json.loads(msg.value().decode('utf-8'))
                ticker    = tick["symbol"]
                price     = float(tick["price"])
                volume    = float(tick["volume"])
                timestamp = tick.get("timestamp", datetime.now(timezone.utc).isoformat())
                msg_count += 1

                # 1. Update state
                if ticker not in state:
                    state[ticker] = TickerState(ticker)
                ts = state[ticker]
                ts.update(price, volume)

                # 2. Check Custom User Rules (Always run these even if stale)
                if time.time() - last_rule_fetch > 5:
                    rules = fetch_rules()
                    last_rule_fetch = time.time()

                user_detections = []
                for rule in rules:
                    if rule['symbol'] != ticker:
                        continue
                    
                    rule_type = rule['rule_type']
                    threshold = float(rule['threshold'])
                    triggered = False
                    msg_text = ""

                    # Create a unique key for this rule instance
                    rule_key = f"{ticker}_{rule_type}_{threshold}"
                    
                    if rule_type == 'price_above' and price > threshold:
                        triggered = True
                        msg_text = f"🚨 {ticker} PRICE ALERT: Current ${price:.2f} is above your threshold of ${threshold:.2f}"
                    elif rule_type == 'price_below' and price < threshold:
                        triggered = True
                        msg_text = f"📉 {ticker} PRICE ALERT: Current ${price:.2f} is below your threshold of ${threshold:.2f}"
                    elif rule_type == 'volume_above' and volume > threshold:
                        triggered = True
                        msg_text = f"📊 {ticker} VOLUME ALERT: Current volume {volume:,} is above your threshold of {threshold:,}"

                    if triggered:
                        # Check cooldown (e.g. 5 minutes)
                        last_triggered = rule_cooldowns.get(rule_key, 0)
                        if time.time() - last_triggered > 300:
                            user_detections.append({
                                "type": "USER_RULE",
                                "severity": "high",
                                "message": msg_text,
                                "value": price if 'volume' not in rule_type else volume
                            })
                            rule_cooldowns[rule_key] = time.time()

                # 3. Check for Stale Data (Ignore automatic anomalies if too old)
                is_stale = False
                try:
                    tick_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    if (datetime.now(timezone.utc) - tick_time).total_seconds() > 300 and tick.get("source") != "yfinance-backfill":
                        is_stale = True
                except Exception:
                    pass

                auto_detections = []
                if not is_stale and tick.get("source") != "yfinance-backfill":
                    auto_detections = [
                        check_bollinger_breach(ts.prices, price),
                        check_volume_spike(ts.volumes, volume),
                        check_price_jump(ts.prices, price),
                    ]

                # Combine detections
                all_detections = user_detections + [d for d in auto_detections if d]

                # 4. Publish Alerts
                for detection in all_detections:
                    # Construct Alert Event — MUST USE FLOAT FOR TIMESTAMP
                    alert_event = {
                        "event_id": str(uuid.uuid4()),
                        "symbol": ticker,
                        "timestamp": time.time(), # Use current system time for the alert itself
                        "alert_type": detection["type"],
                        "severity": detection["severity"],
                        "message": detection.get("message", "Threshold breached"),
                        "trigger_price": price,
                        "metadata": {k: v for k, v in detection.items() if k not in ["type", "severity", "message", "price"]}
                    }

                    log.info("PUBLISHING ALERT: %s | %s", ticker, alert_event["message"])
                    producer.produce(KAFKA_CONFIG.topic_alerts, json.dumps(alert_event).encode('utf-8'))
                
                producer.poll(0)

            except Exception as e:
                log.error("Data error: %s", e)

    except KeyboardInterrupt:
        log.info("Shutting down detector...")
    finally:
        consumer.close()
        producer.flush()

if __name__ == "__main__":
    run()