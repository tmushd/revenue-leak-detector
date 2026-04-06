#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="${1:-revenue-leak-detector}"
HOST_PORT="${PORT:-8501}"
RUN_PIPELINE_ON_START="${RUN_PIPELINE_ON_START:-true}"

if ! docker image inspect "${IMAGE_NAME}" >/dev/null 2>&1; then
  echo "[docker] Image '${IMAGE_NAME}' not found locally. Build it first:"
  echo "  bash docker/build-image.sh ${IMAGE_NAME}"
  exit 1
fi

echo "[docker] Running app on http://localhost:${HOST_PORT} (RUN_PIPELINE_ON_START=${RUN_PIPELINE_ON_START})"
docker run --rm \
  -p "${HOST_PORT}:8501" \
  -e "RUN_PIPELINE_ON_START=${RUN_PIPELINE_ON_START}" \
  "${IMAGE_NAME}"
