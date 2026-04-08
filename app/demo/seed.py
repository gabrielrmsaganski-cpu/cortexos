from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.core.time_utils import iso_now
from app.memory.service import get_memory_service
from app.models.schemas import LinkRecord, MemoryInput


def seed_demo_dataset() -> dict:
    service = get_memory_service()
    dataset_path = Path(
        "/home/saganski/workspace/experiments/cortexos/examples/demo-memories.json"
    )
    payloads = json.loads(dataset_path.read_text())
    items = []
    created = 0
    skipped = 0
    for payload in payloads:
        input_data = MemoryInput(
            text=payload["text"],
            wing=payload.get("wing"),
            room=payload.get("room"),
            memory_type=payload.get("memory_type"),
            source=payload.get("source", "demo-seed"),
            created_at=(
                datetime.fromisoformat(payload["created_at"])
                if payload.get("created_at")
                else None
            ),
            valid_from=(
                datetime.fromisoformat(payload["valid_from"])
                if payload.get("valid_from")
                else None
            ),
            valid_until=(
                datetime.fromisoformat(payload["valid_until"])
                if payload.get("valid_until")
                else None
            ),
        )
        result = service.add_memory(input_data)
        if result.action == "created":
            created += 1
        else:
            skipped += 1
        items.append(
            {
                "id": result.memory.id,
                "action": result.action,
                "wing": result.memory.wing,
                "room": result.memory.room,
                "status": result.memory.status,
                "text": result.memory.verbatim_text,
            }
        )
    _ensure_demo_relations(service)
    return {
        "dataset_path": str(dataset_path),
        "created": created,
        "skipped": skipped,
        "items": items,
    }


def _ensure_demo_relations(service) -> None:
    older = _find_memory_id(service, "demo-product", "launch", "The launch date is 2026-04-12.")
    newer = _find_memory_id(service, "demo-product", "launch", "The launch moved to 2026-05-20.")
    if older and newer:
        service.repo.update_status(older, status="superseded", superseded_by=newer)
        existing_links = service.repo.get_links(newer)
        if not any(
            link.target_memory_id == older and link.relation_type == "supersedes"
            for link in existing_links
        ):
            service.repo.add_link(
                LinkRecord(
                    source_memory_id=newer,
                    target_memory_id=older,
                    relation_type="supersedes",
                    score=1.0,
                    reason="Demo seed enforces explicit launch supersession.",
                    created_at=iso_now(),
                )
            )


def _find_memory_id(service, wing: str, room: str, text: str) -> str | None:
    items = service.list_memories(
        search_text=text,
        wing=wing,
        room=room,
        limit=5,
        offset=0,
    )["items"]
    for item in items:
        memory = item["memory"]
        if memory["verbatim_text"] == text:
            return memory["id"]
    return None
