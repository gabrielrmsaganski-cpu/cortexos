import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { StatusBadge } from "../components/Badge";
import { EmptyState } from "../components/EmptyState";
import { Panel } from "../components/Panel";
import { api } from "../lib/api";
import { clip, formatDateTime } from "../lib/format";

export function ConflictCenterPage() {
  const [selectedPair, setSelectedPair] = useState<{ left: string; right: string } | null>(null);
  const conflictsQuery = useQuery({ queryKey: ["conflicts"], queryFn: () => api.conflicts() });
  const supersededQuery = useQuery({ queryKey: ["superseded"], queryFn: () => api.superseded() });

  const conflicts = ((conflictsQuery.data?.conflicts ?? []) as Array<Record<string, any>>) || [];
  const superseded =
    ((supersededQuery.data?.superseded ?? []) as Array<Record<string, any>>) || [];

  const compareQuery = useQuery({
    queryKey: ["compare", selectedPair],
    queryFn: () => api.compareMemories(String(selectedPair?.left), String(selectedPair?.right)),
    enabled: Boolean(selectedPair),
  });

  return (
    <div className="grid gap-6 xl:grid-cols-[1fr_420px]">
      <div className="space-y-6">
        <Panel>
          <div className="mb-4">
            <h2 className="font-display text-2xl">Conflicting memories</h2>
            <div className="text-sm text-slate-400">Conflicts remain explicit. They are not masked by synthesis.</div>
          </div>
          <div className="space-y-3">
            {conflicts.map((item, index) => (
              <button
                key={item.id}
                onClick={() => {
                  const other = conflicts[(index + 1) % conflicts.length];
                  if (other) setSelectedPair({ left: String(item.id), right: String(other.id) });
                }}
                className="w-full rounded-2xl border border-white/10 bg-white/5 p-4 text-left"
              >
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="text-xs uppercase tracking-[0.18em] text-muted">
                    {item.wing} / {item.room}
                  </div>
                  <StatusBadge status={String(item.status)} />
                </div>
                <div className="mt-2 text-sm text-white">{clip(String(item.verbatim_text), 170)}</div>
                <div className="mt-2 text-xs text-slate-400">{formatDateTime(String(item.updated_at))}</div>
              </button>
            ))}
          </div>
          {!conflicts.length ? (
            <div className="mt-4">
              <EmptyState title="No conflicts detected" description="The current memory graph has no conflicting items." />
            </div>
          ) : null}
        </Panel>

        <Panel>
          <div className="mb-4">
            <h2 className="font-display text-2xl">Superseded memories</h2>
            <div className="text-sm text-slate-400">Earlier memories that were replaced by a newer one.</div>
          </div>
          <div className="space-y-3">
            {superseded.map((item) => (
              <div key={item.id} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="text-xs uppercase tracking-[0.18em] text-muted">
                    {item.wing} / {item.room}
                  </div>
                  <StatusBadge status={String(item.status)} />
                </div>
                <div className="mt-2 text-sm text-white">{clip(String(item.verbatim_text), 170)}</div>
                <div className="mt-2 text-xs text-slate-400">superseded_by {String(item.superseded_by ?? "n/a")}</div>
              </div>
            ))}
          </div>
        </Panel>
      </div>
      <Panel>
        {!selectedPair ? (
          <EmptyState title="Select a comparison" description="Click a conflicting memory to compare it against another conflicting candidate." />
        ) : compareQuery.data ? (
          <div className="space-y-4">
            <div className="font-display text-2xl">Side-by-side comparison</div>
            {(["left", "right"] as const).map((side) => {
              const memory = compareQuery.data[side] as Record<string, any>;
              return (
                <div key={side} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <div className="flex items-center justify-between">
                    <div className="text-xs uppercase tracking-[0.18em] text-muted">{side}</div>
                    <StatusBadge status={String(memory.status)} />
                  </div>
                  <div className="mt-2 text-sm text-white">{String(memory.verbatim_text)}</div>
                </div>
              );
            })}
            <div className="rounded-2xl border border-white/10 bg-black/20 p-4 text-sm text-slate-300">
              {compareQuery.data.link ? JSON.stringify(compareQuery.data.link, null, 2) : "No direct stored link between the selected pair."}
            </div>
          </div>
        ) : (
          <div>Loading comparison...</div>
        )}
      </Panel>
    </div>
  );
}
