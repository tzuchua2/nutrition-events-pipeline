"""Export the dbt marts to JSON for the React dashboard (the 'serving' step)."""
import argparse
import datetime as dt
import decimal
import json
import os

import duckdb

TABLES = {
    "daily_active_users": "select * from fct_daily_active_users order by event_date, platform",
    "funnel": "select * from fct_funnel order by dietary_goal",
    "retention": "select * from fct_weekly_retention order by signup_week, weeks_since_signup",
    "top_recipes": "select * from fct_top_recipes where popularity_rank <= 10 order by popularity_rank, recipe_id",
    "quality": (
        "select (select count(*) from raw.events) as landed, (select count(*) from stg_events) as valid_unique, "
        "(select count(*) from stg_events_rejected) as rejected"
    ),
}


def _j(o):
    if isinstance(o, (dt.date, dt.datetime)):
        return o.isoformat()
    if isinstance(o, decimal.Decimal):
        return float(o)
    raise TypeError(type(o))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/warehouse.duckdb")
    ap.add_argument("--out", default="dashboard/public/marts.json")
    a = ap.parse_args()
    con = duckdb.connect(a.db, read_only=True)
    out = {"generated_at": dt.datetime.now(dt.timezone.utc).isoformat(), "synthetic_data": True}
    for k, q in TABLES.items():
        cur = con.execute(q)
        cols = [c[0] for c in cur.description]
        out[k] = [dict(zip(cols, r)) for r in cur.fetchall()]
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w") as f:
        json.dump(out, f, default=_j, indent=1)
    print(json.dumps({k: len(v) for k, v in out.items() if isinstance(v, list)}))


if __name__ == "__main__":
    main()
