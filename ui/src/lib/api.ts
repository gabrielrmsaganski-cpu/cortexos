import type { AnswerResponse, DashboardResponse, MemoryDetailResponse, SearchResponse } from "./types";

const API_ROOT = "/api/v1";

function cleanPayload<T>(value: T): T {
  if (Array.isArray(value)) {
    return value.map((item) => cleanPayload(item)) as T;
  }
  if (value && typeof value === "object") {
    const entries = Object.entries(value as Record<string, unknown>)
      .map(([key, item]) => [key, cleanPayload(item)] as const)
      .filter(([, item]) => item !== "" && item !== undefined && item !== null);
    return Object.fromEntries(entries) as T;
  }
  if (typeof value === "string") {
    return value.trim() as T;
  }
  return value;
}

function jsonBody(payload: Record<string, unknown>) {
  return JSON.stringify(cleanPayload(payload));
}

async function buildError(response: Response): Promise<string> {
  const text = await response.text();
  if (!text) return `Request failed: ${response.status}`;
  try {
    const parsed = JSON.parse(text) as { detail?: unknown };
    if (Array.isArray(parsed.detail)) {
      return parsed.detail
        .map((item) => {
          const detail = item as { loc?: Array<string | number>; msg?: string };
          const path = detail.loc?.join(".") ?? "request";
          return `${path}: ${detail.msg ?? "invalid value"}`;
        })
        .join("\n");
    }
    if (typeof parsed.detail === "string") return parsed.detail;
  } catch {
    return text;
  }
  return text;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path.startsWith("/api/") ? path : `${API_ROOT}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });
  if (!response.ok) {
    throw new Error(await buildError(response));
  }
  return response.json() as Promise<T>;
}

function withQuery(path: string, params: Record<string, unknown>) {
  const url = new URL(path, "http://localhost");
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") return;
    url.searchParams.set(key, String(value));
  });
  return `${url.pathname}${url.search}`;
}

export const api = {
  health: () => request<Record<string, unknown>>("/healthz"),
  dashboard: () => request<DashboardResponse>("/dashboard"),
  listMemories: (params: Record<string, unknown>) =>
    request<Record<string, unknown>>(withQuery("/memories", params)),
  getMemory: (memoryId: string) => request<MemoryDetailResponse>(`/memories/${memoryId}`),
  compareMemories: (leftId: string, rightId: string) =>
    request<Record<string, unknown>>(`/memories/${leftId}/compare/${rightId}`),
  archiveMemory: (memoryId: string) =>
    request<Record<string, unknown>>(`/memories/${memoryId}/archive`, { method: "POST" }),
  reindexMemory: (memoryId: string) =>
    request<Record<string, unknown>>(`/memories/${memoryId}/reindex`, { method: "POST" }),
  timeline: (params: Record<string, unknown>) =>
    request<Record<string, unknown>>(withQuery("/timeline", params)),
  queryStudio: (payload: Record<string, unknown>) =>
    request<Record<string, unknown>>("/query-studio", {
      method: "POST",
      body: jsonBody(payload),
    }),
  search: (payload: Record<string, unknown>) =>
    request<SearchResponse>("/search", { method: "POST", body: jsonBody(payload) }),
  answer: (payload: Record<string, unknown>) =>
    request<AnswerResponse>("/answer", { method: "POST", body: jsonBody(payload) }),
  explain: (payload: Record<string, unknown>) =>
    request<SearchResponse>("/explain", { method: "POST", body: jsonBody(payload) }),
  previewMemory: (payload: Record<string, unknown>) =>
    request<Record<string, unknown>>("/memories/preview", {
      method: "POST",
      body: jsonBody(payload),
    }),
  addMemory: (payload: Record<string, unknown>) =>
    request<Record<string, unknown>>("/memories", {
      method: "POST",
      body: jsonBody(payload),
    }),
  previewDocument: async (formData: FormData) => {
    const response = await fetch(`${API_ROOT}/ingest/document/preview`, {
      method: "POST",
      body: formData,
    });
    if (!response.ok) throw new Error(await response.text());
    return response.json();
  },
  ingestDocument: async (formData: FormData) => {
    const response = await fetch(`${API_ROOT}/ingest/document`, {
      method: "POST",
      body: formData,
    });
    if (!response.ok) throw new Error(await response.text());
    return response.json();
  },
  previewWebpage: (payload: Record<string, unknown>) =>
    request<Record<string, unknown>>("/ingest/webpage/preview", {
      method: "POST",
      body: jsonBody(payload),
    }),
  ingestWebpage: (payload: Record<string, unknown>) =>
    request<Record<string, unknown>>("/ingest/webpage", {
      method: "POST",
      body: jsonBody(payload),
    }),
  previewSite: (payload: Record<string, unknown>) =>
    request<Record<string, unknown>>("/ingest/site/preview", {
      method: "POST",
      body: jsonBody(payload),
    }),
  ingestSite: (payload: Record<string, unknown>) =>
    request<Record<string, unknown>>("/ingest/site", {
      method: "POST",
      body: jsonBody(payload),
    }),
  conflicts: () => request<Record<string, unknown>>("/conflicts"),
  superseded: () => request<Record<string, unknown>>("/superseded"),
  operations: () => request<Record<string, unknown>>("/operations/status"),
  smoke: () => request<Record<string, unknown>>("/operations/smoke", { method: "POST" }),
  settings: () => request<Record<string, unknown>>("/settings"),
  evals: () => request<Record<string, unknown>>("/evals"),
  runEval: (mode: string) =>
    request<Record<string, unknown>>("/evals/run", {
      method: "POST",
      body: jsonBody({ mode }),
    }),
  getEval: (runId: string) => request<Record<string, unknown>>(`/evals/${runId}`),
  seedDemo: () => request<Record<string, unknown>>("/demo/seed", { method: "POST" }),
};
