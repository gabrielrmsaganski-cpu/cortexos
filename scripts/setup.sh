#!/usr/bin/env bash
set -euo pipefail

cd /home/saganski/workspace/experiments/cortexos

if [[ ! -f .env ]]; then
  cp .env.example .env
fi

if /home/saganski/.local/bin/uv sync --extra dev --extra web --extra ml; then
  echo "Installed dev, web, and ML extras."
else
  echo "Full dependency set failed; retrying with dev and web extras only."
  /home/saganski/.local/bin/uv sync --extra dev --extra web
fi

/home/saganski/.local/bin/uv run python -c "from app.core.database import init_database; init_database()"

cd ui
pnpm install
pnpm build
