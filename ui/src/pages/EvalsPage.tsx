import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { EmptyState } from "../components/EmptyState";
import { Panel } from "../components/Panel";
import { api } from "../lib/api";
import { formatDateTime } from "../lib/format";

export function EvalsPage() {
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [mode, setMode] = useState("balanced");
  const client = useQueryClient();
  const runsQuery = useQuery({ queryKey: ["evals"], queryFn: () => api.evals() });
  const runEvalMutation = useMutation({
    mutationFn: () => api.runEval(mode),
    onSuccess: (data) => {
      setSelectedRunId(String(data.run_id));
      client.invalidateQueries({ queryKey: ["evals"] });
    },
  });
  const detailQuery = useQuery({
    queryKey: ["eval-detail", selectedRunId],
    queryFn: () => api.getEval(String(selectedRunId)),
    enabled: Boolean(selectedRunId),
  });

  const items = ((runsQuery.data?.items ?? []) as Array<Record<string, any>>) || [];

  return (
    <div className="grid gap-6 xl:grid-cols-[360px_1fr]">
      <Panel>
        <div className="mb-4">
          <h2 className="font-display text-2xl">Eval runs</h2>
          <div className="text-sm text-slate-400">Honest local harness execution history.</div>
        </div>
        <div className="flex gap-2">
          {["fast", "balanced", "deep"].map((candidate) => (
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
        <button
          onClick={() => runEvalMutation.mutate()}
          className="mt-4 w-full rounded-2xl bg-accent px-4 py-3 text-sm font-medium text-slate-950"
        >
          Run eval
        </button>
        <div className="mt-4 space-y-3">
          {items.map((item) => (
            <button
              key={String(item.id)}
              onClick={() => setSelectedRunId(String(item.id))}
              className="w-full rounded-2xl border border-white/10 bg-white/5 p-4 text-left"
            >
              <div className="font-medium text-white">{String(item.suite_name)} · {String(item.mode)}</div>
              <div className="mt-1 text-xs text-slate-400">{formatDateTime(String(item.created_at))}</div>
            </button>
          ))}
        </div>
      </Panel>
      <Panel>
        {!selectedRunId ? (
          <EmptyState title="No eval selected" description="Run or select an eval to inspect pass/fail status and details." />
        ) : detailQuery.data ? (
          <pre className="overflow-x-auto rounded-3xl border border-edge bg-black/30 p-4 text-xs leading-6 text-slate-300">
            {JSON.stringify(detailQuery.data, null, 2)}
          </pre>
        ) : (
          <div>Loading eval detail...</div>
        )}
      </Panel>
    </div>
  );
}
