from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from qdrant_client import QdrantClient, models

from app.core.config import get_settings
from app.core.time_utils import parse_iso_datetime
from app.models.schemas import ChunkRecord, MemoryRecord

logger = logging.getLogger(__name__)


@dataclass
class VectorPayload:
    chunk_id: str
    memory_id: str
    dense: list[float]
    sparse_indices: list[int]
    sparse_values: list[float]
    payload: dict[str, Any]


class QdrantIndex:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = QdrantClient(url=self.settings.qdrant_url, timeout=30)

    def ensure_collection(self) -> None:
        if self.client.collection_exists(self.settings.qdrant_collection):
            info = self.client.get_collection(self.settings.qdrant_collection)
            current_size = (
                info.config.params.vectors.get(self.settings.dense_vector_name).size
                if isinstance(info.config.params.vectors, dict)
                else info.config.params.vectors.size
            )
            if current_size == self.settings.dense_dim:
                return
            logger.warning(
                "Recreating Qdrant collection due to vector size mismatch: expected=%s current=%s",
                self.settings.dense_dim,
                current_size,
            )
            self.client.delete_collection(self.settings.qdrant_collection)
        self.client.create_collection(
            collection_name=self.settings.qdrant_collection,
            vectors_config={
                self.settings.dense_vector_name: models.VectorParams(
                    size=self.settings.dense_dim,
                    distance=models.Distance.COSINE,
                )
            },
            sparse_vectors_config={
                self.settings.sparse_vector_name: models.SparseVectorParams()
            },
        )

    def health(self) -> str:
        try:
            info = self.client.get_collections()
            return "ok" if info is not None else "unknown"
        except Exception as exc:
            logger.warning("Qdrant health check failed: %s", exc)
            return "down"

    def upsert_chunks(self, vectors: list[VectorPayload]) -> None:
        if not vectors:
            return
        self.ensure_collection()
        points = [
            models.PointStruct(
                id=vector.chunk_id,
                vector={
                    self.settings.dense_vector_name: vector.dense,
                    self.settings.sparse_vector_name: models.SparseVector(
                        indices=vector.sparse_indices,
                        values=vector.sparse_values,
                    ),
                },
                payload=vector.payload,
            )
            for vector in vectors
        ]
        self.client.upsert(collection_name=self.settings.qdrant_collection, points=points)

    def _metadata_filter(
        self,
        wing: str | None = None,
        room: str | None = None,
        memory_type: str | None = None,
        status: str | None = None,
    ) -> models.Filter | None:
        must: list[models.FieldCondition] = []
        if wing:
            must.append(models.FieldCondition(key="wing", match=models.MatchValue(value=wing)))
        if room:
            must.append(models.FieldCondition(key="room", match=models.MatchValue(value=room)))
        if memory_type:
            must.append(
                models.FieldCondition(
                    key="memory_type", match=models.MatchValue(value=memory_type)
                )
            )
        if status:
            must.append(
                models.FieldCondition(key="status", match=models.MatchValue(value=status))
            )
        if not must:
            return None
        return models.Filter(must=must)

    def search_dense(
        self,
        dense_vector: list[float],
        *,
        wing: str | None = None,
        room: str | None = None,
        memory_type: str | None = None,
        status: str | None = None,
        limit: int = 20,
    ) -> list[models.ScoredPoint]:
        self.ensure_collection()
        return self.client.query_points(
            collection_name=self.settings.qdrant_collection,
            query=dense_vector,
            using=self.settings.dense_vector_name,
            query_filter=self._metadata_filter(wing, room, memory_type, status),
            limit=limit,
            with_payload=True,
        ).points

    def search_sparse(
        self,
        sparse_indices: list[int],
        sparse_values: list[float],
        *,
        wing: str | None = None,
        room: str | None = None,
        memory_type: str | None = None,
        status: str | None = None,
        limit: int = 20,
    ) -> list[models.ScoredPoint]:
        self.ensure_collection()
        return self.client.query_points(
            collection_name=self.settings.qdrant_collection,
            query=models.SparseVector(indices=sparse_indices, values=sparse_values),
            using=self.settings.sparse_vector_name,
            query_filter=self._metadata_filter(wing, room, memory_type, status),
            limit=limit,
            with_payload=True,
        ).points

    @staticmethod
    def build_payload(memory: MemoryRecord, chunk: ChunkRecord) -> dict[str, Any]:
        created = parse_iso_datetime(memory.created_at)
        updated = parse_iso_datetime(memory.updated_at)
        valid_from = parse_iso_datetime(memory.valid_from)
        valid_until = parse_iso_datetime(memory.valid_until)

        def ts(value: datetime | None) -> int | None:
            return int(value.timestamp()) if value else None

        return {
            "chunk_id": chunk.id,
            "memory_id": memory.id,
            "wing": memory.wing,
            "room": memory.room,
            "memory_type": memory.memory_type,
            "status": memory.status,
            "version": memory.version,
            "importance": memory.importance,
            "confidence": memory.confidence,
            "created_at": memory.created_at,
            "updated_at": memory.updated_at,
            "valid_from": memory.valid_from,
            "valid_until": memory.valid_until,
            "created_ts": ts(created),
            "updated_ts": ts(updated),
            "valid_from_ts": ts(valid_from),
            "valid_until_ts": ts(valid_until),
            "source": memory.source,
            "source_uri": memory.source_uri,
            "title": memory.title,
        }
