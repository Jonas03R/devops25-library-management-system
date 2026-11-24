#!/usr/bin/env bash
set -euo pipefail

IMAGE="${1:-library-management:previous}"
EXPECTED_VERSION="${2:-}"
CONTAINER="library-management-demo"

docker info >/dev/null
docker image inspect "$IMAGE" >/dev/null

if docker ps -a --format '{{.Names}}' | grep -Fxq "$CONTAINER"; then
  docker rm --force "$CONTAINER"
fi

docker run -d --name "$CONTAINER" -p 8000:8000 "$IMAGE"

if ! bash scripts/verify.sh; then
  docker logs "$CONTAINER"
  exit 1
fi

ACTUAL_IMAGE=$(docker inspect --format '{{.Config.Image}}' "$CONTAINER")
if [[ "$ACTUAL_IMAGE" != "$IMAGE" ]]; then
  echo "Rollback image mismatch: expected $IMAGE, got $ACTUAL_IMAGE" >&2
  exit 1
fi

if [[ -n "$EXPECTED_VERSION" ]]; then
  version_response=$(curl --fail --silent --show-error http://127.0.0.1:8000/version)
  printf '%s' "$version_response" | python -c '
import json
import sys

data = json.load(sys.stdin)
expected = sys.argv[1]
actual = data.get("version")
if actual != expected:
    raise SystemExit("Expected version " + expected + ", got " + str(actual))
' "$EXPECTED_VERSION"
fi

echo "Rollback completed: $ACTUAL_IMAGE"
