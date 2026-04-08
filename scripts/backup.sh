#!/usr/bin/env bash
set -euo pipefail

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
target="/home/saganski/workspace/experiments/cortexos/data/backup-${timestamp}.tar.gz"

cd /home/saganski/workspace/experiments/cortexos
tar -czf "$target" data ops/qdrant/data docs
echo "$target"
