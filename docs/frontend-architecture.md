# Frontend Architecture

## Stack

Chosen stack:

- React
- Vite
- TypeScript
- Tailwind CSS
- Recharts
- TanStack Query

## Why Vite instead of Next.js

This project already has a Python backend and an established local-first deployment path. A static SPA is the lowest-friction way to add a product UI without introducing another production server process or duplicating API responsibilities.

Vite was chosen because:

- build is fast and reproducible on this server
- dev server is optional and local-only
- production build can be served by FastAPI on the existing API service
- there is no need for Node server-side rendering here

## Runtime topology

Production:

- FastAPI serves:
  - `/api/v1/*`
  - `/healthz`
  - frontend static assets from `ui/dist`

Local dev:

- frontend dev server can run on `127.0.0.1:8012`
- backend remains on `127.0.0.1:8011`

## UI structure

Frontend workspace:

- `ui/src/components`
- `ui/src/lib`
- `ui/src/pages`

Main route groups:

- `/`
- `/explorer`
- `/timeline`
- `/query`
- `/explain`
- `/conflicts`
- `/ingestion`
- `/operations`
- `/evals`
- `/settings`

## Data flow

- browser UI reads the product API from FastAPI
- mutations call the same backend and then invalidate query caches
- no direct browser access to SQLite or Qdrant exists
- dashboard and ops views consume aggregated backend endpoints instead of rebuilding metrics client-side

## Safety posture

- UI stays local-only by default
- archive and reindex actions are explicit mutations
- no destructive delete action is exposed
- optional integrations remain opt-in and visibly optional
