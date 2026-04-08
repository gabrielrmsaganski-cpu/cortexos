from __future__ import annotations

import sqlite3
from pathlib import Path

from .config import get_settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    wing TEXT NOT NULL,
    room TEXT NOT NULL,
    memory_type TEXT NOT NULL,
    source TEXT,
    source_uri TEXT,
    title TEXT,
    verbatim_text TEXT NOT NULL,
    normalized_text TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,
    importance REAL NOT NULL,
    confidence REAL NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    valid_from TEXT,
    valid_until TEXT,
    version INTEGER NOT NULL,
    status TEXT NOT NULL,
    superseded_by TEXT,
    duplicate_of TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    classifier_json TEXT NOT NULL DEFAULT '{}',
    explain_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_memories_lookup ON memories(wing, room, memory_type, status);
CREATE INDEX IF NOT EXISTS idx_memories_hash ON memories(content_sha256);
CREATE INDEX IF NOT EXISTS idx_memories_hash_context ON memories(content_sha256, wing, room);
CREATE INDEX IF NOT EXISTS idx_memories_time
    ON memories(created_at, updated_at, valid_from, valid_until);

CREATE TABLE IF NOT EXISTS chunks (
    id TEXT PRIMARY KEY,
    memory_id TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    token_count INTEGER NOT NULL,
    char_start INTEGER NOT NULL,
    char_end INTEGER NOT NULL,
    FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_chunks_memory ON chunks(memory_id, chunk_index);

CREATE TABLE IF NOT EXISTS memory_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_memory_id TEXT NOT NULL,
    target_memory_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    score REAL NOT NULL,
    reason TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_links_source ON memory_links(source_memory_id, relation_type);
CREATE INDEX IF NOT EXISTS idx_links_target ON memory_links(target_memory_id, relation_type);

CREATE TABLE IF NOT EXISTS memory_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    query_text TEXT,
    mode TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_memory_events_memory ON memory_events(memory_id, created_at);
CREATE INDEX IF NOT EXISTS idx_memory_events_type ON memory_events(event_type, created_at);

CREATE TABLE IF NOT EXISTS query_runs (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    mode TEXT NOT NULL,
    query_text TEXT NOT NULL,
    wing TEXT,
    room TEXT,
    memory_type TEXT,
    status_filter TEXT,
    as_of TEXT,
    llm_used INTEGER NOT NULL DEFAULT 0,
    fallback_used INTEGER NOT NULL DEFAULT 0,
    total_ms REAL NOT NULL DEFAULT 0,
    result_count INTEGER NOT NULL DEFAULT 0,
    conflict_count INTEGER NOT NULL DEFAULT 0,
    success INTEGER NOT NULL DEFAULT 1,
    stage_timings_json TEXT NOT NULL DEFAULT '{}',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_query_runs_created ON query_runs(created_at);
CREATE INDEX IF NOT EXISTS idx_query_runs_mode ON query_runs(mode, created_at);

CREATE TABLE IF NOT EXISTS eval_runs (
    id TEXT PRIMARY KEY,
    suite_name TEXT NOT NULL,
    mode TEXT NOT NULL,
    success INTEGER NOT NULL DEFAULT 0,
    total_ms REAL NOT NULL DEFAULT 0,
    results_json TEXT NOT NULL DEFAULT '{}',
    notes TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_eval_runs_created ON eval_runs(created_at);
"""


def get_connection() -> sqlite3.Connection:
    settings = get_settings()
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_database() -> None:
    with get_connection() as conn:
        conn.executescript(SCHEMA)
