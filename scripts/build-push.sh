#! /usr/bin/env sh

# Exit in case of error
set -e

echo "Building images with TAG=${TAG}..."

TAG=${TAG?Variable not set} \
FRONTEND_ENV=${FRONTEND_ENV-production} \
sh ./scripts/build.sh

echo "Pushing images..."
docker compose -f docker-compose.yml push

echo "Build and push completed."
