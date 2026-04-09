# shared/db_client.py

import psycopg2
import psycopg2.extras
from psycopg2.extensions import connection as PgConnection


# ---------------------------------------------------------------------------
# Hardcoded connection settings — matches docker-compose.yml TimescaleDB setup
# ---------------------------------------------------------------------------

DB_HOST     = "localhost"
DB_PORT     = 5433
DB_NAME     = "stockmarket"
DB_USER     = "postgres"
DB_PASSWORD = "postgres"


# ---------------------------------------------------------------------------
# Connection factory — every module calls this to get a connection
# ---------------------------------------------------------------------------

def get_db_connection() -> PgConnection:
    """
    Returns a new psycopg2 connection to TimescaleDB.

    Usage in any module
    -------------------
        from shared.db_client import get_db_connection

        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM ticks LIMIT 5")
                rows = cur.fetchall()
        finally:
            conn.close()

    Or with a context manager (auto-closes on exit):
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(...)
    """
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )
    # Return dicts instead of tuples — rows["price"] instead of rows[0]
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn


# ---------------------------------------------------------------------------
# Convenience wrapper for one-shot queries (no manual open/close needed)
# ---------------------------------------------------------------------------

def execute_query(sql: str, params: tuple = ()) -> list[dict]:
    """
    Run a SELECT and return all rows as a list of dicts.
    Opens and closes the connection automatically.

    Usage
    -----
        from shared.db_client import execute_query

        rows = execute_query(
            "SELECT * FROM ticks WHERE symbol = %s ORDER BY time DESC LIMIT 100",
            ("AAPL",)
        )
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        conn.close()


def execute_write(sql: str, params: tuple = ()) -> None:
    """
    Run an INSERT / UPDATE / DELETE and commit.
    Opens and closes the connection automatically.

    Usage
    -----
        from shared.db_client import execute_write

        execute_write(
            "INSERT INTO ticks (time, symbol, price, volume) VALUES (%s, %s, %s, %s)",
            (event.timestamp, event.symbol, event.price, event.volume)
        )
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
