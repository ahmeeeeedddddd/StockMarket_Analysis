import json
import logging
from shared.db_client import execute_write

logger = logging.getLogger(__name__)

def report_health(service_name: str, status: str = 'running', metrics: dict = None):
    """
    Update the system_health table with the latest heartbeat and metrics for a service.
    """
    try:
        sql = """
            INSERT INTO system_health (service_name, last_heartbeat, status, metrics)
            VALUES (%s, NOW(), %s, %s)
            ON CONFLICT (service_name) DO UPDATE 
            SET last_heartbeat = NOW(), status = EXCLUDED.status, metrics = EXCLUDED.metrics
        """
        execute_write(sql, (service_name, status, json.dumps(metrics or {})))
    except Exception as e:
        logger.error("Failed to report health for %s: %s", service_name, e)
