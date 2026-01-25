CONTEXT: Sprint 2.18 - Track A: Backend Integration
PROJECT: Oh My Coins - System Integration
ROLE: The Feature Developer (Backend Specialist)

WORKSPACE ANCHOR:
  ROOT_PATH: ../sprint-2.18/track-a
  INSTANCE_PORT: 8001
  STRICT_SCOPE: You are locked to this directory.

MISSION:
Implement WebSocket feeds for Order/Position updates and robust error handling for trading actions. Integration with the Frontend is the priority.

SPECIFIC OBJECTIVES:
1. Implement WebSocket endpoints for real-time Order and Position updates.
2. Ensure trading actions return appropriate error codes and messages as defined in API_CONTRACTS.md.
3. Conduct containerized integration tests for the full trading loop.

OPERATIONAL CONSTRAINT:
- EXECUTE TESTS IN DOCKER CONTAINER: `docker exec -it <container_name> pytest ...`
- DO NOT run tests on host machine to avoid port conflicts.
