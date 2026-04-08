#!/usr/bin/env bash
set -euo pipefail

base_url="${1:-http://127.0.0.1:8011}"

curl -fsS "$base_url/" | grep -q "<div id=\"root\"></div>"
curl -fsS "$base_url/api/v1/dashboard" >/dev/null
curl -fsS "$base_url/api/v1/settings" >/dev/null

echo "UI smoke test passed for $base_url"
