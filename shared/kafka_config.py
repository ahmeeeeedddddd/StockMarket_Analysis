# shared/kafka_config.py

from dataclasses import dataclass
from shared.constants import Topics, ConsumerGroups


# ---------------------------------------------------------------------------
# Broker config — hardcoded for local Docker setup
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class KafkaConfig:
    """
    All Kafka connection settings in one importable object.
    Every module that needs Kafka imports KAFKA_CONFIG — nobody hardcodes
    broker URLs or topic names anywhere else.
    """

    # Broker
    bootstrap_servers: str

    # Topics
    topic_ticks:      str
    topic_aggregates: str
    topic_alerts:     str

    # Consumer groups
    group_processing:        str
    group_anomaly_detection: str
    group_alerts:            str

    # Producer settings
    producer_acks:             str
    producer_retries:          int
    producer_linger_ms:        int
    producer_batch_size:       int

    # Consumer settings
    consumer_auto_offset_reset:  str
    consumer_enable_auto_commit: bool
    consumer_max_poll_records:   int


# ---------------------------------------------------------------------------
# Singleton — this is the only thing teammates need to import
# ---------------------------------------------------------------------------

KAFKA_CONFIG = KafkaConfig(
    # Broker — matches the container name in docker-compose.yml
    bootstrap_servers="127.0.0.1:9092",

    # Topics
    topic_ticks=Topics.TICKS.value,
    topic_aggregates=Topics.AGGREGATES.value,
    topic_alerts=Topics.ALERTS.value,

    # Consumer groups
    group_processing=ConsumerGroups.PROCESSING.value,
    group_anomaly_detection=ConsumerGroups.ANOMALY_DETECTION.value,
    group_alerts=ConsumerGroups.ALERTS.value,

    # Producer
    producer_acks="all",     # wait for all replicas before confirming
    producer_retries=5,
    producer_linger_ms=5,    # small batch window for low latency
    producer_batch_size=16384,

    # Consumer
    consumer_auto_offset_reset="earliest",   # replay from start if no offset found
    consumer_enable_auto_commit=False,        # manual commits — no silent data loss
    consumer_max_poll_records=500,
)