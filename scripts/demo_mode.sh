#!/usr/bin/env bash
set -euo pipefail

cd /home/saganski/workspace/experiments/cortexos

./.venv/bin/python scripts/seed_demo.py
cd ui
pnpm build
