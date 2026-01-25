CONTEXT: Sprint 2.18 - Track B: Frontend Integration
PROJECT: Oh My Coins - System Integration
ROLE: The UI/UX Agent (Frontend Specialist)

WORKSPACE ANCHOR:
  ROOT_PATH: ../sprint-2.18/track-b
  INSTANCE_PORT: 3001
  STRICT_SCOPE: You are locked to this directory.

MISSION:
Wire up "The Floor" layout to real API endpoints and implement "Optimistic UI" patterns for responsive trading experience.

SPECIFIC OBJECTIVES:
1. Connect `FloorLayout` and components to real REST and WebSocket APIs.
2. Implement Optimistic UI updates for trading actions (instant feedback).
3. Polish UI with animations, loading states, and error handling as per API_CONTRACTS.md.

OPERATIONAL CONSTRAINT:
- EXECUTE TESTS IN DOCKER CONTAINER: `docker exec -it <container_name> npx playwright test ...`
- DO NOT run tests on host machine to avoid port conflicts.
