// Pure data helpers (unit-tested in transforms.test.js).

export function dauSeries(rows, platform = "all") {
  const byDay = new Map();
  for (const r of rows) {
    if (platform !== "all" && r.platform !== platform) continue;
    byDay.set(r.event_date, (byDay.get(r.event_date) || 0) + r.active_users);
  }
  return [...byDay.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([date, users]) => ({ date: date.slice(5, 10), users }));
}

export function funnelSteps(rows, goal = "all") {
  const keys = [
    ["opened", "App opened"],
    ["searched", "Searched recipes"],
    ["viewed", "Viewed a recipe"],
    ["added_to_plan", "Added to meal plan"],
    ["completed_plan", "Completed plan"],
  ];
  const sel = goal === "all" ? rows : rows.filter((r) => r.dietary_goal === goal);
  const totals = Object.fromEntries(keys.map(([k]) => [k, sel.reduce((s, r) => s + r[k], 0)]));
  const top = totals.opened || 1;
  return keys.map(([k, label]) => ({ step: label, sessions: totals[k], pct: Math.round((1000 * totals[k]) / top) / 10 }));
}

export function retentionCurve(rows) {
  // size-weighted average retention by weeks since signup across cohorts
  const agg = new Map();
  for (const r of rows) {
    const a = agg.get(r.weeks_since_signup) || { active: 0, size: 0 };
    a.active += r.active_users;
    a.size += r.cohort_size;
    agg.set(r.weeks_since_signup, a);
  }
  return [...agg.entries()].sort(([a], [b]) => a - b).map(([w, { active, size }]) => ({ week: `W${w}`, retention: Math.round((1000 * active) / size) / 10 }));
}
