#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="${1:-revenue-leak-detector}"

echo "[docker] Building image: ${IMAGE_NAME}"
if docker build -t "${IMAGE_NAME}" .; then
  echo "[docker] Build complete using docker build."
  exit 0
fi

echo "[docker] docker build failed; trying buildx with --load..."
docker buildx build --load -t "${IMAGE_NAME}" .
echo "[docker] Build complete using buildx --load."
