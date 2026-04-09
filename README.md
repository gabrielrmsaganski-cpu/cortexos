# CortexOS

[![Release](https://img.shields.io/github/v/release/gabrielrmsaganski-cpu/cortexos?display_name=tag)](https://github.com/gabrielrmsaganski-cpu/cortexos/releases/tag/v0.1.0)
[![Release Date](https://img.shields.io/github/release-date/gabrielrmsaganski-cpu/cortexos)](https://github.com/gabrielrmsaganski-cpu/cortexos/releases/tag/v0.1.0)
[![CI](https://img.shields.io/github/actions/workflow/status/gabrielrmsaganski-cpu/cortexos/ci.yml?branch=main&label=ci)](https://github.com/gabrielrmsaganski-cpu/cortexos/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/gabrielrmsaganski-cpu/cortexos)](LICENSE)
[![Intro Video](https://img.shields.io/badge/intro-video_1080p-0b57d0?logo=github)](https://github.com/gabrielrmsaganski-cpu/cortexos/releases/download/v0.1.0/CortexOS-Intro-1080p.mp4)

## CortexOS - Explainable Memory OS for AI Agents

CortexOS is a local-first memory operating system for AI agents that need more
than vector retrieval. It combines verbatim memory, temporal reasoning,
conflict-aware lifecycle handling, hybrid retrieval, reranking, and explainable
answer synthesis in one inspectable system.

## Why CortexOS

Most agent memory layers end at embedding search. CortexOS is built for teams
that need to understand what was stored, why it was retrieved, which memories
conflict, and how a final answer was assembled.

Core properties:

- temporal memory with validity windows
- explicit conflict and supersession tracking
- explainable retrieval and scoring
- local-first operation with graceful degradation
- product UI for inspection, operations, and demos

## Product Surface

- Query Studio
- Explain Center
- Conflict Center
- Memory Timeline
- Dashboard
- Ingestion Center
- Operations Center
- Evaluations
- Demo Mode

## Key Features

- Verbatim-first canonical memory store
- Wing and room contextual organization
- Episodic, factual, procedural, and reference memory types
- Dense and sparse hybrid retrieval with reranking
- Temporal relevance and lifecycle-aware scoring
- Conflict and supersession detection on ingestion
- Deterministic fallback when the local model is unavailable
- Explain mode with candidate, rerank, penalty, and synthesis visibility
- REST API, CLI, MCP server, and local product UI

## Architecture Overview

- Storage: SQLite
- Retrieval index: Qdrant
- Embeddings: BGE-M3
- Reranking: BGE reranker
- Backend: FastAPI
- Frontend: React + Vite + Tailwind
- Local model support: Ollama

CortexOS keeps verbatim memory as the source of truth, enriches it with
lifecycle metadata and explicit relations, retrieves through a hybrid pipeline,
reranks candidates, and returns a synthesized answer instead of raw chunks.

## Quickstart

```bash
cd /home/saganski/workspace/experiments/cortexos
cp .env.example .env
./scripts/setup.sh
./scripts/start.sh
./scripts/demo_mode.sh
```

Then open:

- `http://127.0.0.1:8011`

## Watch the Intro

[![Watch the CortexOS intro](screenshots/cortexos-intro-cover.png)](https://github.com/gabrielrmsaganski-cpu/cortexos/releases/download/v0.1.0/CortexOS-Intro-1080p.mp4)

Short GitHub-friendly product intro:

- `13.76s`
- `1080p`
- release asset: `CortexOS-Intro-1080p.mp4`

## Presentation Asset

![CortexOS social preview](screenshots/cortexos-social-preview.png)

## Screenshots

Generate screenshots from the running local instance:

```bash
cd /home/saganski/workspace/experiments/cortexos
./.venv/bin/python scripts/generate_screenshots.py
```

Expected outputs:

- `screenshots/cortexos-intro-cover.png`
- `screenshots/cortexos-social-preview.png`
- `screenshots/dashboard.png`
- `screenshots/query.png`
- `screenshots/explain.png`
- `screenshots/conflict.png`

## Local-First Operation

- Default model: `qwen3:8b`
- Optional quality model: `qwen3:14b`
- Optional code model: `qwen3-coder-next:q4_K_M`

Retrieval, reranking, and deterministic synthesis continue to work when the
local LLM is slow or unavailable.

## Documentation

- [Server Inspection](docs/inspection.md)
- [Architecture](docs/architecture.md)
- [Technical Decisions](docs/decisions.md)
- [Verification](docs/verification.md)
- [Product Inspection](docs/product-inspection.md)
- [Product Spec](docs/product-spec.md)
- [Frontend Architecture](docs/frontend-architecture.md)
- [Frontend API Contract](docs/frontend-api-contract.md)
- [Demo Mode](docs/demo-mode.md)
- [Operations UI](docs/operations-ui.md)
- [Screenshots Guide](docs/screenshots-guide.md)
- [Release Plan](docs/release-plan.md)

## Community

- [Contributing Guide](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security Policy](SECURITY.md)
- [Support](SUPPORT.md)
- [Discussions](https://github.com/gabrielrmsaganski-cpu/cortexos/discussions)

## Honest Limitations

- CPU-only local inference can introduce noticeable latency in deeper modes
- The local-first setup prioritizes transparency and control over hosted
  convenience
- External publication is not enabled by default
- Hybrid retrieval can still return semantically weak candidates when the corpus
  does not contain strong evidence for the query

## Roadmap

- Knowledge graph layer
- Richer memory learning signals
- Streaming answer UX
- External deployment profile
- Deeper evaluation scenarios
- Better multilingual retrieval tuning

## Author

Crafted by Gabriel Saganski

- GitHub: https://github.com/gabrielrmsaganski-cpu
- LinkedIn: https://linkedin.com/in/gabriel-saganski-252323346

## License

MIT License © 2026 Gabriel Saganski
