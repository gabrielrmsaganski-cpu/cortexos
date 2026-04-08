import { useMemo, useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { Badge, StatusBadge } from "../components/Badge";
import { EmptyState } from "../components/EmptyState";
import { Panel } from "../components/Panel";
import { api } from "../lib/api";
import { clip, formatNumber } from "../lib/format";
import type { QueryMode } from "../lib/types";

const modes: QueryMode[] = ["fast", "balanced", "deep"];

export function QueryStudioPage() {
  const [mode, setMode] = useState<QueryMode>("balanced");
  const [tab, setTab] = useState<"answer" | "retrieval" | "reranked" | "explain">("answer");
  const [form, setForm] = useState({
    query: "What is the current launch date?",
    wing: "",
    room: "",
    memory_type: "",
    status: "",
  });
  const mutation = useMutation({
    mutationFn: () => api.queryStudio({ ...form, mode }),
  });

  const searchResults = useMemo(
    () => ((mutation.data?.search as Record<string, any>)?.results ?? []) as Array<Record<string, any>>,
    [mutation.data],
  );
  const errorMessage = mutation.error instanceof Error ? mutation.error.message : null;
  const strategy = ((mutation.data?.strategy as Record<string, any>) ?? {}) as Record<string, any>;
  const explain = ((mutation.data?.search as Record<string, any>)?.explain ?? {}) as Record<string, any>;

  return (
    <div className="space-y-6">
      <Panel>
        <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="space-y-4">
            <textarea
              value={form.query}
              onChange={(event) => setForm((current) => ({ ...current, query: event.target.value }))}
              className="min-h-32 w-full rounded-3xl border border-edge bg-black/20 p-4 text-sm outline-none"
            />
            <div className="grid gap-3 md:grid-cols-4">
              {(["wing", "room", "memory_type", "status"] as const).map((field) => (
                <input
                  key={field}
                  value={form[field]}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, [field]: event.target.value }))
                  }
                  placeholder={field}
                  className="rounded-2xl border border-edge bg-black/20 px-4 py-3 text-sm outline-none placeholder:text-slate-500"
                />
              ))}
            </div>
          </div>
          <div className="space-y-4">
            <div>
              <div className="text-[11px] uppercase tracking-[0.18em] text-muted">Mode</div>
              <div className="mt-3 flex gap-2">
                {modes.map((candidate) => (
                  <button
                    key={candidate}
                    onClick={() => setMode(candidate)}
                    className={`rounded-2xl px-4 py-3 text-sm ${
                      mode === candidate ? "bg-white text-slate-950" : "border border-white/15"
                    }`}
                  >
                    {candidate}
                  </button>
                ))}
              </div>
            </div>
            <button
              onClick={() => mutation.mutate()}
              disabled={mutation.isPending}
              className="w-full rounded-2xl bg-accent px-4 py-3 text-sm font-medium text-slate-950"
            >
              {mutation.isPending ? "Running query..." : "Execute query"}
            </button>
            {mutation.data ? (
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-slate-300">
                Total latency: {formatNumber(Number((mutation.data.latency_ms as Record<string, any>)?.total ?? 0))} ms
              </div>
            ) : null}
            {errorMessage ? (
              <div className="rounded-2xl border border-danger/40 bg-danger/10 p-4 text-sm text-rose-200 whitespace-pre-wrap">
                {errorMessage}
              </div>
            ) : null}
          </div>
        </div>
      </Panel>

      {!mutation.data ? (
        <EmptyState
          title="No query executed yet"
          description="Run a question in fast, balanced, or deep mode to inspect retrieval, reranking, and synthesis."
        />
      ) : (
        <div className="space-y-6">
          <Panel>
            <div className="mb-4 flex flex-wrap gap-2">
              {(["answer", "retrieval", "reranked", "explain"] as const).map((candidate) => (
                <button
                  key={candidate}
                  onClick={() => setTab(candidate)}
                  className={`rounded-2xl px-4 py-2 text-sm ${
                    tab === candidate ? "bg-white text-slate-950" : "border border-white/15"
                  }`}
                >
                  {candidate}
                </button>
              ))}
            </div>
            {tab === "answer" ? (
              <div className="space-y-4">
                <div className="rounded-3xl border border-edge bg-black/20 p-5 text-base leading-8 text-slate-100">
                  {(mutation.data.answer as Record<string, any>)?.answer}
                </div>
                <div className="flex flex-wrap gap-2">
                  <Badge>mode {String(mutation.data.mode)}</Badge>
                  <Badge>llm {String((mutation.data.strategy as Record<string, any>)?.llm_used)}</Badge>
                  <Badge>fallback {String((mutation.data.strategy as Record<string, any>)?.fallback_used)}</Badge>
                  <Badge>retrieval {String(strategy.retrieval_backend ?? "hybrid")}</Badge>
                  <Badge>encoder degraded {String(strategy.encoder_fallback_active ?? false)}</Badge>
                  <Badge>reranker degraded {String(strategy.reranker_fallback_active ?? false)}</Badge>
                </div>
                {Array.isArray(strategy.degradation_notes) && strategy.degradation_notes.length ? (
                  <div className="rounded-2xl border border-amber-400/20 bg-amber-400/10 p-4 text-sm text-amber-100">
                    {strategy.degradation_notes.map((note) => String(note)).join("\n")}
                  </div>
                ) : null}
              </div>
            ) : null}
            {tab === "retrieval" ? (
              <div className="space-y-3">
                {searchResults.map((item) => (
                  <div key={String(item.chunk_id)} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div className="font-medium">{clip(String(item.excerpt), 160)}</div>
                      <StatusBadge status={String((item.memory as Record<string, any>)?.status ?? "active")} />
                    </div>
                    <div className="mt-2 text-xs text-slate-400">
                      dense {Number((item.scores as Record<string, any>)?.dense ?? 0).toFixed(3)} · sparse{" "}
                      {Number((item.scores as Record<string, any>)?.sparse ?? 0).toFixed(3)} · hybrid{" "}
                      {Number((item.scores as Record<string, any>)?.hybrid ?? 0).toFixed(3)}
                    </div>
                  </div>
                ))}
              </div>
            ) : null}
            {tab === "reranked" ? (
              <div className="space-y-3">
                {searchResults.map((item) => (
                  <div key={String(item.chunk_id)} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                    <div className="font-medium">{clip(String(item.excerpt), 180)}</div>
                    <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-300">
                      <Badge>rerank {Number((item.scores as Record<string, any>)?.rerank ?? 0).toFixed(3)}</Badge>
                      <Badge>temporal {Number((item.scores as Record<string, any>)?.temporal ?? 0).toFixed(3)}</Badge>
                      <Badge>final {Number((item.scores as Record<string, any>)?.final ?? 0).toFixed(3)}</Badge>
                    </div>
                  </div>
                ))}
              </div>
            ) : null}
            {tab === "explain" ? (
              <pre className="overflow-x-auto rounded-3xl border border-edge bg-black/30 p-4 text-xs leading-6 text-slate-300">
                {JSON.stringify(explain, null, 2)}
              </pre>
            ) : null}
          </Panel>
        </div>
      )}
    </div>
  );
}
