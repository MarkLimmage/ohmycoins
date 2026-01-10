# Archived GitHub Actions Workflows

This directory contains workflows that are no longer active but are preserved for historical reference.

## Archived Files

### deploy-to-eks.yml.archived
- **Date Archived:** 2026-01-09
- **Reason:** Platform transition from EKS to ECS Fargate
- **Replaced By:** `deploy-aws.yml` (Terraform-based ECS deployment)
- **Notes:** The project migrated from Kubernetes/EKS to ECS Fargate for better cost optimization and simplified operations. All production workloads now run on ECS.

## Active Deployment Workflows

For current deployment procedures, see:
- `deploy-aws.yml` - Terraform-based infrastructure deployment (ECS)
- `build-push-ecr.yml` - Docker image builds and ECR pushes
- `deploy-staging.yml` - Staging environment deployment
- `deploy-production.yml` - Production environment deployment

## Documentation

For infrastructure documentation, see:
- `/infrastructure/terraform/DEPLOYMENT_GUIDE_TERRAFORM_ECS.md`
- `/docs/DEPLOYMENT_STATUS.md`
