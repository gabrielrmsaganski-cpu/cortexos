import { useQuery } from "@tanstack/react-query";

import { EmptyState } from "../components/EmptyState";
import { Panel } from "../components/Panel";
import { api } from "../lib/api";

export function SettingsPage() {
  const query = useQuery({ queryKey: ["settings"], queryFn: () => api.settings() });

  if (query.isLoading) return <Panel>Loading settings...</Panel>;
  if (!query.data) {
    return <EmptyState title="Settings unavailable" description="Runtime settings could not be loaded." />;
  }

  return (
    <div className="grid gap-6 xl:grid-cols-2">
      <Panel>
        <h2 className="font-display text-2xl">Runtime summary</h2>
        <pre className="mt-4 overflow-x-auto rounded-3xl border border-edge bg-black/30 p-4 text-xs leading-6 text-slate-300">
          {JSON.stringify(query.data.runtime ?? {}, null, 2)}
        </pre>
      </Panel>
      <Panel>
        <h2 className="font-display text-2xl">Modes</h2>
        <div className="mt-4 space-y-3">
          {((query.data.modes ?? []) as Array<Record<string, any>>).map((mode) => (
            <div key={String(mode.id)} className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <div className="font-medium text-white">{String(mode.label)}</div>
              <div className="mt-2 text-sm text-slate-300">{String(mode.description)}</div>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}
