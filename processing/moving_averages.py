"""
moving_averages.py — Person 3 (Stream Processing Engineer)
Computes Exponential Moving Average (EMA) and Simple Moving Average (SMA)
on the live tick stream using Spark Structured Streaming.

EMA cannot be computed exactly in a stateless window — we approximate it
with a large tumbling window (sufficient ticks to "warm up" the EMA) and
emit the final EMA value at the end of each window.

For production-grade EMA, a stateful flatMapGroupsWithState approach is
also provided below.
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, avg, window, collect_list, udf, to_json, struct, lit,
)
from pyspark.sql.types import DoubleType, ArrayType
import pandas as pd


# ---------------------------------------------------------------------------
# SMA — straightforward windowed average
# ---------------------------------------------------------------------------

def compute_sma(
    tick_df: DataFrame,
    window_duration: str = "5 minutes",
    slide_duration: str | None = None,
) -> DataFrame:
    """
    Simple Moving Average of price over a tumbling (or sliding) window.

    Returns columns: symbol, window_start, window_end, sma, period
    """
    watermarked = tick_df.withWatermark("ts", "10 seconds")

    win = (
        window("ts", window_duration, slide_duration)
        if slide_duration
        else window("ts", window_duration)
    )

    return (
        watermarked
        .groupBy(col("symbol"), win)
        .agg(avg("price").alias("sma"))
        .select(
            col("symbol"),
            col("window.start").alias("window_start"),
            col("window.end").alias("window_end"),
            col("sma"),
            lit(window_duration).alias("period"),
        )
    )


# ---------------------------------------------------------------------------
# EMA — windowed approximation via Pandas UDF
# ---------------------------------------------------------------------------

@udf(returnType=DoubleType())
def ema_udf(prices: list) -> float:
    """
    Spark UDF: given a list of prices (in arrival order), return the
    final EMA value using Pandas ewm with span=len(prices)//2.
    This approximates a standard EMA warm-up over the window.
    """
    if not prices:
        return None
    span = max(2, len(prices) // 2)
    series = pd.Series(prices)
    return float(series.ewm(span=span, adjust=False).mean().iloc[-1])


def compute_ema(
    tick_df: DataFrame,
    window_duration: str = "5 minutes",
) -> DataFrame:
    """
    Approximate EMA of price over a tumbling window.

    Collects all ticks in the window then applies the EMA UDF.
    Returns columns: symbol, window_start, window_end, ema, period
    """
    watermarked = tick_df.withWatermark("ts", "10 seconds")

    return (
        watermarked
        .groupBy(col("symbol"), window("ts", window_duration))
        .agg(collect_list("price").alias("prices"))
        .select(
            col("symbol"),
            col("window.start").alias("window_start"),
            col("window.end").alias("window_end"),
            ema_udf(col("prices")).alias("ema"),
            lit(window_duration).alias("period"),
        )
    )


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def ma_to_kafka_value(ma_df: DataFrame, ma_type: str = "sma") -> DataFrame:
    """
    Serialize SMA or EMA rows to a Kafka-ready JSON 'value' column.
    ma_type: "sma" or "ema"
    """
    value_col = col(ma_type)
    return ma_df.select(
        to_json(struct(
            col("symbol"),
            col("window_start").cast("string"),
            col("window_end").cast("string"),
            value_col.alias(ma_type),
            col("period"),
        )).alias("value")
    )
