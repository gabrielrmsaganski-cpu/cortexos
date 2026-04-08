# Product Specification

## Product position

CortexOS should present as a serious open source memory platform for agents:

- strong engine
- transparent retrieval
- explicit lifecycle handling
- useful human interface
- honest local-first operations

The product should not hide the engine. It should make the engine inspectable.

## Experience model

The application is a local-only product UI served on top of the existing backend. It should support three audiences:

- developers evaluating the architecture
- operators managing the local runtime
- users demonstrating memory ingestion, retrieval, lifecycle, and explainability

## Product areas

### 1. Dashboard

Objective:

- give a system-level overview in under one minute

Data needed:

- total memory count
- counts by type
- counts by status
- top wings and rooms
- recent memory activity
- service health
- recent query/eval activity
- storage sizes

Endpoints needed:

- dashboard stats
- operations status
- recent activity

Empty state:

- no memories yet
- quick action to load demo mode or add first memory

Errors:

- partial service degradation should be shown per card, not as a blank page

User actions:

- open explorer
- add memory
- run smoke test
- run demo seed
- jump into query studio

### 2. Memory Explorer

Objective:

- browse and inspect canonical memories safely

Data needed:

- paginated list
- filters
- search text
- computed access and quality signals
- per-memory detail
- related links
- chunks
- version neighbors

Endpoints needed:

- memory list
- memory detail
- memory compare
- memory archive
- memory reindex

Empty state:

- no memories match current filters

Errors:

- failed fetch should preserve current filters and show retry

User actions:

- filter
- sort
- open detail
- compare two memories
- archive memory
- reindex memory

### 3. Memory Timeline

Objective:

- show how memory evolves over time

Data needed:

- created events
- conflict events
- supersession events
- filter slices by wing, room, type, status

Endpoints needed:

- timeline series
- timeline events

Empty state:

- no events in selected range

Errors:

- if timeline data fails, keep filters and show fallback text

User actions:

- zoom range
- filter dimensions
- click event to open memory detail

### 4. Query Studio

Objective:

- run questions interactively and inspect the pipeline

Data needed:

- query
- selected mode: `fast`, `balanced`, `deep`
- filters
- raw retrieval
- reranked results
- final synthesis
- latency by stage
- fallback and conflict signals

Endpoints needed:

- query studio execution
- explain detail

Empty state:

- suggest example queries and demo dataset prompts

Errors:

- retrieval can still render even if synthesis fails

User actions:

- run search
- run answer
- toggle explain
- switch modes
- inspect result memory

### 5. Explain Center

Objective:

- make the retrieval and ranking path visually understandable

Data needed:

- original query
- normalized query
- mode and strategy
- filters
- dense candidates
- sparse candidates
- merged candidates
- rerank outputs
- penalties and boosts
- final context pack
- synthesis output
- fallback state

Endpoints needed:

- explain detail
- query studio execution

Empty state:

- explanation requires a query run

Errors:

- if some stage data is missing, the UI should mark it unavailable rather than pretending

User actions:

- expand stages
- compare candidates
- inspect supporting memory

### 6. Conflict Center

Objective:

- inspect conflicts and supersessions as first-class product entities

Data needed:

- conflicting memories
- superseded memories
- grouped relation edges
- precedence signals
- related timestamps

Endpoints needed:

- conflicts list
- supersessions list
- memory detail
- compare endpoint

Empty state:

- no conflicts detected

Errors:

- relation fetch failure should still allow list inspection

User actions:

- compare side-by-side
- archive
- reindex
- jump to timeline

### 7. Ingestion Center

Objective:

- provide a strong, safe ingestion UX

Data needed:

- preview classification
- chunk preview
- duplicate/conflict/supersession preview
- final save result

Endpoints needed:

- manual preview
- document preview
- webpage preview
- site preview
- existing save endpoints

Empty state:

- forms with examples

Errors:

- parser errors should explain whether extraction or save failed

User actions:

- preview
- save
- upload file
- ingest webpage
- ingest site

### 8. Operations Center

Objective:

- make local operation easier without exposing dangerous controls by default

Data needed:

- service health
- ports
- storage sizes
- recent logs summary
- smoke test result
- current synthesis settings
- available models

Endpoints needed:

- operations status
- smoke test runner
- logs summary
- settings info

Empty state:

- not applicable, but cards should degrade gracefully

Errors:

- if a subsystem cannot be probed, surface `unavailable`

User actions:

- run smoke test
- refresh status
- inspect logs summary

### 9. Evaluations / Benchmarks

Objective:

- show honest local eval runs, not benchmark theater

Data needed:

- eval harness runs
- pass/fail per case
- timings
- mode, LLM usage, fallback usage

Endpoints needed:

- eval run
- eval history
- eval detail

Empty state:

- no evals yet, run baseline harness

Errors:

- failed eval should still be recorded with stderr

User actions:

- run eval
- compare recent runs
- inspect cases

### 10. Settings / Modes

Objective:

- expose runtime modes and defaults clearly

Data needed:

- current config summary
- mode definitions
- llm enabled flag
- default model names

Endpoints needed:

- settings summary

Empty state:

- not applicable

Errors:

- missing optional config values should show as unavailable

User actions:

- copy example env
- understand fast/balanced/deep tradeoffs

## Mode definitions

### Fast

- prioritize lower latency
- no LLM synthesis on the critical path
- use search + deterministic synthesis
- limit result set and UI detail

### Balanced

- default product mode
- use full hybrid retrieval + rerank
- allow LLM synthesis if enabled
- explain with normal detail

### Deep

- maximize inspectability
- full explain detail
- larger candidate set
- synthesis allowed
- intended for demos and debugging, not lowest latency

## UX constraints

- preserve local-only default
- preserve current API compatibility
- no destructive admin actions without explicit user intent
- show honest degraded states
- avoid fake metrics like cache hit rate when the system does not have a cache

## Operational constraints

- production topology should remain one API service plus existing containers
- frontend should build to static files and be served by the API service
- no new externally exposed port is required for production use

## Deliverables implied by this spec

- React frontend
- extended product API
- demo dataset and seed path
- eval history storage
- README and docs suitable for GitHub
