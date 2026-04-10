import json
import logging
import os
from datetime import datetime, timezone

from confluent_kafka import Producer


KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
OUTPUT_TOPIC = "market-alerts"

log = logging.getLogger("anomaly_detector.publisher")


def make_producer() -> Producer:
    producer = Producer({
        "bootstrap.servers": KAFKA_BOOTSTRAP,
        "linger.ms": 5,
        "compression.type": "snappy",
    })
    log.info("Producer ready — publishing to '%s'", OUTPUT_TOPIC)
    return producer


def build_alert(ticker: str, timestamp: str, detection: dict) -> dict:
    return {
        "alert_id": f"{ticker}_{detection['type']}_{timestamp}",
        "ticker": ticker,
        "detected_at": timestamp,
        "published_at": datetime.now(timezone.utc).isoformat(),
        "anomaly_type": detection["type"],
        "severity": detection["severity"],
        "details": detection,
    }


def publish_alert(producer: Producer, alert: dict) -> None:
    producer.produce(
        topic=OUTPUT_TOPIC,
        key=alert["ticker"].encode(),
        value=json.dumps(alert).encode(),
        callback=_delivery_report,
    )
    producer.poll(0)


def flush(producer: Producer) -> None:
    producer.flush()


def _delivery_report(err, msg) -> None:
    if err:
        log.error("Alert delivery failed: %s", err)
    else:
        log.debug(
            "Alert delivered → %s [partition %d offset %d]",
            msg.topic(), msg.partition(), msg.offset(),
        )