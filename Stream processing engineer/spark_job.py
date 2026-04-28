"""
spark_job.py — Person 3 (Stream Processing Engineer)
Main entrypoint for the stream processing job.

Wires together:
  1. Kafka tick stream  (kafka_consumer.py)
  2. VWAP computation   (vwap.py)
  3. Candlestick bars   (candlesticks.py)
  4. Moving averages    (moving_averages.py)

Writes results to:
  - Kafka topics:   aggregates, candles_1m, candles_5m, candles_15m
  - TimescaleDB:    vwap, candles, moving_averages

Run with:
    spark-submit \
        --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 \
        spark_job.py \
        [--kafka-bootstrap localhost:9092] \
        [--jdbc-url jdbc:postgresql://localhost:5432/market] \
        [--db-user postgres] [--db-password postgres]
"""

import argparse
import logging

from kafka_consumer import get_spark, read_tick_stream, write_to_kafka, write_to_timescale
from vwap import compute_vwap, vwap_to_kafka_value
from candlesticks import compute_all_candles, candles_to_kafka_value
from moving_averages import compute_sma, compute_ema, ma_to_kafka_value

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Market data stream processor")
    p.add_argument("--kafka-bootstrap", default="localhost:9092")
    p.add_argument("--tick-topic",      default="ticks")
    p.add_argument("--jdbc-url",        default="jdbc:postgresql://localhost:5432/market")
    p.add_argument("--db-user",         default="postgres")
    p.add_argument("--db-password",     default="postgres")
    p.add_argument("--checkpoint-base", default="/tmp/checkpoints")
    return p.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()
    spark = get_spark("MarketStreamProcessor")
    spark.sparkContext.setLogLevel("WARN")

    log.info("Reading tick stream from Kafka topic '%s'", args.tick_topic)
    ticks = read_tick_stream(
        spark,
        kafka_bootstrap=args.kafka_bootstrap,
        topic=args.tick_topic,
    )

    # ── VWAP ──────────────────────────────────────────────────────────────
    log.info("Setting up VWAP computation (1-minute windows)")
    vwap_df  = compute_vwap(ticks, window_duration="1 minute")

    write_to_kafka(
        vwap_to_kafka_value(vwap_df),
        kafka_bootstrap=args.kafka_bootstrap,
        topic="aggregates",
        checkpoint_path=f"{args.checkpoint_base}/vwap_kafka",
    )
    write_to_timescale(
        vwap_df,
        table="vwap",
        jdbc_url=args.jdbc_url,
        db_user=args.db_user,
        db_password=args.db_password,
        checkpoint_path=f"{args.checkpoint_base}/vwap_ts",
    )

    # ── Candlesticks (1m / 5m / 15m) ──────────────────────────────────────
    log.info("Setting up candlestick computation for 1m, 5m, 15m")
    candle_streams = compute_all_candles(ticks)

    for label, candle_df in candle_streams.items():
        write_to_kafka(
            candles_to_kafka_value(candle_df),
            kafka_bootstrap=args.kafka_bootstrap,
            topic=f"candles_{label}",
            checkpoint_path=f"{args.checkpoint_base}/candles_{label}_kafka",
        )
        write_to_timescale(
            candle_df,
            table="candles",
            jdbc_url=args.jdbc_url,
            db_user=args.db_user,
            db_password=args.db_password,
            checkpoint_path=f"{args.checkpoint_base}/candles_{label}_ts",
        )

    # ── Moving Averages ────────────────────────────────────────────────────
    log.info("Setting up SMA and EMA computation (5-minute windows)")
    sma_df = compute_sma(ticks, window_duration="5 minutes")
    ema_df = compute_ema(ticks, window_duration="5 minutes")

    write_to_timescale(
        sma_df,
        table="moving_averages",
        jdbc_url=args.jdbc_url,
        db_user=args.db_user,
        db_password=args.db_password,
        checkpoint_path=f"{args.checkpoint_base}/sma_ts",
    )
    write_to_timescale(
        ema_df,
        table="moving_averages",
        jdbc_url=args.jdbc_url,
        db_user=args.db_user,
        db_password=args.db_password,
        checkpoint_path=f"{args.checkpoint_base}/ema_ts",
    )

    # ── Await termination ─────────────────────────────────────────────────
    log.info("All streaming queries started — awaiting termination")
    spark.streams.awaitAnyTermination()


if __name__ == "__main__":
    main()
