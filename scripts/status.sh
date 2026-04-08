#!/usr/bin/env bash
set -euo pipefail

cd /home/saganski/workspace/experiments/cortexos
echo "== systemd =="
sudo systemctl --no-pager --full status cortexos-api.service | sed -n '1,20p'
echo
echo "== containers =="
docker compose ps
echo
echo "== health =="
curl -fsS http://127.0.0.1:8011/healthz || true
