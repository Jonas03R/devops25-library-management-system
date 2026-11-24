#!/usr/bin/env bash
set -euo pipefail

IMAGE="library-management:local"
CONTAINER="library-management-demo"
ROLLBACK_IMAGE="library-management:previous"

docker info >/dev/null
docker build -t "$IMAGE" .

if docker ps -a --format '{{.Names}}' | grep -Fxq "$CONTAINER"; then
  PREVIOUS_IMAGE=$(docker inspect --format '{{.Image}}' "$CONTAINER")
  docker image tag "$PREVIOUS_IMAGE" "$ROLLBACK_IMAGE"
  docker rm --force "$CONTAINER"
fi

docker run -d --name "$CONTAINER" -p 8000:8000 "$IMAGE"
