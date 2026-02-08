# Deployment Status

This document tracks the deployment state of the Oh My Coins platform across all environments.

**Last Updated:** 2026-02-14

---

## 🌍 Environment Overview

| Environment | Status | URL | Database | Last Deployment |
|------------|---------|-----|----------|-----------------|
| **Local Dev** | ✅ Operational | http://localhost:8000 | PostgreSQL 17 (Docker) | N/A - Local |
| **Local Server** | ✅ Operational | http://192.168.0.241:8090 | PostgreSQL 17 (Docker) | Automated (GitHub Actions) |
| **AWS Staging** | 📦 Archived | N/A | RDS PostgreSQL | Deprecated |
| **AWS Prod** | ❌ Cancelled | N/A | N/A | Pivot to On-Prem |

---

## 📊 Environment Details

### Local Server (192.168.0.241)

**Status:** ✅ Operational

**Infrastructure:**
- **Host:** Linux Server (Ubuntu/Debian) @ 192.168.0.241
- **Ingress:** Traefik v3.6 (Docker)
- **Orchestration:** Docker Compose
- **CI/CD:** GitHub Actions (Self-Hosted Runner)
- **Network:** Local LAN (Port 8090 for HTTP)

**Components:**
- **Reverse Proxy:** Traefik (Ports 80/8080/8090)
- **Backend:** FastAPI (Replicas: 2)
- **Frontend:** Nginx serving React/Vite build
- **Database:** PostgreSQL 17 (Volume: `omc-db-data`)
- **Cache:** Redis 7

**Configuration:**
- **Secrets:** `.env` file manually persisted at `~/omc/ohmycoins/.env`
- **Routing:** PathPrefix `/api` -> Backend, PathPrefix `/docs` -> Backend, Default -> Frontend
- **Logs:** `docker compose logs -f`

### Local Development Environment

**Status:** ✅ Fully Operational

**Infrastructure:**
- **Backend:** FastAPI running on http://localhost:8000
- **Frontend:** React + Vite running on http://localhost:5173
- **Database:** PostgreSQL 17 running in Docker container
- **Cache:** Redis 7 running in Docker container
- **Orchestration:** Docker Compose

---

## 🔧 Deployment Procedures

### Local Server Deployment (Automated)

The Local Server (192.168.0.241) uses a Self-Hosted GitHub Actions runner.

1.  **Trigger:** Usage of `git push origin main` triggers the `deploy-local.yml` workflow.
2.  **Process:**
    *   Runner checks out code.
    *   Runner copies `~/omc/ohmycoins/.env` to workspace.
    *   Runner builds new Docker images.
    *   Runner executes `docker compose up -d` (zero-downtime rolling update not guaranteed, but downtime is minimal).
    *   Runner prunes old images.

### Local Server Setup (Manual / First Time)

1.  **SSH into Server:**
    ```bash
    ssh mark@192.168.0.241
    ```
2.  **Prepare Secrets:**
    Ensure `~/omc/ohmycoins/.env` exists and has correct production values.
3.  **Ensure Runner is Active:**
    Check status of the GitHub Actions runner service.

### Local Development Setup

1.  **Clone Repository:**
    ```bash
    git clone https://github.com/MarkLimmage/ohmycoins.git
    cd ohmycoins
    ```
2.  **Configure Environment:**
    ```bash
    cp .env.template .env
    # Edit .env and set required variables
    ```
3.  **Start Services:**
    ```bash
    docker compose up -d
    ```

---

## 📦 Archived Cloud Infrastructure (AWS)

*Note: As of Feb 2026, the project has pivoted to on-prem deployment. The AWS infrastructure code (Terraform) is retained in `infrastructure/terraform` for reference but is not active.*

### Staging (Legacy)
- **Platform:** AWS ECS Fargate
- **Database:** RDS PostgreSQL
- **Secrets:** AWS Secrets Manager
- **Status:** **Decommissioned**

---

## 🔗 Related Documentation

- [Architecture Overview](./ARCHITECTURE.md)
- [Secrets Management](./SECRETS_MANAGEMENT.md)
