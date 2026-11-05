"""Publish synthetic nutrition-app events to Kafka (keyed by user_id so a user's events stay ordered)."""
import argparse, json, sys
from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient, NewTopic
from producer.events import generate, to_message

TOPIC = "app_events"


def ensure_topic(bootstrap: str, partitions: int = 3):
    admin = AdminClient({"bootstrap.servers": bootstrap})
    if TOPIC in admin.list_topics(timeout=10).topics:
        return
    for _, f in admin.create_topics([NewTopic(TOPIC, num_partitions=partitions, replication_factor=1)]).items():
        f.result()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bootstrap", default="localhost:9092")
    ap.add_argument("--users", type=int, default=300)
    ap.add_argument("--days", type=int, default=42)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    ensure_topic(a.bootstrap)
    p = Producer({"bootstrap.servers": a.bootstrap, "enable.idempotence": True, "linger.ms": 20})
    stats = {"ok": 0, "err": 0}

    def cb(err, _msg):
        stats["err" if err else "ok"] += 1

    events = generate(a.users, a.days, a.seed)
    for e in events:
        k, v = to_message(e)
        p.produce(TOPIC, key=k, value=v, callback=cb)
        p.poll(0)
    p.flush(30)
    print(json.dumps({"topic": TOPIC, "generated": len(events), **stats}))
    sys.exit(1 if stats["err"] or stats["ok"] != len(events) else 0)


if __name__ == "__main__":
    main()
