#!/bin/bash
set -euo pipefail

REGISTRY="us-central1-docker.pkg.dev"
PROJECT="lunch-cppnow"
REPO="lunch"
IMAGE="app"
FULL_IMAGE="${REGISTRY}/${PROJECT}/${REPO}/${IMAGE}"

# Ensure Docker is configured to authenticate to Artifact Registry.
# This is a no-op if already configured.
echo "Configuring Docker for Artifact Registry..."
gcloud auth configure-docker "${REGISTRY}" --quiet

# Build a multi-platform image and push it directly to the registry.
# --push is required for multi-platform builds (buildx can't load a
# multi-arch image into the local daemon, only into a registry).
# Docker Desktop's default builder supports linux/amd64 + linux/arm64
# via QEMU emulation with no extra setup needed.
echo "Building ${FULL_IMAGE}:latest for linux/amd64 and linux/arm64..."
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag "${FULL_IMAGE}:latest" \
  --push \
  .

echo "Done. Pull with:"
echo "  docker pull ${FULL_IMAGE}:latest"
