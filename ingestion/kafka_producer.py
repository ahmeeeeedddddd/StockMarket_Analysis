# ingestion/kafka_producer.py
"""
Thin wrapper around kafka-python's KafkaProducer.

Responsibilities
----------------
- Build and manage a single producer instance for the whole ingestion service.
- Serialize TickEvent objects to JSON bytes using the shared schema helper.
- Send to the 'ticks' topic, partitioned by symbol for ordering guarantees.
- Expose a flush-and-close helper for clean shutdown.
"""

import logging
from typing import Optional

from kafka import KafkaProducer  # type: ignore
from kafka.errors import KafkaError  # type: ignore

from shared.schema import TickEvent, serialize
from ingestion.config import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_TICKS_TOPIC,
    KAFKA_PRODUCER_ACKS,
    KAFKA_PRODUCER_RETRIES,
    KAFKA_LINGER_MS,
    KAFKA_BATCH_SIZE,
)

logger = logging.getLogger(__name__)


class TickKafkaProducer:
    """
    Thread-safe Kafka producer for TickEvent messages.

    Usage
    -----
        producer = TickKafkaProducer()
        producer.send(tick_event)
        producer.close()
    """

    def __init__(self) -> None:
        self._producer: KafkaProducer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            api_version=(2, 5, 0),
            acks=KAFKA_PRODUCER_ACKS,
            retries=KAFKA_PRODUCER_RETRIES,
            linger_ms=KAFKA_LINGER_MS,
            batch_size=KAFKA_BATCH_SIZE,
            # key_serializer encodes the symbol string so Kafka can
            # partition by it — same symbol always goes to the same partition.
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            value_serializer=lambda v: v,   # already bytes from serialize()
        )
        logger.info(
            "KafkaProducer connected to %s, topic=%s",
            KAFKA_BOOTSTRAP_SERVERS,
            KAFKA_TICKS_TOPIC,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send(self, event: TickEvent) -> None:
        """
        Serialize and publish a single TickEvent.

        The message key is set to the symbol string so that all ticks for
        the same ticker land on the same partition (preserving order).
        """
        payload: bytes = serialize(event)
        future = self._producer.send(
            KAFKA_TICKS_TOPIC,
            key=event.symbol,
            value=payload,
        )
        future.add_errback(self._on_send_error, event=event)
        logger.debug("Sent tick: symbol=%s price=%.4f", event.symbol, event.price)

    def flush(self) -> None:
        """Block until all outstanding messages have been delivered."""
        self._producer.flush()
        logger.debug("Producer flushed.")

    def close(self) -> None:
        """Flush pending messages and close the producer cleanly."""
        logger.info("Closing KafkaProducer …")
        self._producer.flush()
        self._producer.close()
        logger.info("KafkaProducer closed.")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _on_send_error(exc: Exception, event: Optional[TickEvent] = None) -> None:
        """Error callback — logs but does not crash the producer."""
        symbol = event.symbol if event else "unknown"
        logger.error("Failed to deliver tick [symbol=%s]: %s", symbol, exc)
