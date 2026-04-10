import json
import logging
import os

from confluent_kafka import Consumer, KafkaError


KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
INPUT_TOPIC = "tick-metrics"
CONSUMER_GROUP = "anomaly-detection-group"

log = logging.getLogger("anomaly_detector.consumer")


def make_consumer() -> Consumer:
  
    consumer = Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP,
        "group.id": CONSUMER_GROUP,
        "auto.offset.reset": "latest",
        "enable.auto.commit": True,
    })
    consumer.subscribe([INPUT_TOPIC])
    log.info("Consumer subscribed to '%s'", INPUT_TOPIC)
    return consumer


def poll_tick(consumer: Consumer, timeout: float = 1.0) -> dict | None:
   
    msg = consumer.poll(timeout=timeout)

    if msg is None:
        return None

    if msg.error():
        if msg.error().code() != KafkaError._PARTITION_EOF:
            log.error("Kafka error: %s", msg.error())
        return None

    try:
        tick = json.loads(msg.value().decode())
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        log.warning("Could not parse message: %s", exc)
        return None

    if not _is_valid(tick):
        log.warning("Skipping malformed tick (missing fields): %s", tick)
        return None

    return tick


def _is_valid(tick: dict) -> bool:
    return (
        tick.get("ticker")
        and tick.get("price") is not None
        and tick.get("volume") is not None
    )