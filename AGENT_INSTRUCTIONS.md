CONTEXT: Sprint 2.22 - Track A: Infrastructure Validation
PROJECT: Oh My Coins - Autonomous Trading Platform
ROLE: The DevOps Agent

WORKSPACE ANCHOR:
  ROOT_PATH: ../sprint-2.22/track-a
  INSTANCE_PORT: 8001
  STRICT_SCOPE: You are locked to this directory. Focus on `infrastructure/terraform` and `docs/DEPLOYMENT_STATUS.md`.

OBJECTIVES:
  1. Audit `infrastructure/terraform` modules for Staging configuration.
  2. Create a "Dry Run" report for `terraform plan`.
  3. Validate AWS Secrets Manager integration for Staging.
  4. Update `docs/DEPLOYMENT_STATUS.md` with real-time status.

DELIVERABLES:
  - Validated Terraform configuration.
  - Successful `terraform plan` output log.
  - Updated Deployment Status doc.

CRITICAL INSTRUCTION:
TESTING MUST OCCUR IN CONTAINERS.
DO NOT RUN TESTS ON THE HOST MACHINE.
Use: `docker compose run backend pytest`
To prevent port conflicts, your `docker-compose.override.yml` MUST expose port 8001:80 (or similar) if running services.
