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

### Standard Deployment (Automated)

**Via GitHub Actions:**

1. Push infrastructure changes to `main` branch
   ```bash
   git checkout main
   git push origin main
   ```

2. Automatic workflow triggers:
   - Terraform plan is generated
   - Manual approval required for apply
   - Application deployment proceeds

**Via Manual Workflow Dispatch:**

1. Go to GitHub Actions → "Deploy to AWS"
2. Click "Run workflow"
3. Select environment (staging/production)
4. Select action (plan/apply/destroy)
5. Review plan output
6. Approve or cancel

### Emergency Rollback

1. **Application Rollback** (ECS):
   ```bash
   # Get previous task definition
   aws ecs describe-task-definition \
     --task-definition ohmycoins-backend \
     --query 'taskDefinition.taskDefinitionArn'
   
   # Update service to previous version
   aws ecs update-service \
     --cluster ohmycoins-staging \
     --service backend \
     --task-definition ohmycoins-backend:PREVIOUS_REVISION
   ```

2. **Infrastructure Rollback** (Terraform):
   ```bash
   cd infrastructure/terraform/environments/staging
   
   # Revert to previous commit
   git revert HEAD
   git push origin main
   
   # Or manually apply previous version
   git checkout <previous-commit>
   terraform apply
   ```

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

### Common Issues

#### Issue: ECS Tasks Keep Restarting

**Symptoms:**
- Tasks start but fail health checks
- Constant task replacement

**Diagnosis:**
```bash
# Check task logs
aws logs tail /ecs/ohmycoins-staging/backend --follow

# Check task details
aws ecs describe-tasks \
  --cluster ohmycoins-staging \
  --tasks <task-id>
```

**Solutions:**
1. Verify environment variables in task definition
2. Check database connectivity
3. Review application startup logs
4. Increase health check grace period

#### Issue: Database Connection Timeout

**Symptoms:**
- Application cannot connect to RDS
- Timeout errors in logs

**Diagnosis:**
```bash
# Check security group rules
aws ec2 describe-security-groups \
  --group-ids <rds-sg-id>

# Test connectivity from ECS task
aws ecs execute-command \
  --cluster ohmycoins-staging \
  --task <task-id> \
  --command "nc -zv <rds-endpoint> 5432" \
  --interactive
```

**Solutions:**
1. Verify security group allows traffic from ECS tasks
2. Check subnet routing to database
3. Verify RDS is running
4. Check RDS parameter group settings

#### Issue: High NAT Gateway Costs

**Symptoms:**
- NAT Gateway charges higher than expected
- Excessive data transfer

**Diagnosis:**
```bash
# Check VPC Flow Logs for top talkers
# Use CloudWatch Logs Insights
fields srcAddr, dstAddr, bytes
| stats sum(bytes) as totalBytes by srcAddr, dstAddr
| sort totalBytes desc
```

**Solutions:**
1. Enable VPC endpoints for S3 (already configured)
2. Review which services are using NAT Gateway
3. Consider interface endpoints for other AWS services
4. Optimize data transfer patterns

#### Issue: Redis Connection Failures

**Symptoms:**
- Redis timeouts
- Cache unavailable errors

**Diagnosis:**
```bash
# Check Redis cluster status
aws elasticache describe-cache-clusters \
  --cache-cluster-id ohmycoins-staging-redis \
  --show-cache-node-info
```

**Solutions:**
1. Verify security group rules
2. Check subnet routing
3. Review Redis configuration
4. Check connection pool settings

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

**Last Updated:** 2025-11-17  
**Maintained By:** Developer C (Infrastructure & DevOps)  
**Next Review:** After first production deployment
