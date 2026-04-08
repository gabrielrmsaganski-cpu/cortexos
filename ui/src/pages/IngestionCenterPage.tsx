import { useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { EmptyState } from "../components/EmptyState";
import { Panel } from "../components/Panel";
import { api } from "../lib/api";

export function IngestionCenterPage() {
  const [manual, setManual] = useState({
    text: "",
    wing: "",
    room: "",
    memory_type: "",
    source: "ui",
    importance: "0.6",
  });
  const [web, setWeb] = useState({ url: "", wing: "", room: "" });
  const [site, setSite] = useState({ url: "", wing: "", room: "", max_pages: "3" });
  const [file, setFile] = useState<File | null>(null);
  const previewManual = useMutation({ mutationFn: () => api.previewMemory({ ...manual, importance: Number(manual.importance) }) });
  const saveManual = useMutation({ mutationFn: () => api.addMemory({ ...manual, importance: Number(manual.importance) }) });
  const previewWeb = useMutation({ mutationFn: () => api.previewWebpage(web) });
  const saveWeb = useMutation({ mutationFn: () => api.ingestWebpage(web) });
  const previewSite = useMutation({ mutationFn: () => api.previewSite({ ...site, max_pages: Number(site.max_pages) }) });
  const saveSite = useMutation({ mutationFn: () => api.ingestSite({ ...site, max_pages: Number(site.max_pages) }) });
  const previewDocument = useMutation({
    mutationFn: async () => {
      const form = new FormData();
      form.append("wing", manual.wing);
      form.append("room", manual.room);
      if (file) form.append("file", file);
      return api.previewDocument(form);
    },
  });
  const saveDocument = useMutation({
    mutationFn: async () => {
      const form = new FormData();
      form.append("wing", manual.wing);
      form.append("room", manual.room);
      if (file) form.append("file", file);
      return api.ingestDocument(form);
    },
  });

  return (
    <div className="grid gap-6 xl:grid-cols-2">
      <Panel>
        <div className="mb-4">
          <h2 className="font-display text-2xl">Manual ingestion</h2>
          <div className="text-sm text-slate-400">Preview classification, chunking, duplicate signals, and save result.</div>
        </div>
        <div className="space-y-3">
          <textarea
            value={manual.text}
            onChange={(event) => setManual((current) => ({ ...current, text: event.target.value }))}
            className="min-h-40 w-full rounded-3xl border border-edge bg-black/20 p-4 text-sm outline-none"
            placeholder="Paste verbatim memory text"
          />
          <div className="grid gap-3 md:grid-cols-5">
            {(["wing", "room", "memory_type", "source", "importance"] as const).map((field) => (
              <input
                key={field}
                value={manual[field]}
                onChange={(event) =>
                  setManual((current) => ({ ...current, [field]: event.target.value }))
                }
                placeholder={field}
                className="rounded-2xl border border-edge bg-black/20 px-4 py-3 text-sm outline-none placeholder:text-slate-500"
              />
            ))}
          </div>
          <div className="flex gap-3">
            <button onClick={() => previewManual.mutate()} className="rounded-2xl border border-white/15 px-4 py-3 text-sm">Preview</button>
            <button onClick={() => saveManual.mutate()} className="rounded-2xl bg-accent px-4 py-3 text-sm font-medium text-slate-950">Save</button>
          </div>
          <PreviewBlock data={previewManual.data ?? saveManual.data} error={previewManual.error ?? saveManual.error} />
        </div>
      </Panel>

      <Panel>
        <div className="mb-4">
          <h2 className="font-display text-2xl">Document ingestion</h2>
          <div className="text-sm text-slate-400">Upload PDF, TXT, or Markdown and inspect the parsed preview first.</div>
        </div>
        <div className="space-y-3">
          <input type="file" onChange={(event) => setFile(event.target.files?.[0] ?? null)} className="block w-full text-sm" />
          <div className="flex gap-3">
            <button onClick={() => previewDocument.mutate()} className="rounded-2xl border border-white/15 px-4 py-3 text-sm">Preview</button>
            <button onClick={() => saveDocument.mutate()} className="rounded-2xl bg-accent px-4 py-3 text-sm font-medium text-slate-950">Save</button>
          </div>
          <PreviewBlock data={previewDocument.data ?? saveDocument.data} error={previewDocument.error ?? saveDocument.error} />
        </div>
      </Panel>

      <Panel>
        <div className="mb-4">
          <h2 className="font-display text-2xl">Web ingestion</h2>
        </div>
        <div className="space-y-3">
          {(["url", "wing", "room"] as const).map((field) => (
            <input
              key={field}
              value={web[field]}
              onChange={(event) => setWeb((current) => ({ ...current, [field]: event.target.value }))}
              placeholder={field}
              className="w-full rounded-2xl border border-edge bg-black/20 px-4 py-3 text-sm outline-none placeholder:text-slate-500"
            />
          ))}
          <div className="flex gap-3">
            <button onClick={() => previewWeb.mutate()} className="rounded-2xl border border-white/15 px-4 py-3 text-sm">Preview</button>
            <button onClick={() => saveWeb.mutate()} className="rounded-2xl bg-accent px-4 py-3 text-sm font-medium text-slate-950">Save</button>
          </div>
          <PreviewBlock data={previewWeb.data ?? saveWeb.data} error={previewWeb.error ?? saveWeb.error} />
        </div>
      </Panel>

      <Panel>
        <div className="mb-4">
          <h2 className="font-display text-2xl">Site crawl</h2>
        </div>
        <div className="space-y-3">
          {(["url", "wing", "room", "max_pages"] as const).map((field) => (
            <input
              key={field}
              value={site[field]}
              onChange={(event) => setSite((current) => ({ ...current, [field]: event.target.value }))}
              placeholder={field}
              className="w-full rounded-2xl border border-edge bg-black/20 px-4 py-3 text-sm outline-none placeholder:text-slate-500"
            />
          ))}
          <div className="flex gap-3">
            <button onClick={() => previewSite.mutate()} className="rounded-2xl border border-white/15 px-4 py-3 text-sm">Preview</button>
            <button onClick={() => saveSite.mutate()} className="rounded-2xl bg-accent px-4 py-3 text-sm font-medium text-slate-950">Save</button>
          </div>
          <PreviewBlock data={previewSite.data ?? saveSite.data} error={previewSite.error ?? saveSite.error} />
        </div>
      </Panel>
    </div>
  );
}

function PreviewBlock({ data, error }: { data: unknown; error?: unknown }) {
  const message = error instanceof Error ? error.message : null;
  if (message) {
    return (
      <div className="rounded-3xl border border-danger/40 bg-danger/10 p-4 text-sm text-rose-200 whitespace-pre-wrap">
        {message}
      </div>
    );
  }
  if (!data) {
    return (
      <EmptyState
        title="Nothing previewed yet"
        description="Run preview first to inspect chunking, classification, duplicates, conflicts, and supersession signals."
      />
    );
  }
  return (
    <pre className="overflow-x-auto rounded-3xl border border-edge bg-black/30 p-4 text-xs leading-6 text-slate-300">
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}
