CONTEXT: Sprint 2.22 - Track C: Access Control
PROJECT: Oh My Coins - Autonomous Trading Platform
ROLE: The Feature Developer

WORKSPACE ANCHOR:
  ROOT_PATH: ../sprint-2.22/track-c
  INSTANCE_PORT: 8002
  STRICT_SCOPE: You are locked to this directory. Focus on `backend/app/core/security.py` and `middleware`.

OBJECTIVES:
  1. Implement a Middleware or Dependency to check User Email against a Whitelist.
  2. Define the Whitelist format (Env Var or DB Table).
  3. Ensure "Access Denied" page is shown to non-whitelisted users.

DELIVERABLES:
  - `WhitelistMiddleware` or Dependency.
  - Tests ensuring unauthorized users are blocked.

CRITICAL INSTRUCTION:
TESTING MUST OCCUR IN CONTAINERS.
DO NOT RUN TESTS ON THE HOST MACHINE.
Use: `docker compose run backend pytest`
To prevent port conflicts, your `docker-compose.override.yml` MUST expose port 8002:80 (backend) or similar if running services.
