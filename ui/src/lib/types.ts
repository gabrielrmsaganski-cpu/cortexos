export type QueryMode = "fast" | "balanced" | "deep";
export type MemoryStatus = "active" | "superseded" | "conflicting" | "archived";

export interface MemoryRecord {
  id: string;
  wing: string;
  room: string;
  memory_type: string;
  source: string;
  source_uri?: string | null;
  title?: string | null;
  verbatim_text: string;
  normalized_text: string;
  content_sha256: string;
  importance: number;
  confidence: number;
  created_at: string;
  updated_at: string;
  valid_from?: string | null;
  valid_until?: string | null;
  version: number;
  status: MemoryStatus;
  superseded_by?: string | null;
  duplicate_of?: string | null;
  metadata: Record<string, unknown>;
  classifier: Record<string, unknown>;
  explain: Record<string, unknown>;
}

export interface SearchResult {
  memory: MemoryRecord;
  excerpt: string;
  chunk_id: string;
  scores: Record<string, number>;
  reasons: string[];
}

export interface SearchResponse {
  query: string;
  mode: QueryMode;
  normalized_query: string;
  results: SearchResult[];
  explain?: Record<string, unknown> | null;
  timings_ms?: Record<string, number> | null;
}

export interface AnswerResponse {
  answer: string;
  summary: string[];
  conflicts: string[];
  supporting_memories: string[];
  explain?: Record<string, unknown> | null;
  mode: QueryMode;
  llm_used: boolean;
  fallback_used: boolean;
  timings_ms?: Record<string, number> | null;
}

export interface MemoryListItem {
  memory: MemoryRecord;
  access_count: number;
  quality_score: number;
}

export interface MemoryDetailResponse {
  memory: MemoryRecord;
  chunks: Array<Record<string, unknown>>;
  links: Array<Record<string, unknown>>;
  version_history: MemoryRecord[];
  access_count: number;
  quality_score: number;
}

export interface DashboardResponse {
  stats: Record<string, unknown>;
  timeline: Record<string, unknown>;
  operations: Record<string, unknown>;
}
