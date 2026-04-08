import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ResponsiveContainer, Tooltip, LineChart, Line, CartesianGrid, XAxis, YAxis } from "recharts";

import { EmptyState } from "../components/EmptyState";
import { Panel } from "../components/Panel";
import { StatusBadge } from "../components/Badge";
import { api } from "../lib/api";
import { clip, formatDateTime } from "../lib/format";

export function TimelinePage() {
  const [filters, setFilters] = useState({ wing: "", room: "", memory_type: "", status: "" });
  const query = useQuery({
    queryKey: ["timeline", filters],
    queryFn: () => api.timeline(filters),
  });

  const data = query.data ?? {};
  const created = ((data.series as Record<string, any>)?.created ?? []) as Array<Record<string, any>>;
  const relations = ((data.series as Record<string, any>)?.relations ?? []) as Array<Record<string, any>>;
  const map = new Map<string, { day: string; created: number; relations: number }>();
  created.forEach((item) => {
    map.set(String(item.day), {
      day: String(item.day),
      created: Number(item.count),
      relations: 0,
    });
  });
  relations.forEach((item) => {
    const day = String(item.day);
    const current = map.get(day) ?? { day, created: 0, relations: 0 };
    current.relations += Number(item.count);
    map.set(day, current);
  });
  const mergedSeries = Array.from(map.values()).sort((a, b) => a.day.localeCompare(b.day));

  return (
    <div className="space-y-6">
      <Panel>
        <div className="flex flex-wrap gap-3">
          {Object.entries(filters).map(([key, value]) => (
            <input
              key={key}
              value={value}
              onChange={(event) =>
                setFilters((current) => ({ ...current, [key]: event.target.value }))
              }
              placeholder={key.replace("_", " ")}
              className="rounded-2xl border border-edge bg-black/20 px-4 py-3 text-sm outline-none placeholder:text-slate-500"
            />
          ))}
        </div>
      </Panel>
      <Panel>
        <div className="mb-4">
          <h2 className="font-display text-2xl">Lifecycle timeline</h2>
          <div className="text-sm text-slate-400">
            Created memories and relation events across the selected slice.
          </div>
        </div>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={mergedSeries}>
              <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
              <XAxis dataKey="day" stroke="#7f93a8" />
              <YAxis stroke="#7f93a8" />
              <Tooltip />
              <Line type="monotone" dataKey="created" stroke="#80e7ff" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="relations" stroke="#f48c7f" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Panel>
      <Panel>
        <div className="mb-4">
          <h2 className="font-display text-2xl">Recent events</h2>
          <div className="text-sm text-slate-400">Click through in the explorer for deep inspection.</div>
        </div>
        <div className="space-y-3">
          {(((query.data?.events ?? []) as Array<Record<string, any>>) || []).map((event) => (
            <div key={String(event.id)} className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="text-xs uppercase tracking-[0.18em] text-muted">
                  {event.wing} / {event.room} / {event.memory_type}
                </div>
                <StatusBadge status={String(event.status)} />
              </div>
              <div className="mt-2 text-sm text-white">{clip(String(event.excerpt), 160)}</div>
              <div className="mt-2 text-xs text-slate-400">{formatDateTime(String(event.timestamp))}</div>
            </div>
          ))}
        </div>
        {!((query.data?.events ?? []) as Array<unknown>).length ? (
          <div className="mt-4">
            <EmptyState title="No events in range" description="Adjust the filters or load demo mode." />
          </div>
        ) : null}
      </Panel>
    </div>
  );
}
