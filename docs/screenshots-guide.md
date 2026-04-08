# Screenshots Guide

## Recommended flow

1. Ensure services are up.
2. Seed demo mode.
3. Open the UI locally.
4. Capture the pages below in a desktop browser window.

## Commands

```bash
cd /home/saganski/workspace/experiments/cortexos
./.venv/bin/python scripts/seed_demo.py
cd ui && pnpm build && cd ..
```

If the API service is already serving the built UI:

- open `http://127.0.0.1:8011/`

For isolated validation without touching the running systemd unit:

```bash
cd /home/saganski/workspace/experiments/cortexos
./.venv/bin/python -m uvicorn app.api.main:app --host 127.0.0.1 --port 8012
```

- open `http://127.0.0.1:8012/`

## Screens to capture

- Dashboard
- Memory Explorer with detail panel open
- Timeline
- Query Studio with one executed query
- Explain Center with one executed explain run
- Conflict Center with side-by-side comparison
- Ingestion Center preview state
- Operations Center
- Evals page after one run

## Suggested demo queries

- `What is the current launch date?`
- `Where is the customer support hub?`
- `How should I react if the local model is slow?`
- `rotate atlas_alpha`
