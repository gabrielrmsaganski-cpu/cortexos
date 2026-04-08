from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from app.memory.service import get_memory_service
from app.models.schemas import AnswerRequest, MemoryInput, SearchRequest
from app.rerank.service import build_reranker


@dataclass
class EvalResult:
    name: str
    passed: bool
    details: dict


def _wing(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:8]}"


def run_minimal_eval(mode: str = "balanced") -> dict:
    service = get_memory_service()
    service.synthesizer.ollama.enabled = mode != "fast"
    results = [
        _run_dedup_eval(service),
        _run_conflict_and_supersession_eval(service, mode),
        _run_temporal_eval(service, mode),
        _run_hybrid_eval(service, mode),
        _run_rerank_eval(),
        _run_synthesis_eval(service, mode),
    ]
    return {
        "mode": mode,
        "passed": all(result.passed for result in results),
        "results": [
            {
                "name": result.name,
                "passed": result.passed,
                "details": result.details,
            }
            for result in results
        ],
    }


def _run_dedup_eval(service) -> EvalResult:
    wing = _wing("eval-dedup")
    room = "launch"
    first = service.add_memory(
        MemoryInput(text="The launch date is 2026-05-15.", wing=wing, room=room, source="eval")
    )
    second = service.add_memory(
        MemoryInput(text="The launch date is 2026-05-15.", wing=wing, room=room, source="eval")
    )
    return EvalResult(
        name="dedup",
        passed=first.action == "created" and second.action == "duplicate_skipped",
        details={"first_action": first.action, "second_action": second.action},
    )


def _run_conflict_and_supersession_eval(service, mode: str) -> EvalResult:
    wing = _wing("eval-status")
    room = "launch"
    old = service.add_memory(
        MemoryInput(text="The launch date is 2026-05-15.", wing=wing, room=room, source="eval")
    )
    new = service.add_memory(
        MemoryInput(text="The launch moved to 2026-05-20.", wing=wing, room=room, source="eval")
    )
    old_conflict = service.add_memory(
        MemoryInput(text="The office is in Lisbon.", wing=wing, room="hq", source="eval")
    )
    new_conflict = service.add_memory(
        MemoryInput(text="The office is in Porto.", wing=wing, room="hq", source="eval")
    )
    search = service.search(
        SearchRequest(
            query="What is the current launch date?",
            wing=wing,
            room=room,
            explain=True,
            mode=mode,
        )
    )
    superseded = service.repo.get_memory(old.memory.id)
    conflicting = service.repo.get_memory(old_conflict.memory.id)
    return EvalResult(
        name="conflict_and_supersession",
        passed=bool(search.results)
        and "2026-05-20" in search.results[0].excerpt
        and superseded is not None
        and superseded.status == "superseded"
        and superseded.superseded_by == new.memory.id
        and conflicting is not None
        and conflicting.status == "conflicting"
        and new_conflict.memory.status == "conflicting",
        details={
            "top_excerpt": search.results[0].excerpt if search.results else None,
            "superseded_status": superseded.status if superseded else None,
            "superseded_by": superseded.superseded_by if superseded else None,
            "conflicting_status": conflicting.status if conflicting else None,
            "new_conflict_status": new_conflict.memory.status,
        },
    )


def _run_temporal_eval(service, mode: str) -> EvalResult:
    wing = _wing("eval-time")
    room = "hq"
    service.add_memory(
        MemoryInput(
            text="The office is in Lisbon.",
            wing=wing,
            room=room,
            source="eval",
            valid_from=datetime(2026, 1, 1, tzinfo=UTC),
            valid_until=datetime(2026, 2, 1, tzinfo=UTC),
        )
    )
    service.add_memory(
        MemoryInput(
            text="The office moved to Porto.",
            wing=wing,
            room=room,
            source="eval",
            valid_from=datetime(2026, 2, 1, tzinfo=UTC),
        )
    )
    january = service.search(
        SearchRequest(
            query="Where is the office?",
            wing=wing,
            room=room,
            as_of=datetime(2026, 1, 15, tzinfo=UTC),
            mode=mode,
        )
    )
    march = service.search(
        SearchRequest(
            query="Where is the office?",
            wing=wing,
            room=room,
            as_of=datetime(2026, 3, 1, tzinfo=UTC),
            mode=mode,
        )
    )
    january_top = january.results[0].excerpt if january.results else None
    march_top = march.results[0].excerpt if march.results else None
    return EvalResult(
        name="temporal",
        passed=january_top == "The office is in Lisbon."
        and march_top == "The office moved to Porto.",
        details={"january_top": january_top, "march_top": march_top},
    )


def _run_hybrid_eval(service, mode: str) -> EvalResult:
    wing = _wing("eval-hybrid")
    room = "ops"
    query = "alpha_x7c9"
    service.add_memory(
        MemoryInput(
            text="Procedure: rotate feature flag alpha_x7c9 in searxng and reload nginx.",
            wing=wing,
            room=room,
            source="eval",
        )
    )
    service.add_memory(
        MemoryInput(
            text="Procedure: rotate feature flag alpha in searxng and reload nginx.",
            wing=wing,
            room=room,
            source="eval",
        )
    )
    search = service.search(
        SearchRequest(query=query, wing=wing, room=room, explain=True, mode=mode)
    )
    top_excerpt = search.results[0].excerpt if search.results else None
    sparse_hits = search.explain["sparse_hits"] if search.explain else []
    return EvalResult(
        name="hybrid",
        passed=bool(search.results)
        and "alpha_x7c9" in (top_excerpt or "")
        and bool(sparse_hits),
        details={
            "top_excerpt": top_excerpt,
            "dense_hits": search.explain["dense_hits"][:2] if search.explain else [],
            "sparse_hits": sparse_hits[:2],
        },
    )


def _run_rerank_eval() -> EvalResult:
    reranker = build_reranker()
    query = "How do I restart nginx after editing config?"
    passages = [
        "Restart nginx after editing the config file.",
        "The launch moved to 2026-05-20.",
        "To restart services, edit the search configuration and reload nginx.",
    ]
    scores = reranker.score(query, passages)
    return EvalResult(
        name="rerank",
        passed=scores[0] > scores[2] > scores[1],
        details={"scores": scores, "passages": passages},
    )


def _run_synthesis_eval(service, mode: str) -> EvalResult:
    wing = _wing("eval-answer")
    room = "launch"
    service.add_memory(
        MemoryInput(text="The launch moved to 2026-05-20.", wing=wing, room=room, source="eval")
    )
    service.add_memory(
        MemoryInput(text="The launch is 2026-05-15.", wing=wing, room=room, source="eval")
    )
    answer = service.answer(
        AnswerRequest(query="What is the current launch date?", wing=wing, room=room, mode=mode)
    )
    raw_context = "\n".join(answer.summary)
    return EvalResult(
        name="synthesis",
        passed="unresolved" in answer.answer.lower()
        and answer.answer != raw_context
        and bool(answer.conflicts),
        details={
            "answer": answer.answer,
            "raw_context": raw_context,
            "conflicts": answer.conflicts,
        },
    )


if __name__ == "__main__":
    print(json.dumps(run_minimal_eval(), indent=2))
