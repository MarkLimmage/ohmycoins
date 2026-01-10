# Historical Documentation Notice

## EKS References in This Directory

Several documentation files in this directory contain references to **AWS EKS (Elastic Kubernetes Service)**. These references are **historical** and no longer applicable to the current infrastructure.

### Platform Transition

**Previous Architecture:** AWS EKS (Kubernetes)
**Current Architecture:** AWS ECS Fargate (Containers)
**Transition Date:** Phase 9 (Completed before January 2026)

### Why We Moved from EKS to ECS

1. **Cost Optimization:** ECS Fargate has lower operational costs for our workload size
2. **Operational Simplicity:** ECS requires less Kubernetes expertise and maintenance
3. **Better Fit:** Our application architecture doesn't require Kubernetes-specific features
4. **Faster Deployment:** ECS deployments are simpler and faster for small teams

### Current Infrastructure

All active infrastructure is defined in the **terraform modules** under `modules/`:

- ✅ **modules/vpc/** - VPC, subnets, NAT gateway
- ✅ **modules/security/** - Security groups for ALB, ECS, RDS, Redis  
- ✅ **modules/iam/** - IAM roles and policies for ECS tasks
- ✅ **modules/alb/** - Application Load Balancer
- ✅ **modules/ecs/** - ECS Fargate cluster, services, task definitions
- ✅ **modules/rds/** - RDS PostgreSQL managed database
- ✅ **modules/redis/** - ElastiCache Redis managed cache

### Files Containing Historical EKS References

The following documentation files contain EKS references but should be read for **context only**, not implementation:

- `DEPLOYMENT_GUIDE_WEEK5-6.md` - Week 5-6 sprint used EKS runners for testing
- `INTEGRATION_READINESS_CHECKLIST.md` - References EKS cluster that was used for CI/CD
- `DEVELOPER_C_WEEK5-6_SUMMARY.md` - Historical sprint summary
- `DEVELOPER_C_INDEX.md` - Historical planning document
- `AWS_DEPLOYMENT_REQUIREMENTS.md` - Mixed EKS/ECS references

### Active Documentation

For **current** deployment and infrastructure information, refer to:

1. **Infrastructure:**
   - `DEPLOYMENT_GUIDE_TERRAFORM_ECS.md` - Current ECS deployment guide
   - `OPERATIONS_RUNBOOK.md` - Operations procedures
   - `TROUBLESHOOTING.md` - Common issues and solutions
   - `README.md` - Terraform module overview

2. **Application:**
   - `/docs/DEPLOYMENT_STATUS.md` - Current deployment state
   - `/docs/SECRETS_MANAGEMENT.md` - Secrets management guide
   - `/docs/ARCHITECTURE.md` - System architecture overview

3. **Archived Workflows:**
   - `/.github/workflows/archive/deploy-to-eks.yml.archived` - Old EKS deployment workflow
   - `/.github/workflows/archive/README.md` - Workflow archive explanation

### Active GitHub Actions Workflows

Current CI/CD uses these workflows:

- ✅ `deploy-aws.yml` - Terraform-based ECS infrastructure deployment
- ✅ `build-push-ecr.yml` - Docker image builds and ECR pushes
- ✅ `deploy-staging.yml` - Staging environment deployment
- ✅ `deploy-production.yml` - Production environment deployment

---

## FAQ

**Q: Should I set up an EKS cluster?**  
A: No. All current deployments use ECS Fargate. EKS references are historical.

**Q: Why wasn't the EKS documentation deleted?**  
A: It provides valuable context about the project's evolution and decision-making process. It may also contain useful patterns or lessons learned.

**Q: Can I safely ignore EKS references?**  
A: Yes. Focus on the ECS-based terraform modules and documentation marked as "current" or "active".

**Q: What if I need Kubernetes-specific features?**  
A: Consult with the team before considering a move back to EKS. The current ECS architecture was chosen deliberately for this project's requirements.

---

**For Questions:** Contact the DevOps team or refer to `/docs/DEPLOYMENT_STATUS.md` for current infrastructure details.

**Last Updated:** 2026-01-09
