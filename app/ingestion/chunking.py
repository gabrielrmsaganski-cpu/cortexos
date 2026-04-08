from __future__ import annotations

from uuid import uuid4

from app.core.config import get_settings
from app.core.text_utils import sentence_chunks, tokenize
from app.models.schemas import ChunkRecord


def build_chunks(memory_id: str, text: str) -> list[ChunkRecord]:
    settings = get_settings()
    chunks = sentence_chunks(text, settings.chunk_size, settings.chunk_overlap)
    records: list[ChunkRecord] = []
    for index, (chunk_text, char_start, char_end) in enumerate(chunks):
        records.append(
            ChunkRecord(
                id=str(uuid4()),
                memory_id=memory_id,
                chunk_index=index,
                text=chunk_text,
                token_count=len(tokenize(chunk_text)),
                char_start=char_start,
                char_end=char_end,
            )
        )
    return records
