"""
vwap.py — Person 3 (Stream Processing Engineer)
Computes Volume-Weighted Average Price (VWAP) over tumbling windows.

VWAP = Σ(price × volume) / Σ(volume)  for each symbol inside a window.
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, sum as _sum, window, to_json, struct, round as _round,
)

# Watermark tolerance: how late can events arrive before we drop them?
WATERMARK_DELAY = "10 seconds"


def compute_vwap(
    tick_df: DataFrame,
    window_duration: str = "1 minute",
    slide_duration: str | None = None,
) -> DataFrame:
    """
    Compute VWAP for each (symbol, window).

    Args:
        tick_df:         Streaming DataFrame from kafka_consumer.read_tick_stream()
        window_duration: Tumbling window size  (e.g. "1 minute", "5 minutes")
        slide_duration:  If set, creates a sliding window; otherwise tumbling.

    Returns a streaming DataFrame with columns:
        symbol      STRING
        window_start TIMESTAMP
        window_end   TIMESTAMP
        vwap         DOUBLE
        total_volume LONG
    """
    watermarked = tick_df.withWatermark("ts", WATERMARK_DELAY)

    win = window("ts", window_duration, slide_duration) if slide_duration else window("ts", window_duration)

    agg = (
        watermarked
        .groupBy(col("symbol"), win)
        .agg(
            (_sum(col("price") * col("volume")) / _sum("volume")).alias("vwap"),
            _sum("volume").alias("total_volume"),
        )
        .select(
            col("symbol"),
            col("window.start").alias("window_start"),
            col("window.end").alias("window_end"),
            _round(col("vwap"), 6).alias("vwap"),
            col("total_volume"),
        )
    )

    return agg


def vwap_to_kafka_value(vwap_df: DataFrame) -> DataFrame:
    """
    Serialize VWAP rows to a Kafka-ready JSON 'value' column.
    """
    return vwap_df.select(
        to_json(struct(
            col("symbol"),
            col("window_start").cast("string").alias("window_start"),
            col("window_end").cast("string").alias("window_end"),
            col("vwap"),
            col("total_volume"),
        )).alias("value")
    )
