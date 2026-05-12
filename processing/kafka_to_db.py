import json
import logging
from confluent_kafka import Consumer, KafkaError
from shared.db_client import execute_write
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("kafka_to_db")

def run():
    consumer = Consumer({
        "bootstrap.servers": "127.0.0.1:9092",
        "group.id": "db-persistence-group",
        "auto.offset.reset": "latest"
    })
    # Subscribe to both ticks and alerts
    consumer.subscribe(["ticks", "alerts"])
    log.info("Kafka-to-DB Sink started - listening for 'ticks' and 'alerts'")

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None: continue
            if msg.error():
                if msg.error().code() != KafkaError._PARTITION_EOF:
                    log.error(f"Kafka error: {msg.error()}")
                continue

            topic = msg.topic()
            try:
                data = json.loads(msg.value().decode())
                
                if topic == "ticks":
                    save_tick(data)
                elif topic == "alerts":
                    save_alert(data)
                    
            except Exception as e:
                log.error(f"Failed to process message from {topic}: {e}")

    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()

def save_tick(data):
    sql = """
        INSERT INTO ticks (time, symbol, price, volume, source, event_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
    """
    ts = data.get("timestamp")
    if isinstance(ts, (int, float)):
        ts_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    else:
        ts_dt = datetime.now(timezone.utc)

    execute_write(sql, (
        ts_dt,
        data.get("symbol"),
        float(data.get("price", 0)),
        int(data.get("volume", 0)),
        data.get("source", "unknown"),
        data.get("event_id", "none")
    ))

def save_alert(data):
    sql = """
    INSERT INTO alerts (time, symbol, alert_type, severity, message, trigger_price, event_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (event_id, time) DO NOTHING
    """
    ts = data.get("timestamp")
    if isinstance(ts, (int, float)):
        ts_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    else:
        # Fallback for ISO strings or missing
        try:
            ts_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except:
            ts_dt = datetime.now(timezone.utc)

    execute_write(sql, (
        ts_dt,
        data.get("symbol"),
        data.get("alert_type"),
        data.get("severity"),
        data.get("message", "Anomaly detected"),
        float(data.get("trigger_price", 0)),
        data.get("event_id", "none")
    ))
    log.info(f"Saved alert to DB: {data.get('symbol')} - {data.get('alert_type')}")

if __name__ == "__main__":
    run()
