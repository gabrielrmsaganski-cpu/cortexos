from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    env: str = Field(
        default="development",
        validation_alias=AliasChoices("CORTEXOS_ENV", "MEMORY_OS_ENV"),
    )
    host: str = Field(
        default="127.0.0.1",
        validation_alias=AliasChoices("CORTEXOS_HOST", "MEMORY_OS_HOST"),
    )
    port: int = Field(
        default=8011,
        validation_alias=AliasChoices("CORTEXOS_PORT", "MEMORY_OS_PORT"),
    )
    log_level: str = Field(
        default="INFO",
        validation_alias=AliasChoices("CORTEXOS_LOG_LEVEL", "MEMORY_OS_LOG_LEVEL"),
    )
    data_dir: Path = Field(
        default=Path("./data"),
        validation_alias=AliasChoices("CORTEXOS_DATA_DIR", "MEMORY_OS_DATA_DIR"),
    )
    db_path: Path = Field(
        default=Path("./data/cortexos.sqlite3"),
        validation_alias=AliasChoices("CORTEXOS_DB_PATH", "MEMORY_OS_DB_PATH"),
    )
    qdrant_url: str = Field(
        default="http://127.0.0.1:6333",
        validation_alias=AliasChoices("CORTEXOS_QDRANT_URL", "MEMORY_OS_QDRANT_URL"),
    )
    qdrant_collection: str = Field(
        default="cortexos_chunks",
        validation_alias=AliasChoices("CORTEXOS_QDRANT_COLLECTION", "MEMORY_OS_QDRANT_COLLECTION"),
    )
    dense_vector_name: str = Field(
        default="dense",
        validation_alias=AliasChoices("CORTEXOS_DENSE_VECTOR_NAME", "MEMORY_OS_DENSE_VECTOR_NAME"),
    )
    sparse_vector_name: str = Field(
        default="sparse",
        validation_alias=AliasChoices(
            "CORTEXOS_SPARSE_VECTOR_NAME",
            "MEMORY_OS_SPARSE_VECTOR_NAME",
        ),
    )
    dense_dim: int = Field(
        default=1024,
        validation_alias=AliasChoices("CORTEXOS_DENSE_DIM", "MEMORY_OS_DENSE_DIM"),
    )
    default_model: str = Field(
        default="qwen3:8b",
        validation_alias=AliasChoices("CORTEXOS_DEFAULT_MODEL", "MEMORY_OS_DEFAULT_MODEL"),
    )
    quality_model: str = Field(
        default="qwen3:14b",
        validation_alias=AliasChoices("CORTEXOS_QUALITY_MODEL", "MEMORY_OS_QUALITY_MODEL"),
    )
    code_model: str = Field(
        default="qwen3-coder-next:q4_K_M",
        validation_alias=AliasChoices("CORTEXOS_CODE_MODEL", "MEMORY_OS_CODE_MODEL"),
    )
    ollama_url: str = Field(
        default="http://127.0.0.1:11434",
        validation_alias=AliasChoices("CORTEXOS_OLLAMA_URL", "MEMORY_OS_OLLAMA_URL"),
    )
    embedding_backend: str = Field(
        default="bge-m3",
        validation_alias=AliasChoices("CORTEXOS_EMBEDDING_BACKEND", "MEMORY_OS_EMBEDDING_BACKEND"),
    )
    rerank_backend: str = Field(
        default="bge-reranker-v2-m3",
        validation_alias=AliasChoices("CORTEXOS_RERANK_BACKEND", "MEMORY_OS_RERANK_BACKEND"),
    )
    enable_llm_synthesis: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "CORTEXOS_ENABLE_LLM_SYNTHESIS",
            "MEMORY_OS_ENABLE_LLM_SYNTHESIS",
        ),
    )
    enable_query_expansion: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "CORTEXOS_ENABLE_QUERY_EXPANSION",
            "MEMORY_OS_ENABLE_QUERY_EXPANSION",
        ),
    )
    enable_playwright: bool = Field(
        default=True,
        validation_alias=AliasChoices("CORTEXOS_ENABLE_PLAYWRIGHT", "MEMORY_OS_ENABLE_PLAYWRIGHT"),
    )
    enable_crawl4ai: bool = Field(
        default=True,
        validation_alias=AliasChoices("CORTEXOS_ENABLE_CRAWL4AI", "MEMORY_OS_ENABLE_CRAWL4AI"),
    )
    enable_docling: bool = Field(
        default=True,
        validation_alias=AliasChoices("CORTEXOS_ENABLE_DOCLING", "MEMORY_OS_ENABLE_DOCLING"),
    )
    enable_searxng: bool = Field(
        default=True,
        validation_alias=AliasChoices("CORTEXOS_ENABLE_SEARXNG", "MEMORY_OS_ENABLE_SEARXNG"),
    )
    searxng_url: str = Field(
        default="http://127.0.0.1:8787",
        validation_alias=AliasChoices("CORTEXOS_SEARXNG_URL", "MEMORY_OS_SEARXNG_URL"),
    )
    default_wing: str = Field(
        default="general",
        validation_alias=AliasChoices("CORTEXOS_DEFAULT_WING", "MEMORY_OS_DEFAULT_WING"),
    )
    default_room: str = Field(
        default="inbox",
        validation_alias=AliasChoices("CORTEXOS_DEFAULT_ROOM", "MEMORY_OS_DEFAULT_ROOM"),
    )
    chunk_size: int = Field(
        default=1200,
        ge=200,
        validation_alias=AliasChoices("CORTEXOS_CHUNK_SIZE", "MEMORY_OS_CHUNK_SIZE"),
    )
    chunk_overlap: int = Field(
        default=180,
        ge=0,
        validation_alias=AliasChoices("CORTEXOS_CHUNK_OVERLAP", "MEMORY_OS_CHUNK_OVERLAP"),
    )
    rerank_top_n: int = Field(
        default=20,
        ge=5,
        validation_alias=AliasChoices("CORTEXOS_RERANK_TOP_N", "MEMORY_OS_RERANK_TOP_N"),
    )
    retrieve_top_k: int = Field(
        default=12,
        ge=1,
        validation_alias=AliasChoices("CORTEXOS_RETRIEVE_TOP_K", "MEMORY_OS_RETRIEVE_TOP_K"),
    )

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)


LEGACY_ENV_TO_FIELD = {
    "MEMORY_OS_ENV": "env",
    "MEMORY_OS_HOST": "host",
    "MEMORY_OS_PORT": "port",
    "MEMORY_OS_LOG_LEVEL": "log_level",
    "MEMORY_OS_DATA_DIR": "data_dir",
    "MEMORY_OS_DB_PATH": "db_path",
    "MEMORY_OS_QDRANT_URL": "qdrant_url",
    "MEMORY_OS_QDRANT_COLLECTION": "qdrant_collection",
    "MEMORY_OS_DENSE_VECTOR_NAME": "dense_vector_name",
    "MEMORY_OS_SPARSE_VECTOR_NAME": "sparse_vector_name",
    "MEMORY_OS_DENSE_DIM": "dense_dim",
    "MEMORY_OS_DEFAULT_MODEL": "default_model",
    "MEMORY_OS_QUALITY_MODEL": "quality_model",
    "MEMORY_OS_CODE_MODEL": "code_model",
    "MEMORY_OS_OLLAMA_URL": "ollama_url",
    "MEMORY_OS_EMBEDDING_BACKEND": "embedding_backend",
    "MEMORY_OS_RERANK_BACKEND": "rerank_backend",
    "MEMORY_OS_ENABLE_LLM_SYNTHESIS": "enable_llm_synthesis",
    "MEMORY_OS_ENABLE_QUERY_EXPANSION": "enable_query_expansion",
    "MEMORY_OS_ENABLE_PLAYWRIGHT": "enable_playwright",
    "MEMORY_OS_ENABLE_CRAWL4AI": "enable_crawl4ai",
    "MEMORY_OS_ENABLE_DOCLING": "enable_docling",
    "MEMORY_OS_ENABLE_SEARXNG": "enable_searxng",
    "MEMORY_OS_SEARXNG_URL": "searxng_url",
    "MEMORY_OS_DEFAULT_WING": "default_wing",
    "MEMORY_OS_DEFAULT_ROOM": "default_room",
    "MEMORY_OS_CHUNK_SIZE": "chunk_size",
    "MEMORY_OS_CHUNK_OVERLAP": "chunk_overlap",
    "MEMORY_OS_RERANK_TOP_N": "rerank_top_n",
    "MEMORY_OS_RETRIEVE_TOP_K": "retrieve_top_k",
}


def _legacy_overrides() -> dict[str, str]:
    overrides: dict[str, str] = {}
    for legacy_key, field_name in LEGACY_ENV_TO_FIELD.items():
        cortex_key = f"CORTEXOS_{legacy_key.removeprefix('MEMORY_OS_')}"
        if cortex_key in os.environ or legacy_key not in os.environ:
            continue
        overrides[field_name] = os.environ[legacy_key]
    return overrides


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings(**_legacy_overrides())
    settings.ensure_dirs()
    return settings
