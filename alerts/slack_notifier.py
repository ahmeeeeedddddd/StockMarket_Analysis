# alerts/slack_notifier.py
#
# Person 5 — Alerting & notification engineer
#
# Sends alert notifications to a Slack channel via Incoming Webhook.
#
# Required environment variable
# ------------------------------
#   SLACK_WEBHOOK_URL   — the full Incoming Webhook URL from your Slack app
#
# Optional environment variables
# --------------------------------
#   SLACK_MIN_SEVERITY  — minimum severity to notify (low | medium | high)
#                         default: "low"  (notify on every alert)

import json
import logging
import os

import requests

from shared.constants import AlertSeverity
from shared.schema import AlertEvent

log = logging.getLogger(__name__)

# Severity ordering — used to filter below the minimum threshold
_SEVERITY_ORDER = {
    AlertSeverity.LOW.value:    0,
    AlertSeverity.MEDIUM.value: 1,
    AlertSeverity.HIGH.value:   2,
}

# Colour side-bar per severity level (Slack attachment colour)
_SEVERITY_COLOR = {
    AlertSeverity.LOW.value:    "#36a64f",   # green
    AlertSeverity.MEDIUM.value: "#ffb347",   # orange
    AlertSeverity.HIGH.value:   "#ff4c4c",   # red
}


def _build_payload(event: AlertEvent) -> dict:
    """Construct the Slack Block Kit / attachment payload for *event*."""
    color = _SEVERITY_COLOR.get(event.severity, "#aaaaaa")

    fields = [
        {"title": "Symbol",     "value": event.symbol,      "short": True},
        {"title": "Alert Type", "value": event.alert_type,  "short": True},
        {"title": "Severity",   "value": event.severity.upper(), "short": True},
    ]

    if event.trigger_price is not None:
        fields.append({"title": "Trigger Price",
                        "value": f"${event.trigger_price:.4f}", "short": True})
    if event.trigger_volume is not None:
        fields.append({"title": "Trigger Volume",
                        "value": f"{event.trigger_volume:,}", "short": True})
    if event.zscore is not None:
        fields.append({"title": "Z-Score",
                        "value": f"{event.zscore:.2f}", "short": True})
    if event.reference_value is not None:
        fields.append({"title": "Reference Value",
                        "value": f"{event.reference_value:.4f}", "short": True})
    if event.window_sec is not None:
        fields.append({"title": "Window",
                        "value": f"{event.window_sec}s", "short": True})

    return {
        "attachments": [
            {
                "color":      color,
                "title":      f":rotating_light: Market Alert — {event.symbol}",
                "text":       event.message,
                "fields":     fields,
                "footer":     f"event_id: {event.event_id}",
                "ts":         int(event.timestamp),
            }
        ]
    }


def send_slack_alert(event: AlertEvent) -> None:
    """
    Post *event* to the Slack Incoming Webhook.

    Skips silently when:
    - ``SLACK_WEBHOOK_URL`` is not set.
    - The event severity is below ``SLACK_MIN_SEVERITY``.

    Logs a warning (does **not** raise) on HTTP errors so one bad Slack call
    does not kill the consumer loop.
    """
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "").strip()
    if not webhook_url:
        log.debug("SLACK_WEBHOOK_URL not set — skipping Slack notification")
        return

    min_severity = os.environ.get("SLACK_MIN_SEVERITY", AlertSeverity.LOW.value).strip().lower()
    min_rank = _SEVERITY_ORDER.get(min_severity, 0)
    event_rank = _SEVERITY_ORDER.get(event.severity, 0)

    if event_rank < min_rank:
        log.debug(
            "Slack: skipping event_id=%s — severity %s below minimum %s",
            event.event_id, event.severity, min_severity,
        )
        return

    payload = _build_payload(event)

    try:
        resp = requests.post(
            webhook_url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        resp.raise_for_status()
        log.info(
            "Slack notified | symbol=%s  type=%s  severity=%s  event_id=%s",
            event.symbol, event.alert_type, event.severity, event.event_id,
        )
    except requests.HTTPError as exc:
        log.warning(
            "Slack HTTP error %s for event_id=%s: %s",
            exc.response.status_code, event.event_id, exc.response.text,
        )
    except requests.RequestException as exc:
        log.warning("Slack request failed for event_id=%s: %s", event.event_id, exc)
