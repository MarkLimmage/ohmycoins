# Operational Runbook - Oh My Coins AWS Infrastructure

## Table of Contents
- [Overview](#overview)
- [Daily Operations](#daily-operations)
- [Deployment Procedures](#deployment-procedures)
- [Monitoring and Alerts](#monitoring-and-alerts)
- [Incident Response](#incident-response)
- [Troubleshooting](#troubleshooting)
- [Maintenance Windows](#maintenance-windows)
- [Emergency Contacts](#emergency-contacts)

---

## Overview

This runbook provides operational procedures for managing the Oh My Coins AWS infrastructure deployed via Terraform.

**Environments:**
- **Staging**: `ap-southeast-2` (Sydney)
- **Production**: `ap-southeast-2` (Sydney)

**Key Resources:**
- VPC with public/private subnets
- RDS PostgreSQL database
- ElastiCache Redis cluster
- ECS Fargate services (backend + frontend)
- Application Load Balancer
- CloudWatch monitoring and logging

---

## Daily Operations

### Morning Checks (5 minutes)

1. **Check System Health**
   ```bash
   # Check ECS service status
   aws ecs describe-services \
     --cluster ohmycoins-staging \
     --services backend frontend \
     --query 'services[*].[serviceName,status,runningCount,desiredCount]'
   
   # Check ALB target health
   aws elbv2 describe-target-health \
     --target-group-arn <target-group-arn>
   ```

2. **Review CloudWatch Alarms**
   ```bash
   # List alarms in ALARM state
   aws cloudwatch describe-alarms \
     --state-value ALARM \
     --query 'MetricAlarms[*].[AlarmName,StateReason]'
   ```

3. **Check Recent Errors**
   - Review CloudWatch Logs Insights for application errors
   - Check ECS task failures
   - Review ALB 5xx error rates

### Weekly Checks (30 minutes)

1. **Cost Review**
   - Check AWS Cost Explorer for unexpected spending
   - Review ECS Fargate usage patterns
   - Verify NAT Gateway data transfer costs

2. **Security Review**
   - Review CloudTrail logs for unusual activity
   - Check VPC Flow Logs for blocked connections
   - Verify security group rules are up to date

3. **Performance Review**
   - RDS Performance Insights for slow queries
   - Redis cache hit rates
   - ALB response times and latency

---

## Deployment Procedures

### Pre-Deployment Checklist

Before any deployment, complete this checklist to ensure readiness:

**Infrastructure Validation:**
- [ ] Run pre-deployment check script:
  ```bash
  cd infrastructure/terraform/scripts
  ./pre-deployment-check.sh staging  # or production
  ```
- [ ] Verify AWS credentials are valid and have necessary permissions
- [ ] Confirm Terraform state is not locked (no concurrent operations)
- [ ] Check ECR repositories exist and are accessible
- [ ] Verify ECS cluster and services are healthy

**Code & Build Validation:**
- [ ] All tests passing in CI/CD pipeline (>95% pass rate)
- [ ] Code reviewed and approved
- [ ] No critical security vulnerabilities in Docker images (Trivy scan)
- [ ] Database migrations tested in staging (if applicable)
- [ ] Environment variables and secrets configured correctly

**Backup & Recovery:**
- [ ] Recent database backup exists (within last 24 hours)
- [ ] Previous working Docker image tags documented
- [ ] Rollback procedure reviewed and understood
- [ ] Incident response team notified of deployment window

**Monitoring & Alerts:**
- [ ] CloudWatch dashboards accessible
- [ ] Alert channels (Slack/email) functioning
- [ ] On-call engineer identified and available
- [ ] Deployment monitoring dashboard prepared

**Communication:**
- [ ] Stakeholders notified of deployment (for production)
- [ ] Deployment change log prepared
- [ ] Expected downtime communicated (if any)
- [ ] Success criteria defined

**Production-Specific (Additional):**
- [ ] Deployment approved by tech lead
- [ ] Maintenance window scheduled (if needed)
- [ ] Customer-facing status page updated
- [ ] Rollback decision criteria defined

### Deployment Steps (Step-by-Step)

#### Method 1: One-Command Deployment (Recommended for Staging)

**Prerequisites:** AWS CLI configured, Docker running, Git repository cloned

**Steps:**
1. Navigate to scripts directory:
   ```bash
   cd infrastructure/terraform/scripts
   ```

2. Run deployment script:
   ```bash
   ./deploy-ecs.sh staging
   ```

3. Monitor output and verify each step completes:
   - ✓ Prerequisites validated
   - ✓ Docker images built and pushed
   - ✓ ECS services updated
   - ✓ Services stabilized

4. Proceed to "Health Check Validation" section below

**Expected Duration:** 10-15 minutes

#### Method 2: GitHub Actions Deployment (Recommended for Production)

**Via Automated Trigger:**

1. Push infrastructure changes to `main` branch:
   ```bash
   git checkout main
   git pull origin main
   git merge feature-branch
   git push origin main
   ```

2. Automatic workflow triggers:
   - Terraform plan is generated
   - Manual approval required for apply
   - Application deployment proceeds

3. Monitor workflow in GitHub Actions UI:
   - Go to repository → Actions tab
   - Select "Deploy to AWS" workflow
   - Watch progress of each job

**Via Manual Workflow Dispatch:**

1. Go to GitHub Actions → "Deploy to AWS"
2. Click "Run workflow"
3. Select environment (staging/production)
4. Select action (plan/apply/destroy)
5. Review plan output in workflow logs
6. For apply: Click "Review deployments" and approve
7. Monitor deployment progress

**Expected Duration:** 15-25 minutes (including approval wait time)

#### Method 3: Manual Step-by-Step (For Troubleshooting)

**Step 1: Build Docker Images**
```bash
# Set variables
export AWS_REGION=ap-southeast-2
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export ECR_REGISTRY=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
export IMAGE_TAG=$(git rev-parse --short HEAD)

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin $ECR_REGISTRY

# Build backend
docker build -t $ECR_REGISTRY/omc-backend:$IMAGE_TAG ./backend
docker tag $ECR_REGISTRY/omc-backend:$IMAGE_TAG $ECR_REGISTRY/omc-backend:latest

# Build frontend
docker build -t $ECR_REGISTRY/omc-frontend:$IMAGE_TAG ./frontend
docker tag $ECR_REGISTRY/omc-frontend:$IMAGE_TAG $ECR_REGISTRY/omc-frontend:latest
```

**Step 2: Push Images to ECR**
```bash
# Push backend
docker push $ECR_REGISTRY/omc-backend:$IMAGE_TAG
docker push $ECR_REGISTRY/omc-backend:latest

# Push frontend
docker push $ECR_REGISTRY/omc-frontend:$IMAGE_TAG
docker push $ECR_REGISTRY/omc-frontend:latest
```

**Step 3: Update ECS Services**
```bash
# Set environment-specific variables
export CLUSTER_NAME=ohmycoins-staging-cluster
export BACKEND_SERVICE=ohmycoins-staging-backend-service
export FRONTEND_SERVICE=ohmycoins-staging-frontend-service

# Update backend service
aws ecs update-service \
    --cluster $CLUSTER_NAME \
    --service $BACKEND_SERVICE \
    --force-new-deployment \
    --region $AWS_REGION

# Update frontend service
aws ecs update-service \
    --cluster $CLUSTER_NAME \
    --service $FRONTEND_SERVICE \
    --force-new-deployment \
    --region $AWS_REGION
```

**Step 4: Wait for Deployment Stability**
```bash
# Wait for backend (timeout: 10 minutes)
echo "Waiting for backend service to stabilize..."
aws ecs wait services-stable \
    --cluster $CLUSTER_NAME \
    --services $BACKEND_SERVICE \
    --region $AWS_REGION

# Wait for frontend (timeout: 10 minutes)
echo "Waiting for frontend service to stabilize..."
aws ecs wait services-stable \
    --cluster $CLUSTER_NAME \
    --services $FRONTEND_SERVICE \
    --region $AWS_REGION

echo "Deployment complete!"
```

**Step 5: Validate Deployment**
Proceed to "Health Check Validation" section below.

**Expected Duration:** 15-20 minutes

### Health Check Validation

After deployment completes, validate system health using these checks:

#### 1. ECS Service Health

**Check Service Status:**
```bash
aws ecs describe-services \
    --cluster ohmycoins-staging-cluster \
    --services ohmycoins-staging-backend-service ohmycoins-staging-frontend-service \
    --region ap-southeast-2 \
    --query 'services[*].{Service:serviceName,Status:status,Running:runningCount,Desired:desiredCount,Deployment:deployments[0].status}'
```

**Expected Output:**
```json
[
    {
        "Service": "ohmycoins-staging-backend-service",
        "Status": "ACTIVE",
        "Running": 2,
        "Desired": 2,
        "Deployment": "PRIMARY"
    },
    {
        "Service": "ohmycoins-staging-frontend-service",
        "Status": "ACTIVE",
        "Running": 2,
        "Desired": 2,
        "Deployment": "PRIMARY"
    }
]
```

**Success Criteria:**
- [ ] Status is "ACTIVE"
- [ ] Running count equals Desired count
- [ ] Only one deployment with status "PRIMARY"
- [ ] No stopped tasks with error codes

#### 2. Application Health Endpoints

**Backend API Health:**
```bash
# Get ALB DNS name
ALB_DNS=$(aws elbv2 describe-load-balancers \
    --names ohmycoins-staging-alb \
    --query 'LoadBalancers[0].DNSName' \
    --output text)

# Test health endpoint
curl -f https://$ALB_DNS/api/v1/health

# Or with detailed output
curl -s https://$ALB_DNS/api/v1/health | jq
```

**Expected Response:**
```json
{
    "status": "healthy",
    "database": "connected",
    "redis": "connected",
    "version": "1.0.0",
    "timestamp": "2026-01-10T02:30:00Z"
}
```

**Frontend Health:**
```bash
# Test frontend loads
curl -I https://$ALB_DNS/

# Expected: HTTP 200 OK
```

**Success Criteria:**
- [ ] Backend health endpoint returns 200 OK
- [ ] Database connection is "connected"
- [ ] Redis connection is "connected"
- [ ] Frontend returns 200 OK
- [ ] No 5xx errors in response

#### 3. ALB Target Health

**Check Target Group Health:**
```bash
# Get backend target group ARN
BACKEND_TG_ARN=$(aws elbv2 describe-target-groups \
    --names ohmycoins-staging-backend-tg \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text)

# Check target health
aws elbv2 describe-target-health \
    --target-group-arn $BACKEND_TG_ARN \
    --query 'TargetHealthDescriptions[*].{Target:Target.Id,Port:Target.Port,Health:TargetHealth.State,Reason:TargetHealth.Reason}'
```

**Expected Output:**
```json
[
    {
        "Target": "10.0.1.100",
        "Port": 8000,
        "Health": "healthy",
        "Reason": null
    }
]
```

**Success Criteria:**
- [ ] All targets show "healthy" state
- [ ] No targets in "unhealthy" or "draining" state
- [ ] Number of healthy targets matches desired count

#### 4. Database Connectivity

**Test Database Connection:**
```bash
# Execute command in ECS task
TASK_ARN=$(aws ecs list-tasks \
    --cluster ohmycoins-staging-cluster \
    --service-name ohmycoins-staging-backend-service \
    --query 'taskArns[0]' \
    --output text)

# Test database connection (if ECS Exec enabled)
aws ecs execute-command \
    --cluster ohmycoins-staging-cluster \
    --task $TASK_ARN \
    --container backend \
    --command "python -c 'import psycopg2; conn = psycopg2.connect(host=\"$DB_HOST\"); print(\"Connected\")'" \
    --interactive
```

**Or check from logs:**
```bash
aws logs tail /ecs/ohmycoins-staging/backend \
    --follow \
    --filter-pattern "database" \
    --region ap-southeast-2
```

**Success Criteria:**
- [ ] Database connection successful
- [ ] No connection timeout errors in logs
- [ ] Connection pool properly initialized

#### 5. Application Logs Review

**Check for Errors:**
```bash
# Recent errors in last 10 minutes
aws logs filter-log-events \
    --log-group-name /ecs/ohmycoins-staging/backend \
    --filter-pattern "ERROR" \
    --start-time $(date -u -d '10 minutes ago' +%s)000 \
    --region ap-southeast-2 \
    --query 'events[*].message' \
    --output text
```

**Success Criteria:**
- [ ] No critical errors in logs
- [ ] No startup failures
- [ ] No unexpected warnings
- [ ] Application logging correctly

#### 6. Performance Metrics

**Check Response Times:**
```bash
# Get average response time from ALB
aws cloudwatch get-metric-statistics \
    --namespace AWS/ApplicationELB \
    --metric-name TargetResponseTime \
    --dimensions Name=LoadBalancer,Value=app/ohmycoins-staging-alb/xxx \
    --start-time $(date -u -d '5 minutes ago' --iso-8601) \
    --end-time $(date -u --iso-8601) \
    --period 300 \
    --statistics Average \
    --region ap-southeast-2
```

**Success Criteria:**
- [ ] Average response time < 500ms
- [ ] No significant degradation from baseline
- [ ] CPU usage < 70%
- [ ] Memory usage < 80%

#### Health Check Summary

Create a deployment validation report:

```bash
echo "Deployment Validation Report - $(date)"
echo "========================================="
echo ""
echo "ECS Services:"
aws ecs describe-services --cluster ohmycoins-staging-cluster --services ohmycoins-staging-backend-service --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount}' --output table
echo ""
echo "ALB Target Health:"
aws elbv2 describe-target-health --target-group-arn $BACKEND_TG_ARN --query 'TargetHealthDescriptions[*].TargetHealth.State' --output table
echo ""
echo "Recent Errors (last 10 minutes):"
ERROR_COUNT=$(aws logs filter-log-events --log-group-name /ecs/ohmycoins-staging/backend --filter-pattern "ERROR" --start-time $(date -u -d '10 minutes ago' +%s)000 --region ap-southeast-2 --query 'length(events)' --output text)
echo "Error count: $ERROR_COUNT"
echo ""
echo "Deployment Status: $([ $ERROR_COUNT -eq 0 ] && echo 'SUCCESS ✓' || echo 'REVIEW REQUIRED ⚠')"
```

**Overall Success Criteria:**
- [ ] All ECS services active with desired count
- [ ] All health endpoints return 200 OK
- [ ] All ALB targets healthy
- [ ] No critical errors in logs
- [ ] Performance metrics within acceptable range
- [ ] Database and Redis connectivity confirmed

If all criteria are met: **Deployment validated successfully! ✓**

If any criteria fail: **Review logs and proceed to Rollback Procedure below**

### Rollback Procedures

#### When to Rollback

Initiate rollback if:
- Health checks fail after 10 minutes
- Error rate exceeds 5% of requests
- Critical functionality is broken
- Performance degradation exceeds 50%
- Database connectivity issues
- Security vulnerability discovered

#### Automatic Rollback (ECS Circuit Breaker)

ECS services have circuit breaker enabled (configured in Terraform):
- Automatically triggers on deployment failures
- Rolls back to previous task definition
- Threshold: 3 consecutive task failures
- No manual intervention required

**Verify Automatic Rollback:**
```bash
# Check deployment status
aws ecs describe-services \
    --cluster ohmycoins-staging-cluster \
    --service ohmycoins-staging-backend-service \
    --query 'services[0].deployments[*].{Status:status,TaskDef:taskDefinition,RolloutState:rolloutState}'
```

If circuit breaker triggered, you'll see:
- Previous task definition marked as PRIMARY
- Failed deployment in FAILED state
- RolloutState showing the circuit breaker activated

#### Manual Rollback - Method 1: Revert to Previous Image Tag

**Fastest rollback method (5 minutes):**

1. **Identify Previous Working Image:**
   ```bash
   # List recent images with timestamps
   aws ecr describe-images \
       --repository-name omc-backend \
       --region ap-southeast-2 \
       --query 'sort_by(imageDetails,& imagePushedAt)[-5:].[imageTags[0],imagePushedAt]' \
       --output table
   
   # Select the image tag before current deployment
   PREVIOUS_TAG="<previous-commit-sha>"
   ```

2. **Update Task Definition with Previous Image:**
   ```bash
   # Get current task definition
   CURRENT_TASK_DEF=$(aws ecs describe-services \
       --cluster ohmycoins-staging-cluster \
       --service ohmycoins-staging-backend-service \
       --query 'services[0].taskDefinition' \
       --output text)
   
   # Download task definition JSON
   aws ecs describe-task-definition \
       --task-definition $CURRENT_TASK_DEF \
       --query 'taskDefinition' > task-def.json
   
   # Edit task-def.json to update image tag to $PREVIOUS_TAG
   # Remove non-required fields: taskDefinitionArn, revision, status, requiresAttributes, compatibilities, registeredAt, registeredBy
   
   # Register new task definition
   NEW_TASK_DEF=$(aws ecs register-task-definition \
       --cli-input-json file://task-def.json \
       --query 'taskDefinition.taskDefinitionArn' \
       --output text)
   
   # Update service with new task definition
   aws ecs update-service \
       --cluster ohmycoins-staging-cluster \
       --service ohmycoins-staging-backend-service \
       --task-definition $NEW_TASK_DEF
   ```

3. **Wait for Rollback to Complete:**
   ```bash
   aws ecs wait services-stable \
       --cluster ohmycoins-staging-cluster \
       --services ohmycoins-staging-backend-service
   
   echo "Rollback complete!"
   ```

4. **Validate Rollback:**
   Follow "Health Check Validation" steps above

#### Manual Rollback - Method 2: Revert to Previous Task Definition Revision

**Use when previous task definition is known to be good:**

1. **List Recent Task Definitions:**
   ```bash
   aws ecs list-task-definitions \
       --family-prefix ohmycoins-staging-backend \
       --sort DESC \
       --max-items 5
   ```

2. **Update Service to Previous Revision:**
   ```bash
   # Use the revision number before current
   PREVIOUS_REVISION="ohmycoins-staging-backend:123"  # Replace with actual
   
   aws ecs update-service \
       --cluster ohmycoins-staging-cluster \
       --service ohmycoins-staging-backend-service \
       --task-definition $PREVIOUS_REVISION
   ```

3. **Repeat for Frontend if Needed:**
   ```bash
   aws ecs update-service \
       --cluster ohmycoins-staging-cluster \
       --service ohmycoins-staging-frontend-service \
       --task-definition ohmycoins-staging-frontend:PREVIOUS_REVISION
   ```

4. **Wait for Stability and Validate:**
   ```bash
   aws ecs wait services-stable \
       --cluster ohmycoins-staging-cluster \
       --services ohmycoins-staging-backend-service ohmycoins-staging-frontend-service
   ```

#### Manual Rollback - Method 3: Infrastructure Rollback (Terraform)

**Use for infrastructure changes that caused issues:**

1. **Identify Problem Commit:**
   ```bash
   cd infrastructure/terraform
   git log --oneline -5
   ```

2. **Revert Infrastructure Changes:**
   ```bash
   # Option A: Revert specific commit
   git revert <commit-hash>
   git push origin main
   
   # Option B: Reset to previous commit (use with caution)
   git checkout <previous-good-commit>
   ```

3. **Apply Terraform Changes:**
   ```bash
   cd environments/staging
   terraform init
   terraform plan -out=rollback.tfplan
   
   # Review plan carefully
   terraform show rollback.tfplan
   
   # Apply rollback
   terraform apply rollback.tfplan
   ```

4. **Monitor Rollback:**
   ```bash
   # Watch for infrastructure changes to complete
   watch -n 5 'aws ecs describe-services --cluster ohmycoins-staging-cluster --services ohmycoins-staging-backend-service --query "services[0].events[0:5]"'
   ```

#### Emergency Rollback Procedure (Critical Situation)

**When immediate action is required (< 2 minutes):**

1. **Stop New Task Launches:**
   ```bash
   # Set desired count to 0 for new deployment
   aws ecs update-service \
       --cluster ohmycoins-staging-cluster \
       --service ohmycoins-staging-backend-service \
       --desired-count 0
   
   # Wait 30 seconds for drain
   sleep 30
   ```

2. **Quickly Scale Back to Previous Tasks:**
   ```bash
   # Update to previous task definition and restore count
   aws ecs update-service \
       --cluster ohmycoins-staging-cluster \
       --service ohmycoins-staging-backend-service \
       --task-definition ohmycoins-staging-backend:PREVIOUS_REVISION \
       --desired-count 2
   ```

3. **Verify Services Recover:**
   ```bash
   # Quick health check
   curl -f https://$ALB_DNS/api/v1/health || echo "FAILED"
   ```

#### Post-Rollback Actions

After successful rollback:

1. **Document the Incident:**
   ```markdown
   ## Incident Report - [Date]
   
   **Deployment Time:** [timestamp]
   **Rollback Time:** [timestamp]
   **Root Cause:** [description]
   **Impact:** [affected services/users]
   **Resolution:** [rollback method used]
   **Action Items:**
   - [ ] Fix identified issue
   - [ ] Add test coverage
   - [ ] Update deployment checklist
   ```

2. **Notify Stakeholders:**
   - Inform team of rollback completion
   - Update status page (if production)
   - Send post-mortem invite

3. **Investigate Root Cause:**
   - Review logs and metrics
   - Identify what went wrong
   - Create tickets for fixes

4. **Update Runbook:**
   - Add new failure mode if not documented
   - Update rollback procedures if needed
   - Document lessons learned

5. **Plan Remediation:**
   - Fix the underlying issue
   - Add tests to prevent recurrence
   - Schedule redeployment when ready

#### Rollback Decision Tree

```
Deployment Failed?
│
├─ Health checks failing?
│  ├─ YES → Manual Rollback Method 1 (Previous Image)
│  └─ NO → Continue monitoring
│
├─ High error rate (>5%)?
│  ├─ YES → Check if circuit breaker triggered
│  │  ├─ Auto-rolled back → Validate and investigate
│  │  └─ Still failing → Manual Rollback Method 1
│  └─ NO → Continue monitoring
│
├─ Performance degraded (>50%)?
│  ├─ YES → Check resource utilization
│  │  ├─ OOM/CPU → Scale up or rollback
│  │  └─ Code issue → Manual Rollback Method 1
│  └─ NO → Continue monitoring
│
└─ Infrastructure issue?
   ├─ YES → Manual Rollback Method 3 (Terraform)
   └─ NO → Investigate application logs
```

#### Testing Rollback Procedures

**Practice rollbacks quarterly in staging:**

1. Deploy intentionally broken version
2. Execute rollback procedure
3. Time the rollback process
4. Document any issues
5. Update runbook as needed

This ensures team is prepared for real incidents.

### Scaling Operations

**Manual Scaling (ECS):**
```bash
# Scale backend service
aws ecs update-service \
  --cluster ohmycoins-staging \
  --service backend \
  --desired-count 4

# Scale frontend service
aws ecs update-service \
  --cluster ohmycoins-staging \
  --service frontend \
  --desired-count 4
```

**Auto-Scaling Configuration:**
- Backend scales between 2-10 tasks based on CPU (70%) and memory (80%)
- Frontend scales between 2-10 tasks based on CPU (70%)
- Scaling policies defined in Terraform

---

## Monitoring and Alerts

### CloudWatch Dashboards

1. **Infrastructure Dashboard**
   - ECS service metrics (CPU, memory, task count)
   - ALB metrics (requests, response times, errors)
   - RDS metrics (connections, CPU, storage)
   - Redis metrics (cache hits, evictions)

2. **Application Dashboard**
   - Application logs with error filtering
   - API response times
   - Request rates by endpoint

### Alert Response

**High Priority Alerts:**

1. **Database Connection Failures**
   - **Symptom**: RDS connection count > 80%
   - **Action**: Check application connection pooling
   - **Escalation**: Increase RDS instance size if needed

2. **High Error Rate (5xx)**
   - **Symptom**: ALB 5xx errors > 5%
   - **Action**: Check application logs in CloudWatch
   - **Escalation**: Rollback deployment if recent change

3. **Service Unhealthy**
   - **Symptom**: ECS tasks failing health checks
   - **Action**: Check task logs for startup errors
   - **Escalation**: Review recent deployments

**Medium Priority Alerts:**

1. **High CPU Usage**
   - **Symptom**: ECS task CPU > 80%
   - **Action**: Monitor auto-scaling behavior
   - **Escalation**: Increase task CPU allocation

2. **Redis Cache Hit Rate Low**
   - **Symptom**: Cache hit rate < 70%
   - **Action**: Review cache key TTLs
   - **Escalation**: Increase Redis memory

### Log Analysis

**Find Recent Errors:**
```bash
# CloudWatch Logs Insights query
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 100
```

**Track Slow Queries:**
```bash
# RDS Performance Insights
aws pi get-resource-metrics \
  --service-type RDS \
  --identifier db-XXXXX \
  --metric-queries file://query.json
```

---

## Incident Response

### Severity Levels

**SEV-1 (Critical)**: Service completely down
- Response time: Immediate
- All hands on deck
- Customer communication required

**SEV-2 (High)**: Service degraded
- Response time: 15 minutes
- Primary on-call engineer
- Monitor for escalation

**SEV-3 (Medium)**: Minor issue
- Response time: 1 hour
- Can be handled during business hours

### Incident Response Steps

1. **Acknowledge**
   - Acknowledge alert in monitoring system
   - Create incident ticket
   - Notify team

2. **Assess**
   - Determine severity level
   - Check affected services
   - Review recent changes

3. **Mitigate**
   - Apply immediate fix or rollback
   - Redirect traffic if needed
   - Scale resources if capacity issue

4. **Resolve**
   - Verify service is healthy
   - Monitor for 15 minutes
   - Update incident ticket

5. **Post-Mortem**
   - Document root cause
   - Create action items
   - Update runbook

---

## Troubleshooting

### Common Issues and Solutions

#### Issue: ECS Tasks Keep Restarting

**Symptoms:**
- Tasks start but fail health checks
- Constant task replacement
- Service shows "deployments in progress" continuously

**Diagnosis:**
```bash
# Check task logs
aws logs tail /ecs/ohmycoins-staging/backend --follow

# Check task details and stop reason
aws ecs describe-tasks \
  --cluster ohmycoins-staging-cluster \
  --tasks $(aws ecs list-tasks --cluster ohmycoins-staging-cluster --service ohmycoins-staging-backend-service --query 'taskArns[0]' --output text) \
  --query 'tasks[0].{Status:lastStatus,StopCode:stopCode,StopReason:stoppedReason,HealthStatus:healthStatus}'

# Check stopped tasks for patterns
aws ecs list-tasks \
  --cluster ohmycoins-staging-cluster \
  --service ohmycoins-staging-backend-service \
  --desired-status STOPPED \
  --max-results 5
```

**Common Causes & Solutions:**

1. **Application Startup Failure:**
   - Check logs for Python/Node errors
   - Verify all dependencies installed in Docker image
   - Check if database migrations need to run
   - Solution: Fix startup script or rebuild image

2. **Health Check Configuration:**
   - Health check path incorrect (should be `/api/v1/health`)
   - Grace period too short (should be 60+ seconds)
   - Solution: Update task definition health check settings

3. **Environment Variables Missing:**
   ```bash
   # Verify secrets are accessible
   aws secretsmanager get-secret-value \
     --secret-id ohmycoins-staging-app-secrets
   ```
   - Solution: Update secrets in AWS Secrets Manager

4. **Resource Limits:**
   - Check if OOM (Out of Memory) killed
   ```bash
   # Look for exit code 137 (OOM)
   aws ecs describe-tasks --cluster ohmycoins-staging-cluster --tasks TASK_ARN | grep -i "exitCode\|reason"
   ```
   - Solution: Increase memory allocation in task definition

**Quick Fix:**
```bash
# Increase health check grace period
# Edit modules/ecs/main.tf and update:
health_check_grace_period_seconds = 90  # from 60

# Redeploy
cd infrastructure/terraform/environments/staging
terraform apply -target=module.ecs
```

#### Issue: Database Connection Timeout

**Symptoms:**
- Application cannot connect to RDS
- Timeout errors in logs: "FATAL: could not connect to server"
- Tasks fail immediately after startup

**Diagnosis:**
```bash
# Check security group rules
RDS_SG=$(aws rds describe-db-instances \
  --db-instance-identifier ohmycoins-staging \
  --query 'DBInstances[0].VpcSecurityGroups[0].VpcSecurityGroupId' \
  --output text)

aws ec2 describe-security-groups \
  --group-ids $RDS_SG \
  --query 'SecurityGroups[0].IpPermissions'

# Check if RDS is available
aws rds describe-db-instances \
  --db-instance-identifier ohmycoins-staging \
  --query 'DBInstances[0].{Status:DBInstanceStatus,Endpoint:Endpoint.Address}'

# Test connectivity from ECS task (if ECS Exec enabled)
aws ecs execute-command \
  --cluster ohmycoins-staging-cluster \
  --task TASK_ARN \
  --container backend \
  --command "nc -zv $DB_HOST 5432" \
  --interactive
```

**Common Causes & Solutions:**

1. **Security Group Misconfiguration:**
   - ECS security group not allowed in RDS security group
   - Solution:
   ```bash
   # Add ECS SG to RDS SG inbound rules
   aws ec2 authorize-security-group-ingress \
     --group-id $RDS_SG \
     --protocol tcp \
     --port 5432 \
     --source-group $ECS_SG
   ```

2. **RDS Not Running:**
   - Check RDS status in AWS console
   - Solution: Start or restore RDS instance

3. **Wrong Connection String:**
   - Verify DATABASE_URL or connection parameters
   - Check secrets manager values
   ```bash
   aws secretsmanager get-secret-value \
     --secret-id ohmycoins-staging-app-secrets \
     --query 'SecretString' \
     --output text | jq .POSTGRES_SERVER
   ```

4. **Network Routing Issue:**
   - Verify subnet has route to RDS subnet
   - Check NAT gateway is running (for private subnets)

**Quick Fix:**
```bash
# Verify and update security groups via Terraform
cd infrastructure/terraform/environments/staging
terraform plan | grep -i security_group
terraform apply -target=module.security
```

#### Issue: Image Pull Errors

**Symptoms:**
- Tasks fail with "CannotPullContainerError"
- Logs show: "Failed to pull image"
- Tasks remain in PENDING state

**Diagnosis:**
```bash
# Check ECR repository exists
aws ecr describe-repositories \
  --repository-names omc-backend omc-frontend

# Check if image tag exists
aws ecr list-images \
  --repository-name omc-backend \
  --filter tagStatus=TAGGED \
  --query 'imageIds[*].imageTag'

# Check task execution role permissions
aws iam get-role-policy \
  --role-name ohmycoins-staging-ecs-task-execution-role \
  --policy-name ecr-access
```

**Common Causes & Solutions:**

1. **Image Tag Doesn't Exist:**
   - Build failed or wasn't pushed
   - Solution: Rebuild and push image
   ```bash
   cd /path/to/backend
   docker build -t $ECR_REGISTRY/omc-backend:latest .
   docker push $ECR_REGISTRY/omc-backend:latest
   ```

2. **IAM Permission Issues:**
   - Task execution role missing ECR permissions
   - Solution: Verify role has `AmazonECSTaskExecutionRolePolicy`
   ```bash
   aws iam attach-role-policy \
     --role-name ohmycoins-staging-ecs-task-execution-role \
     --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
   ```

3. **ECR Authentication Expired:**
   - Docker login token expired
   - Solution: Re-authenticate
   ```bash
   aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_REGISTRY
   ```

4. **Cross-Region Issues:**
   - Trying to pull from wrong region
   - Solution: Verify ECR region matches ECS region (ap-southeast-2)

#### Issue: High Error Rate (5xx Errors)

**Symptoms:**
- ALB returning 503 or 504 errors
- CloudWatch alarms triggered
- Users report application unavailable

**Diagnosis:**
```bash
# Check ALB metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name HTTPCode_Target_5XX_Count \
  --dimensions Name=LoadBalancer,Value=app/ohmycoins-staging-alb/xxx \
  --start-time $(date -u -d '10 minutes ago' --iso-8601) \
  --end-time $(date -u --iso-8601) \
  --period 60 \
  --statistics Sum

# Check unhealthy targets
aws elbv2 describe-target-health \
  --target-group-arn $BACKEND_TG_ARN \
  --query 'TargetHealthDescriptions[?TargetHealth.State!=`healthy`]'

# Check application errors
aws logs filter-log-events \
  --log-group-name /ecs/ohmycoins-staging/backend \
  --filter-pattern "ERROR 500" \
  --start-time $(date -u -d '10 minutes ago' +%s)000
```

**Common Causes & Solutions:**

1. **All Targets Unhealthy:**
   - Application crash or startup failure
   - Solution: Check logs and rollback if needed

2. **Target Response Timeout:**
   - Slow database queries
   - Solution: Check RDS Performance Insights, optimize queries

3. **Resource Exhaustion:**
   - CPU or memory at 100%
   - Solution: Scale up task count or increase task resources

4. **Bad Deployment:**
   - Recent code change causing errors
   - Solution: Rollback to previous version immediately

**Quick Fix:**
```bash
# Emergency: Scale up to handle load
aws ecs update-service \
  --cluster ohmycoins-staging-cluster \
  --service ohmycoins-staging-backend-service \
  --desired-count 4

# If errors persist after 5 minutes, rollback
# See "Rollback Procedures" section
```

#### Issue: High Memory Usage / OOM Kills

**Symptoms:**
- Tasks stopped with exit code 137
- Memory CloudWatch metric at 100%
- Frequent task restarts

**Diagnosis:**
```bash
# Check memory metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name MemoryUtilization \
  --dimensions Name=ServiceName,Value=ohmycoins-staging-backend-service Name=ClusterName,Value=ohmycoins-staging-cluster \
  --start-time $(date -u -d '1 hour ago' --iso-8601) \
  --end-time $(date -u --iso-8601) \
  --period 300 \
  --statistics Maximum

# Check container insights (if enabled)
# Go to CloudWatch Console → Container Insights → ECS Services

# Check stopped tasks for OOM
aws ecs list-tasks \
  --cluster ohmycoins-staging-cluster \
  --service ohmycoins-staging-backend-service \
  --desired-status STOPPED | xargs -I {} aws ecs describe-tasks --cluster ohmycoins-staging-cluster --tasks {} --query 'tasks[0].{StopCode:stopCode,ExitCode:containers[0].exitCode,Reason:stoppedReason}'
```

**Common Causes & Solutions:**

1. **Memory Leak in Application:**
   - Application not releasing memory
   - Solution: Fix memory leak in code, redeploy

2. **Insufficient Memory Allocation:**
   - Task memory too low for workload
   - Current: 1024 MB (staging)
   - Solution: Increase memory
   ```bash
   # Edit modules/ecs/variables.tf
   backend_memory = 2048  # from 1024
   
   cd infrastructure/terraform/environments/staging
   terraform apply -target=module.ecs
   ```

3. **Memory-Intensive Operation:**
   - Large data processing
   - Solution: Optimize algorithm or use batch processing

4. **Too Many Concurrent Requests:**
   - Workers/threads consuming too much memory
   - Solution: Add rate limiting or scale horizontally

**Quick Fix:**
```bash
# Double the memory allocation immediately
# Update task definition with more memory
# See "Manual Deployment" for updating task definition
```

#### Issue: High NAT Gateway Costs

**Symptoms:**
- NAT Gateway charges higher than expected
- Excessive data transfer costs in billing
- Data transfer costs increasing over time

**Diagnosis:**
```bash
# Check VPC Flow Logs for top talkers
# Run this CloudWatch Logs Insights query:
fields srcAddr, dstAddr, bytes
| filter dstAddr not like /^10\./
| stats sum(bytes) as totalBytes by srcAddr, dstAddr
| sort totalBytes desc
| limit 20

# Check NAT Gateway metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/NATGateway \
  --metric-name BytesOutToDestination \
  --dimensions Name=NatGatewayId,Value=nat-xxx \
  --start-time $(date -u -d '1 day ago' --iso-8601) \
  --end-time $(date -u --iso-8601) \
  --period 3600 \
  --statistics Sum
```

**Common Causes & Solutions:**

1. **S3 Traffic Through NAT:**
   - Accessing S3 without VPC endpoint
   - Solution: Use S3 VPC Gateway Endpoint (already configured in staging)
   ```bash
   # Verify S3 endpoint exists
   aws ec2 describe-vpc-endpoints \
     --filters "Name=vpc-id,Values=$VPC_ID" \
     --query 'VpcEndpoints[?ServiceName==`com.amazonaws.ap-southeast-2.s3`]'
   ```

2. **Unnecessary External API Calls:**
   - Application making frequent external API calls
   - Solution: Cache API responses, use internal services where possible

3. **Large Image Pulls from Public Registries:**
   - Pulling Docker images from Docker Hub instead of ECR
   - Solution: Mirror images to ECR

4. **Logging/Monitoring to External Services:**
   - Sending all logs to external service
   - Solution: Filter logs, use CloudWatch first

**Cost Optimization:**
```bash
# Enable VPC endpoints for AWS services
# Already configured: S3
# Consider adding: ECR, CloudWatch, Secrets Manager

# In Terraform, update modules/vpc/main.tf:
enable_vpc_endpoints = true
```

#### Issue: Redis Connection Failures

**Symptoms:**
- Redis timeouts
- Cache unavailable errors: "Error connecting to Redis"
- Intermittent connection drops

**Diagnosis:**
```bash
# Check Redis cluster status
aws elasticache describe-cache-clusters \
  --cache-cluster-id ohmycoins-staging-redis \
  --show-cache-node-info \
  --query 'CacheClusters[0].{Status:CacheClusterStatus,Engine:Engine,Endpoint:CacheNodes[0].Endpoint}'

# Check Redis metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ElastiCache \
  --metric-name CurrConnections \
  --dimensions Name=CacheClusterId,Value=ohmycoins-staging-redis \
  --start-time $(date -u -d '1 hour ago' --iso-8601) \
  --end-time $(date -u --iso-8601) \
  --period 300 \
  --statistics Maximum

# Test Redis connectivity from ECS task
aws ecs execute-command \
  --cluster ohmycoins-staging-cluster \
  --task TASK_ARN \
  --container backend \
  --command "redis-cli -h $REDIS_HOST ping" \
  --interactive
```

**Common Causes & Solutions:**

1. **Connection Pool Exhausted:**
   - Too many open connections
   - Solution: Review connection pool configuration
   ```python
   # In backend code, ensure proper pooling:
   redis_pool = redis.ConnectionPool(
       host=REDIS_HOST,
       max_connections=50,  # Adjust based on task count
       decode_responses=True
   )
   ```

2. **Security Group Misconfiguration:**
   - Similar to database issue
   - Solution: Verify ECS SG can access Redis SG on port 6379

3. **Redis Overloaded:**
   - Too many operations
   - Solution: Scale up Redis node type or optimize queries

4. **Network Issues:**
   - Subnet routing problems
   - Solution: Verify routing tables

**Quick Fix:**
```bash
# Restart Redis cluster (staging only!)
aws elasticache reboot-cache-cluster \
  --cache-cluster-id ohmycoins-staging-redis

# This causes brief downtime - use only if Redis is unresponsive
```

#### Issue: Slow Application Performance

**Symptoms:**
- Response times > 1 second
- Users reporting slow page loads
- CloudWatch showing high latency

**Diagnosis:**
```bash
# Check ALB latency metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name TargetResponseTime \
  --dimensions Name=LoadBalancer,Value=app/ohmycoins-staging-alb/xxx \
  --start-time $(date -u -d '1 hour ago' --iso-8601) \
  --end-time $(date -u --iso-8601) \
  --period 300 \
  --statistics Average,Maximum \
  --query 'Datapoints | sort_by(@, &Timestamp)[-5:]'

# Check database performance
# Go to RDS Console → ohmycoins-staging → Performance Insights
# Look for:
# - Slow queries
# - High CPU
# - Lock waits

# Check application logs for slow requests
aws logs insights query --log-group-name /ecs/ohmycoins-staging/backend \
  --query-string 'fields @timestamp, @message | filter @message like /response_time/ | sort @timestamp desc | limit 20' \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s)
```

**Common Causes & Solutions:**

1. **Database Slow Queries:**
   - Missing indexes
   - N+1 query problems
   - Solution: Add indexes, optimize queries
   ```sql
   -- Check for missing indexes
   SELECT schemaname, tablename, indexname
   FROM pg_indexes
   WHERE schemaname = 'public';
   ```

2. **High Database CPU:**
   - Too many concurrent queries
   - Solution: Enable connection pooling, add read replicas

3. **Cache Miss Rate High:**
   - Redis not being used effectively
   - Solution: Review caching strategy
   ```bash
   # Check cache hit rate
   aws cloudwatch get-metric-statistics \
     --namespace AWS/ElastiCache \
     --metric-name CacheHitRate \
     --dimensions Name=CacheClusterId,Value=ohmycoins-staging-redis
   ```

4. **Insufficient Resources:**
   - CPU or memory throttling
   - Solution: Scale up task size or count

**Performance Tuning:**
```bash
# Enable RDS Performance Insights (staging doesn't have it by default)
cd infrastructure/terraform/environments/staging
# Edit main.tf: performance_insights_enabled = true
terraform apply -target=module.rds

# Add database indexes via migration
# Create new Alembic migration in backend
```

#### Issue: Certificate/SSL Errors

**Symptoms:**
- HTTPS not working
- Certificate expired warnings
- Mixed content errors

**Diagnosis:**
```bash
# Check certificate expiration
aws acm describe-certificate \
  --certificate-arn $CERT_ARN \
  --query 'Certificate.{Status:Status,NotAfter:NotAfter,InUse:InUseBy}'

# Test SSL endpoint
openssl s_client -connect $ALB_DNS:443 -servername $DOMAIN
```

**Solutions:**

1. **Certificate Not Found:**
   - ACM certificate not issued or validation pending
   - Solution: Complete DNS validation in ACM

2. **Certificate Expired:**
   - Certificate not auto-renewed
   - Solution: Request new certificate

3. **Wrong Certificate on ALB:**
   - ALB using default certificate
   - Solution: Update ALB listener to use correct certificate

#### Troubleshooting Checklist

Before escalating issues, verify:

- [ ] Recent deployments (last 24 hours)
- [ ] CloudWatch alarms triggered
- [ ] Application logs reviewed
- [ ] Resource utilization checked (CPU, memory)
- [ ] Network connectivity verified
- [ ] Security groups validated
- [ ] Recent AWS service issues (status.aws.amazon.com)
- [ ] Database and Redis accessible
- [ ] Secrets Manager values correct
- [ ] Task definitions up to date

#### Getting Help

If issue persists after troubleshooting:

1. **Gather Diagnostic Information:**
   ```bash
   # Create diagnostic bundle
   mkdir -p /tmp/omc-diagnostics
   
   # Service status
   aws ecs describe-services --cluster ohmycoins-staging-cluster --services ohmycoins-staging-backend-service > /tmp/omc-diagnostics/service-status.json
   
   # Recent logs
   aws logs tail /ecs/ohmycoins-staging/backend --since 1h > /tmp/omc-diagnostics/recent-logs.txt
   
   # Task details
   aws ecs describe-tasks --cluster ohmycoins-staging-cluster --tasks $(aws ecs list-tasks --cluster ohmycoins-staging-cluster --service ohmycoins-staging-backend-service --query 'taskArns[0]' --output text) > /tmp/omc-diagnostics/task-details.json
   
   # CloudWatch alarms
   aws cloudwatch describe-alarms --alarm-name-prefix ohmycoins-staging > /tmp/omc-diagnostics/alarms.json
   
   tar -czf omc-diagnostics-$(date +%Y%m%d-%H%M%S).tar.gz /tmp/omc-diagnostics/
   ```

2. **Open Support Ticket:**
   - Include diagnostic bundle
   - Document steps already taken
   - Specify severity level
   - Note any customer impact

3. **Escalate per On-Call Rotation:**
   - See "Emergency Contacts" section
   - Follow escalation chain

---

## Maintenance Windows

### Recommended Schedule

- **Staging**: Rolling updates, no maintenance window needed
- **Production**: Sundays 2:00-4:00 AM AEST (lowest traffic period)

### Pre-Maintenance Checklist

1. [ ] Notify team of maintenance window
2. [ ] Create backup of database
3. [ ] Verify rollback plan
4. [ ] Prepare monitoring dashboard
5. [ ] Test changes in staging first

### During Maintenance

1. Apply changes incrementally
2. Monitor metrics continuously
3. Keep communication channel open
4. Document any issues encountered

### Post-Maintenance

1. Verify all services are healthy
2. Check error rates returned to baseline
3. Monitor for 1 hour
4. Send all-clear notification
5. Update runbook if needed

---

## Emergency Contacts

### On-Call Rotation

**Primary On-Call:**
- Developer C (Infrastructure/DevOps)
- Response time: 15 minutes
- Escalation after: 30 minutes

**Secondary On-Call:**
- Developer B (Backend/Application)
- Response time: 30 minutes

**Escalation Chain:**
1. Primary On-Call (15 min)
2. Secondary On-Call (30 min)
3. Tech Lead (45 min)
4. Engineering Manager (1 hour)

### Communication Channels

- **Incidents**: #incidents Slack channel
- **Monitoring**: #alerts Slack channel
- **General**: #devops Slack channel

### External Contacts

- **AWS Support**: Enterprise Support Plan
- **Database Expert**: [Contact Info]
- **Network Specialist**: [Contact Info]

---

## Appendix

### Useful Commands

**SSH into ECS Task (for debugging):**
```bash
aws ecs execute-command \
  --cluster ohmycoins-staging \
  --task <task-id> \
  --container backend \
  --command "/bin/bash" \
  --interactive
```

**Database Connection:**
```bash
psql -h <rds-endpoint> -U ohmycoins -d ohmycoins
```

**Redis Connection:**
```bash
redis-cli -h <redis-endpoint> -p 6379 --tls
```

**View Recent Deployments:**
```bash
aws ecs list-tasks \
  --cluster ohmycoins-staging \
  --service-name backend \
  --query 'taskArns[0]' \
  --output text
```

### References

- [Terraform README](../README.md)
- [Quick Start Guide](../QUICKSTART.md)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [ECS Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/)

---

**Last Updated:** 2026-01-18  
**Maintained By:** Developer C (Infrastructure & DevOps)  
**Version:** 2.1 - Sprint 2.12 Production Deployment Edition
**Next Review:** After first production workload deployment

---

## Production Deployment Procedures

### Production Environment Setup (Sprint 2.12)

**Infrastructure Deployed:**
- **Region:** ap-southeast-2 (Sydney)
- **VPC:** 10.0.0.0/16
- **Database:** RDS PostgreSQL db.t3.small (Multi-AZ)
- **Cache:** ElastiCache Redis cache.t3.small (Multi-AZ, 1 primary + 1 replica)
- **Compute:** ECS Fargate (2 backend + 2 frontend tasks, scaled to 0)
- **Load Balancer:** ALB with HTTP (port 80)
- **Monitoring:** 9 CloudWatch alarms configured

**Production Deployment Command:**
```bash
cd /home/mark/omc/ohmycoins/infrastructure/terraform/environments/production
terraform init -reconfigure
terraform workspace select production
terraform plan -out=production.tfplan
terraform apply production.tfplan
```

**Deployed Resources:** 101 resources created

**Deployment Outputs:**
```
alb_dns_name = "ohmycoins-prod-alb-1133770157.ap-southeast-2.elb.amazonaws.com"
backend_service_name = "ohmycoins-prod-backend"
frontend_service_name = "ohmycoins-prod-frontend"
db_endpoint = "ohmycoins-prod-postgres.cnuko2w8idh1.ap-southeast-2.rds.amazonaws.com:5432"
redis_endpoint = "master.ohmycoins-prod-redis.faxg1m.apse2.cache.amazonaws.com"
redis_reader_endpoint = "replica.ohmycoins-prod-redis.faxg1m.apse2.cache.amazonaws.com"
```

---

## Resource Scaling and Cost Management

### Scale Down Production Resources (Minimize Costs)

When production is not actively serving traffic, scale down to minimize AWS costs:

**Step 1: Scale ECS Services to Zero**
```bash
# Scale backend to 0
aws ecs update-service \
    --cluster ohmycoins-prod-cluster \
    --service ohmycoins-prod-backend \
    --desired-count 0 \
    --region ap-southeast-2

# Scale frontend to 0
aws ecs update-service \
    --cluster ohmycoins-prod-cluster \
    --service ohmycoins-prod-frontend \
    --desired-count 0 \
    --region ap-southeast-2

# Verify
aws ecs describe-services \
    --cluster ohmycoins-prod-cluster \
    --services ohmycoins-prod-backend ohmycoins-prod-frontend \
    --region ap-southeast-2 \
    --query 'services[*].{Name:serviceName,Desired:desiredCount,Running:runningCount}'
```

**Expected Output:**
```
| Desired | Name                     | Running |
|---------|--------------------------|---------|
| 0       | ohmycoins-prod-backend   | 0       |
| 0       | ohmycoins-prod-frontend  | 0       |
```

**Step 2: Stop RDS Instance**
```bash
# Stop RDS (will auto-restart after 7 days)
aws rds stop-db-instance \
    --db-instance-identifier ohmycoins-prod-postgres \
    --region ap-southeast-2

# Verify status
aws rds describe-db-instances \
    --db-instance-identifier ohmycoins-prod-postgres \
    --region ap-southeast-2 \
    --query 'DBInstances[0].DBInstanceStatus'
```

**Expected:** `"stopping"` or `"stopped"`

**Step 3: ElastiCache Redis - Note on Limitations**

⚠️ **Important:** ElastiCache does not support stopping clusters like RDS. Options:
- **Keep running** (recommended for demo/dev): ~$0.034/hour = ~$25/month
- **Delete cluster** (not recommended): Requires Terraform destroy/apply cycle to recreate

Current production Redis remains running for infrastructure preservation.

### Scale Up Production Resources

When ready to serve traffic, scale resources back up:

**Step 1: Start RDS Instance**
```bash
aws rds start-db-instance \
    --db-instance-identifier ohmycoins-prod-postgres \
    --region ap-southeast-2

# Wait for availability (5-10 minutes)
aws rds wait db-instance-available \
    --db-instance-identifier ohmycoins-prod-postgres \
    --region ap-southeast-2
```

**Step 2: Scale ECS Services**
```bash
# Scale backend to 2 tasks
aws ecs update-service \
    --cluster ohmycoins-prod-cluster \
    --service ohmycoins-prod-backend \
    --desired-count 2 \
    --region ap-southeast-2

# Scale frontend to 2 tasks
aws ecs update-service \
    --cluster ohmycoins-prod-cluster \
    --service ohmycoins-prod-frontend \
    --desired-count 2 \
    --region ap-southeast-2

# Wait for services to stabilize
aws ecs wait services-stable \
    --cluster ohmycoins-prod-cluster \
    --services ohmycoins-prod-backend ohmycoins-prod-frontend \
    --region ap-southeast-2
```

**Step 3: Validate Production Health**
```bash
# Check services
aws ecs describe-services \
    --cluster ohmycoins-prod-cluster \
    --services ohmycoins-prod-backend ohmycoins-prod-frontend \
    --region ap-southeast-2 \
    --query 'services[*].{Name:serviceName,Running:runningCount,Desired:desiredCount}'

# Test backend health
ALB_DNS="ohmycoins-prod-alb-1133770157.ap-southeast-2.elb.amazonaws.com"
curl -H "Host: api.ohmycoins.com" http://$ALB_DNS/api/v1/utils/health-check/

# Test frontend
curl -H "Host: dashboard.ohmycoins.com" http://$ALB_DNS/
```

---

## CloudWatch Monitoring Configuration

### Production Alarms (9 Configured)

**RDS Alarms:**
1. **CPU Utilization** - Threshold: 80%
2. **Database Connections** - Threshold: 80 connections
3. **Free Storage Space** - Threshold: 10 GB

**ElastiCache Redis Alarms:**
4. **CPU Utilization** - Threshold: 75%
5. **Memory Utilization** - Threshold: 80%
6. **Evictions** - Threshold: 1000 evictions/period

**ALB Alarms:**
7. **5XX Errors** - Threshold: 10 errors/period
8. **Target Response Time** - Threshold: 2 seconds
9. **Unhealthy Target Count** - Threshold: 0 (alert on any unhealthy target)

### View Alarms
```bash
aws cloudwatch describe-alarms \
    --region ap-southeast-2 \
    --alarm-name-prefix "ohmycoins-prod" \
    --query 'MetricAlarms[*].{Name:AlarmName,Metric:MetricName,Threshold:Threshold,State:StateValue}'
```

### CloudWatch Dashboard (Future Enhancement)
A production dashboard should be created with:
- ECS service metrics (CPU, memory, task count)
- RDS performance metrics
- Redis cache performance
- ALB request rates and latencies
- Error rates and 5XX counts

---
