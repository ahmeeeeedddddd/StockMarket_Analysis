"""
infrastructure/init_all.py
~~~~~~~~~~~~~~~~~~~~~~~~~~
Master initialization script for the local development environment.
Runs kafka_setup.py to create topics and applies timescale_schema.sql
to instantiate the database tables.

Usage
-----
    python -m infrastructure.init_all
"""

import logging
import time
import sys
from pathlib import Path

from shared.db_client import get_db_connection
from infrastructure.kafka_setup import create_topics, verify_topics

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

_HERE = Path(__file__).parent
SCHEMA_FILE = _HERE / "timescale_schema.sql"

def init_database() -> None:
    """Connect to TimescaleDB and execute the schema initialization script."""
    log.info("Connecting to TimescaleDB...")
    
    # Simple retry loop for DB connection wait
    conn = None
    for attempt in range(1, 16):
        try:
            conn = get_db_connection()
            log.info("Connected to TimescaleDB.")
            break
        except Exception as e:
            log.warning(f"Database not ready (attempt {attempt}/15): {e} - retrying in 2s...")
            time.sleep(2)
            
    if not conn:
        log.error("Could not connect to TimescaleDB after 30 seconds.")
        sys.exit(1)

    log.info(f"Applying schema from {SCHEMA_FILE.name}...")
    try:
        sql = SCHEMA_FILE.read_text(encoding="utf-8")
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql)
        log.info("TimescaleDB schema applied successfully.")
    except Exception as e:
        log.error(f"Failed to apply database schema: {e}")
        sys.exit(1)
    finally:
        conn.close()

def main():
    log.info("=== Starting Infrastructure Initialization ===")
    
    # 1. Initialize Kafka
    log.info("--- Step 1: Initializing Kafka topics ---")
    try:
        create_topics()
        if not verify_topics():
            log.error("Kafka topic verification failed!")
            sys.exit(1)
    except Exception as e:
        log.error(f"Failed to initialize Kafka: {e}")
        sys.exit(1)

    # 2. Initialize TimescaleDB
    log.info("--- Step 2: Initializing TimescaleDB schema ---")
    init_database()

    log.info("=== Infrastructure Initialization Complete ===")
    log.info("You can now start the ingestion and processing modules.")

if __name__ == "__main__":
    main()
