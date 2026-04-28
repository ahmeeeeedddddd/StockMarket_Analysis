"""
kafka_consumer.py — Person 3 (Stream Processing Engineer)
Wraps a PySpark Structured Streaming Kafka source with sensible defaults.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import (
    StructType, StructField,
    StringType, DoubleType, LongType, TimestampType,
)

# ---------------------------------------------------------------------------
# Schema for raw tick events published by Person 1
# { "symbol": "AAPL", "price": 189.45, "volume": 1200, "timestamp": 1713000000000 }
# ---------------------------------------------------------------------------
TICK_SCHEMA = StructType([
    StructField("symbol",    StringType(),  nullable=False),
    StructField("price",     DoubleType(),  nullable=False),
    StructField("volume",    LongType(),    nullable=False),
    StructField("timestamp", LongType(),    nullable=False),   # epoch ms
])


def get_spark(app_name: str = "StreamProcessor") -> SparkSession:
    """
    Return (or create) a SparkSession configured for Kafka + TimescaleDB.
    In production the jars are supplied via spark-submit --packages.
    """
    return (
        SparkSession.builder
        .appName(app_name)
        .config(
            "spark.jars.packages",
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,"
            "org.postgresql:postgresql:42.6.0",
        )
        .config("spark.sql.shuffle.partitions", "4")   # tune for cluster size
        .getOrCreate()
    )


def read_tick_stream(
    spark: SparkSession,
    kafka_bootstrap: str = "localhost:9092",
    topic: str = "ticks",
    starting_offsets: str = "latest",
):
    """
    Return a streaming DataFrame of decoded tick events.

    Schema after parsing:
        symbol  STRING
        price   DOUBLE
        volume  LONG
        ts      TIMESTAMP   (derived from epoch-ms 'timestamp' field)
    """
    raw = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", kafka_bootstrap)
        .option("subscribe", topic)
        .option("startingOffsets", starting_offsets)
        .option("failOnDataLoss", "false")
        .load()
    )

    parsed = (
        raw
        .select(from_json(col("value").cast("string"), TICK_SCHEMA).alias("d"))
        .select("d.*")
        .withColumn(
            "ts",
            (col("timestamp") / 1000).cast(TimestampType()),
        )
        .drop("timestamp")
    )

    return parsed


def write_to_kafka(
    df,
    kafka_bootstrap: str = "localhost:9092",
    topic: str,
    checkpoint_path: str,
    trigger_seconds: int = 5,
):
    """
    Write a streaming DataFrame (must have a 'value' STRING column) to Kafka.
    """
    return (
        df.writeStream
        .format("kafka")
        .option("kafka.bootstrap.servers", kafka_bootstrap)
        .option("topic", topic)
        .option("checkpointLocation", checkpoint_path)
        .trigger(processingTime=f"{trigger_seconds} seconds")
        .start()
    )


def write_to_timescale(
    df,
    table: str,
    jdbc_url: str = "jdbc:postgresql://localhost:5432/market",
    db_user: str = "postgres",
    db_password: str = "postgres",
    checkpoint_path: str,
    trigger_seconds: int = 5,
):
    """
    Write a streaming DataFrame to TimescaleDB via the JDBC foreachBatch sink.
    TimescaleDB is Postgres-compatible so we use the standard PG driver.
    """

    def write_batch(batch_df, _epoch_id):
        (
            batch_df.write
            .format("jdbc")
            .option("url", jdbc_url)
            .option("dbtable", table)
            .option("user", db_user)
            .option("password", db_password)
            .option("driver", "org.postgresql.Driver")
            .mode("append")
            .save()
        )

    return (
        df.writeStream
        .foreachBatch(write_batch)
        .option("checkpointLocation", checkpoint_path)
        .trigger(processingTime=f"{trigger_seconds} seconds")
        .start()
    )
