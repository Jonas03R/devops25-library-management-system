#!/usr/bin/env bash
set -euo pipefail

HEALTH_URL="${1:-http://127.0.0.1:8000/health}"
CATALOG_URL="${2:-${HEALTH_URL%/health}/api/books}"
HEALTH_READY=0

echo "Verifying $HEALTH_URL"
for attempt in {1..10}; do
  if curl --fail --silent "$HEALTH_URL" >/dev/null; then
    HEALTH_READY=1
    break
  fi
  echo "Waiting for application ($attempt/10)..."
  sleep 2
done

if [[ "$HEALTH_READY" -ne 1 ]]; then
  echo "Health check failed: $HEALTH_URL" >&2
  exit 1
fi

health_response=$(curl --fail --silent --show-error "$HEALTH_URL")
printf '%s' "$health_response" | python -c '
import json
import sys

if json.load(sys.stdin).get("status") != "ok":
    raise SystemExit("Health check returned an unexpected response")
'
echo "Health check OK"

echo "Verifying $CATALOG_URL"
catalog_response=$(curl --fail --silent --show-error "$CATALOG_URL")
printf '%s' "$catalog_response" | python -c '
import json
import sys

if not isinstance(json.load(sys.stdin), list):
    raise SystemExit("Book catalogue did not return a JSON list")
'
echo "Book catalogue OK"
