# Contributing to CortexOS

Thanks for considering a contribution.

CortexOS is opinionated software. The goal is not to accept every possible
feature, but to keep the project technically coherent, inspectable, and useful
for serious agent-memory work.

## What Helps Most

High-value contributions usually fall into one of these buckets:

- retrieval quality improvements with clear before/after evidence
- explainability and observability improvements
- better evaluations and reproducible demos
- UI improvements that increase clarity without hiding system behavior
- docs that reduce setup or operations ambiguity
- bug fixes with focused tests

## Before Opening a Pull Request

1. Read the README and the docs under `docs/`.
2. Check open issues and discussions for overlap.
3. Keep the scope narrow and the reasoning explicit.
4. Prefer incremental changes over large unreviewable rewrites.

## Local Setup

### Backend

```bash
cd /home/saganski/workspace/experiments/cortexos
cp .env.example .env
/home/saganski/.local/bin/uv sync --extra dev
```

If you also need ingestion integrations:

```bash
/home/saganski/.local/bin/uv sync --extra dev --extra web
```

### Frontend

```bash
cd /home/saganski/workspace/experiments/cortexos/ui
pnpm install
```

## Run the Quality Checks

### Python

```bash
cd /home/saganski/workspace/experiments/cortexos
./.venv/bin/ruff check app tests
./.venv/bin/pytest -q
```

### Frontend

```bash
cd /home/saganski/workspace/experiments/cortexos/ui
pnpm build
```

## Pull Request Expectations

- explain the problem being solved
- explain the chosen approach and tradeoffs
- include tests when behavior changes
- update docs when the UX, API, or operations model changes
- avoid unrelated refactors in the same PR

## Engineering Bar

Contributions are much more likely to be accepted when they:

- preserve explainability
- preserve local-first operation
- do not hide failure modes
- do not add hype-driven complexity
- degrade gracefully when optional components are unavailable

## Areas That Need Extra Care

- retrieval scoring
- lifecycle transitions
- conflict and supersession logic
- API contracts used by the UI
- operations scripts and service management

## If You Are Unsure

Open a GitHub Discussion or issue first with:

- the problem statement
- why the current design is insufficient
- the concrete change you propose
- how you would validate it
