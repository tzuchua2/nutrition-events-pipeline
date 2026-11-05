"""Deterministic synthetic event generator for a nutrition/meal-planning app.

The data is SYNTHETIC (no real user or company data). It models a funnel:
app_opened -> recipe_searched -> recipe_viewed -> meal_added_to_plan -> plan_completed,
with users retaining/churning over weeks, so downstream retention and funnel models have real structure.
"""
import hashlib
import json
import random
import uuid
from datetime import datetime, timedelta, timezone

EVENT_TYPES = ["app_opened", "recipe_searched", "recipe_viewed", "meal_added_to_plan", "plan_completed"]
PLATFORMS = ["ios", "android", "web"]
GOALS = ["balanced", "high_protein", "low_sodium", "diabetes_friendly", "heart_healthy"]
RECIPES = [f"recipe_{i:03d}" for i in range(1, 61)]
SCHEMA_VERSION = 1


def _eid(*parts) -> str:
    return str(uuid.UUID(hashlib.md5("|".join(map(str, parts)).encode()).hexdigest()))


def generate(n_users=300, days=42, seed=7, start=None):
    """Yield event dicts in timestamp order (deterministic for a given seed)."""
    rng = random.Random(seed)
    start = start or datetime(2026, 9, 1, tzinfo=timezone.utc)
    events = []
    for u in range(n_users):
        uid = f"user_{u:04d}"
        platform = rng.choices(PLATFORMS, weights=[5, 4, 2])[0]
        goal = rng.choice(GOALS)
        signup_day = int(rng.random() ** 1.5 * (days - 7))
        stickiness = rng.betavariate(2, 3)  # probability of returning on a given day
        day = signup_day
        while day < days:
            if day == signup_day or rng.random() < stickiness * 0.55:
                t = start + timedelta(days=day, hours=rng.randint(6, 22), minutes=rng.randint(0, 59))
                seq = 0

                def emit(kind, recipe=None, dt=0):
                    nonlocal seq
                    seq += 1
                    ts = t + timedelta(seconds=dt + seq * rng.randint(5, 40))
                    events.append({
                        "event_id": _eid(uid, day, seq, kind),
                        "schema_version": SCHEMA_VERSION,
                        "user_id": uid,
                        "event_type": kind,
                        "event_ts": ts.isoformat(),
                        "platform": platform,
                        "dietary_goal": goal,
                        "recipe_id": recipe,
                    })

                emit("app_opened")
                if rng.random() < 0.8:
                    emit("recipe_searched")
                    for _ in range(rng.randint(1, 4)):
                        r = rng.choice(RECIPES)
                        emit("recipe_viewed", r)
                        if rng.random() < 0.35:
                            emit("meal_added_to_plan", r)
                    if rng.random() < 0.25 * (1 + stickiness):
                        emit("plan_completed")
            day += 1
    events.sort(key=lambda e: e["event_ts"])
    # inject realistic mess: ~1% duplicates (at-least-once delivery) and ~0.3% malformed events
    out = []
    for e in events:
        out.append(e)
        if rng.random() < 0.01:
            out.append(dict(e))  # duplicate delivery with same event_id
    bad = []
    for i in range(0, len(out), 330):
        # malformed copy of a real event (unknown type, new id) -> must be caught and quarantined downstream
        bad.append({**out[i], "event_id": _eid("bad", i), "event_type": "BAD_TYPE_%d" % i})
    out = out + bad
    out.sort(key=lambda e: e["event_ts"])
    return out


def to_message(e: dict) -> tuple[str, bytes]:
    return e["user_id"], json.dumps(e).encode()
