# alerts/email_notifier.py
#
# Person 5 — Alerting & notification engineer
#
# Sends alert notifications via SendGrid's Mail Send API.
# Only fires for HIGH-severity alerts by default (configurable).
#
# Required environment variables
# --------------------------------
#   SENDGRID_API_KEY    — your SendGrid API key
#   EMAIL_FROM          — verified sender address (e.g. alerts@yourapp.com)
#   EMAIL_TO            — recipient address (comma-separated for multiple)
#
# Optional environment variables
# --------------------------------
#   EMAIL_MIN_SEVERITY  — minimum severity to email (low | medium | high)
#                         default: "high"

import json
import logging
import os

import requests

from shared.constants import AlertSeverity
from shared.schema import AlertEvent

log = logging.getLogger(__name__)

SENDGRID_MAIL_URL = "https://api.sendgrid.com/v3/mail/send"

_SEVERITY_ORDER = {
    AlertSeverity.LOW.value:    0,
    AlertSeverity.MEDIUM.value: 1,
    AlertSeverity.HIGH.value:   2,
}


def _build_html_body(event: AlertEvent) -> str:
    """Render a simple HTML email body for *event*."""
    rows = [
        ("Symbol",     event.symbol),
        ("Alert Type", event.alert_type),
        ("Severity",   event.severity.upper()),
        ("Message",    event.message),
    ]
    if event.trigger_price is not None:
        rows.append(("Trigger Price", f"${event.trigger_price:.4f}"))
    if event.trigger_volume is not None:
        rows.append(("Trigger Volume", f"{event.trigger_volume:,}"))
    if event.zscore is not None:
        rows.append(("Z-Score", f"{event.zscore:.2f}"))
    if event.reference_value is not None:
        rows.append(("Reference Value", f"{event.reference_value:.4f}"))
    if event.window_sec is not None:
        rows.append(("Window", f"{event.window_sec}s"))
    rows.append(("Event ID", event.event_id))

    table_rows = "".join(
        f"<tr><td style='padding:4px 12px;font-weight:bold'>{k}</td>"
        f"<td style='padding:4px 12px'>{v}</td></tr>"
        for k, v in rows
    )
    return f"""
<html><body>
<h2 style='color:#cc0000'>Market Alert — {event.symbol}</h2>
<table border='0' cellpadding='0' cellspacing='0'>
{table_rows}
</table>
</body></html>
"""


def _build_payload(event: AlertEvent, from_addr: str, to_addrs: list[str]) -> dict:
    """Build the SendGrid v3 mail/send JSON payload."""
    subject = (
        f"[{event.severity.upper()}] Market Alert — {event.symbol} / {event.alert_type}"
    )
    return {
        "personalizations": [
            {"to": [{"email": addr.strip()} for addr in to_addrs]}
        ],
        "from":    {"email": from_addr},
        "subject": subject,
        "content": [
            {"type": "text/html", "value": _build_html_body(event)},
        ],
    }


def send_email_alert(event: AlertEvent) -> None:
    """
    Send an email notification for *event* via SendGrid.

    Skips silently when:
    - Any of ``SENDGRID_API_KEY``, ``EMAIL_FROM``, or ``EMAIL_TO`` is missing.
    - The event severity is below ``EMAIL_MIN_SEVERITY`` (default: high).

    Logs a warning (does **not** raise) on HTTP errors.
    """
    api_key   = os.environ.get("SENDGRID_API_KEY", "").strip()
    from_addr = os.environ.get("EMAIL_FROM", "").strip()
    to_raw    = os.environ.get("EMAIL_TO", "").strip()

    if not api_key or not from_addr or not to_raw:
        log.debug("SendGrid env vars not fully set — skipping email notification")
        return

    min_severity = os.environ.get(
        "EMAIL_MIN_SEVERITY", AlertSeverity.HIGH.value
    ).strip().lower()
    min_rank   = _SEVERITY_ORDER.get(min_severity, 2)
    event_rank = _SEVERITY_ORDER.get(event.severity, 0)

    if event_rank < min_rank:
        log.debug(
            "Email: skipping event_id=%s — severity %s below minimum %s",
            event.event_id, event.severity, min_severity,
        )
        return

    to_addrs = [a for a in to_raw.split(",") if a.strip()]
    payload  = _build_payload(event, from_addr, to_addrs)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type":  "application/json",
    }

    try:
        resp = requests.post(
            SENDGRID_MAIL_URL,
            data=json.dumps(payload),
            headers=headers,
            timeout=15,
        )
        resp.raise_for_status()
        log.info(
            "Email sent | symbol=%s  type=%s  severity=%s  to=%s  event_id=%s",
            event.symbol, event.alert_type, event.severity,
            to_addrs, event.event_id,
        )
    except requests.HTTPError as exc:
        log.warning(
            "SendGrid HTTP error %s for event_id=%s: %s",
            exc.response.status_code, event.event_id, exc.response.text,
        )
    except requests.RequestException as exc:
        log.warning("Email request failed for event_id=%s: %s", event.event_id, exc)
