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

echo "Building ${FULL_IMAGE}:latest ..."
docker build -t "${FULL_IMAGE}:latest" .

echo "Pushing ${FULL_IMAGE}:latest ..."
docker push "${FULL_IMAGE}:latest"

echo "Done. Pull with:"
echo "  docker pull ${FULL_IMAGE}:latest"
