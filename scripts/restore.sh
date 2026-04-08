#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <backup.tar.gz>" >&2
  exit 1
fi

cd /home/saganski/workspace/experiments/cortexos
scripts/stop.sh
tar -xzf "$1" -C /home/saganski/workspace/experiments/cortexos
scripts/start.sh
