"""
infrastructure/kafka_setup.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Reads infrastructure/kafka/topics.yml and idempotently creates every Kafka
topic required by the stock-analytics pipeline.

Design decisions
----------------
* Uses the official confluent-kafka AdminClient (same library the rest of the
  team uses for producing/consuming).
* Idempotent — safe to run multiple times; existing topics are skipped, not
  deleted.
* All topic-level configs (retention, cleanup policy, …) come from topics.yml
  so this script never needs to be edited when tuning topic settings.
* Retries with exponential back-off while the Kafka broker is still starting
  (common in Docker Compose bring-ups).

Usage
-----
    python -m infrastructure.kafka_setup          # from repo root
    # or directly:
    python infrastructure/kafka_setup.py
"""

from __future__ import annotations

import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

import yaml
from confluent_kafka.admin import (
    AdminClient,
    ConfigResource,
    NewTopic,
)
from confluent_kafka import KafkaException

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)-8s]  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------
_HERE = Path(__file__).parent
TOPICS_YAML = _HERE / "kafka" / "topics.yml"

BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

# How long to retry connecting to the broker before giving up
CONNECT_RETRY_LIMIT   = 15          # attempts
CONNECT_RETRY_DELAY_S = 4.0         # seconds (doubles each retry up to cap)
CONNECT_RETRY_DELAY_CAP_S = 30.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_topics_config(path: Path) -> list[dict[str, Any]]:
    """Parse topics.yml and return the list of topic definitions."""
    if not path.exists():
        raise FileNotFoundError(f"topics.yml not found at {path}")
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    topics: list[dict] = data.get("topics", [])
    if not topics:
        raise ValueError("topics.yml contains no topic definitions")
    return topics


def _make_admin_client(broker: str) -> AdminClient:
    """
    Create an AdminClient, retrying with exponential back-off until the broker
    is reachable or the retry limit is exceeded.
    """
    cfg = {
        "bootstrap.servers": broker,
        # Low timeouts so failed attempts fail fast during the retry loop
        "socket.timeout.ms": 5_000,
        "metadata.request.timeout.ms": 5_000,
    }

    delay = CONNECT_RETRY_DELAY_S
    for attempt in range(1, CONNECT_RETRY_LIMIT + 1):
        try:
            client = AdminClient(cfg)
            # Probe: list existing topics — raises if broker unreachable
            client.list_topics(timeout=5)
            log.info("Connected to Kafka broker at %s", broker)
            return client
        except KafkaException as exc:
            if attempt == CONNECT_RETRY_LIMIT:
                log.error(
                    "Could not connect to Kafka after %d attempts: %s",
                    CONNECT_RETRY_LIMIT,
                    exc,
                )
                raise
            log.warning(
                "Kafka not ready (attempt %d/%d): %s — retrying in %.0fs …",
                attempt,
                CONNECT_RETRY_LIMIT,
                exc,
                delay,
            )
            time.sleep(delay)
            delay = min(delay * 2, CONNECT_RETRY_DELAY_CAP_S)

    # Should never reach here
    raise RuntimeError("Exhausted retry attempts connecting to Kafka")  # pragma: no cover


def _existing_topics(client: AdminClient) -> set[str]:
    """Return the set of topic names that already exist on the broker."""
    metadata = client.list_topics(timeout=10)
    return set(metadata.topics.keys())


def _build_new_topic(td: dict[str, Any]) -> NewTopic:
    """
    Convert a topics.yml entry into a confluent_kafka NewTopic object.
    Every per-topic config key maps directly to a Kafka broker config string.
    """
    name = td["name"]
    config: dict[str, str] = {}

    if "retention_ms" in td:
        config["retention.ms"] = str(td["retention_ms"])
    if "retention_bytes" in td:
        config["retention.bytes"] = str(td["retention_bytes"])
    if "cleanup_policy" in td:
        config["cleanup.policy"] = td["cleanup_policy"]
    if "segment_ms" in td:
        config["segment.ms"] = str(td["segment_ms"])

    return NewTopic(
        topic=name,
        num_partitions=td.get("partitions", 1),
        replication_factor=td.get("replication", 1),
        config=config,
    )


def create_topics(broker: str = BROKER) -> None:
    """
    Main entry point: read topics.yml, connect to Kafka, and create any
    missing topics.  Existing topics are left untouched (idempotent).
    """
    log.info("Loading topic definitions from %s", TOPICS_YAML)
    topic_defs = _load_topics_config(TOPICS_YAML)

    client = _make_admin_client(broker)
    existing = _existing_topics(client)

    to_create: list[NewTopic] = []
    for td in topic_defs:
        name = td["name"]
        desc = td.get("description", "").strip().replace("\n", " ")
        if name in existing:
            log.info("  SKIP   %-20s (already exists)", name)
        else:
            log.info("  CREATE %-20s  partitions=%s  replication=%s",
                     name, td.get("partitions", 1), td.get("replication", 1))
            if desc:
                log.info("         %s", desc)
            to_create.append(_build_new_topic(td))

    if not to_create:
        log.info("All topics already exist — nothing to do.")
        return

    # create_topics returns a future-per-topic dict
    futures = client.create_topics(to_create)

    all_ok = True
    for topic_name, future in futures.items():
        try:
            future.result()          # blocks until creation confirmed
            log.info("  ✓ Created topic: %s", topic_name)
        except KafkaException as exc:
            # TOPIC_ALREADY_EXISTS (36) is not an error in idempotent mode
            err = exc.args[0]
            if err.code() == 36:    # TOPIC_ALREADY_EXISTS
                log.info("  ~ Topic already exists (race condition): %s", topic_name)
            else:
                log.error("  ✗ Failed to create topic %s: %s", topic_name, exc)
                all_ok = False

    if not all_ok:
        log.error("One or more topics could not be created. Review errors above.")
        sys.exit(1)

    log.info("Kafka topic setup complete.")


def verify_topics(broker: str = BROKER) -> bool:
    """
    Verify that every topic in topics.yml exists on the broker.
    Returns True if all topics are present, False otherwise.
    Used by init_all.py to gate the rest of initialisation.
    """
    topic_defs = _load_topics_config(TOPICS_YAML)
    required = {td["name"] for td in topic_defs}

    client = _make_admin_client(broker)
    existing = _existing_topics(client)

    missing = required - existing
    if missing:
        log.warning("Missing topics: %s", sorted(missing))
        return False

    log.info("All required topics verified: %s", sorted(required))
    return True


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    create_topics()
