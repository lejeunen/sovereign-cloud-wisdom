#!/usr/bin/env bash
set -euo pipefail

PROVIDER="${1:-scaleway}"
IMAGE_NAME="sovereign-cloud-wisdom"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_DIR/.env.$PROVIDER"

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: $ENV_FILE not found. Copy .env.$PROVIDER.example and fill in your credentials." >&2
    exit 1
fi

# shellcheck source=/dev/null
source "$ENV_FILE"

if [ -z "${REGISTRY:-}" ]; then
    echo "Error: REGISTRY is not set in $ENV_FILE" >&2
    exit 1
fi

if [ -z "${REGISTRY_LOGIN_CMD:-}" ]; then
    echo "Error: REGISTRY_LOGIN_CMD is not set in $ENV_FILE" >&2
    exit 1
fi

COMMIT_SHA=$(git -C "$PROJECT_DIR" rev-parse --short HEAD)
TAG="$(date -u +%Y%m%d%H%M%S)-${COMMIT_SHA}"
FULL_IMAGE="$REGISTRY/$IMAGE_NAME"

echo "==> Logging in to $REGISTRY"
eval "$REGISTRY_LOGIN_CMD"

echo "==> Building and pushing multi-platform image"
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -t "$FULL_IMAGE:$TAG" \
    -t "$FULL_IMAGE:latest" \
    --push \
    "$PROJECT_DIR"

echo "==> Done"
