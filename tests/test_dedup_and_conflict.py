from app.ingestion.dedup import compare_memories
from app.models.schemas import MemoryRecord


def build_memory(text: str) -> MemoryRecord:
    return MemoryRecord(
        id="m1",
        wing="product",
        room="launch",
        memory_type="factual",
        source="test",
        verbatim_text=text,
        normalized_text=text.lower(),
        content_sha256="x",
        importance=0.5,
        confidence=0.7,
        created_at="2026-04-08T00:00:00+00:00",
        updated_at="2026-04-08T00:00:00+00:00",
        valid_from="2026-04-08T00:00:00+00:00",
        valid_until=None,
        version=1,
        status="active",
        metadata={},
        classifier={},
        explain={},
    )


def test_conflict_detection():
    existing = build_memory("The launch is 2026-05-15.")
    relation = compare_memories("The launch is 2026-05-20.", existing)
    assert relation is not None
    assert relation.relation_type == "conflicts_with"


def test_supersession_detection():
    existing = build_memory("The launch is 2026-05-15.")
    relation = compare_memories("The launch moved to 2026-05-20.", existing)
    assert relation is not None
    assert relation.relation_type == "supersedes"
