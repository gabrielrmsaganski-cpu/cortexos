#!/usr/bin/env bash
set -euo pipefail

cd /home/saganski/workspace/experiments/cortexos
sudo systemctl stop cortexos-api.service || true
docker compose stop qdrant searxng || true
