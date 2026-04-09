-- infrastructure/timescale_schema.sql
--
-- Idempotent TimescaleDB schema definition for the stockmarket database.
-- Creates hyper-tables for ticks, aggregates, and alerts.
--
-- Applies the TIMESCALE_CHUNK_INTERVAL from shared/constants.py (1 day).

-- Ensure the TimescaleDB extension is enabled
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ============================================================================
-- 1. Ticks Table (Raw trade data and quotes)
-- ============================================================================
CREATE TABLE IF NOT EXISTS ticks (
    time        TIMESTAMPTZ NOT NULL,
    symbol      TEXT        NOT NULL,
    price       DOUBLE PRECISION NOT NULL,
    volume      INTEGER     NOT NULL,
    bid         DOUBLE PRECISION,
    ask         DOUBLE PRECISION,
    source      TEXT        NOT NULL,
    event_id    TEXT        NOT NULL
);

-- Make it a TimescaleDB hypertable partitioned by time
-- chunk_time_interval = 1 day (default, good for our volume)
SELECT create_hypertable(
    'ticks',
    by_range('time'),
    if_not_exists => TRUE
);

-- Index for fast symbol lookups (Timescale automatically indexes 'time')
CREATE INDEX IF NOT EXISTS ix_ticks_symbol_time ON ticks (symbol, time DESC);

-- ============================================================================
-- 2. Aggregates Table (OHLCV and VWAP candles)
-- ============================================================================
-- Note: 'window_start' and 'window_end' are from the schema, but we'll use
-- window_start as 'time' to partition cleanly in Timescale.
CREATE TABLE IF NOT EXISTS aggregates (
    time        TIMESTAMPTZ NOT NULL,
    symbol      TEXT        NOT NULL,
    window_sec  INTEGER     NOT NULL,
    open        DOUBLE PRECISION NOT NULL,
    high        DOUBLE PRECISION NOT NULL,
    low         DOUBLE PRECISION NOT NULL,
    close       DOUBLE PRECISION NOT NULL,
    volume      INTEGER     NOT NULL,
    vwap        DOUBLE PRECISION NOT NULL,
    trade_count INTEGER     NOT NULL,
    event_id    TEXT        NOT NULL,
    window_end  TIMESTAMPTZ NOT NULL
);

SELECT create_hypertable(
    'aggregates',
    by_range('time'),
    if_not_exists => TRUE
);

-- We frequently query specific window sizes (e.g. 1 min or 5 min candles)
CREATE INDEX IF NOT EXISTS ix_aggregates_symbol_window_time ON aggregates (symbol, window_sec, time DESC);

-- ============================================================================
-- 3. Alerts Table (Anomaly detection history)
-- ============================================================================
CREATE TABLE IF NOT EXISTS alerts (
    time            TIMESTAMPTZ NOT NULL,
    symbol          TEXT        NOT NULL,
    alert_type      TEXT        NOT NULL,
    severity        TEXT        NOT NULL,
    message         TEXT        NOT NULL,
    trigger_price   DOUBLE PRECISION,
    trigger_volume  INTEGER,
    zscore          DOUBLE PRECISION,
    reference_value DOUBLE PRECISION,
    window_sec      INTEGER,
    event_id        TEXT        NOT NULL
);

SELECT create_hypertable(
    'alerts',
    by_range('time'),
    if_not_exists => TRUE
);

-- Common dashboard queries: recent alerts per symbol, or all high-severity alerts
CREATE INDEX IF NOT EXISTS ix_alerts_symbol_time ON alerts (symbol, time DESC);
CREATE INDEX IF NOT EXISTS ix_alerts_severity_time ON alerts (severity, time DESC);

-- ============================================================================
-- Permissions (assuming the default postgres user for development)
-- ============================================================================
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
