#!/usr/bin/env bash
set -euo pipefail

sudo cp /home/saganski/workspace/experiments/cortexos/ops/systemd/cortexos-api.service /etc/systemd/system/cortexos-api.service
sudo systemctl daemon-reload
sudo systemctl enable cortexos-api.service
