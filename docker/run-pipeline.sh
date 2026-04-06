#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="${1:-revenue-leak-detector}"

if ! docker image inspect "${IMAGE_NAME}" >/dev/null 2>&1; then
  echo "[docker] Image '${IMAGE_NAME}' not found locally. Build it first:"
  echo "  bash docker/build-image.sh ${IMAGE_NAME}"
  exit 1
fi

echo "[docker] Running pipeline only..."
docker run --rm "${IMAGE_NAME}" pipeline
