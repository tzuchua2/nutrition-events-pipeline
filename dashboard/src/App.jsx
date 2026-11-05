import React, { useEffect, useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { dauSeries, funnelSteps, retentionCurve } from "./transforms.js";

const PLATFORMS = ["all", "ios", "android", "web"];

function Card({ title, note, children }) {
  return (
    <section className="card">
      <h2>{title}</h2>
      {note && <p className="note">{note}</p>}
      <div className="chart">{children}</div>
    </section>
  );
}

export default function App() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [platform, setPlatform] = useState("all");
  const [goal, setGoal] = useState("all");

  useEffect(() => {
    fetch("./marts.json")
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`marts.json: HTTP ${r.status}`))))
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);

  const dau = useMemo(() => (data ? dauSeries(data.daily_active_users, platform) : []), [data, platform]);
  const funnel = useMemo(() => (data ? funnelSteps(data.funnel, goal) : []), [data, goal]);
  const retention = useMemo(() => (data ? retentionCurve(data.retention) : []), [data]);

  if (error) return <main className="wrap"><p role="alert">Could not load data: {error}. Run the pipeline first.</p></main>;
  if (!data) return <main className="wrap"><p>Loading…</p></main>;

  const q = data.quality[0];
  const goals = ["all", ...data.funnel.map((f) => f.dietary_goal)];
  return (
    <main className="wrap">
      <header>
        <h1>Nutrition App Events</h1>
        <p className="sub">
          Kafka → Airflow → dbt → React. Synthetic data. Updated {new Date(data.generated_at).toLocaleString()}.
        </p>
      </header>

      <div className="kpis">
        <div><b>{q.landed.toLocaleString()}</b><span>events landed</span></div>
        <div><b>{q.valid_unique.toLocaleString()}</b><span>valid, de-duplicated</span></div>
        <div><b>{q.rejected}</b><span>quarantined as malformed</span></div>
      </div>

      <Card title="Daily active users" note="Distinct users with at least one event per day.">
        <div className="filters" role="group" aria-label="Platform filter">
          {PLATFORMS.map((p) => (
            <button key={p} className={p === platform ? "on" : ""} onClick={() => setPlatform(p)}>{p}</button>
          ))}
        </div>
        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={dau}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--line)" />
            <XAxis dataKey="date" interval={6} tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Line type="monotone" dataKey="users" stroke="#2563eb" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </Card>

      <Card title="Meal-planning funnel" note="Daily sessions reaching each step, as % of app opens.">
        <div className="filters" role="group" aria-label="Dietary goal filter">
          {goals.map((g) => (
            <button key={g} className={g === goal ? "on" : ""} onClick={() => setGoal(g)}>{g.replace("_", " ")}</button>
          ))}
        </div>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={funnel} layout="vertical" margin={{ left: 40 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis type="number" domain={[0, 100]} unit="%" tick={{ fontSize: 12 }} />
            <YAxis type="category" dataKey="step" width={140} tick={{ fontSize: 12 }} />
            <Tooltip formatter={(v, n, p) => [`${v}% (${p.payload.sessions} sessions)`, "of opens"]} />
            <Bar dataKey="pct" fill="#16a34a" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Card>

      <Card title="Weekly retention" note="Share of each signup cohort still active N weeks later (cohort-size weighted).">
        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={retention}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="week" tick={{ fontSize: 12 }} />
            <YAxis unit="%" domain={[0, 100]} tick={{ fontSize: 12 }} />
            <Tooltip />
            <Line type="monotone" dataKey="retention" stroke="#9333ea" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </Card>

      <Card title="Most added recipes" note="Top recipes by additions to a meal plan.">
        <table>
          <thead><tr><th>#</th><th>Recipe</th><th>Views</th><th>Added</th><th>Add rate</th></tr></thead>
          <tbody>
            {data.top_recipes.map((r) => (
              <tr key={r.recipe_id}>
                <td>{r.popularity_rank}</td><td>{r.recipe_id}</td><td>{r.views}</td><td>{r.adds_to_plan}</td>
                <td>{(r.add_rate * 100).toFixed(0)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </main>
  );
}
