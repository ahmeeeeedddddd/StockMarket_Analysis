# alerts/email_notifier.py
#
# Person 5 — Alerting & notification engineer
#
# Sends alert notifications via standard SMTP (e.g. Gmail).
# Only fires for HIGH-severity alerts by default (configurable).
#
# Required environment variables
# --------------------------------
#   GMAIL_SMTP_HOST     — smtp.gmail.com
#   GMAIL_SMTP_PORT     — 587
#   GMAIL_SMTP_USER     — your Gmail address
#   GMAIL_SMTP_PASS     — your Gmail App Password
#   EMAIL_TO            — recipient address (comma-separated for multiple)
#
# Optional environment variables
# --------------------------------
#   EMAIL_MIN_SEVERITY  — minimum severity to email (low | medium | high)
#                         default: "high"

import logging
import os
import smtplib
from email.message import EmailMessage

from shared.constants import AlertSeverity
from shared.schema import AlertEvent

log = logging.getLogger(__name__)

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


def _build_email(event: AlertEvent, from_addr: str, to_addrs: list[str]) -> EmailMessage:
    """Build the EmailMessage object for SMTP sending."""
    msg = EmailMessage()
    subject = f"[{event.severity.upper()}] Market Alert — {event.symbol} / {event.alert_type}"
    
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_addrs)
    
    html_content = _build_html_body(event)
    msg.set_content(f"Market Alert: {subject}\n\n{event.message}") # Fallback text
    msg.add_alternative(html_content, subtype='html')
    
    return msg


def send_email_alert(event: AlertEvent) -> None:
    """
    Send an email notification for *event* via SMTP.

    Skips silently when required SMTP env vars or EMAIL_TO are missing.
    Logs a warning (does **not** raise) on SMTP errors.
    """
    smtp_host = os.environ.get("GMAIL_SMTP_HOST", "").strip()
    smtp_port = os.environ.get("GMAIL_SMTP_PORT", "").strip()
    smtp_user = os.environ.get("GMAIL_SMTP_USER", "").strip()
    smtp_pass = os.environ.get("GMAIL_SMTP_PASS", "").strip()
    to_raw    = os.environ.get("EMAIL_TO", "").strip()

    if not smtp_host or not smtp_user or not smtp_pass or not to_raw:
        log.warning("SMTP configuration is incomplete in .env! (HOST=%s, USER=%s, TO=%s)", 
                    bool(smtp_host), bool(smtp_user), bool(to_raw))
        return
        
    try:
        port = int(smtp_port) if smtp_port else 587
    except ValueError:
        port = 587

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
    msg = _build_email(event, smtp_user, to_addrs)

    try:
        # Connect to SMTP server
        log.info("Connecting to SMTP server %s:%s...", smtp_host, port)
        server = smtplib.SMTP(smtp_host, port, timeout=15)
        # server.set_debuglevel(1) # Uncomment for extreme raw SMTP logs in console
        server.starttls()
        
        log.info("Attempting SMTP login for %s...", smtp_user)
        server.login(smtp_user, smtp_pass)
        
        # Send
        server.send_message(msg)
        server.quit()
        
        log.info(
            "SUCCESS: Email sent | symbol=%s  type=%s  to=%s",
            event.symbol, event.alert_type, to_addrs
        )
    except smtplib.SMTPAuthenticationError:
        log.error("CRITICAL: SMTP Authentication failed. Check GMAIL_SMTP_USER and GMAIL_SMTP_PASS (App Password).")
    except smtplib.SMTPConnectError:
        log.error("CRITICAL: Could not connect to SMTP server. Check host/port and internet connection.")
    except Exception as exc:
        log.error(
            "ERROR: SMTP sending failed for event_id=%s: %s",
            event.event_id, exc,
        )
