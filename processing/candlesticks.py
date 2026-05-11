"""
candlesticks.py — Person 3 (Stream Processing Engineer)
Produces OHLCV candlestick bars (1m, 5m, 15m) from the raw tick stream.

Each output row:
    symbol      STRING
    interval    STRING   ("1m" | "5m" | "15m")
    open_time   TIMESTAMP
    close_time  TIMESTAMP
    open        DOUBLE
    high        DOUBLE
    low         DOUBLE
    close       DOUBLE
    volume      LONG
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, first, max as _max, min as _min, last, sum as _sum,
    window, to_json, struct, lit,
)

WATERMARK_DELAY = "15 seconds"

# Supported candlestick intervals
INTERVALS: dict[str, str] = {
    "1m":  "1 minute",
    "5m":  "5 minutes",
    "15m": "15 minutes",
}


def compute_candles(
    tick_df: DataFrame,
    interval: str = "1m",
) -> DataFrame:
    """
    Compute OHLCV candles for the given interval.

    Args:
        tick_df:  Streaming tick DataFrame (symbol, price, volume, ts).
        interval: One of "1m", "5m", "15m".

    Returns a streaming DataFrame with OHLCV columns.
    """
    if interval not in INTERVALS:
        raise ValueError(f"interval must be one of {list(INTERVALS)}; got '{interval}'")

    window_duration = INTERVALS[interval]

    watermarked = tick_df.withWatermark("ts", WATERMARK_DELAY)

    candles = (
        watermarked
        .groupBy(col("symbol"), window("ts", window_duration))
        .agg(
            first("price").alias("open"),
            _max("price").alias("high"),
            _min("price").alias("low"),
            last("price").alias("close"),
            _sum("volume").alias("volume"),
        )
        .select(
            col("symbol"),
            lit(interval).alias("interval"),
            col("window.start").alias("open_time"),
            col("window.end").alias("close_time"),
            col("open"),
            col("high"),
            col("low"),
            col("close"),
            col("volume"),
        )
    )

    return candles


def compute_all_candles(tick_df: DataFrame) -> dict[str, DataFrame]:
    """
    Return a dict of streaming DataFrames for every supported interval.

    Usage:
        candle_streams = compute_all_candles(tick_df)
        for label, df in candle_streams.items():
            write_to_kafka(candles_to_kafka_value(df), topic=f"candles_{label}", ...)
    """
    return {interval: compute_candles(tick_df, interval) for interval in INTERVALS}


def candles_to_kafka_value(candle_df: DataFrame) -> DataFrame:
    """
    Serialize candle rows to a Kafka-ready JSON 'value' column.
    """
    return candle_df.select(
        to_json(struct(
            col("symbol"),
            col("interval"),
            col("open_time").cast("string").alias("open_time"),
            col("close_time").cast("string").alias("close_time"),
            col("open"),
            col("high"),
            col("low"),
            col("close"),
            col("volume"),
        )).alias("value")
    )
