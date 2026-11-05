"""Consume the app_events topic and land it in DuckDB. Commits offsets only AFTER the batch is durably written
(at-least-once delivery + idempotent landing = effectively-once into the warehouse)."""
import argparse, json, time
from confluent_kafka import Consumer, KafkaError
from consumer.landing import connect, land_messages

TOPIC = "app_events"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bootstrap", default="localhost:9092")
    ap.add_argument("--db", default="data/warehouse.duckdb")
    ap.add_argument("--group", default="nep-warehouse-loader")
    ap.add_argument("--idle-seconds", type=float, default=8.0, help="stop after this long with no new messages")
    ap.add_argument("--batch", type=int, default=2000)
    a = ap.parse_args()
    con = connect(a.db)
    c = Consumer({"bootstrap.servers": a.bootstrap, "group.id": a.group, "auto.offset.reset": "earliest",
                  "enable.auto.commit": False})
    c.subscribe([TOPIC])
    rows, landed, seen, last = [], 0, 0, time.time()
    while time.time() - last < a.idle_seconds:
        m = c.poll(1.0)
        if m is None:
            continue
        if m.error():
            if m.error().code() != KafkaError._PARTITION_EOF:
                raise RuntimeError(m.error())
            continue
        last = time.time()
        seen += 1
        rows.append((m.topic(), m.partition(), m.offset(), (m.key() or b"").decode(), m.value().decode(), m.timestamp()[1]))
        if len(rows) >= a.batch:
            landed += land_messages(con, rows); c.commit(asynchronous=False); rows = []
    landed += land_messages(con, rows)
    if seen:
        c.commit(asynchronous=False)
    c.close()
    print(json.dumps({"consumed": seen, "newly_landed": landed,
                      "raw_total": con.execute("select count(*) from raw.events").fetchone()[0]}))


if __name__ == "__main__":
    main()
