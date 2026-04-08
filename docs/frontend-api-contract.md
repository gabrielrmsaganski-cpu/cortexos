# Frontend API Contract

## Existing engine endpoints reused

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

## Product endpoints added

### Dashboard

- `GET /api/v1/dashboard`
  - returns:
    - `stats`
    - `timeline`
    - `operations`

### Memory explorer

- `GET /api/v1/memories`
  - query params:
    - `search_text`
    - `wing`
    - `room`
    - `memory_type`
    - `status`
    - `min_importance`
    - `max_importance`
    - `created_from`
    - `created_to`
    - `conflict_only`
    - `superseded_only`
    - `limit`
    - `offset`
  - returns:
    - `total`
    - `limit`
    - `offset`
    - `items[]`
      - `memory`
      - `access_count`
      - `quality_score`

- `POST /api/v1/memories/preview`
  - body: `MemoryInput`
  - returns:
    - classifier output
    - chunk preview
    - duplicate hit or related links

- `GET /api/v1/memories/{memory_id}`
  - returns:
    - `memory`
    - `chunks`
    - `links`
    - `version_history`
    - `access_count`
    - `quality_score`

- `GET /api/v1/memories/{memory_id}/compare/{other_id}`
  - returns:
    - `left`
    - `right`
    - `link`

- `POST /api/v1/memories/{memory_id}/archive`
  - returns archived memory

- `POST /api/v1/memories/{memory_id}/reindex`
  - returns reindex count

### Timeline

- `GET /api/v1/timeline`
  - query params:
    - `wing`
    - `room`
    - `memory_type`
    - `status`
    - `limit`
  - returns:
    - `events[]`
    - `series.created[]`
    - `series.relations[]`

### Query studio

- `POST /api/v1/query-studio`
  - body: `AnswerRequest`
  - mode values:
    - `fast`
    - `balanced`
    - `deep`
  - returns:
    - `mode`
    - `query`
    - `filters`
    - `search`
    - `answer`
    - `latency_ms`
    - `strategy`

### Ingestion center preview paths

- `POST /api/v1/ingest/document/preview`
- `POST /api/v1/ingest/webpage/preview`
- `POST /api/v1/ingest/site/preview`

### Operations center

- `GET /api/v1/operations/status`
  - returns:
    - `health`
    - `ports`
    - `storage`
    - `service`
    - `containers`
    - `api_logs`
    - `available_models`
    - `recent_queries`
    - `recent_evals`

- `POST /api/v1/operations/smoke`
  - executes `scripts/smoke_test.sh`
  - returns:
    - `success`
    - `returncode`
    - `stdout`
    - `stderr`
    - `total_ms`

### Evaluations

- `GET /api/v1/evals`
  - returns stored eval runs

- `POST /api/v1/evals/run`
  - body:
    - `mode`
  - runs local harness

- `GET /api/v1/evals/{run_id}`
  - returns stored eval detail

### Settings and demo mode

- `GET /api/v1/settings`
  - returns runtime summary and mode definitions

- `POST /api/v1/demo/seed`
  - loads the reproducible demo dataset from `examples/demo-memories.json`

## Explain contract notes

`search.explain` now includes:

- `mode`
- `normalized_query`
- `expanded_query`
- `keywords`
- `filters`
- `strategy`
- `timings_ms`
- `dense_hits`
- `sparse_hits`
- `final`

This is the main contract used by Query Studio and Explain Center.
