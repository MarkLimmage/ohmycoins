# Oh My Coins (OMC)

**An Autonomous Agentic Trading Platform**

## Overview
Oh My Coins is a microservices-based algorithmic trading platform that integrates high-fidelity data collection (The 4 Ledgers) with an autonomous multi-agent data science capability (The Lab). It is designed to discover, validate, and execute trading strategies without human intervention, while maintaining strict "Lab-to-Floor" integrity.

## Documentation
The documentation has been consolidated to provide a Single Source of Truth:

### Core Documentation
*   **[System Requirements](/docs/SYSTEM_REQUIREMENTS.md)**: Comprehensive EARS-compliant requirements for Data Collection and Agentic AI.
*   **[Architecture](/docs/ARCHITECTURE.md)**: High-level system design, microservices breakdown, and infrastructure stack.
*   **[Project Handoff](/docs/PROJECT_HANDOFF.md)**: Current status of parallel development tracks and next steps.
*   **[Roadmap](/ROADMAP.md)**: Active project timeline and progress tracking.

### Operations & Deployment
*   **[Deployment Status](/docs/DEPLOYMENT_STATUS.md)**: Current state of local/staging/production environments
*   **[Secrets Management](/docs/SECRETS_MANAGEMENT.md)**: Guide to managing secrets across environments
*   **[Terraform Infrastructure](/infrastructure/terraform/README.md)**: AWS ECS infrastructure documentation

> **Note**: Historical planning documents and decision records have been archived in `/docs/archive/`.

## Quick Start

### 1. Prerequisites
*   Docker & Docker Compose
*   Python 3.11+
*   Node.js 18+
*   Terraform 1.5+

### 2. Configure Environment
```bash
# Clone the repository
git clone https://github.com/MarkLimmage/ohmycoins.git
cd ohmycoins

# Copy environment template and configure secrets
cp .env.template .env
# Edit .env and set required variables (see .env.template for details)
# Required: SECRET_KEY, POSTGRES_PASSWORD, OPENAI_API_KEY, FIRST_SUPERUSER_PASSWORD
```

**Important:** See [Secrets Management Guide](/docs/SECRETS_MANAGEMENT.md) for detailed setup instructions.

### 3. Start Development Environment
```bash
# Start all services (PostgreSQL, Redis, Backend, Frontend)
docker compose up -d

# View logs
docker compose logs -f

# Access the application
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Frontend: http://localhost:5173
```

### 4. Run Tests
```bash
# Run backend tests
cd backend
pytest

# Run tests with markers
pytest -m "not integration"  # Skip integration tests
pytest -m "not slow"         # Skip slow tests
```

## System Structure
*   **`backend/`**: FastAPI services (Collectors, Agents, Trading Engine).
*   **`frontend/`**: React/Vite admin dashboard.
*   **`infrastructure/`**: Terraform modules for AWS ECS deployment.
*   **`docs/`**: Centralized documentation.
*   **`.env.template`**: Environment variable template (copy to `.env` for local development).
*   **`backend/pytest.ini`**: Test configuration with markers.

## Development

### Testing
The project uses pytest with custom markers for test categorization:
- `integration`: Tests requiring external services (database, Redis, APIs)
- `slow`: Long-running tests
- `requires_api`: Tests requiring API keys

See `backend/pytest.ini` for full configuration.

### Secrets Management
- **Local:** Secrets in `.env` file (not committed to git)
- **AWS:** Secrets in AWS Secrets Manager, injected by ECS

See [Secrets Management Guide](/docs/SECRETS_MANAGEMENT.md) for details.

### CI/CD Pipeline
- **Build:** GitHub Actions builds and pushes Docker images to ECR
- **Deploy:** Terraform manages infrastructure on AWS ECS Fargate
- **Monitoring:** CloudWatch logs and Container Insights

See [Deployment Status](/docs/DEPLOYMENT_STATUS.md) for current state.

## License
Proprietary & Confidential.
