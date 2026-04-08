import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import { EmptyState } from "../components/EmptyState";
import { Panel } from "../components/Panel";
import { api } from "../lib/api";

export function ExplainCenterPage() {
  const [query, setQuery] = useState("current launch date");
  const mutation = useMutation({
    mutationFn: () => api.explain({ query, mode: "deep", explain: true }),
  });

  const explain = (mutation.data?.explain ?? {}) as Record<string, any>;
  const errorMessage = mutation.error instanceof Error ? mutation.error.message : null;

  return (
    <div className="space-y-6">
      <Panel>
        <div className="grid gap-4 lg:grid-cols-[1fr_auto]">
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            className="rounded-2xl border border-edge bg-black/20 px-4 py-3 text-sm outline-none"
          />
          <button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
            className="rounded-2xl bg-accent px-4 py-3 text-sm font-medium text-slate-950"
          >
            {mutation.isPending ? "Running explain..." : "Explain retrieval"}
          </button>
        </div>
        {errorMessage ? (
          <div className="mt-4 rounded-2xl border border-danger/40 bg-danger/10 p-4 text-sm text-rose-200 whitespace-pre-wrap">
            {errorMessage}
          </div>
        ) : null}
      </Panel>

      {!mutation.data ? (
        <EmptyState
          title="No explain run yet"
          description="Run a deep explain query to inspect normalized query, dense hits, sparse hits, merge, penalties, and final ranking."
        />
      ) : (
        <div className="grid gap-6 xl:grid-cols-2">
          <Panel>
            <div className="space-y-4">
              <Stage title="Original query" value={mutation.data.query} />
              <Stage title="Normalized query" value={mutation.data.normalized_query} />
              <Stage title="Expanded query" value={String(explain.expanded_query ?? "n/a")} />
              <Stage title="Keywords" value={JSON.stringify(explain.keywords ?? [])} />
              <Stage title="Filters" value={JSON.stringify(explain.filters ?? {}, null, 2)} />
              <Stage title="Strategy" value={JSON.stringify(explain.strategy ?? {}, null, 2)} />
              <Stage title="Timings" value={JSON.stringify(explain.timings_ms ?? {}, null, 2)} />
            </div>
          </Panel>
          <Panel>
            <div className="space-y-4">
              <Stage title="Dense candidates" value={JSON.stringify(explain.dense_hits ?? [], null, 2)} />
              <Stage title="Sparse candidates" value={JSON.stringify(explain.sparse_hits ?? [], null, 2)} />
              <Stage title="Final ranking" value={JSON.stringify(explain.final ?? [], null, 2)} />
            </div>
          </Panel>
        </div>
      )}
    </div>
  );
}

function Stage({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
      <div className="text-[11px] uppercase tracking-[0.18em] text-muted">{title}</div>
      <pre className="mt-3 overflow-x-auto whitespace-pre-wrap text-xs leading-6 text-slate-300">{value}</pre>
    </div>
  );
}
