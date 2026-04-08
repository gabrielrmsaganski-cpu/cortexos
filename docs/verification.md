# Verification

Verification date: 2026-04-08 UTC

Project root: `/home/saganski/workspace/experiments/cortexos`

## Static checks

- `./.venv/bin/ruff check app tests`
  - result: `All checks passed!`
- `./.venv/bin/pytest -q`
  - result: `14 passed, 2 warnings in 10.64s`

## Services

- `systemctl status cortexos-api --no-pager`
  - result: service active and running as `User=saganski`
  - installed unit description validated as `CortexOS API`
- `docker compose ps`
  - result:
    - `cortexos-qdrant` up on `127.0.0.1:6333-6334`
    - `cortexos-searxng` up on `127.0.0.1:8787`
- `curl -fsS http://127.0.0.1:8011/healthz`
  - result:

```json
{"status":"ok","api":"ok","db":"ok","qdrant":"ok","ollama":"ok","time":"2026-04-08T18:53:24+00:00"}
```

## Local models

- `ollama list`
  - verified installed:
    - `qwen3:8b`
    - `aion:latest`
    - `qwen2.5:3b`
    - `qwen2.5:7b`
    - `nous-hermes:latest`

## Runtime eval harness

- `./.venv/bin/python -m app.evals.harness`
  - result: `passed: true`
  - validated:
    - exact dedup inside the same `wing/room`
    - supersession status and `superseded_by`
    - conflict status for incompatible memories
    - temporal retrieval with `as_of`
    - hybrid retrieval path returning both dense and sparse hits
    - reranker ordering for relevant vs irrelevant passages
    - synthesis returning conflict-aware resolution instead of raw chunks

Observed harness output excerpt:

```json
{
  "passed": true,
  "results": [
    {"name": "dedup", "passed": true},
    {"name": "conflict_and_supersession", "passed": true},
    {"name": "temporal", "passed": true},
    {"name": "hybrid", "passed": true},
    {"name": "rerank", "passed": true},
    {"name": "synthesis", "passed": true}
  ]
}
```

## API validation

The following API flow was executed against the running service using a fresh wing:

- added launch memory: `The launch date is 2026-05-15.`
- added updated launch memory: `The launch moved to 2026-05-20.`
- added conflicting office memory: `The office is in Lisbon.`
- added conflicting office memory: `The office is in Porto.`

Observed results:

- `GET /api/v1/superseded`
  - filtered result count for the test wing: `1`
  - superseded text: `The launch date is 2026-05-15.`
- `GET /api/v1/conflicts`
  - filtered result count for the test wing: `2`
  - conflicting texts:
    - `The office is in Lisbon.`
    - `The office is in Porto.`
- `POST /api/v1/answer` for launch room
  - latency: `61.86s`
  - answer:

```text
The current launch date is **2026-05-20**, as specified in the active memory. The earlier date of 2026-05-15 is superseded and no longer valid.
```

- `POST /api/v1/answer` for hq room
  - latency: `60.26s`
  - answer:

```text
The answer is unresolved due to conflicting memories:
- One memory states the office is in **Porto**.
- Another memory states the office is in **Lisbon**.

Both memories are marked as conflicting and do not resolve the discrepancy.
```

## CLI and MCP

- `./.venv/bin/cortexos-cli search --query 'current launch date' --wing smoke --room launch`
  - result: returned the stored smoke memory with final score breakdown
- `./.venv/bin/python - <<'PY' ... from app.mcp.server import mcp ...`
  - result:
    - `cortexos`
    - `tools-ready`

## External tools path

- `curl -fsS 'http://127.0.0.1:8787/search?q=memory&format=json'`
  - result: SearXNG returned JSON search results successfully

## Product UI validation

- `cd ui && pnpm install && pnpm build`
  - result: build passed
  - build output includes `ui/dist/index.html` and split JS bundles
- isolated UI/API validation server:

```bash
./.venv/bin/python -m uvicorn app.api.main:app --host 127.0.0.1 --port 8012
```

- `curl -fsS http://127.0.0.1:8012/`
  - result: returned SPA `index.html`
- `curl -fsS http://127.0.0.1:8012/explorer`
  - result: returned SPA `index.html`
- `./scripts/ui_smoke_test.sh http://127.0.0.1:8012`
  - result: `UI smoke test passed for http://127.0.0.1:8012`
- `./scripts/ui_smoke_test.sh http://127.0.0.1:8011`
  - result: `UI smoke test passed for http://127.0.0.1:8011`
- `./.venv/bin/python scripts/generate_screenshots.py`
  - result: generated:
    - `screenshots/dashboard.png`
    - `screenshots/query.png`
    - `screenshots/explain.png`
    - `screenshots/conflict.png`

## Demo mode validation

- `POST /api/v1/demo/seed` on `127.0.0.1:8012`
  - first run result: `created: 13`, `skipped: 0`
  - second run result: `created: 0`, `skipped: 13`
  - validated that demo seed is idempotent at the content level
- `GET /api/v1/memories?wing=demo-product`
  - result: returned 4 demo launch memories
  - verified one demo memory in `superseded` state
- `GET /api/v1/timeline?wing=demo-product`
  - result: returned created-series data for `2026-03-01`, `2026-03-18`, and `2026-03-22`
  - relation-series included `supersedes`

## Query Studio validation

- `POST /api/v1/query-studio` with:

```json
{"query":"What is the current launch date?","wing":"demo-product","room":"launch","mode":"fast"}
```

- result:
  - top answer: `Best-supported answer: The launch moved to 2026-05-20.`
  - `llm_used: false`
  - `fallback_used: false`
  - returned:
    - `search`
    - `answer`
    - `latency_ms`
    - `strategy`
  - observed stage timings in one validated run:
    - `encode`: `565.38 ms`
    - `rerank`: `3142.29 ms`
    - `total`: `3727.49 ms`

## Eval endpoint validation

- `POST /api/v1/evals/run` with:

```json
{"mode":"fast"}
```

- result:
  - `run_id`: `eval_fcb293eaa5c9449c97d00720dfb4b02e`
  - `passed: true`
  - `total_ms: 16794.32`
  - all cases passed:
    - dedup
    - conflict_and_supersession
    - temporal
    - hybrid
    - rerank
    - synthesis

## Corrections made during verification

- fixed Qdrant dense vector dimension to `1024` for `BAAI/bge-m3`
- fixed Qdrant point IDs to use UUIDs
- ensured collection recreation when vector dimensions do not match
- made encoder and reranker lazy-loaded to avoid startup failures
- scoped exact dedup to the same `wing/room` instead of global hash-only dedup
- improved deterministic synthesis so conflicting-only evidence returns unresolved status instead of arbitrarily selecting one chunk

## Remaining limits

- `qwen3:8b` works through Ollama on this host, but first-answer latency after service restart and subsequent answer latency were both about 60 seconds in the API test. This is the main operational tradeoff on this 4 vCPU CPU-only machine.
- `qwen3:14b` was not installed or validated.
- `qwen3-coder-next:q4_K_M` was configured as an optional profile only and not installed.
- Playwright, Crawl4AI, and Docling integrations are wired and importable, but they were not fully exercised against a real site/document corpus in this verification pass.
- Exa, Tavily, and Firecrawl remain optional integration points and were not enabled because no API keys were provided.

## Final product validation

- validated on the production-bound local endpoint `http://127.0.0.1:8011`
- runtime moved from `.../experiments/memory-os` to `.../experiments/cortexos`
- active systemd unit migrated from `memory-os-api.service` to `cortexos-api.service`
- active Qdrant collection migrated from `memory_os_chunks` to `cortexos_chunks`
- `GET /` served the SPA shell with split assets:
  - page title: `CortexOS`
  - `/assets/index-3D3xRbWw.js`
  - `/assets/react-CQ0ucGi3.js`
  - `/assets/charts-jZT_xPoX.js`
- `GET http://127.0.0.1:6333/collections`
  - result: only `cortexos_chunks` remained after migration cleanup
- `GET /api/v1/dashboard` returned populated product data with:
  - `72` total memories
  - status breakdown:
    - `41` active
    - `20` conflicting
    - `11` superseded
  - recent query and eval telemetry
- `POST /api/v1/query-studio` on `2026-04-08` with fast mode returned:
  - answer: `Best-supported answer: The launch moved to 2026-05-20.`
  - `llm_used: false`
  - `fallback_used: true`
  - stage timings:
    - `encode`: `5272.67 ms`
    - `rerank`: `1722.66 ms`
    - `total`: `7009.7 ms`
- `./scripts/ui_smoke_test.sh http://127.0.0.1:8011` passed
- repository checks after final edits:
  - `./.venv/bin/pytest -q` -> `14 passed`
  - `./.venv/bin/ruff check app tests` -> passed
  - `cd ui && pnpm build` -> passed

## Query Studio hardening validation

- previous failure reproduced before the fix:
  - `POST /api/v1/query-studio` on `127.0.0.1:8011` returned `500`
  - journal showed `NotImplementedError: Cannot copy out of meta tensor` from `BGEM3FlagModel`
- after the fix:
  - `POST /api/v1/query-studio` with blank optional filters now returns `200`
  - UI-facing JSON payloads with `wing=""`, `room=""`, `memory_type=""`, `status=""` are accepted and normalized
  - `POST /api/v1/query-studio` in Portuguese now returns `200` and no longer answers confidently from weak evidence
  - current deterministic synthesis result for weak evidence:
    - `No high-confidence memory matched this query. The retrieved candidates were too weak or semantically off-target.`
- regression coverage added:
  - blank optional filter acceptance
  - lexical fallback path when the encoder breaks
  - weak-evidence synthesis guard
