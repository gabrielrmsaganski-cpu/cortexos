#!/usr/bin/env bash
set -euo pipefail

base_url="http://127.0.0.1:8011"

curl -fsS "$base_url/healthz"
echo
curl -fsS -X POST "$base_url/api/v1/memories" \
  -H 'content-type: application/json' \
  -d '{"text":"The launch moved to 2026-05-20.","wing":"smoke","room":"launch","source":"smoke"}'
echo
curl -fsS -X POST "$base_url/api/v1/search" \
  -H 'content-type: application/json' \
  -d '{"query":"current launch date","wing":"smoke","room":"launch","explain":true}'
echo
curl -fsS -X POST "$base_url/api/v1/answer" \
  -H 'content-type: application/json' \
  -d '{"query":"What is the current launch date?","wing":"smoke","room":"launch"}'
echo
