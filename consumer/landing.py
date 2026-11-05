"""Land raw Kafka messages into DuckDB (ELT: store the payload untouched; validation/dedup happen in dbt).
Landing is idempotent on (topic, partition, offset): replays never create duplicates."""
import duckdb

DDL = """
create schema if not exists raw;
create table if not exists raw.events (
    kafka_topic varchar, kafka_partition integer, kafka_offset bigint,
    kafka_key varchar, payload varchar, kafka_ts timestamp,
    ingested_at timestamp default current_timestamp,
    primary key (kafka_topic, kafka_partition, kafka_offset)
);
"""


def connect(path: str) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(path)
    con.execute(DDL)
    return con


def land_messages(con, rows: list[tuple]) -> int:
    """rows: (topic, partition, offset, key, payload, kafka_ts). Returns rows newly inserted."""
    if not rows:
        return 0
    before = con.execute("select count(*) from raw.events").fetchone()[0]
    con.executemany(
        "insert or ignore into raw.events (kafka_topic, kafka_partition, kafka_offset, kafka_key, payload, kafka_ts) "
        "values (?, ?, ?, ?, ?, to_timestamp(?/1000.0))",
        rows,
    )
    return con.execute("select count(*) from raw.events").fetchone()[0] - before
