import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Link } from "react-router-dom";

import { EmptyState } from "../components/EmptyState";
import { Panel } from "../components/Panel";
import { StatCard } from "../components/StatCard";
import { formatNumber, healthTone } from "../lib/format";
import { api } from "../lib/api";

export function DashboardPage() {
  const client = useQueryClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => api.dashboard(),
  });
  const seedMutation = useMutation({
    mutationFn: () => api.seedDemo(),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["dashboard"] });
      client.invalidateQueries({ queryKey: ["memories"] });
      client.invalidateQueries({ queryKey: ["timeline"] });
    },
  });

  if (isLoading) {
    return <Panel>Loading dashboard...</Panel>;
  }
  if (error || !data) {
    return <EmptyState title="Dashboard unavailable" description="The product dashboard could not be loaded." />;
  }

  const stats = data.stats as Record<string, any>;
  const operations = data.operations as Record<string, any>;
  const totals = stats.totals ?? {};
  const createdSeries = ((data.timeline as Record<string, any>)?.created ?? []) as Array<Record<string, any>>;
  const relationSeries = ((data.timeline as Record<string, any>)?.relations ?? []) as Array<Record<string, any>>;
  const byStatus = (stats.by_status ?? []) as Array<Record<string, any>>;
  const byType = (stats.by_type ?? []) as Array<Record<string, any>>;
  const recentMemories = (stats.recent_memories ?? []) as Array<Record<string, any>>;

  return (
    <div className="space-y-6">
      <Panel className="overflow-hidden bg-gradient-to-r from-accent/10 via-transparent to-accentWarm/10">
        <div className="grid gap-6 lg:grid-cols-[1.3fr_0.7fr]">
          <div>
            <div className="text-[11px] uppercase tracking-[0.2em] text-accent">Open Source Product Surface</div>
            <h1 className="mt-3 max-w-3xl font-display text-4xl leading-tight text-white">
              A memory platform for agents with timeline, explainability, lifecycle control, and local-first operations.
            </h1>
            <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-300">
              The engine remains the same. The product layer turns it into something inspectable, demonstrable, and usable by humans.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link className="rounded-2xl bg-white px-4 py-3 text-sm font-medium text-slate-950" to="/ingestion">
                Add memory
              </Link>
              <Link className="rounded-2xl border border-white/15 px-4 py-3 text-sm text-white" to="/query">
                Open query studio
              </Link>
              <Link className="rounded-2xl border border-white/15 px-4 py-3 text-sm text-white" to="/conflicts">
                Inspect conflicts
              </Link>
              <button
                onClick={() => seedMutation.mutate()}
                className="rounded-2xl border border-white/15 px-4 py-3 text-sm text-white"
              >
                Seed demo mode
              </button>
            </div>
            {seedMutation.data ? (
              <div className="mt-4 rounded-2xl border border-success/20 bg-success/10 px-4 py-3 text-sm text-slate-200">
                Demo dataset applied: created {String(seedMutation.data.created)} memories, skipped {String(seedMutation.data.skipped)} duplicates.
              </div>
            ) : null}
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-1">
            {Object.entries((operations.health as Record<string, string>) ?? {}).map(([key, value]) => (
              <div key={key} className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3">
                <div className="text-[11px] uppercase tracking-[0.18em] text-muted">{key}</div>
                <div className={`mt-2 text-lg font-medium ${healthTone(String(value))}`}>{String(value)}</div>
              </div>
            ))}
          </div>
        </div>
      </Panel>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total Memories" value={formatNumber(totals.memories)} />
        <StatCard label="Active" value={formatNumber(byStatus.find((item) => item.status === "active")?.count)} />
        <StatCard label="Conflicting" value={formatNumber(byStatus.find((item) => item.status === "conflicting")?.count)} />
        <StatCard label="Superseded" value={formatNumber(byStatus.find((item) => item.status === "superseded")?.count)} />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]">
        <Panel>
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="font-display text-xl">Memory activity</h2>
              <div className="text-sm text-slate-400">Created memories over time</div>
            </div>
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={createdSeries}>
                <defs>
                  <linearGradient id="fillCreated" x1="0" x2="0" y1="0" y2="1">
                    <stop offset="5%" stopColor="#80e7ff" stopOpacity={0.7} />
                    <stop offset="95%" stopColor="#80e7ff" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
                <XAxis dataKey="day" stroke="#7f93a8" />
                <YAxis stroke="#7f93a8" />
                <Tooltip />
                <Area type="monotone" dataKey="count" stroke="#80e7ff" fill="url(#fillCreated)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Panel>
        <Panel>
          <div>
            <h2 className="font-display text-xl">Distribution</h2>
            <div className="text-sm text-slate-400">Memory types currently indexed</div>
          </div>
          <div className="mt-4 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={byType}>
                <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
                <XAxis dataKey="memory_type" stroke="#7f93a8" />
                <YAxis stroke="#7f93a8" />
                <Tooltip />
                <Bar dataKey="count" fill="#f6c88f" radius={[10, 10, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Panel>
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-display text-xl">Recent memories</h2>
              <div className="text-sm text-slate-400">Latest inserts and lifecycle changes</div>
            </div>
            <Link className="text-sm text-accent" to="/explorer">
              Open explorer
            </Link>
          </div>
          <div className="mt-4 space-y-3">
            {recentMemories.map((item) => (
              <div key={item.id} className="rounded-2xl border border-white/10 bg-black/15 p-4">
                <div className="text-xs uppercase tracking-[0.18em] text-muted">
                  {item.wing} / {item.room} / {item.status}
                </div>
                <div className="mt-2 text-sm text-white">{item.excerpt}</div>
              </div>
            ))}
          </div>
        </Panel>
        <Panel>
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-display text-xl">Relation timeline</h2>
              <div className="text-sm text-slate-400">Conflict and supersession events</div>
            </div>
            <Link className="text-sm text-accent" to="/timeline">
              Open timeline
            </Link>
          </div>
          <div className="mt-4 h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={relationSeries}>
                <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
                <XAxis dataKey="day" stroke="#7f93a8" />
                <YAxis stroke="#7f93a8" />
                <Tooltip />
                <Bar dataKey="count" fill="#58d6a2" radius={[10, 10, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 text-sm text-slate-400">Cache hit/miss: not available in the current engine.</div>
        </Panel>
      </div>
    </div>
  );
}
