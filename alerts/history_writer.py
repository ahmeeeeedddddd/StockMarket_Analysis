# alerts/history_writer.py
#
# Person 5 — Alerting & notification engineer
#
# Persists every AlertEvent into the TimescaleDB `alerts` hypertable so the
# dashboard (Person 6) and users can review the full alert history.

import logging
from datetime import datetime, timezone

from shared.db_client import execute_write
from shared.schema import AlertEvent

log = logging.getLogger(__name__)

_INSERT_SQL = """
INSERT INTO alerts (
    time,
    symbol,
    alert_type,
    severity,
    message,
    trigger_price,
    trigger_volume,
    zscore,
    reference_value,
    window_sec,
    event_id
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (event_id, time) DO NOTHING;
"""


def write_alert(event: AlertEvent) -> None:
    """
    Persist *event* to the ``alerts`` hypertable in TimescaleDB.

    The ``time`` column is derived from ``event.timestamp`` (Unix epoch float).
    Duplicate event_ids are silently ignored via ``ON CONFLICT DO NOTHING``.

    Raises
    ------
    Exception
        Re-raises any database error so the caller (alert_consumer) can decide
        whether to retry or dead-letter the message.
    """
    ts = datetime.fromtimestamp(event.timestamp, tz=timezone.utc)
    
    # Try to extract fields from metadata if missing on the main object
    meta = event.metadata or {}
    zscore = event.zscore or meta.get("z_score") or meta.get("std")
    ref_val = event.reference_value or meta.get("upper_band") or meta.get("lower_band") or meta.get("rolling_mean_volume")

    params = (
        ts,
        event.symbol,
        event.alert_type,
        event.severity,
        event.message,
        event.trigger_price,
        event.trigger_volume or meta.get("current_volume"),
        zscore,
        ref_val,
        event.window_sec or meta.get("window_sec"),
        event.event_id,
    )

    execute_write(_INSERT_SQL, params)
    log.debug(
        "Wrote alert to DB | event_id=%s  symbol=%s  type=%s  severity=%s",
        event.event_id,
        event.symbol,
        event.alert_type,
        event.severity,
    )
