from app.core.config import get_settings
from app.core.database import init_database
from app.storage.repository import MemoryRepository


def _memory(memory_id: str, wing: str, room: str, content_sha256: str):
    return {
        "id": memory_id,
        "wing": wing,
        "room": room,
        "memory_type": "reference",
        "source": "test",
        "source_uri": None,
        "title": None,
        "verbatim_text": "Same text across contexts.",
        "normalized_text": "same text across contexts.",
        "content_sha256": content_sha256,
        "importance": 0.4,
        "confidence": 0.7,
        "created_at": "2026-04-08T00:00:00+00:00",
        "updated_at": "2026-04-08T00:00:00+00:00",
        "valid_from": "2026-04-08T00:00:00+00:00",
        "valid_until": None,
        "version": 1,
        "status": "active",
        "superseded_by": None,
        "duplicate_of": None,
        "metadata": {},
        "classifier": {},
        "explain": {},
    }


def test_duplicate_lookup_is_scoped_to_wing_and_room(tmp_path, monkeypatch):
    monkeypatch.setenv("MEMORY_OS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("MEMORY_OS_DB_PATH", str(tmp_path / "memory-os.sqlite3"))
    get_settings.cache_clear()
    try:
        init_database()

        from app.models.schemas import MemoryRecord

        repo = MemoryRepository()
        shared_hash = "abc123"
        repo.create_memory(MemoryRecord(**_memory("m1", "wing-a", "room-1", shared_hash)), [])
        repo.create_memory(MemoryRecord(**_memory("m2", "wing-b", "room-2", shared_hash)), [])

        assert repo.find_duplicate_by_hash(shared_hash, wing="wing-a", room="room-1") is not None
        assert repo.find_duplicate_by_hash(shared_hash, wing="wing-b", room="room-2") is not None
        assert repo.find_duplicate_by_hash(shared_hash, wing="wing-a", room="room-2") is None
    finally:
        get_settings.cache_clear()
