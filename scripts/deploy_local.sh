#!/usr/bin/env bash
set -euo pipefail

IMAGE="library-management:local"
CONTAINER="library-management-demo"

docker info >/dev/null
docker build -t "$IMAGE" .

if docker ps -a --format '{{.Names}}' | grep -Fxq "$CONTAINER"; then
  docker rm --force "$CONTAINER"
fi

docker run -d --name "$CONTAINER" -p 8000:8000 "$IMAGE"
