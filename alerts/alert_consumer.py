# alerts/alert_consumer.py
#
# Person 5 — Alerting & notification engineer
#
# Entry-point for the alerting service.
# Consumes the Kafka `alerts` topic, then for every AlertEvent:
#   1. Writes history to TimescaleDB  (history_writer)
#   2. Posts a Slack webhook message  (slack_notifier)
#   3. Sends a SendGrid email         (email_notifier)
#
# Usage
# -----
#   python -m alerts.alert_consumer
#
# Environment variables (see individual notifier modules for the full list)
# -------------------------------------------------------------------------
#   SLACK_WEBHOOK_URL   — Slack Incoming Webhook URL
#   SENDGRID_API_KEY    — SendGrid API key
#   EMAIL_FROM          — verified sender address
#   EMAIL_TO            — comma-separated recipient addresses
#   SLACK_MIN_SEVERITY  — minimum severity for Slack  (default: low)
#   EMAIL_MIN_SEVERITY  — minimum severity for email  (default: high)

import logging
import signal
import sys

from kafka import KafkaConsumer
from kafka.errors import KafkaError

from shared.kafka_config import KAFKA_CONFIG
from shared.schema import deserialize_alert, AlertEvent

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


def _handle_signal(signum, frame):  # noqa: ANN001
    global _running
    log.info("Shutdown signal received (%s) — stopping consumer…", signum)
    _running = False


signal.signal(signal.SIGINT,  _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)


# ---------------------------------------------------------------------------
# Consumer factory
# ---------------------------------------------------------------------------

def _make_consumer() -> KafkaConsumer:
    return KafkaConsumer(
        KAFKA_CONFIG.topic_alerts,
        bootstrap_servers=KAFKA_CONFIG.bootstrap_servers,
        group_id=KAFKA_CONFIG.group_alerts,
        auto_offset_reset=KAFKA_CONFIG.consumer_auto_offset_reset,
        enable_auto_commit=KAFKA_CONFIG.consumer_enable_auto_commit,
        max_poll_records=KAFKA_CONFIG.consumer_max_poll_records,
        # Raw bytes — we handle deserialization ourselves
        value_deserializer=None,
        key_deserializer=None,
    )


# ---------------------------------------------------------------------------
# Per-message processing
# ---------------------------------------------------------------------------

def _process(event: AlertEvent) -> None:
    """Run all notification / persistence handlers for one alert."""

    # 1. Always persist to DB first — this is the source of truth
    try:
        write_alert(event)
    except Exception as exc:
        log.error(
            "DB write failed for event_id=%s: %s — continuing with notifications",
            event.event_id, exc,
        )

    # 2. Slack — non-blocking (errors logged inside, never raised)
    send_slack_alert(event)

    # 3. Email — non-blocking (errors logged inside, never raised)
    send_email_alert(event)


# ---------------------------------------------------------------------------
# Main consumer loop
# ---------------------------------------------------------------------------

def run() -> None:
    """Start the blocking Kafka consumer loop."""
    log.info(
        "Starting alert consumer | broker=%s  topic=%s  group=%s",
        KAFKA_CONFIG.bootstrap_servers,
        KAFKA_CONFIG.topic_alerts,
        KAFKA_CONFIG.group_alerts,
    )

    consumer = _make_consumer()

    try:
        while _running:
            # poll() returns {TopicPartition: [ConsumerRecord, ...]}
            records_by_partition = consumer.poll(timeout_ms=1_000)

            if not records_by_partition:
                continue  # idle — just loop again to check _running

            for tp, records in records_by_partition.items():
                for record in records:
                    try:
                        event = deserialize_alert(record.value)
                    except Exception as exc:
                        log.error(
                            "Deserialization failed on partition=%s offset=%s: %s",
                            tp.partition, record.offset, exc,
                        )
                        # Commit anyway so we don't loop on a permanently bad message
                        consumer.commit()
                        continue

                    log.info(
                        "Received alert | symbol=%s  type=%s  severity=%s  event_id=%s",
                        event.symbol, event.alert_type, event.severity, event.event_id,
                    )
                    _process(event)

                # Manual commit after all records in this partition batch are handled
                consumer.commit()

    except KafkaError as exc:
        log.critical("Fatal Kafka error: %s", exc)
        sys.exit(1)
    finally:
        consumer.close()
        log.info("Alert consumer stopped.")


if __name__ == "__main__":
    run()
