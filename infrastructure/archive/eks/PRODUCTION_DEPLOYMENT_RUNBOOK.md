# Production Deployment Runbook - Oh My Coins
**Last Updated:** 2025-11-20  
**Sprint:** Weeks 9-10  
**Owner:** Developer C (Infrastructure & DevOps)

> **NOTE:** This runbook contains example values (account IDs, zone IDs, endpoints) that 
> should be replaced with your actual values. The ALB hosted zone ID shown (Z1GM3OXH4ZPM65) 
> is specific to ap-southeast-2 region. Verify the correct zone ID for your target region 
> from [AWS Documentation](https://docs.aws.amazon.com/general/latest/gr/elb.html).

---

## Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Week 9: Production Infrastructure Deployment](#week-9-production-infrastructure-deployment)
3. [DNS and SSL Configuration](#dns-and-ssl-configuration)
4. [Application Deployment Support](#application-deployment-support)
5. [Post-Deployment Validation](#post-deployment-validation)
6. [Rollback Procedures](#rollback-procedures)

---

## Pre-Deployment Checklist

### Prerequisites Verification

**1. AWS Account Setup**
- [ ] AWS account configured and accessible
- [ ] AWS CLI configured with production credentials
- [ ] Terraform state backend configured (S3 + DynamoDB)
- [ ] Cost budgets and alerts configured

**2. Domain and DNS**
- [ ] Domain registered (ohmycoins.com)
- [ ] Route53 hosted zone created or accessible
- [ ] Domain registrar NS records updated (if using Route53)
- [ ] DNS propagation completed (24-48 hours)

**3. SSL Certificates**
- [ ] ACM certificate requested for `ohmycoins.com` and `*.ohmycoins.com`
- [ ] Certificate validated (DNS or email validation)
- [ ] Certificate ARN documented in terraform.tfvars

**4. Secrets and Credentials**
- [ ] Database password generated (strong, random, 32+ characters)
- [ ] Redis auth token generated (strong, random, 32+ characters)
- [ ] Secrets stored in AWS Secrets Manager
- [ ] GitHub OIDC provider created (from staging deployment)
- [ ] Container images built and pushed to registry

**5. Team Coordination**
- [ ] Developer A notified of deployment timeline
- [ ] Developer B notified of deployment timeline
- [ ] Maintenance window scheduled
- [ ] Communication plan established

**6. Backup Strategy**
- [ ] Backup policies defined
- [ ] Recovery procedures documented
- [ ] Test restore procedures executed (on staging)

---

## Week 9: Production Infrastructure Deployment

### Day 1-2: Terraform Configuration and Planning

**Step 1: Update Production Variables**

```bash
cd /home/runner/work/ohmycoins/ohmycoins/infrastructure/terraform/environments/production

# Copy and update terraform.tfvars
cp terraform.tfvars.example terraform.tfvars

# Update the following values:
# - master_password (use AWS Secrets Manager reference or strong password)
# - redis_auth_token (use AWS Secrets Manager reference or strong password)
# - certificate_arn (actual ACM certificate ARN)
# - backend_image_tag and frontend_image_tag (specific version, never "latest")

# Example:
vi terraform.tfvars
```

**Step 2: Initialize Terraform**

```bash
# Initialize Terraform with production backend
terraform init \
    -backend-config="bucket=ohmycoins-terraform-state" \
    -backend-config="key=production/terraform.tfstate" \
    -backend-config="region=ap-southeast-2" \
    -backend-config="dynamodb_table=ohmycoins-terraform-locks"

# Verify backend configuration
terraform providers
```

**Step 3: Terraform Plan and Review**

```bash
# Generate and save plan
terraform plan -out=production.tfplan

# Review plan output carefully
# Look for:
# - Number of resources to create (should be ~40-50 for fresh deployment)
# - No unexpected deletions or replacements
# - Correct instance sizes and configurations
# - Proper tagging

# Share plan with team for review
# Save plan output for documentation
terraform show production.tfplan > production-plan-$(date +%Y%m%d).txt
```

**Step 4: Cost Estimation**

```bash
# Estimate monthly costs
cd /home/runner/work/ohmycoins/ohmycoins/infrastructure/terraform
./scripts/estimate-costs.sh production

# Expected production costs: ~$390/month
# - RDS PostgreSQL (db.t3.small, Multi-AZ): ~$60
# - ElastiCache Redis (cache.t3.small, 2 nodes): ~$60
# - ECS Fargate (2 backend + 2 frontend): ~$120
# - ALB: ~$20
# - NAT Gateways (2, Multi-AZ): ~$70
# - Data Transfer: ~$30
# - CloudWatch Logs: ~$20
# - VPC Flow Logs: ~$10

# Get approval for costs before proceeding
```

### Day 3-4: Terraform Apply and Deployment

**Step 5: Execute Terraform Apply**

```bash
# Apply the plan
terraform apply production.tfplan

# Monitor the apply process
# This will take approximately 15-20 minutes
# Key resources being created:
# - VPC and subnets
# - RDS instance (this takes the longest, ~10 minutes)
# - ElastiCache Redis cluster
# - ECS cluster and task definitions
# - ALB and target groups
# - Security groups
# - IAM roles and policies

# Wait for completion and review output
```

**Step 6: Verify Infrastructure Creation**

```bash
# Check VPC
aws ec2 describe-vpcs \
    --filters "Name=tag:Environment,Values=production" \
    --region ap-southeast-2

# Check RDS
aws rds describe-db-instances \
    --db-instance-identifier ohmycoins-prod \
    --region ap-southeast-2

# Check Redis
aws elasticache describe-cache-clusters \
    --cache-cluster-id ohmycoins-prod-redis \
    --region ap-southeast-2

# Check ALB
aws elbv2 describe-load-balancers \
    --names ohmycoins-prod-alb \
    --region ap-southeast-2

# Check ECS cluster
aws ecs describe-clusters \
    --clusters ohmycoins-prod \
    --region ap-southeast-2
```

**Step 7: Document Infrastructure Outputs**

```bash
# Save Terraform outputs
terraform output > production-outputs.txt

# Important outputs to document:
# - alb_dns_name
# - rds_endpoint
# - redis_endpoint
# - vpc_id
# - backend_task_definition_arn
# - frontend_task_definition_arn

# Store outputs in secure location (password manager or Secrets Manager)
```

---

## DNS and SSL Configuration

### Day 5: Configure Route53 DNS

**Step 1: Create DNS Records**

```bash
# Get ALB DNS name from Terraform outputs
ALB_DNS=$(terraform output -raw alb_dns_name)

# Get hosted zone ID
ZONE_ID=$(aws route53 list-hosted-zones-by-name \
    --dns-name ohmycoins.com \
    --query 'HostedZones[0].Id' \
    --output text | cut -d'/' -f3)

# Create A record for apex domain (ohmycoins.com)
aws route53 change-resource-record-sets \
    --hosted-zone-id $ZONE_ID \
    --change-batch '{
      "Changes": [{
        "Action": "CREATE",
        "ResourceRecordSet": {
          "Name": "ohmycoins.com",
          "Type": "A",
          "AliasTarget": {
            "HostedZoneId": "Z1GM3OXH4ZPM65",
            "DNSName": "'"$ALB_DNS"'",
            "EvaluateTargetHealth": true
          }
        }
      }]
    }'

# Create A record for API subdomain (api.ohmycoins.com)
aws route53 change-resource-record-sets \
    --hosted-zone-id $ZONE_ID \
    --change-batch '{
      "Changes": [{
        "Action": "CREATE",
        "ResourceRecordSet": {
          "Name": "api.ohmycoins.com",
          "Type": "A",
          "AliasTarget": {
            "HostedZoneId": "Z1GM3OXH4ZPM65",
            "DNSName": "'"$ALB_DNS"'",
            "EvaluateTargetHealth": true
          }
        }
      }]
    }'

# Create A record for dashboard subdomain (dashboard.ohmycoins.com)
aws route53 change-resource-record-sets \
    --hosted-zone-id $ZONE_ID \
    --change-batch '{
      "Changes": [{
        "Action": "CREATE",
        "ResourceRecordSet": {
          "Name": "dashboard.ohmycoins.com",
          "Type": "A",
          "AliasTarget": {
            "HostedZoneId": "Z1GM3OXH4ZPM65",
            "DNSName": "'"$ALB_DNS"'",
            "EvaluateTargetHealth": true
          }
        }
      }]
    }'
```

**Step 2: Verify DNS Propagation**

```bash
# Check DNS resolution (may take a few minutes)
dig +short ohmycoins.com
dig +short api.ohmycoins.com
dig +short dashboard.ohmycoins.com

# All should resolve to ALB IP addresses

# Check from external DNS
nslookup api.ohmycoins.com 8.8.8.8
```

**Step 3: Test HTTPS Access**

```bash
# Test HTTPS endpoints
curl -I https://api.ohmycoins.com/api/v1/health
curl -I https://dashboard.ohmycoins.com

# Should return 200 OK with valid SSL certificate
# If certificate warnings, check ACM certificate configuration
```

---

## Application Deployment Support

### Coordinate with Developer A and B

**Timeline:**
- Day 6-7: Support application deployments to staging
- Ongoing: Monitor and troubleshoot

**Support Checklist:**

**For Developer A (Phase 2.5 Collectors):**

- [ ] Verify RDS database is accessible from EKS
  ```bash
  kubectl run -it --rm debug --image=postgres:15 --restart=Never -- \
      psql -h <RDS_ENDPOINT> -U postgres -d ohmycoins
  ```
  
- [ ] Verify collector images are available
  ```bash
  docker pull ghcr.io/marklimmage/ohmycoins-backend:latest
  ```
  
- [ ] Monitor collector deployments
  ```bash
  kubectl get cronjobs -n default
  kubectl get deployments -n default -l app=collector
  ```
  
- [ ] Check collector logs for errors
  ```bash
  kubectl logs -n default -l app=collector --tail=100
  ```
  
- [ ] Verify data ingestion to database
  ```bash
  # Connect to RDS and check latest data
  psql -h <RDS_ENDPOINT> -U postgres -d ohmycoins -c \
      "SELECT COUNT(*), MAX(created_at) FROM price_data_5min;"
  ```

**For Developer B (Phase 3 Agentic System):**

- [ ] Verify Redis is accessible from EKS
  ```bash
  kubectl run -it --rm debug --image=redis:7 --restart=Never -- \
      redis-cli -h <REDIS_ENDPOINT> -a <REDIS_AUTH_TOKEN> ping
  ```
  
- [ ] Verify agent images are available
  ```bash
  docker pull ghcr.io/marklimmage/ohmycoins-agents:latest
  ```
  
- [ ] Monitor agent deployments
  ```bash
  kubectl get deployments -n default -l app=agent
  kubectl get hpa -n default -l app=agent
  ```
  
- [ ] Check agent logs for errors
  ```bash
  kubectl logs -n default -l app=agent --tail=100 -f
  ```
  
- [ ] Verify agent API connectivity
  ```bash
  curl https://api.ohmycoins.com/api/v1/lab/agent/sessions
  ```

**Monitoring During Deployments:**

```bash
# Watch pod status
kubectl get pods -n default -w

# Check resource utilization
kubectl top pods -n default
kubectl top nodes

# View events for troubleshooting
kubectl get events -n default --sort-by='.lastTimestamp'

# Check monitoring stack
kubectl get pods -n monitoring
```

**Common Issues and Solutions:**

1. **ImagePullBackOff:**
   - Check image name and tag
   - Verify registry credentials
   - Check pull secrets

2. **CrashLoopBackOff:**
   - Check application logs
   - Verify environment variables
   - Check database connectivity

3. **Pending Pods:**
   - Check node resources
   - Verify resource requests/limits
   - Check for scheduling constraints

---

## Post-Deployment Validation

### Comprehensive System Checks

**Step 1: Infrastructure Health**

```bash
# Check all resources are running
terraform state list | wc -l  # Should match plan

# Verify RDS
aws rds describe-db-instances \
    --db-instance-identifier ohmycoins-prod \
    --query 'DBInstances[0].DBInstanceStatus' \
    --output text
# Should be: available

# Verify Redis
aws elasticache describe-cache-clusters \
    --cache-cluster-id ohmycoins-prod-redis \
    --query 'CacheClusters[0].CacheClusterStatus' \
    --output text
# Should be: available

# Verify ALB
aws elbv2 describe-target-health \
    --target-group-arn <BACKEND_TARGET_GROUP_ARN>
# All targets should be healthy
```

**Step 2: Application Health**

```bash
# Backend API health check
curl https://api.ohmycoins.com/api/v1/health
# Expected: {"status": "healthy"}

# Check Grafana dashboard
open https://grafana.staging.ohmycoins.com

# Verify metrics are flowing
# - Backend request rate > 0
# - Collector execution count > 0
# - No error spikes
```

**Step 3: Security Validation**

```bash
# Run security hardening checklist
# See: infrastructure/aws/eks/security/SECURITY_HARDENING.md

# Key checks:
- [ ] GuardDuty enabled
- [ ] CloudTrail enabled
- [ ] AWS Config enabled
- [ ] WAF configured on ALB
- [ ] Network policies applied
- [ ] All data encrypted
```

**Step 4: Performance Baseline**

```bash
# Run load test to establish baseline
# Document:
# - Response time (p50, p95, p99)
# - Throughput (requests/second)
# - Error rate
# - Resource utilization (CPU, memory)

# Store baseline metrics for future comparison
```

---

## Rollback Procedures

### Emergency Rollback

**Scenario 1: Infrastructure Rollback**

```bash
# If production deployment fails, rollback infrastructure

# Option A: Terraform destroy (clean rollback)
terraform destroy -auto-approve

# Option B: Terraform apply with previous state
terraform apply -state=terraform.tfstate.backup

# Verify rollback
terraform plan  # Should show no changes
```

**Scenario 2: Application Rollback**

```bash
# Rollback to previous image version
kubectl set image deployment/backend \
    backend=ghcr.io/marklimmage/ohmycoins-backend:v0.9.0 \
    -n default

# Rollback using Kubernetes rollout
kubectl rollout undo deployment/backend -n default

# Verify rollback
kubectl rollout status deployment/backend -n default
```

**Scenario 3: Database Rollback**

```bash
# Restore from snapshot (if schema changes broke production)
aws rds restore-db-instance-from-db-snapshot \
    --db-instance-identifier ohmycoins-prod-restored \
    --db-snapshot-identifier ohmycoins-prod-pre-migration \
    --db-instance-class db.t3.small \
    --region ap-southeast-2

# Update DNS to point to restored instance
# Or update application configuration
```

---

## Success Criteria

### Production Deployment Complete When:

- [x] All Terraform resources created successfully
- [x] Infrastructure health checks passing
- [x] DNS records configured and resolving
- [x] SSL certificates valid and applied
- [x] Applications deployed to staging (Developer A and B)
- [x] Monitoring stack operational
- [x] Security hardening implemented
- [x] Documentation updated
- [x] Team trained on operational procedures
- [x] Rollback procedures tested

---

## Appendix: Useful Commands

### Quick Status Checks

```bash
# Infrastructure status
terraform state list | head -20

# Application status
kubectl get pods -A

# Database status
aws rds describe-db-instances \
    --query 'DBInstances[*].[DBInstanceIdentifier,DBInstanceStatus]' \
    --output table

# DNS status
dig +short api.ohmycoins.com

# SSL certificate status
echo | openssl s_client -connect api.ohmycoins.com:443 2>/dev/null | \
    openssl x509 -noout -dates
```

### Debugging Commands

```bash
# View logs
kubectl logs -n default <pod-name> --tail=100 -f

# Exec into pod
kubectl exec -it -n default <pod-name> -- /bin/bash

# Check events
kubectl get events -n default --sort-by='.lastTimestamp' | tail -20

# Resource usage
kubectl top pods -n default
kubectl top nodes
```

---

**Last Updated:** 2025-11-20  
**Next Review:** After production deployment completion  
**Owner:** Developer C (Infrastructure & DevOps)
