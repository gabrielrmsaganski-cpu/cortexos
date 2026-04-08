from __future__ import annotations

from app.core.text_utils import lexical_overlap_score
from app.models.schemas import AnswerResponse, SearchResponse, SearchResult
from app.tools.ollama_client import OllamaClient


class Synthesizer:
    def __init__(self) -> None:
        self.ollama = OllamaClient()

    def answer(
        self,
        query: str,
        search: SearchResponse,
        preferred_model: str | None,
        *,
        allow_llm: bool = True,
        timings_ms: dict[str, float] | None = None,
    ) -> AnswerResponse:
        conflicts = [
            result.memory.id
            for result in search.results
            if result.memory.status == "conflicting"
        ]
        llm_used = False
        fallback_used = False
        if self.ollama.enabled and allow_llm:
            answer, llm_used, fallback_used = self._llm_answer(query, search, preferred_model)
        else:
            answer = self._deterministic_answer(query, search, conflicts)
            fallback_used = not allow_llm and self.ollama.enabled
        return AnswerResponse(
            answer=answer,
            summary=[result.excerpt for result in search.results[:3]],
            conflicts=conflicts,
            supporting_memories=[result.memory.id for result in search.results[:5]],
            explain=search.explain,
            mode=search.mode,
            llm_used=llm_used,
            fallback_used=fallback_used,
            timings_ms=timings_ms,
        )

    def _llm_answer(
        self, query: str, search: SearchResponse, preferred_model: str | None
    ) -> tuple[str, bool, bool]:
        context_blocks = []
        for result in search.results[:6]:
            context_blocks.append(
                f"[{result.memory.id}] status={result.memory.status} "
                f"wing={result.memory.wing} room={result.memory.room} "
                f"excerpt={result.excerpt}"
            )
        prompt = (
            "Answer the user using only the memory context.\n"
            "State conflicts explicitly.\n"
            "Prefer active memories over superseded memories.\n"
            "If only conflicting memories are available, say the answer is unresolved.\n"
            f"Question: {query}\n"
            "Context:\n"
            + "\n".join(context_blocks)
        )
        reply = self.ollama.chat(prompt, model=preferred_model)
        if reply:
            return reply, True, False
        conflicts = [
            result.memory.id
            for result in search.results
            if result.memory.status == "conflicting"
        ]
        return self._deterministic_answer(query, search, conflicts), False, True

    @staticmethod
    def _deterministic_answer(query: str, search: SearchResponse, conflicts: list[str]) -> str:
        if not search.results:
            return "No supporting memory was found."
        if not Synthesizer._has_strong_support(query, search.results):
            answer = (
                "No high-confidence memory matched this query. "
                "The retrieved candidates were too weak or semantically off-target."
            )
            if conflicts:
                answer += f" Conflicts were also detected in memories: {', '.join(conflicts)}."
            return answer
        active = [result for result in search.results if result.memory.status == "active"]
        if active:
            lead = active[0]
            answer = f"Best-supported answer: {lead.excerpt}"
            if conflicts:
                answer += f" Conflicts were also detected in memories: {', '.join(conflicts)}."
            return answer

        conflicting = [result for result in search.results if result.memory.status == "conflicting"]
        if conflicting:
            excerpts = Synthesizer._format_excerpt_list(conflicting[:2])
            answer = "The memory set is currently unresolved because the top memories conflict."
            if excerpts:
                answer += f" Conflicting candidates: {excerpts}."
            answer += f" Conflicts were detected in memories: {', '.join(conflicts)}."
            return answer

        lead = search.results[0]
        return f"Best-supported answer: {lead.excerpt}"

    @staticmethod
    def _format_excerpt_list(results: list[SearchResult]) -> str:
        excerpts = [result.excerpt.strip() for result in results if result.excerpt.strip()]
        return " | ".join(excerpts)

    @staticmethod
    def _has_strong_support(query: str, results: list[SearchResult]) -> bool:
        top = results[0]
        top_final = float(top.scores.get("final", 0.0))
        top_rerank = float(top.scores.get("rerank", 0.0))
        top_overlap = lexical_overlap_score(query, top.excerpt)
        if top_rerank >= 0.1:
            return True
        if top_final >= 0.3:
            return True
        return top_overlap >= 0.35
