CONTEXT: Sprint 2.22 - Track B: CI/CD Pipeline
PROJECT: Oh My Coins - Autonomous Trading Platform
ROLE: The Feature Developer

WORKSPACE ANCHOR:
  ROOT_PATH: ../sprint-2.22/track-b
  INSTANCE_PORT: 3001
  STRICT_SCOPE: You are locked to this directory. Focus on `.github/workflows` and `scripts/deploy.sh`.

OBJECTIVES:
  1. Refine `build-push.sh` and `deploy.sh` for reliability.
  2. Implement GitHub Action `deploy-staging.yml`.
  3. Ensure zero-downtime deployment Config (Rolling Update).

DELIVERABLES:
  - `.github/workflows/deploy-staging.yml`
  - Verified `scripts/deploy.sh`

CRITICAL INSTRUCTION:
TESTING MUST OCCUR IN CONTAINERS.
DO NOT RUN TESTS ON THE HOST MACHINE.
Use: `docker compose run backend pytest`
To prevent port conflicts, your `docker-compose.override.yml` MUST expose port 3001:3000 (frontend) or similar if running services.
