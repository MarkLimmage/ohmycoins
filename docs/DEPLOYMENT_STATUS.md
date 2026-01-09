# Deployment Status

This document tracks the deployment state of the Oh My Coins platform across all environments.

**Last Updated:** 2026-01-09

---

## 🌍 Environment Overview

| Environment | Status | URL | Database | Last Deployment |
|------------|---------|-----|----------|-----------------|
| **Local** | ✅ Operational | http://localhost:8000 (backend)<br>http://localhost:5173 (frontend) | PostgreSQL 17 (Docker) | N/A - Local Dev |
| **Staging** | 🟡 Deployed | TBD - AWS ECS | RDS PostgreSQL | Pending Validation |
| **Production** | 🔴 Not Deployed | TBD | Not Configured | Pending Approval |

---

## 📊 Environment Details

### Local Development Environment

**Status:** ✅ Fully Operational

**Infrastructure:**
- **Backend:** FastAPI running on http://localhost:8000
- **Frontend:** React + Vite running on http://localhost:5173
- **Database:** PostgreSQL 17 running in Docker container
- **Cache:** Redis 7 running in Docker container
- **Orchestration:** Docker Compose

**Database Status:**
- All 12 migrations applied successfully
- Database seeding operational
- Health checks passing

**Test Status:**
- ✅ 579 tests passing
- ⚠️ Some integration tests require OPENAI_API_KEY configuration
- All containers healthy with proper health checks

**Configuration:**
- Secrets: Loaded from `.env` file
- API Keys: Configure in `.env` (see `.env.template`)
- Docker Compose: `docker-compose.yml` + `docker-compose.override.yml`

**Access:**
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:5173
- Database: localhost:5432

---

### Staging Environment

**Status:** 🟡 Deployed (Pending Validation)

**Infrastructure:**
- **Platform:** AWS ECS Fargate
- **Region:** ap-southeast-2 (Sydney)
- **Cluster:** ohmycoins-staging
- **Database:** RDS PostgreSQL (Managed)
- **Cache:** ElastiCache Redis (Managed)
- **Load Balancer:** Application Load Balancer (ALB)
- **Networking:** VPC with public/private subnets

**Terraform Modules:**
- ✅ VPC Module (networking, subnets, NAT gateway)
- ✅ Security Groups (ALB, ECS, RDS, Redis)
- ✅ IAM Roles (ECS task execution, task roles)
- ✅ RDS PostgreSQL (managed database)
- ✅ ElastiCache Redis (managed cache)
- ✅ Application Load Balancer
- ✅ ECS Cluster & Services
- ✅ AWS Secrets Manager integration

**Services:**
- Backend: ECS Fargate service (1 task, 512 CPU, 1024 MB memory)
- Frontend: ECS Fargate service (1 task, 256 CPU, 512 MB memory)

**Secrets Management:**
- AWS Secrets Manager: `ohmycoins-staging-app-secrets`
- Secrets automatically injected into ECS tasks
- Configuration includes: DB credentials, API keys, SMTP, JWT secret

**Monitoring:**
- CloudWatch Logs: 7-day retention
- Container Insights: Disabled (cost optimization)
- Health Checks: Configured on backend service

**CI/CD:**
- GitHub Actions workflows configured
- ECR repositories for Docker images
- Automated deployment on push to main branch

**Validation Checklist:**
- [ ] ECS services running and healthy
- [ ] Database migrations applied
- [ ] Backend health check responding
- [ ] Frontend accessible via ALB
- [ ] Secrets properly configured in Secrets Manager
- [ ] CloudWatch logs flowing
- [ ] Domain/DNS configured (if applicable)

**Access:**
- Backend API: TBD (ALB DNS name)
- API Docs: TBD (ALB DNS name)/docs
- Frontend: TBD (ALB DNS name)
- Database: Via RDS endpoint (private subnet only)

---

### Production Environment

**Status:** 🔴 Not Deployed

**Infrastructure:**
- **Platform:** AWS ECS Fargate (configured but not deployed)
- **Region:** ap-southeast-2 (Sydney)
- **Cluster:** Not created yet
- **Database:** Not configured
- **Cache:** Not configured

**Requirements:**
- [ ] Terraform configuration reviewed and approved
- [ ] Production secrets configured in AWS Secrets Manager
- [ ] Domain and SSL certificates configured
- [ ] Production database backup strategy defined
- [ ] Monitoring and alerting configured
- [ ] Load testing completed
- [ ] Security audit completed
- [ ] Deployment runbook created
- [ ] Rollback procedures documented
- [ ] Production approval from stakeholders

**Target Timeline:**
- Week 11-12 (pending Track A & B completion)

**Deployment Approval:**
- Requires sign-off from: Product Owner, Tech Lead, DevOps Lead
- Go/No-Go meeting scheduled: TBD

---

## 🔧 Deployment Procedures

### Local Development Setup

1. **Clone Repository:**
   ```bash
   git clone https://github.com/MarkLimmage/ohmycoins.git
   cd ohmycoins
   ```

2. **Configure Environment:**
   ```bash
   cp .env.template .env
   # Edit .env and set required variables
   # Minimum required: OPENAI_API_KEY, SECRET_KEY, POSTGRES_PASSWORD
   ```

3. **Start Services:**
   ```bash
   docker compose up -d
   ```

4. **Access Application:**
   - Backend: http://localhost:8000
   - Frontend: http://localhost:5173
   - API Docs: http://localhost:8000/docs

### Staging Deployment

**Prerequisites:**
- AWS credentials configured
- Terraform installed
- Required secrets available

**Deployment Steps:**

1. **Configure Secrets:**
   ```bash
   # Update secrets in AWS Secrets Manager
   aws secretsmanager put-secret-value \
     --secret-id ohmycoins-staging-app-secrets \
     --secret-string file://secrets.json
   ```

2. **Deploy Infrastructure:**
   ```bash
   cd infrastructure/terraform/environments/staging
   terraform init
   terraform plan
   terraform apply
   ```

3. **Build and Push Images:**
   ```bash
   # Triggered automatically by GitHub Actions on push to main
   # Or manually trigger workflow_dispatch
   ```

4. **Verify Deployment:**
   ```bash
   # Check ECS service status
   aws ecs describe-services \
     --cluster ohmycoins-staging \
     --services backend frontend
   
   # Check health endpoint
   curl https://<alb-dns>/api/v1/utils/health-check/
   ```

### Production Deployment

**Coming Soon** - Pending approval and completion of validation checklist.

---

## 📈 Monitoring & Health Checks

### Local Development
- Docker container health checks
- Manual monitoring via logs: `docker compose logs -f`

### Staging
- **CloudWatch Logs:**
  - Backend: `/ecs/ohmycoins-staging/backend`
  - Frontend: `/ecs/ohmycoins-staging/frontend`
- **Health Endpoints:**
  - Backend: `/api/v1/utils/health-check/`
- **ECS Service Status:**
  ```bash
  aws ecs describe-services \
    --cluster ohmycoins-staging \
    --services backend
  ```

### Production
- TBD - Will include CloudWatch dashboards, alarms, and PagerDuty integration

---

## 🚨 Troubleshooting

### Common Issues

**Issue: ECS tasks not starting**
- Check CloudWatch logs for error messages
- Verify secrets are configured in Secrets Manager
- Check security group rules allow traffic
- Verify task execution role has permissions

**Issue: Database connection failures**
- Verify RDS instance is available
- Check security group rules for database access
- Verify database credentials in Secrets Manager
- Check VPC subnet routing

**Issue: Health check failures**
- Check application logs in CloudWatch
- Verify backend is binding to correct port (8000)
- Check database connectivity from backend
- Verify health check endpoint implementation

**Issue: Missing OPENAI_API_KEY**
- For local: Set in `.env` file
- For staging/production: Configure in AWS Secrets Manager
- Verify secrets are being injected into ECS tasks

---

## 📝 Change Log

| Date | Environment | Change | Author |
|------|-------------|--------|--------|
| 2026-01-09 | Documentation | Initial DEPLOYMENT_STATUS.md created | Track C Developer |
| TBD | Staging | Initial deployment | TBD |
| TBD | Production | Production deployment | TBD |

---

## 🔗 Related Documentation

- [Architecture Overview](./ARCHITECTURE.md)
- [Terraform Deployment Guide](../infrastructure/terraform/DEPLOYMENT_GUIDE_TERRAFORM_ECS.md)
- [Operations Runbook](../infrastructure/terraform/OPERATIONS_RUNBOOK.md)
- [Troubleshooting Guide](../infrastructure/terraform/TROUBLESHOOTING.md)
- [Current Sprint Plan](../CURRENT_SPRINT.md)

---

**Note:** This document should be updated after each deployment or significant infrastructure change.
