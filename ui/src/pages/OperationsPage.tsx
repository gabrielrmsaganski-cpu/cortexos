import { useMutation, useQuery } from "@tanstack/react-query";

import { EmptyState } from "../components/EmptyState";
import { Panel } from "../components/Panel";
import { api } from "../lib/api";
import { formatNumber, healthTone } from "../lib/format";

export function OperationsPage() {
  const query = useQuery({ queryKey: ["operations"], queryFn: () => api.operations() });
  const smokeMutation = useMutation({ mutationFn: () => api.smoke() });

  if (query.isLoading) return <Panel>Loading operations...</Panel>;
  if (!query.data) {
    return <EmptyState title="Operations unavailable" description="The operations center could not load runtime state." />;
  }

  const health = (query.data.health ?? {}) as Record<string, string>;
  const runtime = (query.data.runtime ?? {}) as Record<string, unknown>;
  const storage = (query.data.storage ?? {}) as Record<string, number>;
  const ports = (query.data.ports ?? {}) as Record<string, number>;
  const logs = (query.data.api_logs ?? []) as string[];
  const models = (query.data.available_models ?? []) as Array<Record<string, any>>;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        {Object.entries(health).map(([key, value]) => (
          <Panel key={key}>
            <div className="text-[11px] uppercase tracking-[0.18em] text-muted">{key}</div>
            <div className={`mt-3 text-xl font-medium ${healthTone(String(value))}`}>{String(value)}</div>
          </Panel>
        ))}
      </div>
      <div className="grid gap-6 xl:grid-cols-2">
        <Panel>
          <h2 className="font-display text-2xl">Runtime mode</h2>
          <div className="mt-4 space-y-3 text-sm text-slate-300">
            {Object.entries(runtime).map(([key, value]) => (
              <div key={key} className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                <span>{key}</span>
                <span className="max-w-[55%] text-right text-slate-400">{String(value ?? "n/a")}</span>
              </div>
            ))}
          </div>
        </Panel>
        <Panel>
          <h2 className="font-display text-2xl">Storage</h2>
          <div className="mt-4 space-y-3 text-sm text-slate-300">
            {Object.entries(storage).map(([key, value]) => (
              <div key={key} className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                <span>{key}</span>
                <span>{formatNumber(value)} bytes</span>
              </div>
            ))}
          </div>
        </Panel>
        <Panel>
          <h2 className="font-display text-2xl">Ports</h2>
          <div className="mt-4 space-y-3 text-sm text-slate-300">
            {Object.entries(ports).map(([key, value]) => (
              <div key={key} className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                <span>{key}</span>
                <span>{value}</span>
              </div>
            ))}
          </div>
        </Panel>
      </div>
      <div className="grid gap-6 xl:grid-cols-2">
        <Panel>
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-display text-2xl">Smoke test</h2>
              <div className="text-sm text-slate-400">Run the local smoke script through the product UI.</div>
            </div>
            <button onClick={() => smokeMutation.mutate()} className="rounded-2xl bg-accent px-4 py-3 text-sm font-medium text-slate-950">
              Run smoke
            </button>
          </div>
          {smokeMutation.data ? (
            <pre className="mt-4 overflow-x-auto rounded-3xl border border-edge bg-black/30 p-4 text-xs leading-6 text-slate-300">
              {JSON.stringify(smokeMutation.data, null, 2)}
            </pre>
          ) : null}
        </Panel>
        <Panel>
          <h2 className="font-display text-2xl">Ollama models</h2>
          <div className="mt-4 space-y-3">
            {models.map((model) => (
              <div key={String(model.name)} className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-300">
                <div className="font-medium text-white">{String(model.name)}</div>
                <div className="mt-1 text-xs text-slate-400">{String((model.details as Record<string, any>)?.parameter_size ?? "n/a")}</div>
              </div>
            ))}
          </div>
        </Panel>
      </div>
      <Panel>
        <h2 className="font-display text-2xl">Recent API logs</h2>
        <pre className="mt-4 overflow-x-auto rounded-3xl border border-edge bg-black/30 p-4 text-xs leading-6 text-slate-300">
          {logs.join("\n")}
        </pre>
      </Panel>
    </div>
  );
}
