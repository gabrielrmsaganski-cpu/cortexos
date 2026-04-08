import importlib

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.database import init_database
from app.memory.service import reset_memory_service
from app.models.schemas import ChunkRecord, LinkRecord, MemoryRecord
from app.storage.repository import MemoryRepository


def build_memory(
    memory_id: str,
    *,
    wing: str,
    room: str,
    text: str,
    status: str,
    version: int,
    superseded_by: str | None = None,
) -> MemoryRecord:
    return MemoryRecord(
        id=memory_id,
        wing=wing,
        room=room,
        memory_type="factual",
        source="test",
        source_uri=None,
        title=None,
        verbatim_text=text,
        normalized_text=text.lower(),
        content_sha256=f"hash-{memory_id}",
        importance=0.6,
        confidence=0.8,
        created_at="2026-04-08T00:00:00+00:00",
        updated_at="2026-04-08T00:00:00+00:00",
        valid_from="2026-04-08T00:00:00+00:00",
        valid_until=None,
        version=version,
        status=status,
        superseded_by=superseded_by,
        duplicate_of=None,
        metadata={},
        classifier={},
        explain={},
    )


def build_chunk(memory_id: str) -> ChunkRecord:
    return ChunkRecord(
        id=f"chunk-{memory_id}",
        memory_id=memory_id,
        chunk_index=0,
        text=f"Chunk for {memory_id}",
        token_count=4,
        char_start=0,
        char_end=12,
    )


def make_client(tmp_path, monkeypatch) -> tuple[TestClient, MemoryRepository, object]:
    monkeypatch.setenv("MEMORY_OS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("MEMORY_OS_DB_PATH", str(tmp_path / "memory-os.sqlite3"))
    get_settings.cache_clear()
    reset_memory_service()
    init_database()

    repo = MemoryRepository()
    newer = build_memory(
        "mem-new",
        wing="demo",
        room="launch",
        text="The launch moved to 2026-05-20.",
        status="active",
        version=2,
    )
    older = build_memory(
        "mem-old",
        wing="demo",
        room="launch",
        text="The launch date is 2026-05-15.",
        status="superseded",
        version=1,
        superseded_by="mem-new",
    )
    repo.create_memory(newer, [build_chunk(newer.id)])
    repo.create_memory(older, [build_chunk(older.id)])
    repo.add_link(
        LinkRecord(
            source_memory_id="mem-new",
            target_memory_id="mem-old",
            relation_type="supersedes",
            score=0.9,
            reason="Updated date",
            created_at="2026-04-08T00:00:00+00:00",
        )
    )

    import app.api.main as api_main

    api_main = importlib.reload(api_main)
    return TestClient(api_main.app), repo, api_main


def test_dashboard_and_timeline_endpoints(tmp_path, monkeypatch):
    client, _repo, _api_main = make_client(tmp_path, monkeypatch)

    dashboard = client.get("/api/v1/dashboard")
    assert dashboard.status_code == 200
    assert dashboard.json()["stats"]["totals"]["memories"] == 2

    timeline = client.get("/api/v1/timeline?wing=demo&room=launch")
    assert timeline.status_code == 200
    assert timeline.json()["events"]


def test_memory_list_detail_and_archive(tmp_path, monkeypatch):
    client, _repo, _api_main = make_client(tmp_path, monkeypatch)

    listing = client.get("/api/v1/memories?wing=demo")
    assert listing.status_code == 200
    assert listing.json()["total"] == 2

    search_listing = client.get("/api/v1/memories?wing=demo&room=launch&search_text=2026-05")
    assert search_listing.status_code == 200
    assert search_listing.json()["total"] == 2
    assert all(
        item["memory"]["wing"] == "demo" and item["memory"]["room"] == "launch"
        for item in search_listing.json()["items"]
    )

    detail = client.get("/api/v1/memories/mem-old")
    assert detail.status_code == 200
    assert detail.json()["memory"]["status"] == "superseded"
    assert detail.json()["version_history"]

    archive = client.post("/api/v1/memories/mem-new/archive")
    assert archive.status_code == 200
    assert archive.json()["memory"]["status"] == "archived"


def test_memory_list_supports_combined_status_filters(tmp_path, monkeypatch):
    client, _repo, _api_main = make_client(tmp_path, monkeypatch)

    combined = client.get("/api/v1/memories?wing=demo&conflict_only=true&superseded_only=true")
    assert combined.status_code == 200
    assert combined.json()["total"] == 1
    assert combined.json()["items"][0]["memory"]["status"] == "superseded"


def test_settings_endpoint(tmp_path, monkeypatch):
    client, _repo, _api_main = make_client(tmp_path, monkeypatch)

    response = client.get("/api/v1/settings")
    assert response.status_code == 200
    body = response.json()
    assert body["runtime"]["default_model"]
    assert any(item["id"] == "fast" for item in body["modes"])


def test_query_studio_accepts_blank_optional_filters(tmp_path, monkeypatch):
    client, _repo, _api_main = make_client(tmp_path, monkeypatch)

    response = client.post(
        "/api/v1/query-studio",
        json={
            "query": "What is the current launch date?",
            "mode": "fast",
            "wing": "",
            "room": "",
            "memory_type": "",
            "status": "",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"]["answer"]
    assert body["search"]["explain"]["strategy"]


def test_query_studio_falls_back_when_encoder_breaks(tmp_path, monkeypatch):
    client, _repo, api_main = make_client(tmp_path, monkeypatch)

    class BrokenEncoder:
        def encode_queries(self, _texts):
            raise RuntimeError("encoder exploded")

    api_main.service._encoder = None
    api_main.service._encoder_fallback_active = False
    api_main.service._encoder_failure_reason = None
    monkeypatch.setattr(api_main.service, "_get_encoder", lambda: BrokenEncoder())

    response = client.post(
        "/api/v1/query-studio",
        json={"query": "launch moved", "mode": "fast", "wing": "demo", "room": "launch"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["strategy"]["retrieval_backend"] == "lexical_fallback"
    assert body["strategy"]["encoder_fallback_active"] is True
    assert body["search"]["results"]
