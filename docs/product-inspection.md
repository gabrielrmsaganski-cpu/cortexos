# Product Inspection

Inspection date: 2026-04-08 UTC

Project root: `/home/saganski/workspace/experiments/cortexos`

## Current runtime state

- API service: `cortexos-api.service`
  - status: active
  - bind: `127.0.0.1:8011`
- Qdrant:
  - container: `cortexos-qdrant`
  - bind: `127.0.0.1:6333`, `127.0.0.1:6334`
- SearXNG:
  - container: `cortexos-searxng`
  - bind: `127.0.0.1:8787`
- Ollama:
  - host service already present
  - bind: `127.0.0.1:11434`

Current health endpoint:

```json
{"status":"ok","api":"ok","db":"ok","qdrant":"ok","ollama":"ok","time":"2026-04-08T15:05:44+00:00"}
```

## Current backend architecture

The backend is already a usable memory engine and should be preserved.

Existing layers:

- FastAPI API in [`app/api/main.py`](/home/saganski/workspace/experiments/cortexos/app/api/main.py)
- orchestration and scoring in [`app/memory/service.py`](/home/saganski/workspace/experiments/cortexos/app/memory/service.py)
- canonical storage in SQLite via [`app/storage/repository.py`](/home/saganski/workspace/experiments/cortexos/app/storage/repository.py)
- retrieval index in Qdrant via [`app/storage/qdrant_store.py`](/home/saganski/workspace/experiments/cortexos/app/storage/qdrant_store.py)
- hybrid query normalization and reranking via [`app/retrieval/query.py`](/home/saganski/workspace/experiments/cortexos/app/retrieval/query.py) and [`app/rerank/service.py`](/home/saganski/workspace/experiments/cortexos/app/rerank/service.py)
- synthesis via [`app/reasoning/synthesizer.py`](/home/saganski/workspace/experiments/cortexos/app/reasoning/synthesizer.py)
- CLI via [`app/cli/main.py`](/home/saganski/workspace/experiments/cortexos/app/cli/main.py)
- MCP server via [`app/mcp/server.py`](/home/saganski/workspace/experiments/cortexos/app/mcp/server.py)

## Existing public API

Already implemented:

- `GET /healthz`
- `POST /api/v1/memories`
- `POST /api/v1/search`
- `POST /api/v1/answer`
- `POST /api/v1/ingest/document`
- `POST /api/v1/ingest/webpage`
- `POST /api/v1/ingest/site`
- `GET /api/v1/wings`
- `GET /api/v1/rooms`
- `GET /api/v1/conflicts`
- `GET /api/v1/superseded`
- `POST /api/v1/explain`

Current API coverage is enough for programmatic usage, but not enough for a strong product UI. The main gap is read-oriented product endpoints: stats, list/detail, timeline, eval runs, operations summaries, and richer explain contracts.

## Existing memory data model

Current canonical memory shape:

- `id`
- `wing`
- `room`
- `memory_type`
- `source`
- `source_uri`
- `title`
- `verbatim_text`
- `normalized_text`
- `content_sha256`
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
- `metadata`
- `classifier`
- `explain`

Current explicit relation model:

- `duplicate`
- `complements`
- `conflicts_with`
- `supersedes`

Current chunk model:

- `id`
- `memory_id`
- `chunk_index`
- `text`
- `token_count`
- `char_start`
- `char_end`

## Existing explainability

Current explain mode returns:

- `normalized_query`
- `expanded_query`
- `keywords`
- `dense_hits`
- `sparse_hits`
- `final`

Current search scoring already includes:

- dense score
- sparse score
- hybrid score
- rerank score
- temporal score
- importance
- recency
- penalty
- final score

This is a strong base for an Explain Center, but the response still lacks explicit stage timings, selected strategy/mode, and a UI-friendly contract for penalties, lifecycle weighting, and synthesis fallback.

## Existing operations surface

Current scripts:

- [`scripts/start.sh`](/home/saganski/workspace/experiments/cortexos/scripts/start.sh)
- [`scripts/stop.sh`](/home/saganski/workspace/experiments/cortexos/scripts/stop.sh)
- [`scripts/status.sh`](/home/saganski/workspace/experiments/cortexos/scripts/status.sh)
- [`scripts/smoke_test.sh`](/home/saganski/workspace/experiments/cortexos/scripts/smoke_test.sh)
- [`scripts/backup.sh`](/home/saganski/workspace/experiments/cortexos/scripts/backup.sh)
- [`scripts/restore.sh`](/home/saganski/workspace/experiments/cortexos/scripts/restore.sh)

Current system operation is good for infra use, but not yet productized:

- no browser UI
- no visual dashboard
- no built-in ops panel
- no timeline view
- no eval history viewer

## Existing sample data state

Current local database snapshot at inspection time:

- total memories: `48`
- by status:
  - `active`: `26`
  - `conflicting`: `14`
  - `superseded`: `8`
- by type:
  - `episodic`: `38`
  - `procedural`: `10`

The current corpus is mostly smoke/eval/probe data. It is enough to build the product shell, but not ideal for demos. A reproducible demo dataset is needed.

## Product gaps

Main product gaps found:

- no web interface
- no visual explorer for memories, links, and versions
- no timeline view for lifecycle evolution
- no query workbench for comparing raw retrieval, rerank, and synthesis
- no operations dashboard for service health and runtime checks
- no eval history or benchmark UI
- no demo mode with seeded, coherent example data
- no GitHub-grade landing and screenshots workflow

## Frontend stack decision

Recommended frontend stack:

- React + Vite
- TypeScript
- Tailwind CSS
- static build served by FastAPI

Reasoning:

- the backend already exists and should remain the runtime authority
- a static SPA is simpler than introducing a second server-side framework
- Vite is lighter operationally than Next.js for this server and this product shape
- build artifacts can be served by the existing API service on the existing local port
- dev mode can still use a separate frontend dev server on a verified free local port when needed

Verified available tooling for this choice:

- `node`: `v24.14.1`
- `pnpm`: `10.33.0`
- verified free at inspection now:
  - `8012`
  - `4173`
  - `5173`

## Integration approach

Recommended integration path:

1. keep FastAPI as the backend API and control plane
2. add product endpoints without breaking the existing API
3. build a React SPA in a dedicated `ui/` workspace
4. serve the compiled frontend from FastAPI for local-only production use
5. keep Docker and systemd topology unchanged

This preserves the current architecture while turning it into a demonstrable product.
