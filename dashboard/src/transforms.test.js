import { describe, expect, it } from "vitest";
import { dauSeries, funnelSteps, retentionCurve } from "./transforms.js";

describe("transforms", () => {
  it("sums active users across platforms per day and filters by platform", () => {
    const rows = [
      { event_date: "2026-09-02T00:00:00", platform: "ios", active_users: 3 },
      { event_date: "2026-09-02T00:00:00", platform: "web", active_users: 2 },
      { event_date: "2026-09-01T00:00:00", platform: "ios", active_users: 1 },
    ];
    expect(dauSeries(rows)).toEqual([{ date: "09-01", users: 1 }, { date: "09-02", users: 5 }]);
    expect(dauSeries(rows, "web")).toEqual([{ date: "09-02", users: 2 }]);
  });

  it("computes funnel percentages relative to app opens", () => {
    const rows = [{ dietary_goal: "a", opened: 10, searched: 8, viewed: 8, added_to_plan: 4, completed_plan: 2 }];
    const f = funnelSteps(rows);
    expect(f[0].pct).toBe(100);
    expect(f[3].pct).toBe(40);
    expect(f[4].pct).toBe(20);
  });

  it("weights retention by cohort size", () => {
    const rows = [
      { weeks_since_signup: 1, active_users: 5, cohort_size: 10 },
      { weeks_since_signup: 1, active_users: 30, cohort_size: 30 },
    ];
    expect(retentionCurve(rows)).toEqual([{ week: "W1", retention: 87.5 }]);
  });
});
