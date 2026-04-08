import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Badge, StatusBadge } from "../components/Badge";
import { EmptyState } from "../components/EmptyState";
import { Panel } from "../components/Panel";
import { clip, formatDateTime, formatPct, formatRelativeTime } from "../lib/format";
import { api } from "../lib/api";
import type { MemoryListItem } from "../lib/types";

export function ExplorerPage() {
  const [filters, setFilters] = useState({
    search_text: "",
    wing: "",
    room: "",
    memory_type: "",
    status: "",
  });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const client = useQueryClient();

  const listQuery = useQuery({
    queryKey: ["memories", filters],
    queryFn: () => api.listMemories(filters),
  });

  const detailQuery = useQuery({
    queryKey: ["memory-detail", selectedId],
    queryFn: () => api.getMemory(String(selectedId)),
    enabled: Boolean(selectedId),
  });

  const archiveMutation = useMutation({
    mutationFn: (memoryId: string) => api.archiveMemory(memoryId),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["memories"] });
      if (selectedId) client.invalidateQueries({ queryKey: ["memory-detail", selectedId] });
    },
  });

  const reindexMutation = useMutation({
    mutationFn: (memoryId: string) => api.reindexMemory(memoryId),
  });

  const items = ((listQuery.data?.items ?? []) as MemoryListItem[]) || [];

  return (
    <div className="grid gap-6 xl:grid-cols-[1fr_420px]">
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
        <div className="mt-4 overflow-hidden rounded-3xl border border-edge">
          <div className="grid grid-cols-[1.6fr_0.9fr_0.8fr_0.8fr_0.7fr_1fr_1fr] gap-3 border-b border-edge bg-white/5 px-4 py-3 text-[11px] uppercase tracking-[0.18em] text-muted">
            <div>Memory</div>
            <div>Wing / Room</div>
            <div>Type</div>
            <div>Status</div>
            <div>Access</div>
            <div>Quality</div>
            <div>Updated</div>
          </div>
          <div className="divide-y divide-edge">
            {items.map((item) => (
              <button
                key={item.memory.id}
                onClick={() => setSelectedId(item.memory.id)}
                className="grid w-full grid-cols-[1.6fr_0.9fr_0.8fr_0.8fr_0.7fr_1fr_1fr] gap-3 px-4 py-4 text-left transition hover:bg-white/5"
              >
                <div>
                  <div className="font-medium text-white">{clip(item.memory.verbatim_text, 92)}</div>
                  <div className="mt-1 text-xs text-slate-400">{item.memory.id}</div>
                </div>
                <div className="text-sm text-slate-300">
                  {item.memory.wing}
                  <div className="text-slate-500">{item.memory.room}</div>
                </div>
                <div className="text-sm text-slate-300">{item.memory.memory_type}</div>
                <div><StatusBadge status={item.memory.status} /></div>
                <div className="text-sm text-slate-300">{item.access_count}</div>
                <div className="text-sm text-slate-300">{formatPct(item.quality_score)}</div>
                <div className="text-sm text-slate-300">{formatRelativeTime(item.memory.updated_at)}</div>
              </button>
            ))}
          </div>
        </div>
        {!items.length && !listQuery.isLoading ? (
          <div className="mt-4">
            <EmptyState
              title="No memories match the current filters"
              description="Adjust the filters, load demo mode, or ingest new memories."
            />
          </div>
        ) : null}
      </Panel>

      <Panel>
        {!selectedId ? (
          <EmptyState
            title="Select a memory"
            description="Open any row from the explorer to inspect verbatim text, links, versions, chunks, and admin actions."
          />
        ) : detailQuery.isLoading ? (
          <div>Loading memory detail...</div>
        ) : detailQuery.data ? (
          <div className="space-y-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <div className="text-[11px] uppercase tracking-[0.18em] text-muted">
                  {detailQuery.data.memory.wing} / {detailQuery.data.memory.room}
                </div>
                <h2 className="mt-2 font-display text-2xl">{clip(detailQuery.data.memory.verbatim_text, 180)}</h2>
              </div>
              <StatusBadge status={detailQuery.data.memory.status} />
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge>{detailQuery.data.memory.memory_type}</Badge>
              <Badge>quality {formatPct(detailQuery.data.quality_score)}</Badge>
              <Badge>access {detailQuery.data.access_count}</Badge>
            </div>
            <div className="rounded-3xl border border-edge bg-black/20 p-4 text-sm leading-7 text-slate-200">
              {detailQuery.data.memory.verbatim_text}
            </div>
            <div className="grid gap-3 text-sm text-slate-300 md:grid-cols-2">
              <div>Created: {formatDateTime(detailQuery.data.memory.created_at)}</div>
              <div>Updated: {formatDateTime(detailQuery.data.memory.updated_at)}</div>
              <div>Importance: {detailQuery.data.memory.importance}</div>
              <div>Confidence: {detailQuery.data.memory.confidence}</div>
            </div>
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => archiveMutation.mutate(detailQuery.data.memory.id)}
                className="rounded-2xl border border-white/15 px-4 py-3 text-sm"
              >
                Archive
              </button>
              <button
                onClick={() => reindexMutation.mutate(detailQuery.data.memory.id)}
                className="rounded-2xl border border-white/15 px-4 py-3 text-sm"
              >
                Reindex
              </button>
            </div>
            <div>
              <div className="mb-3 font-display text-lg">Related links</div>
              <div className="space-y-3">
                {(detailQuery.data.links as Array<Record<string, any>>).map((link, index) => (
                  <div key={`${link.target_memory_id}-${index}`} className="rounded-2xl border border-white/10 bg-white/5 p-3 text-sm">
                    <div className="font-medium text-white">{link.relation_type}</div>
                    <div className="mt-1 text-slate-300">{link.reason}</div>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <div className="mb-3 font-display text-lg">Version history</div>
              <div className="space-y-2">
                {detailQuery.data.version_history.map((version) => (
                  <div key={version.id} className="rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-sm">
                    v{version.version} · {version.status} · {clip(version.verbatim_text, 100)}
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <EmptyState title="Memory detail unavailable" description="The selected memory could not be loaded." />
        )}
      </Panel>
    </div>
  );
}
