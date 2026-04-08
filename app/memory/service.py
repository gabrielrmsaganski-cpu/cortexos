from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from uuid import uuid4

from app.core.config import get_settings
from app.core.database import init_database
from app.core.text_utils import content_sha256, normalize_text
from app.core.time_utils import iso_now, now_utc, parse_iso_datetime, parse_temporal_intent
from app.ingestion.chunking import build_chunks
from app.ingestion.classifier import classify_memory
from app.ingestion.dedup import compare_memories
from app.models.schemas import (
    AnswerRequest,
    IngestResponse,
    LinkRecord,
    MemoryInput,
    MemoryRecord,
    SearchRequest,
    SearchResponse,
    SearchResult,
)
from app.reasoning.synthesizer import Synthesizer
from app.rerank.service import FallbackReranker, build_reranker
from app.retrieval.encoders import FallbackHybridEncoder, build_encoder
from app.retrieval.query import normalize_query
from app.storage.qdrant_store import QdrantIndex, VectorPayload
from app.storage.repository import MemoryRepository

logger = logging.getLogger(__name__)


@dataclass
class Candidate:
    chunk_id: str
    memory_id: str
    excerpt: str
    dense_score: float = 0.0
    sparse_score: float = 0.0
    hybrid_score: float = 0.0
    rerank_score: float = 0.0
    temporal_score: float = 0.0
    importance_score: float = 0.0
    recency_score: float = 0.0
    penalty: float = 0.0


class MemoryService:
    def __init__(self) -> None:
        self.settings = get_settings()
        init_database()
        self.repo = MemoryRepository()
        self.index = QdrantIndex()
        self._encoder = None
        self._reranker = None
        self._encoder_fallback_active = False
        self._reranker_fallback_active = False
        self._encoder_failure_reason: str | None = None
        self._reranker_failure_reason: str | None = None
        self.synthesizer = Synthesizer()

    def add_memory(self, input_data: MemoryInput) -> IngestResponse:
        wing = input_data.wing or self.settings.default_wing
        room = input_data.room or self.settings.default_room
        normalized = normalize_text(input_data.text)
        content_hash = content_sha256(input_data.text)

        duplicate = self.repo.find_duplicate_by_hash(content_hash, wing=wing, room=room)
        if duplicate:
            link = LinkRecord(
                source_memory_id=duplicate.id,
                target_memory_id=duplicate.id,
                relation_type="duplicate",
                score=1.0,
                reason="Exact normalized duplicate skipped.",
                created_at=iso_now(),
            )
            return IngestResponse(
                memory=duplicate,
                chunks=[],
                links=[link],
                action="duplicate_skipped",
            )

        memory_type, classifier = classify_memory(input_data)
        created_at = (input_data.created_at or now_utc()).replace(microsecond=0).isoformat()
        valid_from = input_data.valid_from.isoformat() if input_data.valid_from else created_at
        valid_until = input_data.valid_until.isoformat() if input_data.valid_until else None
        memory_id = f"mem_{uuid4().hex}"
        version = self.repo.latest_version(wing, room) + 1
        memory = MemoryRecord(
            id=memory_id,
            wing=wing,
            room=room,
            memory_type=input_data.memory_type or memory_type,
            source=input_data.source,
            source_uri=input_data.source_uri,
            title=input_data.title,
            verbatim_text=input_data.text.strip(),
            normalized_text=normalized,
            content_sha256=content_hash,
            importance=input_data.importance or float(classifier["importance"]),
            confidence=input_data.confidence or float(classifier["confidence"]),
            created_at=created_at,
            updated_at=created_at,
            valid_from=valid_from,
            valid_until=valid_until,
            version=version,
            status="active",
            superseded_by=None,
            duplicate_of=None,
            metadata=input_data.metadata,
            classifier=classifier,
            explain={},
        )
        chunks = build_chunks(memory.id, memory.verbatim_text)

        related_links: list[LinkRecord] = []
        for candidate in self._find_related_memories(memory.verbatim_text, wing, room):
            decision = compare_memories(memory.verbatim_text, candidate)
            if not decision:
                continue
            related_links.append(
                LinkRecord(
                    source_memory_id=memory.id,
                    target_memory_id=candidate.id,
                    relation_type=decision.relation_type,
                    score=decision.score,
                    reason=decision.reason,
                    created_at=iso_now(),
                )
            )
            if decision.relation_type == "supersedes":
                self.repo.update_status(candidate.id, status="superseded", superseded_by=memory.id)
            elif decision.relation_type == "conflicts_with":
                self.repo.update_status(candidate.id, status="conflicting")
                memory.status = "conflicting"

        encoded_chunks = self._encode_documents_safe([chunk.text for chunk in chunks])
        vectors = [
            VectorPayload(
                chunk_id=chunk.id,
                memory_id=chunk.memory_id,
                dense=encoded.dense,
                sparse_indices=encoded.sparse_indices,
                sparse_values=encoded.sparse_values,
                payload=self.index.build_payload(memory, chunk),
            )
            for chunk, encoded in zip(chunks, encoded_chunks, strict=False)
        ]
        self.repo.create_memory(memory, chunks)
        try:
            self.index.upsert_chunks(vectors)
        except Exception:
            self.repo.delete_memory(memory.id)
            raise
        for link in related_links:
            self.repo.add_link(link)
        return IngestResponse(memory=memory, chunks=chunks, links=related_links, action="created")

    def search(self, request: SearchRequest) -> SearchResponse:
        return self._search_impl(request, log_run=True)

    def _search_impl(self, request: SearchRequest, *, log_run: bool) -> SearchResponse:
        total_started = time.perf_counter()
        timings_ms: dict[str, float] = {}

        started = time.perf_counter()
        normalized = normalize_query(request.query)
        timings_ms["normalize"] = round((time.perf_counter() - started) * 1000, 2)

        started = time.perf_counter()
        mode_limit_multiplier = {"fast": 2, "balanced": 3, "deep": 5}.get(request.mode, 3)
        minimum_candidates = 20 if request.mode == "deep" else 12
        candidate_limit = max(request.limit * mode_limit_multiplier, minimum_candidates)
        dense_hits = []
        sparse_hits = []
        retrieval_backend = "hybrid"
        degradation_notes: list[str] = []
        if self._encoder_fallback_active:
            timings_ms["encode"] = round((time.perf_counter() - started) * 1000, 2)
            timings_ms["dense"] = 0.0
            timings_ms["sparse"] = 0.0
            started = time.perf_counter()
            candidates, memories, chunks = self._lexical_candidates(
                request,
                normalized.expanded,
                candidate_limit,
            )
            timings_ms["merge"] = round((time.perf_counter() - started) * 1000, 2)
            retrieval_backend = "lexical_fallback"
            degradation_notes.append(self._encoder_failure_reason or "primary encoder unavailable")
        else:
            try:
                query_encoding = self._get_encoder().encode_queries([normalized.expanded])[0]
                timings_ms["encode"] = round((time.perf_counter() - started) * 1000, 2)

                started = time.perf_counter()
                dense_hits = self.index.search_dense(
                    query_encoding.dense,
                    wing=request.wing,
                    room=request.room,
                    memory_type=request.memory_type,
                    status=request.status,
                    limit=candidate_limit,
                )
                timings_ms["dense"] = round((time.perf_counter() - started) * 1000, 2)

                started = time.perf_counter()
                sparse_hits = self.index.search_sparse(
                    query_encoding.sparse_indices,
                    query_encoding.sparse_values,
                    wing=request.wing,
                    room=request.room,
                    memory_type=request.memory_type,
                    status=request.status,
                    limit=candidate_limit,
                )
                timings_ms["sparse"] = round((time.perf_counter() - started) * 1000, 2)

                started = time.perf_counter()
                candidates = self._merge_candidates(dense_hits, sparse_hits)
                memory_ids = [candidate.memory_id for candidate in candidates.values()]
                memories = {memory.id: memory for memory in self.repo.get_memories(memory_ids)}
                chunks = self.repo.get_chunks_for_memories(memory_ids)
                timings_ms["merge"] = round((time.perf_counter() - started) * 1000, 2)
            except Exception as exc:
                logger.exception(
                    "Hybrid retrieval failed; switching query to lexical fallback: %s",
                    exc,
                )
                self._activate_encoder_fallback(exc)
                retrieval_backend = "lexical_fallback"
                degradation_notes.append(self._encoder_failure_reason or str(exc))
                timings_ms["encode"] = round((time.perf_counter() - started) * 1000, 2)
                timings_ms["dense"] = 0.0
                timings_ms["sparse"] = 0.0
                started = time.perf_counter()
                candidates, memories, chunks = self._lexical_candidates(
                    request,
                    normalized.expanded,
                    candidate_limit,
                )
                timings_ms["merge"] = round((time.perf_counter() - started) * 1000, 2)

        passages: list[str] = []
        candidate_list: list[Candidate] = []
        started = time.perf_counter()
        for candidate in candidates.values():
            memory = memories.get(candidate.memory_id)
            if not memory:
                continue
            if request.as_of and not self._memory_valid_as_of(memory, request.as_of.isoformat()):
                continue
            chunk = next(
                (
                    chunk
                    for chunk in chunks.get(candidate.memory_id, [])
                    if chunk.id == candidate.chunk_id
                ),
                None,
            )
            if not chunk:
                continue
            candidate.excerpt = chunk.text
            candidate.importance_score = memory.importance
            candidate.recency_score = self._recency_score(memory.updated_at)
            candidate.temporal_score = self._temporal_score(memory, request.query)
            candidate.penalty = self._status_penalty(memory.status)
            passages.append(chunk.text)
            candidate_list.append(candidate)
        timings_ms["hydrate"] = round((time.perf_counter() - started) * 1000, 2)

        started = time.perf_counter()
        rerank_scores = self._score_passages_safe(normalized.expanded, passages) if passages else []
        timings_ms["rerank"] = round((time.perf_counter() - started) * 1000, 2)

        started = time.perf_counter()
        results: list[SearchResult] = []
        for candidate, rerank_score in zip(candidate_list, rerank_scores, strict=False):
            memory = memories[candidate.memory_id]
            candidate.rerank_score = rerank_score
            final_score = self._final_score(candidate)
            results.append(
                SearchResult(
                    memory=memory,
                    excerpt=candidate.excerpt,
                    chunk_id=candidate.chunk_id,
                    scores={
                        "dense": candidate.dense_score,
                        "sparse": candidate.sparse_score,
                        "hybrid": candidate.hybrid_score,
                        "rerank": candidate.rerank_score,
                        "temporal": candidate.temporal_score,
                        "importance": candidate.importance_score,
                        "recency": candidate.recency_score,
                        "penalty": candidate.penalty,
                        "final": final_score,
                    },
                    reasons=self._reasons(memory, candidate),
                )
            )

        results.sort(key=lambda item: item.scores["final"], reverse=True)
        final_results = self._group_by_memory(results, request.limit)
        timings_ms["finalize"] = round((time.perf_counter() - started) * 1000, 2)
        explain = None
        if request.explain:
            explain = {
                "mode": request.mode,
                "normalized_query": normalized.normalized,
                "expanded_query": normalized.expanded,
                "keywords": normalized.keywords,
                "filters": {
                    "wing": request.wing,
                    "room": request.room,
                    "memory_type": request.memory_type,
                    "status": request.status,
                    "as_of": request.as_of.isoformat() if request.as_of else None,
                },
                "strategy": {
                    "hybrid": retrieval_backend == "hybrid",
                    "rerank": True,
                    "llm_allowed": request.mode != "fast" and self.synthesizer.ollama.enabled,
                    "candidate_limit": candidate_limit,
                    "retrieval_backend": retrieval_backend,
                    "encoder_fallback_active": self._encoder_fallback_active,
                    "reranker_fallback_active": self._reranker_fallback_active,
                    "degradation_notes": degradation_notes
                    + (
                        [self._reranker_failure_reason]
                        if self._reranker_fallback_active and self._reranker_failure_reason
                        else []
                    ),
                },
                "timings_ms": timings_ms,
                "dense_hits": [
                    {"chunk_id": hit.payload.get("chunk_id"), "score": float(hit.score)}
                    for hit in dense_hits
                ],
                "sparse_hits": [
                    {"chunk_id": hit.payload.get("chunk_id"), "score": float(hit.score)}
                    for hit in sparse_hits
                ],
                "final": [
                    {
                        "memory_id": result.memory.id,
                        "chunk_id": result.chunk_id,
                        "scores": result.scores,
                        "status": result.memory.status,
                    }
                    for result in final_results
                ],
            }
        response = SearchResponse(
            query=request.query,
            mode=request.mode,
            normalized_query=normalized.normalized,
            results=final_results,
            explain=explain,
            timings_ms=timings_ms,
        )
        total_ms = round((time.perf_counter() - total_started) * 1000, 2)
        timings_ms["total"] = total_ms
        self._record_result_accesses(final_results, request.query, request.mode, "search")
        if log_run:
            self.repo.record_query_run(
                run_id=f"run_{uuid4().hex}",
                kind="search",
                mode=request.mode,
                query_text=request.query,
                wing=request.wing,
                room=request.room,
                memory_type=request.memory_type,
                status_filter=request.status,
                as_of=request.as_of.isoformat() if request.as_of else None,
                llm_used=False,
                fallback_used=False,
                total_ms=total_ms,
                result_count=len(final_results),
                conflict_count=sum(
                    1 for result in final_results if result.memory.status == "conflicting"
                ),
                success=True,
                stage_timings=timings_ms,
                metadata={
                    "normalized_query": normalized.normalized,
                    "expanded_query": normalized.expanded,
                    "retrieval_backend": retrieval_backend,
                    "encoder_fallback_active": self._encoder_fallback_active,
                    "reranker_fallback_active": self._reranker_fallback_active,
                },
                created_at=iso_now(),
            )
        return response

    def answer(self, request: AnswerRequest):
        total_started = time.perf_counter()
        search = self._search_impl(request, log_run=False)
        synth_started = time.perf_counter()
        response = self.synthesizer.answer(
            request.query,
            search,
            request.synthesis_model,
            allow_llm=request.mode != "fast",
        )
        timings_ms = {
            key: value
            for key, value in (search.timings_ms or {}).items()
            if key != "total"
        }
        timings_ms["synthesis"] = round((time.perf_counter() - synth_started) * 1000, 2)
        timings_ms["total"] = round((time.perf_counter() - total_started) * 1000, 2)
        response.timings_ms = timings_ms
        self._record_result_accesses(search.results, request.query, request.mode, "answer")
        self.repo.record_query_run(
            run_id=f"run_{uuid4().hex}",
            kind="answer",
            mode=request.mode,
            query_text=request.query,
            wing=request.wing,
            room=request.room,
            memory_type=request.memory_type,
            status_filter=request.status,
            as_of=request.as_of.isoformat() if request.as_of else None,
            llm_used=response.llm_used,
            fallback_used=response.fallback_used,
            total_ms=timings_ms["total"],
            result_count=len(search.results),
            conflict_count=len(response.conflicts),
            success=True,
            stage_timings=timings_ms,
            metadata={
                "normalized_query": search.normalized_query,
                "supporting_memories": response.supporting_memories,
            },
            created_at=iso_now(),
        )
        return response

    def get_conflicts(self) -> list[MemoryRecord]:
        return self.repo.list_by_status("conflicting")

    def get_superseded(self) -> list[MemoryRecord]:
        return self.repo.list_by_status("superseded")

    def list_wings(self):
        return self.repo.list_wings()

    def list_rooms(self, wing: str | None = None):
        return self.repo.list_rooms(wing)

    def dashboard_stats(self):
        return self.repo.dashboard_stats()

    def list_memories(self, **filters):
        return self.repo.list_memories(**filters)

    def get_memory_detail(self, memory_id: str):
        return self.repo.get_memory_detail(memory_id)

    def compare_memories(self, left_id: str, right_id: str):
        return self.repo.compare_memory_pair(left_id, right_id)

    def archive_memory(self, memory_id: str):
        self.repo.update_status(memory_id, status="archived")
        return self.repo.get_memory(memory_id)

    def reindex_memory(self, memory_id: str):
        memory = self.repo.get_memory(memory_id)
        if not memory:
            return None
        chunks = self.repo.get_chunks_for_memories([memory_id]).get(memory_id, [])
        if not chunks:
            return {"memory": memory.model_dump(), "reindexed": 0}
        encoded_chunks = self._encode_documents_safe([chunk.text for chunk in chunks])
        vectors = [
            VectorPayload(
                chunk_id=chunk.id,
                memory_id=chunk.memory_id,
                dense=encoded.dense,
                sparse_indices=encoded.sparse_indices,
                sparse_values=encoded.sparse_values,
                payload=self.index.build_payload(memory, chunk),
            )
            for chunk, encoded in zip(chunks, encoded_chunks, strict=False)
        ]
        self.index.upsert_chunks(vectors)
        return {"memory": memory.model_dump(), "reindexed": len(vectors)}

    def timeline(self, **filters):
        return self.repo.timeline(**filters)

    def health(self) -> dict[str, str]:
        return {
            "db": "ok",
            "qdrant": self.index.health(),
            "ollama": self.synthesizer.ollama.health(),
        }

    def runtime_state(self) -> dict[str, object]:
        return {
            "encoder_backend": (
                "fallback" if self._encoder_fallback_active else self.settings.embedding_backend
            ),
            "reranker_backend": (
                "fallback" if self._reranker_fallback_active else self.settings.rerank_backend
            ),
            "encoder_fallback_active": self._encoder_fallback_active,
            "reranker_fallback_active": self._reranker_fallback_active,
            "encoder_failure_reason": self._encoder_failure_reason,
            "reranker_failure_reason": self._reranker_failure_reason,
            "degraded": self._encoder_fallback_active or self._reranker_fallback_active,
        }

    def preview_memory(self, input_data: MemoryInput) -> dict:
        wing = input_data.wing or self.settings.default_wing
        room = input_data.room or self.settings.default_room
        memory_type, classifier = classify_memory(input_data)
        chunks = build_chunks("preview", input_data.text.strip())
        content_hash = content_sha256(input_data.text)
        duplicate = self.repo.find_duplicate_by_hash(content_hash, wing=wing, room=room)
        related = []
        if not duplicate:
            for candidate in self._find_related_memories(input_data.text.strip(), wing, room):
                decision = compare_memories(input_data.text.strip(), candidate)
                if not decision:
                    continue
                related.append(
                    {
                        "target_memory_id": candidate.id,
                        "relation_type": decision.relation_type,
                        "score": decision.score,
                        "reason": decision.reason,
                        "target_excerpt": candidate.verbatim_text[:180],
                        "target_status": candidate.status,
                    }
                )
        return {
            "memory_type": input_data.memory_type or memory_type,
            "classifier": classifier,
            "chunk_count": len(chunks),
            "chunks": [chunk.model_dump() for chunk in chunks[:8]],
            "duplicate": duplicate.model_dump() if duplicate else None,
            "related": related,
        }

    def query_studio(self, request: AnswerRequest) -> dict:
        payload = request.model_dump()
        payload["explain"] = True
        search = self._search_impl(SearchRequest(**payload), log_run=False)
        synth_started = time.perf_counter()
        answer = self.synthesizer.answer(
            request.query,
            search,
            request.synthesis_model,
            allow_llm=request.mode != "fast",
        )
        synthesis_ms = round((time.perf_counter() - synth_started) * 1000, 2)
        timings = {key: value for key, value in (search.timings_ms or {}).items() if key != "total"}
        timings["synthesis"] = synthesis_ms
        timings["total"] = round(sum(value for key, value in timings.items() if key != "total"), 2)
        answer.timings_ms = timings
        self._record_result_accesses(search.results, request.query, request.mode, "query_studio")
        self.repo.record_query_run(
            run_id=f"run_{uuid4().hex}",
            kind="query_studio",
            mode=request.mode,
            query_text=request.query,
            wing=request.wing,
            room=request.room,
            memory_type=request.memory_type,
            status_filter=request.status,
            as_of=request.as_of.isoformat() if request.as_of else None,
            llm_used=answer.llm_used,
            fallback_used=answer.fallback_used,
            total_ms=timings["total"],
            result_count=len(search.results),
            conflict_count=len(answer.conflicts),
            success=True,
            stage_timings=timings,
            metadata={"normalized_query": search.normalized_query},
            created_at=iso_now(),
        )
        return {
            "mode": request.mode,
            "query": request.query,
            "filters": {
                "wing": request.wing,
                "room": request.room,
                "memory_type": request.memory_type,
                "status": request.status,
                "as_of": request.as_of.isoformat() if request.as_of else None,
            },
            "search": search.model_dump(),
            "answer": answer.model_dump(),
            "latency_ms": timings,
            "strategy": {
                "llm_allowed": request.mode != "fast" and self.synthesizer.ollama.enabled,
                "llm_used": answer.llm_used,
                "fallback_used": answer.fallback_used,
                "retrieval_backend": (
                    ((search.explain or {}).get("strategy") or {}).get(
                        "retrieval_backend",
                        "hybrid",
                    )
                ),
                "encoder_fallback_active": self._encoder_fallback_active,
                "reranker_fallback_active": self._reranker_fallback_active,
                "degradation_notes": (
                    ((search.explain or {}).get("strategy") or {}).get("degradation_notes", [])
                ),
            },
        }

    def _find_related_memories(self, text: str, wing: str, room: str) -> list[MemoryRecord]:
        if self._encoder_fallback_active:
            matches = self.repo.search_chunks_text(query_text=text, wing=wing, room=room, limit=8)
            return [match["memory"] for match in matches]
        try:
            query_encoding = self._get_encoder().encode_queries([text])[0]
            hits = self.index.search_dense(
                query_encoding.dense,
                wing=wing,
                room=room,
                limit=8,
            )
            memory_ids = [hit.payload.get("memory_id") for hit in hits if hit.payload]
            return self.repo.get_memories(memory_ids)
        except Exception as exc:
            logger.exception("Related-memory lookup failed; using lexical fallback: %s", exc)
            self._activate_encoder_fallback(exc)
            matches = self.repo.search_chunks_text(query_text=text, wing=wing, room=room, limit=8)
            return [match["memory"] for match in matches]

    def _record_result_accesses(
        self,
        results: list[SearchResult],
        query_text: str,
        mode: str,
        event_type: str,
    ) -> None:
        created_at = iso_now()
        for result in results[:5]:
            self.repo.record_memory_event(
                memory_id=result.memory.id,
                event_type=event_type,
                query_text=query_text,
                mode=mode,
                metadata={"final_score": result.scores.get("final")},
                created_at=created_at,
            )

    def _encode_documents_safe(self, texts: list[str]):
        try:
            return self._get_encoder().encode_documents(texts)
        except Exception as exc:
            logger.exception("Document encoding failed; degrading to fallback encoder: %s", exc)
            self._activate_encoder_fallback(exc)
            return self._get_encoder().encode_documents(texts)

    def _encode_queries_safe(self, texts: list[str]):
        try:
            return self._get_encoder().encode_queries(texts)
        except Exception as exc:
            logger.exception("Query encoding failed; degrading to fallback encoder: %s", exc)
            self._activate_encoder_fallback(exc)
            return self._get_encoder().encode_queries(texts)

    def _score_passages_safe(self, query: str, passages: list[str]) -> list[float]:
        try:
            return self._get_reranker().score(query, passages)
        except Exception as exc:
            logger.exception("Reranker failed; degrading to lexical reranker: %s", exc)
            self._activate_reranker_fallback(exc)
            return self._get_reranker().score(query, passages)

    def _activate_encoder_fallback(self, exc: Exception | str) -> None:
        self._encoder = FallbackHybridEncoder(self.settings.dense_dim)
        self._encoder_fallback_active = True
        self._encoder_failure_reason = str(exc)

    def _activate_reranker_fallback(self, exc: Exception | str) -> None:
        self._reranker = FallbackReranker()
        self._reranker_fallback_active = True
        self._reranker_failure_reason = str(exc)

    def _lexical_candidates(
        self,
        request: SearchRequest,
        query_text: str,
        candidate_limit: int,
    ) -> tuple[dict[str, Candidate], dict[str, MemoryRecord], dict[str, list]]:
        matches = self.repo.search_chunks_text(
            query_text=query_text,
            wing=request.wing,
            room=request.room,
            memory_type=request.memory_type,
            status=request.status,
            limit=candidate_limit,
        )
        candidates: dict[str, Candidate] = {}
        memories: dict[str, MemoryRecord] = {}
        chunks: dict[str, list] = {}
        for rank, match in enumerate(matches, start=1):
            memory = match["memory"]
            chunk_id = match["chunk_id"]
            memory_id = memory.id
            memories[memory_id] = memory
            candidate = Candidate(
                chunk_id=chunk_id,
                memory_id=memory_id,
                excerpt=match["chunk_text"],
            )
            candidate.sparse_score = float(match["score"])
            candidate.hybrid_score = 1 / (40 + rank) + candidate.sparse_score * 0.5
            candidates[chunk_id] = candidate
        if memories:
            chunks = self.repo.get_chunks_for_memories(memories.keys())
        return candidates, memories, chunks

    def _get_encoder(self):
        if self._encoder is None:
            self._encoder = build_encoder()
            if isinstance(self._encoder, FallbackHybridEncoder):
                self._encoder_fallback_active = True
                if not self._encoder_failure_reason:
                    self._encoder_failure_reason = (
                        "primary encoder unavailable during initialization"
                    )
        return self._encoder

    def _get_reranker(self):
        if self._reranker is None:
            self._reranker = build_reranker()
            if isinstance(self._reranker, FallbackReranker):
                self._reranker_fallback_active = True
                if not self._reranker_failure_reason:
                    self._reranker_failure_reason = (
                        "primary reranker unavailable during initialization"
                    )
        return self._reranker

    @staticmethod
    def _merge_candidates(dense_hits, sparse_hits) -> dict[str, Candidate]:
        candidates: dict[str, Candidate] = {}
        for rank, hit in enumerate(dense_hits, start=1):
            payload = hit.payload or {}
            chunk_id = payload.get("chunk_id")
            memory_id = payload.get("memory_id")
            if not chunk_id or not memory_id:
                continue
            candidate = candidates.setdefault(
                chunk_id,
                Candidate(chunk_id=chunk_id, memory_id=memory_id, excerpt=""),
            )
            candidate.dense_score = float(hit.score)
            candidate.hybrid_score += 1 / (60 + rank)
        for rank, hit in enumerate(sparse_hits, start=1):
            payload = hit.payload or {}
            chunk_id = payload.get("chunk_id")
            memory_id = payload.get("memory_id")
            if not chunk_id or not memory_id:
                continue
            candidate = candidates.setdefault(
                chunk_id,
                Candidate(chunk_id=chunk_id, memory_id=memory_id, excerpt=""),
            )
            candidate.sparse_score = float(hit.score)
            candidate.hybrid_score += 1 / (60 + rank)
        return candidates

    @staticmethod
    def _memory_valid_as_of(memory: MemoryRecord, as_of: str) -> bool:
        target = parse_iso_datetime(as_of)
        if not target:
            return True
        start = parse_iso_datetime(memory.valid_from) or parse_iso_datetime(memory.created_at)
        end = parse_iso_datetime(memory.valid_until)
        if start and start > target:
            return False
        if end and end < target:
            return False
        return True

    @staticmethod
    def _recency_score(updated_at: str) -> float:
        updated = parse_iso_datetime(updated_at)
        if not updated:
            return 0.4
        days = max((now_utc() - updated).days, 0)
        return max(0.1, 1.0 / (1.0 + days / 30))

    @staticmethod
    def _temporal_score(memory: MemoryRecord, query: str) -> float:
        intent = parse_temporal_intent(query)
        if not intent.target:
            return 0.5
        memory_time = parse_iso_datetime(memory.valid_from) or parse_iso_datetime(memory.created_at)
        if not memory_time:
            return 0.2
        diff = abs((memory_time - intent.target).days)
        window = max(intent.window_days, 1)
        if diff > window * 6:
            return 0.0
        return max(0.0, 1 - (diff / (window * 6)))

    @staticmethod
    def _status_penalty(status: str) -> float:
        return {
            "active": 0.0,
            "superseded": -0.25,
            "archived": -0.3,
            "conflicting": -0.2,
        }.get(status, -0.1)

    @staticmethod
    def _final_score(candidate: Candidate) -> float:
        return (
            (candidate.hybrid_score * 0.25)
            + (candidate.dense_score * 0.15)
            + (candidate.sparse_score * 0.1)
            + (candidate.rerank_score * 0.25)
            + (candidate.temporal_score * 0.1)
            + (candidate.importance_score * 0.1)
            + (candidate.recency_score * 0.05)
            + candidate.penalty
        )

    @staticmethod
    def _reasons(memory: MemoryRecord, candidate: Candidate) -> list[str]:
        reasons = [f"hybrid={candidate.hybrid_score:.4f}", f"rerank={candidate.rerank_score:.4f}"]
        if memory.status != "active":
            reasons.append(f"status={memory.status}")
        if candidate.temporal_score > 0.7:
            reasons.append("temporal match")
        return reasons

    @staticmethod
    def _group_by_memory(results: list[SearchResult], limit: int) -> list[SearchResult]:
        grouped: dict[str, SearchResult] = {}
        for result in results:
            current = grouped.get(result.memory.id)
            if current is None or result.scores["final"] > current.scores["final"]:
                grouped[result.memory.id] = result
        ordered = sorted(grouped.values(), key=lambda item: item.scores["final"], reverse=True)
        return ordered[:limit]


_SERVICE: MemoryService | None = None


def get_memory_service() -> MemoryService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = MemoryService()
    return _SERVICE


def reset_memory_service() -> None:
    global _SERVICE
    _SERVICE = None
