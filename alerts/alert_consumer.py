# alerts/alert_consumer.py
import logging
import signal
import sys
import json
import time
from dotenv import load_dotenv
from confluent_kafka import Consumer, KafkaError

# Load environment variables from .env file
load_dotenv()

from shared.kafka_config import KAFKA_CONFIG
from shared.schema import deserialize_alert, AlertEvent
from shared.health_check import report_health

from alerts.history_writer  import write_alert
from alerts.slack_notifier  import send_slack_alert
from alerts.email_notifier  import send_email_alert

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Graceful shutdown via SIGINT / SIGTERM
# ---------------------------------------------------------------------------
_running = True

def _handle_signal(signum, frame):
    global _running
    log.info("Shutdown signal received (%s) — stopping consumer...", signum)
    _running = False

signal.signal(signal.SIGINT,  _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)

# ---------------------------------------------------------------------------
# Main consumer loop
# ---------------------------------------------------------------------------

def run() -> None:
    """Start the confluent-kafka consumer loop."""
    conf = {
        'bootstrap.servers': KAFKA_CONFIG.bootstrap_servers,
        'group.id': KAFKA_CONFIG.group_alerts,
        'auto.offset.reset': KAFKA_CONFIG.consumer_auto_offset_reset,
        'enable.auto.commit': True
    }

    try:
        consumer = Consumer(conf)
        consumer.subscribe([KAFKA_CONFIG.topic_alerts])
        log.info("Starting confluent-kafka alert consumer | topic=%s", KAFKA_CONFIG.topic_alerts)
    except Exception as e:
        log.critical("Failed to create Kafka consumer: %s", e)
        sys.exit(1)

    last_report = 0
    msg_count = 0

    try:
        while _running:
            # Report health every 10s
            now = time.time()
            if now - last_report > 10:
                report_health("alerts", "running", {
                    "total_processed": msg_count
                })
                last_report = now

            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    log.error("Kafka error: %s", msg.error())
                    continue

            try:
                # Value is raw bytes
                data = msg.value()
                event = deserialize_alert(data)
                
                log.info(
                    "Received alert | symbol=%s  type=%s  severity=%s  event_id=%s",
                    event.symbol, event.alert_type, event.severity, event.event_id,
                )
                
                # Increment processed count for telemetry
                msg_count += 1
                
                # Handle persistence and notifications
                try:
                    write_alert(event)
                except Exception as e:
                    log.error("Failed to write to DB: %s", e)
                
                send_slack_alert(event)
                send_email_alert(event)
                
            except Exception as e:
                log.error("Failed to process message: %s", e)

    finally:
        consumer.close()
        log.info("Alert consumer stopped.")

if __name__ == "__main__":
    run()
