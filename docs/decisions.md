# Technical Decisions

## Why Qdrant

Qdrant was selected because it supports named dense vectors, sparse vectors, metadata filters, hybrid fusion, and operationally simple local deployment. On this server Docker is already used in production, so running Qdrant locally with persistent storage is lower risk than introducing another database stack.

## Why BGE-M3

BGE-M3 is the preferred embedding backend because one model can produce dense and sparse representations for hybrid retrieval, which reduces architectural drift between dense and lexical paths. It also supports multilingual inputs and longer contexts than smaller sentence-transformer baselines.

## Why `bge-reranker-v2-m3`

Dense and sparse retrieval are still recall-oriented stages. The reranker is used after fusion to improve precision on the top candidate set, especially for exact entity matches, temporal phrasing, and near-duplicate memories that need discrimination.

## Why `qwen3:8b` as default local model

This server has 4 vCPUs, 31 GiB RAM, and no swap. `qwen3:8b` is the best default compromise between answer quality and acceptable local latency for synthesis and optional classification tasks. The memory system does not depend on it to function.

## When to use `qwen3:14b`

Use `qwen3:14b` only when higher answer quality matters more than latency, such as deeper synthesis, conflict explanation, or review-style memory answers. It should not be the default on this CPU-only machine.

## When to use `qwen3-coder-next:q4_K_M`

Use the coder profile only for code-oriented memory synthesis or MCP scenarios where the retrieved memories contain implementation detail and code review context. It is optional and not part of the baseline runtime path.

## Why host systemd for the API

The API needs easy access to local files, Ollama, Playwright, Crawl4AI, and Docling. Running the app on the host is operationally simpler here than containerizing every integration point.

## Why Docker for Qdrant and SearXNG

These services are self-contained and already fit the machine's operational pattern. Docker also keeps their lifecycle and data directories isolated from the Python app while letting containers restart automatically with the Docker daemon.

## Tradeoffs accepted

- SQLite as canonical store is simpler than PostgreSQL, but it limits concurrent write throughput. This is acceptable for a single-server agent memory system.
- Default fallbacks exist for embeddings, reranking, and synthesis so the system remains operational even when heavyweight model dependencies are missing.
- SearXNG is integrated as a local-only helper, not an internet-facing search service.
