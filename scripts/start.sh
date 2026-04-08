#!/usr/bin/env bash
set -euo pipefail

cd /home/saganski/workspace/experiments/cortexos
docker compose up -d qdrant searxng
if ! systemctl list-unit-files | grep -q '^cortexos-api.service'; then
  scripts/install_systemd.sh
fi
sudo systemctl restart cortexos-api.service
sudo systemctl --no-pager --full status cortexos-api.service | sed -n '1,20p'
