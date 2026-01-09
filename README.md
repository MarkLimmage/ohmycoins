# Oh My Coins (OMC)

**An Autonomous Agentic Trading Platform**

## Overview
Oh My Coins is a microservices-based algorithmic trading platform that integrates high-fidelity data collection (The 4 Ledgers) with an autonomous multi-agent data science capability (The Lab). It is designed to discover, validate, and execute trading strategies without human intervention, while maintaining strict "Lab-to-Floor" integrity.

## Documentation
The documentation has been consolidated to provide a Single Source of Truth:

*   **[System Requirements](/docs/SYSTEM_REQUIREMENTS.md)**: Comprehensive EARS-compliant requirements for Data Collection and Agentic AI.
*   **[Architecture](/docs/ARCHITECTURE.md)**: High-level system design, microservices breakdown, and infrastructure stack.
*   **[Project Handoff](/docs/PROJECT_HANDOFF.md)**: Current status of parallel development tracks and next steps.
*   **[Roadmap](/ROADMAP.md)**: Active project timeline and progress tracking.

> **Note**: Historical planning documents and decision records have been archived in `/docs/archive/`.

## Quick Start

### 1. Prerequisites
*   Docker & Docker Compose
*   Python 3.11+
*   Node.js 18+
*   Terraform 1.5+

### 2. Development Environment
```bash
# Clone the repository
git clone https://github.com/your-org/ohmycoins.git
cd ohmycoins

# Start core services (PostgreSQL, Redis)
docker-compose up -d

# Install backend dependencies
cd backend
uv sync

# Install frontend dependencies
cd ../frontend
npm install
```

## System Structure
*   **`backend/`**: FastAPI services (Collectors, Agents, Trading Engine).
*   **`frontend/`**: React/Vite admin dashboard.
*   **`infrastructure/`**: Terraform modules for AWS deployment (EKS, RDS).
*   **`docs/`**: Centralized documentation.

## License
Proprietary & Confidential.
