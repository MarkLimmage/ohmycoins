#! /usr/bin/env sh

# Exit in case of error
set -e

echo "Deploying stack ${STACK_NAME}..."

# Create the network if it doesn't exist (idempotent-ish check)
ssh mark@192.168.0.241 "docker network create --driver=overlay --attachable traefik-public || true"

DOMAIN=${DOMAIN?Variable not set} \
STACK_NAME=${STACK_NAME?Variable not set} \
TAG=${TAG?Variable not set} \
docker compose \
-f docker-compose.yml \
config > docker-stack.yml

# docker-auto-labels docker-stack.yml

docker stack deploy -c docker-stack.yml --with-registry-auth "${STACK_NAME?Variable not set}"

echo "Deployment initiated."
