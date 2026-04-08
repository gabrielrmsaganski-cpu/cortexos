# Server Inspection

Inspection date: 2026-04-08 UTC

## Host

- Hostname: `saganskiai`
- OS: Ubuntu 24.04.4 LTS
- Kernel: `6.17.0-1010-azure`
- Virtualization: Microsoft Hyper-V

## Compute

- CPU: 4 vCPUs
- RAM: 31 GiB total, about 21 GiB available during inspection
- Swap: none configured
- Root disk: 247 GiB total, 197 GiB available

## Available tooling

- `python3`: 3.12.3
- `pip`: 24.0
- `uv`: installed during bootstrap at `/home/saganski/.local/bin/uv`
- `node`: v24.14.1
- `npm`: 11.11.0
- `pnpm`: 10.33.0
- `git`: 2.43.0
- `tmux`: 3.4
- `nginx`: 1.24.0
- `systemd`: running
- `docker`: 28.2.2
- `docker compose`: v5.1.1
- `ollama`: 0.20.2

Not present before bootstrap:

- `uv`
- `qdrant` system package

## Existing local models in Ollama before this project

- `aion:latest`
- `qwen2.5:3b`
- `qwen2.5:7b`
- `nous-hermes:latest`

## Ports already in use during inspection

- `22`, `80`, `443`
- `3000`, `3001`, `3002`, `3003`, `3105`
- `5000`, `5001`, `5002`
- `5432`, `6379`
- `8000`, `8080`, `8088`, `9000`, `9090`
- `11434` for Ollama

Verified free at inspection time:

- `6333`, `6334`
- `8011`, `8012`, `8013`
- `8787`
- `8999`

## Existing services and workloads

Enabled system services of note:

- `nginx.service`
- `docker.service`
- `ollama.service`
- `redis-server.service`
- `autonomous-ai-api.service`
- `autonomous-ai-voice.service`
- `dorkhunter.service`

Running Docker containers of note:

- `aletis-postgres`
- `open-webui`
- `portainer`

Existing reverse proxy config already routes several path-based apps through `/etc/nginx/sites-available/saganskiai`.

## Existing projects checked to avoid collisions

- `/home/saganski/workspace/agents/saganski-ia`
- `/home/saganski/workspace/agents/iq-trading`
- `/opt/autonomous-ai`
- `/home/saganski/ai-core/memory` existed as a directory but had no project files

## Installation decision

Chosen project root:

- `/home/saganski/workspace/experiments/cortexos`

Rationale:

- isolated from active production projects
- writable by current user
- consistent with existing workspace layout
- easy to back up without mixing unrelated code

Chosen service layout:

- FastAPI app on host via systemd on `127.0.0.1:8011`
- Qdrant in Docker on `127.0.0.1:6333`
- Qdrant gRPC on `127.0.0.1:6334`
- SearXNG in Docker on `127.0.0.1:8787`

This avoids collision with current workloads while keeping the stack local-only by default.
