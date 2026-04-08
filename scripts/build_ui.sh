#!/usr/bin/env bash
set -euo pipefail

cd /home/saganski/workspace/experiments/cortexos/ui
pnpm install
pnpm build
