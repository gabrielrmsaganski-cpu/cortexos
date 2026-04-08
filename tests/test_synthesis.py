from app.models.schemas import MemoryRecord, SearchResponse, SearchResult
from app.reasoning.synthesizer import Synthesizer


def build_result(status: str, excerpt: str) -> SearchResult:
    memory = MemoryRecord(
        id=f"mem-{status}",
        wing="product",
        room="launch",
        memory_type="factual",
        source="test",
        verbatim_text=excerpt,
        normalized_text=excerpt.lower(),
        content_sha256="hash",
        importance=0.5,
        confidence=0.7,
        created_at="2026-04-08T00:00:00+00:00",
        updated_at="2026-04-08T00:00:00+00:00",
        valid_from="2026-04-08T00:00:00+00:00",
        valid_until=None,
        version=1,
        status=status,
        metadata={},
        classifier={},
        explain={},
    )
    return SearchResult(
        memory=memory,
        excerpt=excerpt,
        chunk_id="chk",
        scores={"final": 1.0},
        reasons=[],
    )


def test_deterministic_synthesis_mentions_conflicts():
    synthesizer = Synthesizer()
    synthesizer.ollama.enabled = False
    response = synthesizer.answer(
        "What is the launch date?",
        SearchResponse(
            query="What is the launch date?",
            normalized_query="what is the launch date?",
            results=[
                build_result("active", "The launch is 2026-05-20."),
                build_result("conflicting", "The launch is 2026-05-15."),
            ],
        ),
        preferred_model=None,
    )
    assert "Best-supported answer" in response.answer
    assert "2026-05-20" in response.answer
    assert "conflicts were also detected" in response.answer.lower()
    assert response.conflicts


def test_deterministic_synthesis_marks_unresolved_when_only_conflicts():
    synthesizer = Synthesizer()
    synthesizer.ollama.enabled = False
    response = synthesizer.answer(
        "What is the launch date?",
        SearchResponse(
            query="What is the launch date?",
            normalized_query="what is the launch date?",
            results=[
                build_result("conflicting", "The launch is 2026-05-20."),
                build_result("conflicting", "The launch is 2026-05-15."),
            ],
        ),
        preferred_model=None,
    )
    assert "unresolved" in response.answer.lower()
    assert response.conflicts


def test_deterministic_synthesis_rejects_weak_evidence():
    synthesizer = Synthesizer()
    synthesizer.ollama.enabled = False
    weak = build_result("active", "The office is in Porto.")
    weak.scores = {"final": 0.21, "rerank": 0.00001}
    response = synthesizer.answer(
        "Qual a situação do cliente João?",
        SearchResponse(
            query="Qual a situação do cliente João?",
            normalized_query="qual a situação do cliente joão?",
            results=[weak],
        ),
        preferred_model=None,
    )
    assert "no high-confidence memory matched this query" in response.answer.lower()
