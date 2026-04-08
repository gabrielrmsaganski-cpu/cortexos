# Architecture

## Goal

CortexOS is a memory operating system for agents, not a thin vector wrapper. The design keeps verbatim memory records intact, enriches them with lifecycle metadata and links, and uses a multi-stage retrieval pipeline before synthesis.

## Core components

### Canonical store

- SQLite stores canonical memory records, chunk metadata, lifecycle status, versions, and explicit relations such as duplicate, complement, conflict, and supersession.
- Verbatim text remains the source of truth.

### Retrieval store

- Qdrant stores dense and sparse vectors for chunks.
- Each indexed chunk carries payload metadata for:
  - wing
  - room
  - memory type
  - status
  - version
  - confidence
  - importance
  - created and validity timestamps

### Ingestion layer

- accepts raw API input, files, webpages, and crawl jobs
- classifies memories as episodic, factual, procedural, or reference
- chunks with overlap to preserve local context
- detects duplicate, complement, contradiction, and supersession before final commit

### Retrieval layer

Pipeline:

1. query normalization
2. optional query expansion
3. metadata and temporal filtering
4. dense retrieval
5. sparse retrieval
6. hybrid fusion
7. reranking
8. temporal reweighting
9. lifecycle and conflict penalties
10. final grouped context pack

### Reasoning layer

- constructs a coherent answer payload
- surfaces conflict explicitly
- prefers active and current records
- cites supporting memory ids and excerpts
- uses Ollama for synthesis when configured and available
- falls back to deterministic synthesis when the model is unavailable

### External tools

- Playwright for rendered webpage capture
- Crawl4AI for site and page crawling
- Docling for document parsing
- SearXNG for local search discovery
- MCP server for tool-based access

## Storage decision

Single Qdrant collection with named vectors was chosen instead of one collection per memory type.

Reasons:

- hybrid retrieval over all memory types is a first-class requirement
- lifecycle filters are easier as payload filters than cross-collection fan-out
- one collection simplifies reranking, scoring, and explain mode
- type-specific slicing is still possible through payload filters

## Data model summary

Memory record:

- `id`
- `wing`
- `room`
- `memory_type`
- `source`
- `source_uri`
- `verbatim_text`
- `importance`
- `confidence`
- `created_at`
- `updated_at`
- `valid_from`
- `valid_until`
- `version`
- `status`
- `superseded_by`
- `duplicate_of`

Explicit links:

- `duplicate`
- `complements`
- `conflicts_with`
- `supersedes`

Chunk record:

- `id`
- `memory_id`
- `chunk_index`
- `text`
- `char_start`
- `char_end`

## Explain mode

Explain mode captures:

- normalized query
- applied filters
- dense hits
- sparse hits
- fused candidate set
- rerank scores
- temporal adjustments
- status and conflict penalties
- final selected evidence
