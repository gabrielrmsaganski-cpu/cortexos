from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

MemoryType = Literal["episodic", "factual", "procedural", "reference"]
MemoryStatus = Literal["active", "superseded", "conflicting", "archived"]
QueryMode = Literal["fast", "balanced", "deep"]


def _blank_to_none(value: Any) -> Any:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return value


class MemoryInput(BaseModel):
    text: str = Field(min_length=1)
    wing: str | None = None
    room: str | None = None
    memory_type: MemoryType | None = None
    source: str = "api"
    source_uri: str | None = None
    title: str | None = None
    importance: float | None = Field(default=None, ge=0.0, le=1.0)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    created_at: datetime | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("text", mode="before")
    @classmethod
    def validate_text(cls, value: Any) -> str:
        if not isinstance(value, str):
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("text cannot be empty")
        return stripped

    @field_validator(
        "wing",
        "room",
        "memory_type",
        "source_uri",
        "title",
        "created_at",
        "valid_from",
        "valid_until",
        mode="before",
    )
    @classmethod
    def blank_optional_fields_to_none(cls, value: Any) -> Any:
        return _blank_to_none(value)


class MemoryRecord(BaseModel):
    id: str
    wing: str
    room: str
    memory_type: MemoryType
    source: str
    source_uri: str | None = None
    title: str | None = None
    verbatim_text: str
    normalized_text: str
    content_sha256: str
    importance: float
    confidence: float
    created_at: str
    updated_at: str
    valid_from: str | None = None
    valid_until: str | None = None
    version: int
    status: MemoryStatus
    superseded_by: str | None = None
    duplicate_of: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    classifier: dict[str, Any] = Field(default_factory=dict)
    explain: dict[str, Any] = Field(default_factory=dict)


class ChunkRecord(BaseModel):
    id: str
    memory_id: str
    chunk_index: int
    text: str
    token_count: int
    char_start: int
    char_end: int


class LinkRecord(BaseModel):
    source_memory_id: str
    target_memory_id: str
    relation_type: str
    score: float
    reason: str | None = None
    created_at: str


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    mode: QueryMode = "balanced"
    wing: str | None = None
    room: str | None = None
    memory_type: MemoryType | None = None
    status: MemoryStatus | None = None
    as_of: datetime | None = None
    limit: int = Field(default=12, ge=1, le=50)
    explain: bool = False

    @field_validator("query", mode="before")
    @classmethod
    def validate_query(cls, value: Any) -> str:
        if not isinstance(value, str):
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("query cannot be empty")
        return stripped

    @field_validator("wing", "room", "memory_type", "status", "as_of", mode="before")
    @classmethod
    def blank_search_fields_to_none(cls, value: Any) -> Any:
        return _blank_to_none(value)


class SearchResult(BaseModel):
    memory: MemoryRecord
    excerpt: str
    chunk_id: str
    scores: dict[str, float]
    reasons: list[str] = Field(default_factory=list)


class SearchResponse(BaseModel):
    query: str
    mode: QueryMode = "balanced"
    normalized_query: str
    results: list[SearchResult]
    explain: dict[str, Any] | None = None
    timings_ms: dict[str, float] | None = None


class AnswerRequest(SearchRequest):
    synthesis_model: str | None = None

    @field_validator("synthesis_model", mode="before")
    @classmethod
    def blank_synthesis_model_to_none(cls, value: Any) -> Any:
        return _blank_to_none(value)


class AnswerResponse(BaseModel):
    answer: str
    summary: list[str]
    conflicts: list[str]
    supporting_memories: list[str]
    explain: dict[str, Any] | None = None
    mode: QueryMode = "balanced"
    llm_used: bool = False
    fallback_used: bool = False
    timings_ms: dict[str, float] | None = None


class IngestResponse(BaseModel):
    memory: MemoryRecord
    chunks: list[ChunkRecord]
    links: list[LinkRecord]
    action: str


class HealthResponse(BaseModel):
    status: str
    api: str
    db: str
    qdrant: str
    ollama: str
    time: str
