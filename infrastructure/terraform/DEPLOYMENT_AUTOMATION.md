# ECS Deployment Automation Guide

This document describes the automated deployment system for Oh My Coins on AWS ECS.

## Overview

The deployment system consists of three layers:

1. **GitHub Actions Workflows** - Automated CI/CD pipelines
2. **Shell Scripts** - Local deployment tools
3. **Terraform** - Infrastructure as Code

## Deployment Methods

### Method 1: GitHub Actions (Recommended for Production)

Automated deployment triggered by code changes or manual workflow dispatch.

**Workflows:**
- `build-push-ecr.yml` - Builds and pushes Docker images to ECR with security scanning
- `deploy-aws.yml` - Deploys infrastructure and application to AWS

**Trigger Deployment:**
1. Push to `main` branch (automatic)
2. Manual dispatch from GitHub Actions tab

**Manual Deployment:**
```bash
# Go to GitHub repository → Actions tab
# Select "Deploy to AWS" workflow
# Click "Run workflow"
# Choose:
#   - Environment: staging or production
#   - Terraform action: plan, apply, or destroy
```

### Method 2: One-Command Script (Recommended for Staging)

Fast deployment for development and staging environments.

**Prerequisites:**
- AWS CLI configured
- Docker installed and running
- Git repository

**Usage:**
```bash
# Deploy to staging
cd infrastructure/terraform/scripts
./deploy-ecs.sh staging

# Deploy to production
./deploy-ecs.sh production
```

**What it does:**
1. Validates prerequisites (AWS CLI, Docker, credentials)
2. Builds Docker images for backend and frontend
3. Pushes images to Amazon ECR
4. Updates ECS services with new images
5. Waits for services to stabilize (5-10 minutes)
6. Shows deployment summary and status

**Output:**
```
=========================================
  Oh My Coins - ECS Deployment
  Environment: staging
=========================================

[1/5] Validating prerequisites...
✓ AWS CLI found
✓ Docker found
✓ AWS credentials valid
✓ Docker daemon running

[2/5] Building and pushing Docker images...
✓ Backend image pushed
✓ Frontend image pushed

[3/5] Getting ECS cluster information...
  Cluster: ohmycoins-staging-cluster
  Backend Service: ohmycoins-staging-backend-service
  Frontend Service: ohmycoins-staging-frontend-service

[4/5] Updating ECS services...
✓ Backend service update initiated
✓ Frontend service update initiated

[5/5] Waiting for services to stabilize...
✓ Backend service stable
✓ Frontend service stable

=========================================
  Deployment Complete!
=========================================
```

### Method 3: Manual Steps

For fine-grained control or troubleshooting.

**1. Build and Push Images:**
```bash
# Login to ECR
aws ecr get-login-password --region ap-southeast-2 | \
    docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.ap-southeast-2.amazonaws.com

# Build and push backend
docker build -t ACCOUNT_ID.dkr.ecr.ap-southeast-2.amazonaws.com/omc-backend:latest ./backend
docker push ACCOUNT_ID.dkr.ecr.ap-southeast-2.amazonaws.com/omc-backend:latest

# Build and push frontend
docker build -t ACCOUNT_ID.dkr.ecr.ap-southeast-2.amazonaws.com/omc-frontend:latest ./frontend
docker push ACCOUNT_ID.dkr.ecr.ap-southeast-2.amazonaws.com/omc-frontend:latest
```

**2. Update ECS Services:**
```bash
# Update backend
aws ecs update-service \
    --cluster ohmycoins-staging-cluster \
    --service ohmycoins-staging-backend-service \
    --force-new-deployment \
    --region ap-southeast-2

# Update frontend
aws ecs update-service \
    --cluster ohmycoins-staging-cluster \
    --service ohmycoins-staging-frontend-service \
    --force-new-deployment \
    --region ap-southeast-2
```

**3. Wait for Stability:**
```bash
aws ecs wait services-stable \
    --cluster ohmycoins-staging-cluster \
    --services ohmycoins-staging-backend-service ohmycoins-staging-frontend-service \
    --region ap-southeast-2
```

## Deployment Gates and Checks

### Pre-Deployment Checks

Run before any deployment:
```bash
cd infrastructure/terraform/scripts
./pre-deployment-check.sh staging
```

Validates:
- AWS CLI and Terraform installed
- AWS credentials configured
- ECR repositories exist
- ECS cluster and services exist
- RDS and Redis available
- Secrets configured

### Security Scanning

All images are scanned with Trivy before deployment:
- **Critical vulnerabilities:** Build fails
- **High vulnerabilities:** Reported in GitHub Security
- **Medium/Low vulnerabilities:** Logged for review

### Deployment Stability

Deployment waits for:
- All tasks to reach RUNNING state
- Health checks to pass
- Old tasks to drain and stop
- Timeout: 10 minutes (configurable)

If stability check fails:
- Old tasks remain running (automatic rollback)
- Deployment is marked as failed
- Manual investigation required

## Rollback Procedures

### Automatic Rollback

If new tasks fail health checks, ECS automatically:
1. Stops launching new tasks
2. Keeps old tasks running
3. Marks deployment as failed

### Manual Rollback

**Option 1: Redeploy Previous Image**
```bash
# Get previous image tag
aws ecr describe-images \
    --repository-name omc-backend \
    --query 'sort_by(imageDetails,& imagePushedAt)[-2].imageTags[0]' \
    --output text

# Update task definition with previous image
# Then force new deployment
aws ecs update-service \
    --cluster ohmycoins-staging-cluster \
    --service ohmycoins-staging-backend-service \
    --force-new-deployment
```

**Option 2: Revert Task Definition**
```bash
# List task definition revisions
aws ecs list-task-definitions \
    --family-prefix ohmycoins-staging-backend

# Update service to use previous revision
aws ecs update-service \
    --cluster ohmycoins-staging-cluster \
    --service ohmycoins-staging-backend-service \
    --task-definition ohmycoins-staging-backend:PREVIOUS_REVISION
```

**Option 3: Circuit Breaker (Automatic)**

ECS Circuit Breaker is enabled on all services:
- Automatically rolls back failed deployments
- Threshold: 3 consecutive failures
- Configured in `modules/ecs/main.tf`

## Health Check Validation

### Application Health Endpoints

**Backend:**
```bash
# Health check endpoint
curl https://api.staging.ohmycoins.com/health

# Expected response:
{"status": "healthy", "database": "connected", "redis": "connected"}
```

**Frontend:**
```bash
# Frontend should load
curl https://app.staging.ohmycoins.com

# Expected: HTTP 200 with HTML content
```

### ECS Service Health

```bash
# Get service status
aws ecs describe-services \
    --cluster ohmycoins-staging-cluster \
    --services ohmycoins-staging-backend-service \
    --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount,Deployments:deployments[0].status}'

# Expected output:
{
    "Status": "ACTIVE",
    "Running": 2,
    "Desired": 2,
    "Deployments": "PRIMARY"
}
```

### ALB Target Health

```bash
# Get target group ARN
TARGET_GROUP_ARN=$(aws elbv2 describe-target-groups \
    --names ohmycoins-staging-backend-tg \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text)

# Check target health
aws elbv2 describe-target-health \
    --target-group-arn $TARGET_GROUP_ARN \
    --query 'TargetHealthDescriptions[*].{Target:Target.Id,Health:TargetHealth.State}'

# Expected: All targets "healthy"
```

## Monitoring Deployment

### View Deployment Progress

```bash
# Watch service events
aws ecs describe-services \
    --cluster ohmycoins-staging-cluster \
    --services ohmycoins-staging-backend-service \
    --query 'services[0].events[0:10]' \
    --output table
```

### View Application Logs

```bash
# Backend logs
aws logs tail /ecs/ohmycoins-staging/backend --follow

# Frontend logs
aws logs tail /ecs/ohmycoins-staging/frontend --follow

# Filter errors only
aws logs tail /ecs/ohmycoins-staging/backend --follow --filter-pattern "ERROR"
```

### View Running Tasks

```bash
# List running tasks
aws ecs list-tasks \
    --cluster ohmycoins-staging-cluster \
    --service-name ohmycoins-staging-backend-service

# Describe specific task
aws ecs describe-tasks \
    --cluster ohmycoins-staging-cluster \
    --tasks TASK_ARN
```

## Troubleshooting

### Deployment Stuck

**Symptom:** Service update never completes

**Possible causes:**
1. New tasks failing health checks
2. Insufficient resources (CPU/memory)
3. Image pull errors
4. Container startup failures

**Investigation:**
```bash
# Check task status
aws ecs describe-tasks --cluster CLUSTER --tasks TASK_ARN

# Check logs for the failing task
aws logs tail /ecs/ohmycoins-staging/backend --follow

# Check stopped tasks
aws ecs list-tasks --cluster CLUSTER --desired-status STOPPED
```

### Image Pull Errors

**Symptom:** Tasks fail with "CannotPullContainerError"

**Solutions:**
1. Verify ECR repository exists
2. Check IAM permissions for task execution role
3. Verify image tag exists in ECR
4. Check ECR login credentials

### Health Check Failures

**Symptom:** Tasks start but fail health checks

**Investigation:**
1. Check application logs for startup errors
2. Verify database connectivity
3. Check Redis connectivity
4. Verify secrets are injected correctly
5. Test health endpoint locally

### Out of Memory (OOM) Errors

**Symptom:** Tasks stopped with exit code 137

**Solutions:**
1. Increase task memory in `modules/ecs/variables.tf`
2. Check for memory leaks in application
3. Review memory usage in CloudWatch Container Insights

## Performance Optimization

### Build Optimization

**Use Docker BuildKit:**
```bash
export DOCKER_BUILDKIT=1
docker build --cache-from=REGISTRY/image:latest -t REGISTRY/image:new .
```

**Multi-stage builds:**
- Already implemented in Dockerfiles
- Reduces image size
- Faster deployments

### Deployment Speed

**Parallel deployments:**
- Backend and frontend deploy simultaneously
- Use `--no-wait` flag for multiple services

**Image caching:**
- GitHub Actions uses layer caching
- Local builds pull from ECR cache

## Security Considerations

### Secrets Management

- Secrets stored in AWS Secrets Manager
- Injected at runtime via ECS task definition
- Never committed to code or logs

### IAM Permissions

- Principle of least privilege
- Task execution role: Pull images, write logs, read secrets
- Task role: Application-specific AWS API access

### Network Security

- Tasks run in private subnets
- No direct internet access (NAT gateway required)
- Security groups restrict traffic
- ALB terminates SSL/TLS

## Cost Optimization

### Staging Environment

- Single NAT Gateway
- Single AZ deployment
- Smaller task sizes (512 CPU, 1GB memory)
- No Performance Insights
- Shorter log retention (7 days)

### Production Environment

- Multi-AZ deployment
- Larger task sizes for performance
- Performance Insights enabled
- Longer log retention (30 days)
- CloudWatch Container Insights

## Next Steps

After deployment:

1. **Verify Application:**
   - Access frontend URL
   - Test API endpoints
   - Check database migrations
   - Verify agent functionality

2. **Monitor Metrics:**
   - Review CloudWatch dashboards
   - Check for errors in logs
   - Monitor resource utilization

3. **Update Documentation:**
   - Document any issues encountered
   - Update runbook with solutions
   - Share knowledge with team

## Additional Resources

- [AWS ECS Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/)
- [ECS Deployment Types](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-types.html)
- [ECS Service Quotas](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-quotas.html)
- [Operations Runbook](OPERATIONS_RUNBOOK.md) - Detailed operational procedures
