from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from typing import Any

from app.core.database import get_connection
from app.core.json_utils import dumps, loads
from app.core.text_utils import extract_keywords, lexical_overlap_score, normalize_text
from app.models.schemas import ChunkRecord, LinkRecord, MemoryRecord


def _build_where(filters: list[str]) -> str:
    clean = [item.strip() for item in filters if item and item.strip()]
    if not clean:
        return ""
    return "WHERE " + " AND ".join(clean)


def _row_to_memory(row: sqlite3.Row) -> MemoryRecord:
    return MemoryRecord(
        id=row["id"],
        wing=row["wing"],
        room=row["room"],
        memory_type=row["memory_type"],
        source=row["source"] or "unknown",
        source_uri=row["source_uri"],
        title=row["title"],
        verbatim_text=row["verbatim_text"],
        normalized_text=row["normalized_text"],
        content_sha256=row["content_sha256"],
        importance=float(row["importance"]),
        confidence=float(row["confidence"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        valid_from=row["valid_from"],
        valid_until=row["valid_until"],
        version=int(row["version"]),
        status=row["status"],
        superseded_by=row["superseded_by"],
        duplicate_of=row["duplicate_of"],
        metadata=loads(row["metadata_json"], default={}) or {},
        classifier=loads(row["classifier_json"], default={}) or {},
        explain=loads(row["explain_json"], default={}) or {},
    )


def _row_to_chunk(row: sqlite3.Row) -> ChunkRecord:
    return ChunkRecord(
        id=row["id"],
        memory_id=row["memory_id"],
        chunk_index=int(row["chunk_index"]),
        text=row["text"],
        token_count=int(row["token_count"]),
        char_start=int(row["char_start"]),
        char_end=int(row["char_end"]),
    )


class MemoryRepository:
    def create_memory(self, memory: MemoryRecord, chunks: list[ChunkRecord]) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO memories (
                    id, wing, room, memory_type, source, source_uri, title, verbatim_text,
                    normalized_text, content_sha256, importance, confidence, created_at,
                    updated_at, valid_from, valid_until, version, status, superseded_by,
                    duplicate_of, metadata_json, classifier_json, explain_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    memory.id,
                    memory.wing,
                    memory.room,
                    memory.memory_type,
                    memory.source,
                    memory.source_uri,
                    memory.title,
                    memory.verbatim_text,
                    memory.normalized_text,
                    memory.content_sha256,
                    memory.importance,
                    memory.confidence,
                    memory.created_at,
                    memory.updated_at,
                    memory.valid_from,
                    memory.valid_until,
                    memory.version,
                    memory.status,
                    memory.superseded_by,
                    memory.duplicate_of,
                    dumps(memory.metadata),
                    dumps(memory.classifier),
                    dumps(memory.explain),
                ),
            )
            conn.executemany(
                """
                INSERT INTO chunks (
                    id, memory_id, chunk_index, text, token_count, char_start, char_end
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        chunk.id,
                        chunk.memory_id,
                        chunk.chunk_index,
                        chunk.text,
                        chunk.token_count,
                        chunk.char_start,
                        chunk.char_end,
                    )
                    for chunk in chunks
                ],
            )

    def get_memory(self, memory_id: str) -> MemoryRecord | None:
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
        return _row_to_memory(row) if row else None

    def get_memories(self, memory_ids: Iterable[str]) -> list[MemoryRecord]:
        ids = list(dict.fromkeys(memory_ids))
        if not ids:
            return []
        placeholders = ",".join("?" for _ in ids)
        with get_connection() as conn:
            rows = conn.execute(
                f"SELECT * FROM memories WHERE id IN ({placeholders})", ids
            ).fetchall()
        return [_row_to_memory(row) for row in rows]

    def get_chunks_for_memories(self, memory_ids: Iterable[str]) -> dict[str, list[ChunkRecord]]:
        ids = list(dict.fromkeys(memory_ids))
        if not ids:
            return {}
        placeholders = ",".join("?" for _ in ids)
        with get_connection() as conn:
            rows = conn.execute(
                (
                    "SELECT * FROM chunks "
                    f"WHERE memory_id IN ({placeholders}) "
                    "ORDER BY memory_id, chunk_index"
                ),
                ids,
            ).fetchall()
        grouped: dict[str, list[ChunkRecord]] = {}
        for row in rows:
            chunk = _row_to_chunk(row)
            grouped.setdefault(chunk.memory_id, []).append(chunk)
        return grouped

    def find_duplicate_by_hash(
        self,
        content_sha256: str,
        *,
        wing: str,
        room: str,
    ) -> MemoryRecord | None:
        with get_connection() as conn:
            row = conn.execute(
                (
                    "SELECT * FROM memories "
                    "WHERE content_sha256 = ? AND wing = ? AND room = ? "
                    "ORDER BY created_at DESC LIMIT 1"
                ),
                (content_sha256, wing, room),
            ).fetchone()
        return _row_to_memory(row) if row else None

    def add_link(self, link: LinkRecord) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO memory_links (
                    source_memory_id, target_memory_id, relation_type, score, reason, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    link.source_memory_id,
                    link.target_memory_id,
                    link.relation_type,
                    link.score,
                    link.reason,
                    link.created_at,
                ),
            )

    def get_links(self, memory_id: str) -> list[LinkRecord]:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT source_memory_id, target_memory_id, relation_type, score, reason, created_at
                FROM memory_links
                WHERE source_memory_id = ? OR target_memory_id = ?
                ORDER BY created_at DESC
                """,
                (memory_id, memory_id),
            ).fetchall()
        return [
            LinkRecord(
                source_memory_id=row["source_memory_id"],
                target_memory_id=row["target_memory_id"],
                relation_type=row["relation_type"],
                score=float(row["score"]),
                reason=row["reason"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def update_status(
        self,
        memory_id: str,
        *,
        status: str | None = None,
        superseded_by: str | None = None,
        duplicate_of: str | None = None,
    ) -> None:
        updates: list[str] = []
        params: list[str | None] = []
        if status is not None:
            updates.append("status = ?")
            params.append(status)
        if superseded_by is not None:
            updates.append("superseded_by = ?")
            params.append(superseded_by)
        if duplicate_of is not None:
            updates.append("duplicate_of = ?")
            params.append(duplicate_of)
        if not updates:
            return
        params.append(memory_id)
        with get_connection() as conn:
            conn.execute(f"UPDATE memories SET {', '.join(updates)} WHERE id = ?", params)

    def list_wings(self) -> list[dict[str, int | str]]:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT wing, COUNT(*) AS total FROM memories GROUP BY wing ORDER BY wing"
            ).fetchall()
        return [{"wing": row["wing"], "count": int(row["total"])} for row in rows]

    def list_rooms(self, wing: str | None = None) -> list[dict[str, int | str]]:
        query = "SELECT room, COUNT(*) AS total FROM memories"
        params: list[str] = []
        if wing:
            query += " WHERE wing = ?"
            params.append(wing)
        query += " GROUP BY room ORDER BY room"
        with get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
        return [{"room": row["room"], "count": int(row["total"])} for row in rows]

    def list_by_status(self, status: str) -> list[MemoryRecord]:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM memories WHERE status = ? ORDER BY updated_at DESC", (status,)
            ).fetchall()
        return [_row_to_memory(row) for row in rows]

    def latest_version(self, wing: str, room: str) -> int:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT MAX(version) AS version FROM memories WHERE wing = ? AND room = ?",
                (wing, room),
            ).fetchone()
        return int(row["version"] or 0)

    def delete_memory(self, memory_id: str) -> None:
        with get_connection() as conn:
            conn.execute("DELETE FROM chunks WHERE memory_id = ?", (memory_id,))
            conn.execute(
                "DELETE FROM memory_links WHERE source_memory_id = ? OR target_memory_id = ?",
                (memory_id, memory_id),
            )
            conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))

    def list_memories(
        self,
        *,
        search_text: str | None = None,
        wing: str | None = None,
        room: str | None = None,
        memory_type: str | None = None,
        status: str | None = None,
        min_importance: float | None = None,
        max_importance: float | None = None,
        created_from: str | None = None,
        created_to: str | None = None,
        conflict_only: bool = False,
        superseded_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        filters: list[str] = []
        aliased_filters: list[str] = []
        params: list[Any] = []
        if search_text:
            filters.append("(verbatim_text LIKE ? OR normalized_text LIKE ? OR id LIKE ?)")
            aliased_filters.append(
                "(m.verbatim_text LIKE ? OR m.normalized_text LIKE ? OR m.id LIKE ?)"
            )
            needle = f"%{search_text}%"
            params.extend([needle, needle.lower(), needle])
        if wing:
            filters.append("wing = ?")
            aliased_filters.append("m.wing = ?")
            params.append(wing)
        if room:
            filters.append("room = ?")
            aliased_filters.append("m.room = ?")
            params.append(room)
        if memory_type:
            filters.append("memory_type = ?")
            aliased_filters.append("m.memory_type = ?")
            params.append(memory_type)
        if min_importance is not None:
            filters.append("importance >= ?")
            aliased_filters.append("m.importance >= ?")
            params.append(min_importance)
        if max_importance is not None:
            filters.append("importance <= ?")
            aliased_filters.append("m.importance <= ?")
            params.append(max_importance)
        if created_from:
            filters.append("created_at >= ?")
            aliased_filters.append("m.created_at >= ?")
            params.append(created_from)
        if created_to:
            filters.append("created_at <= ?")
            aliased_filters.append("m.created_at <= ?")
            params.append(created_to)
        requested_statuses: list[str] = []
        if status:
            requested_statuses.append(status)
        if conflict_only and "conflicting" not in requested_statuses:
            requested_statuses.append("conflicting")
        if superseded_only and "superseded" not in requested_statuses:
            requested_statuses.append("superseded")
        if len(requested_statuses) == 1:
            filters.append("status = ?")
            aliased_filters.append("m.status = ?")
            params.append(requested_statuses[0])
        elif requested_statuses:
            placeholders = ",".join("?" for _ in requested_statuses)
            filters.append(f"status IN ({placeholders})")
            aliased_filters.append(f"m.status IN ({placeholders})")
            params.extend(requested_statuses)

        where = _build_where(filters)
        aliased_where = _build_where(aliased_filters)
        base_params = list(params)
        with get_connection() as conn:
            total_row = conn.execute(
                f"SELECT COUNT(*) AS total FROM memories {where}",
                base_params,
            ).fetchone()
            rows = conn.execute(
                f"""
                WITH access_counts AS (
                    SELECT memory_id, COUNT(*) AS access_count
                    FROM memory_events
                    GROUP BY memory_id
                )
                SELECT m.*, COALESCE(a.access_count, 0) AS access_count
                FROM memories m
                LEFT JOIN access_counts a ON a.memory_id = m.id
                {aliased_where}
                ORDER BY m.updated_at DESC, m.created_at DESC
                LIMIT ? OFFSET ?
                """,
                [*base_params, limit, offset],
            ).fetchall()
        items: list[dict[str, Any]] = []
        for row in rows:
            memory = _row_to_memory(row)
            access_count = int(row["access_count"])
            items.append(
                {
                    "memory": memory.model_dump(),
                    "access_count": access_count,
                    "quality_score": self._quality_score(memory, access_count),
                }
            )
        return {
            "total": int(total_row["total"] if total_row else 0),
            "limit": limit,
            "offset": offset,
            "items": items,
        }

    def get_memory_detail(self, memory_id: str) -> dict[str, Any] | None:
        memory = self.get_memory(memory_id)
        if not memory:
            return None
        with get_connection() as conn:
            access_row = conn.execute(
                "SELECT COUNT(*) AS total FROM memory_events WHERE memory_id = ?",
                (memory_id,),
            ).fetchone()
            versions = conn.execute(
                """
                SELECT * FROM memories
                WHERE wing = ? AND room = ?
                ORDER BY version DESC, updated_at DESC
                """,
                (memory.wing, memory.room),
            ).fetchall()
        chunks = self.get_chunks_for_memories([memory_id]).get(memory_id, [])
        links = self.get_links(memory_id)
        access_count = int(access_row["total"] if access_row else 0)
        return {
            "memory": memory.model_dump(),
            "chunks": [chunk.model_dump() for chunk in chunks],
            "links": [link.model_dump() for link in links],
            "version_history": [_row_to_memory(row).model_dump() for row in versions],
            "access_count": access_count,
            "quality_score": self._quality_score(memory, access_count),
        }

    def compare_memory_pair(self, left_id: str, right_id: str) -> dict[str, Any] | None:
        left = self.get_memory(left_id)
        right = self.get_memory(right_id)
        if not left or not right:
            return None
        with get_connection() as conn:
            link = conn.execute(
                """
                SELECT source_memory_id, target_memory_id, relation_type, score, reason, created_at
                FROM memory_links
                WHERE (source_memory_id = ? AND target_memory_id = ?)
                   OR (source_memory_id = ? AND target_memory_id = ?)
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (left_id, right_id, right_id, left_id),
            ).fetchone()
        return {
            "left": left.model_dump(),
            "right": right.model_dump(),
            "link": (
                LinkRecord(
                    source_memory_id=link["source_memory_id"],
                    target_memory_id=link["target_memory_id"],
                    relation_type=link["relation_type"],
                    score=float(link["score"]),
                    reason=link["reason"],
                    created_at=link["created_at"],
                ).model_dump()
                if link
                else None
            ),
        }

    def search_chunks_text(
        self,
        *,
        query_text: str,
        wing: str | None = None,
        room: str | None = None,
        memory_type: str | None = None,
        status: str | None = None,
        limit: int = 24,
    ) -> list[dict[str, Any]]:
        filters: list[str] = []
        params: list[Any] = []
        if wing:
            filters.append("m.wing = ?")
            params.append(wing)
        if room:
            filters.append("m.room = ?")
            params.append(room)
        if memory_type:
            filters.append("m.memory_type = ?")
            params.append(memory_type)
        if status:
            filters.append("m.status = ?")
            params.append(status)

        keywords = extract_keywords(query_text)[:8]
        normalized_query = normalize_text(query_text)
        lexical_terms = keywords or [token for token in normalized_query.split(" ") if token][:8]
        if lexical_terms:
            like_clauses: list[str] = []
            for term in lexical_terms:
                needle = f"%{term}%"
                like_clauses.extend(
                    [
                        "c.text LIKE ?",
                        "m.verbatim_text LIKE ?",
                        "m.normalized_text LIKE ?",
                    ]
                )
                params.extend([needle, needle, needle])
            filters.append("(" + " OR ".join(like_clauses) + ")")

        where = _build_where(filters)
        with get_connection() as conn:
            rows = conn.execute(
                f"""
                SELECT
                    c.id AS chunk_id,
                    c.text AS chunk_text,
                    c.chunk_index AS chunk_index,
                    m.*
                FROM chunks c
                JOIN memories m ON m.id = c.memory_id
                {where}
                ORDER BY m.updated_at DESC, m.created_at DESC, c.chunk_index ASC
                LIMIT ?
                """,
                [*params, max(limit * 4, limit)],
            ).fetchall()

        scored: list[dict[str, Any]] = []
        for row in rows:
            lexical_source = f"{row['chunk_text']} {row['verbatim_text']}"
            score = lexical_overlap_score(query_text, lexical_source)
            if lexical_terms and score <= 0:
                continue
            scored.append(
                {
                    "chunk_id": row["chunk_id"],
                    "chunk_text": row["chunk_text"],
                    "memory": _row_to_memory(row),
                    "score": score,
                }
            )
        scored.sort(
            key=lambda item: (
                item["score"],
                item["memory"].updated_at,
                item["memory"].created_at,
            ),
            reverse=True,
        )
        return scored[:limit]

    def timeline(
        self,
        *,
        wing: str | None = None,
        room: str | None = None,
        memory_type: str | None = None,
        status: str | None = None,
        limit: int = 250,
    ) -> dict[str, Any]:
        filters: list[str] = []
        params: list[Any] = []
        if wing:
            filters.append("wing = ?")
            params.append(wing)
        if room:
            filters.append("room = ?")
            params.append(room)
        if memory_type:
            filters.append("memory_type = ?")
            params.append(memory_type)
        if status:
            filters.append("status = ?")
            params.append(status)
        where = f"WHERE {' AND '.join(filters)}" if filters else ""
        with get_connection() as conn:
            memories = conn.execute(
                f"""
                SELECT id, wing, room, memory_type, status, created_at, updated_at, verbatim_text
                FROM memories
                {where}
                ORDER BY created_at DESC
                LIMIT ?
                """,
                [*params, limit],
            ).fetchall()
            created_series = conn.execute(
                f"""
                SELECT substr(created_at, 1, 10) AS day, COUNT(*) AS total
                FROM memories
                {where}
                GROUP BY day
                ORDER BY day
                """,
                params,
            ).fetchall()
            link_filters = []
            link_params: list[Any] = []
            if wing or room:
                link_filters.append(
                    "EXISTS (SELECT 1 FROM memories m WHERE m.id = l.source_memory_id"
                    + (" AND m.wing = ?" if wing else "")
                    + (" AND m.room = ?" if room else "")
                    + ")"
                )
                if wing:
                    link_params.append(wing)
                if room:
                    link_params.append(room)
            link_where = f"WHERE {' AND '.join(link_filters)}" if link_filters else ""
            relation_series = conn.execute(
                f"""
                SELECT substr(created_at, 1, 10) AS day, relation_type, COUNT(*) AS total
                FROM memory_links l
                {link_where}
                GROUP BY day, relation_type
                ORDER BY day, relation_type
                """,
                link_params,
            ).fetchall()
        return {
            "events": [
                {
                    "id": row["id"],
                    "kind": "memory_created",
                    "wing": row["wing"],
                    "room": row["room"],
                    "memory_type": row["memory_type"],
                    "status": row["status"],
                    "timestamp": row["created_at"],
                    "excerpt": row["verbatim_text"][:180],
                }
                for row in memories
            ],
            "series": {
                "created": [
                    {"day": row["day"], "count": int(row["total"])}
                    for row in created_series
                ],
                "relations": [
                    {
                        "day": row["day"],
                        "relation_type": row["relation_type"],
                        "count": int(row["total"]),
                    }
                    for row in relation_series
                ],
            },
        }

    def dashboard_stats(self) -> dict[str, Any]:
        with get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) AS total FROM memories").fetchone()
            by_status = conn.execute(
                "SELECT status, COUNT(*) AS total FROM memories GROUP BY status ORDER BY status"
            ).fetchall()
            by_type = conn.execute(
                "SELECT memory_type, COUNT(*) AS total "
                "FROM memories GROUP BY memory_type ORDER BY memory_type"
            ).fetchall()
            by_wing = conn.execute(
                "SELECT wing, COUNT(*) AS total FROM memories "
                "GROUP BY wing ORDER BY total DESC, wing LIMIT 8"
            ).fetchall()
            by_room = conn.execute(
                "SELECT room, COUNT(*) AS total FROM memories "
                "GROUP BY room ORDER BY total DESC, room LIMIT 8"
            ).fetchall()
            recent = conn.execute(
                """
                SELECT id, wing, room, memory_type, status, verbatim_text, created_at
                FROM memories
                ORDER BY created_at DESC
                LIMIT 8
                """
            ).fetchall()
            recent_queries = conn.execute(
                """
                SELECT
                    id, kind, mode, query_text, total_ms, llm_used,
                    fallback_used, result_count, created_at
                FROM query_runs
                ORDER BY created_at DESC
                LIMIT 8
                """
            ).fetchall()
            llm_by_mode = conn.execute(
                """
                SELECT mode, SUM(llm_used) AS llm_used, COUNT(*) AS total
                FROM query_runs
                GROUP BY mode
                ORDER BY mode
                """
            ).fetchall()
        return {
            "totals": {"memories": int(total["total"] if total else 0)},
            "by_status": [
                {"status": row["status"], "count": int(row["total"])}
                for row in by_status
            ],
            "by_type": [
                {"memory_type": row["memory_type"], "count": int(row["total"])}
                for row in by_type
            ],
            "top_wings": [{"wing": row["wing"], "count": int(row["total"])} for row in by_wing],
            "top_rooms": [{"room": row["room"], "count": int(row["total"])} for row in by_room],
            "recent_memories": [
                {
                    "id": row["id"],
                    "wing": row["wing"],
                    "room": row["room"],
                    "memory_type": row["memory_type"],
                    "status": row["status"],
                    "excerpt": row["verbatim_text"][:180],
                    "created_at": row["created_at"],
                }
                for row in recent
            ],
            "recent_queries": [
                {
                    "id": row["id"],
                    "kind": row["kind"],
                    "mode": row["mode"],
                    "query_text": row["query_text"],
                    "total_ms": float(row["total_ms"]),
                    "llm_used": bool(row["llm_used"]),
                    "fallback_used": bool(row["fallback_used"]),
                    "result_count": int(row["result_count"]),
                    "created_at": row["created_at"],
                }
                for row in recent_queries
            ],
            "llm_by_mode": [
                {
                    "mode": row["mode"],
                    "llm_used": int(row["llm_used"] or 0),
                    "total": int(row["total"]),
                }
                for row in llm_by_mode
            ],
        }

    def record_memory_event(
        self,
        *,
        memory_id: str,
        event_type: str,
        query_text: str | None,
        mode: str | None,
        metadata: dict[str, Any] | None,
        created_at: str,
    ) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO memory_events (
                    memory_id, event_type, query_text, mode, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (memory_id, event_type, query_text, mode, dumps(metadata or {}), created_at),
            )

    def record_query_run(
        self,
        *,
        run_id: str,
        kind: str,
        mode: str,
        query_text: str,
        wing: str | None,
        room: str | None,
        memory_type: str | None,
        status_filter: str | None,
        as_of: str | None,
        llm_used: bool,
        fallback_used: bool,
        total_ms: float,
        result_count: int,
        conflict_count: int,
        success: bool,
        stage_timings: dict[str, Any],
        metadata: dict[str, Any],
        created_at: str,
    ) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO query_runs (
                    id, kind, mode, query_text, wing, room, memory_type, status_filter,
                    as_of, llm_used, fallback_used, total_ms, result_count, conflict_count,
                    success, stage_timings_json, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    kind,
                    mode,
                    query_text,
                    wing,
                    room,
                    memory_type,
                    status_filter,
                    as_of,
                    int(llm_used),
                    int(fallback_used),
                    total_ms,
                    result_count,
                    conflict_count,
                    int(success),
                    dumps(stage_timings),
                    dumps(metadata),
                    created_at,
                ),
            )

    def list_query_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM query_runs
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._query_run_row(row) for row in rows]

    def record_eval_run(
        self,
        *,
        run_id: str,
        suite_name: str,
        mode: str,
        success: bool,
        total_ms: float,
        results: dict[str, Any],
        notes: str | None,
        created_at: str,
    ) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO eval_runs (
                    id, suite_name, mode, success, total_ms, results_json, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    suite_name,
                    mode,
                    int(success),
                    total_ms,
                    dumps(results),
                    notes,
                    created_at,
                ),
            )

    def list_eval_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM eval_runs ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._eval_run_row(row) for row in rows]

    def get_eval_run(self, run_id: str) -> dict[str, Any] | None:
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM eval_runs WHERE id = ?", (run_id,)).fetchone()
        return self._eval_run_row(row) if row else None

    @staticmethod
    def _quality_score(memory: MemoryRecord, access_count: int) -> float:
        status_bonus = {
            "active": 0.2,
            "superseded": 0.05,
            "archived": 0.0,
            "conflicting": 0.02,
        }.get(memory.status, 0.0)
        access_bonus = min(access_count, 10) / 10 * 0.1
        score = (memory.importance * 0.4) + (memory.confidence * 0.3) + status_bonus + access_bonus
        return round(min(max(score, 0.0), 1.0), 4)

    @staticmethod
    def _query_run_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "kind": row["kind"],
            "mode": row["mode"],
            "query_text": row["query_text"],
            "wing": row["wing"],
            "room": row["room"],
            "memory_type": row["memory_type"],
            "status_filter": row["status_filter"],
            "as_of": row["as_of"],
            "llm_used": bool(row["llm_used"]),
            "fallback_used": bool(row["fallback_used"]),
            "total_ms": float(row["total_ms"]),
            "result_count": int(row["result_count"]),
            "conflict_count": int(row["conflict_count"]),
            "success": bool(row["success"]),
            "stage_timings": loads(row["stage_timings_json"], default={}) or {},
            "metadata": loads(row["metadata_json"], default={}) or {},
            "created_at": row["created_at"],
        }

    @staticmethod
    def _eval_run_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "suite_name": row["suite_name"],
            "mode": row["mode"],
            "success": bool(row["success"]),
            "total_ms": float(row["total_ms"]),
            "results": loads(row["results_json"], default={}) or {},
            "notes": row["notes"],
            "created_at": row["created_at"],
        }
