import duckdb

from consumer.landing import DDL, land_messages
from producer.events import EVENT_TYPES, generate


def test_generator_is_deterministic():
    assert generate(30, 14, seed=3) == generate(30, 14, seed=3)


def test_generator_injects_duplicates_and_malformed_events():
    ev = generate(120, 30, seed=1)
    ids = [e["event_id"] for e in ev]
    assert len(ids) > len(set(ids)), "expected duplicate deliveries"
    assert any(e["event_type"] not in EVENT_TYPES for e in ev), "expected malformed events"


def test_landing_is_idempotent_on_replay():
    con = duckdb.connect(":memory:")
    con.execute(DDL)
    rows = [("app_events", 0, i, "u", '{"event_id": "%d"}' % i, 1_700_000_000_000) for i in range(5)]
    assert land_messages(con, rows) == 5
    assert land_messages(con, rows) == 0  # replaying the same offsets inserts nothing
    assert land_messages(con, rows + [("app_events", 0, 5, "u", "{}", 1_700_000_000_000)]) == 1
