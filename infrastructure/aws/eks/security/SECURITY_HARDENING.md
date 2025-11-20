# Security Hardening Guide - Oh My Coins Production Environment
**Last Updated:** 2025-11-20  
**Status:** Week 10 Implementation Guide  
**Owner:** Developer C (Infrastructure & DevOps)

> **NOTE:** This guide contains example values (email addresses, account IDs, resource names) 
> that should be replaced with your actual values when implementing. All example values are 
> clearly marked with comments. Refer to your specific AWS account and infrastructure configuration.

---

## Table of Contents
1. [Overview](#overview)
2. [AWS Security Services](#aws-security-services)
3. [Web Application Firewall (WAF)](#web-application-firewall-waf)
4. [Network Security](#network-security)
5. [Backup and Disaster Recovery](#backup-and-disaster-recovery)
6. [Security Audit Checklist](#security-audit-checklist)
7. [Compliance and Monitoring](#compliance-and-monitoring)

---

## Overview

This guide provides step-by-step instructions for implementing security hardening measures for the Oh My Coins production environment. These measures implement defense-in-depth principles and follow AWS Well-Architected Framework security best practices.

**Security Objectives:**
- Prevent unauthorized access to resources
- Detect and respond to security threats in real-time
- Ensure data protection at rest and in transit
- Maintain audit trail for compliance
- Enable rapid disaster recovery

**Timeline:**
- Week 10, Day 1-2: AWS Security Services (GuardDuty, CloudTrail, Config)
- Week 10, Day 3-4: WAF Configuration
- Week 10, Day 5: Network Policies and Security Groups
- Week 10, Day 6-7: Backup Testing and Documentation

---

## AWS Security Services

### 1. AWS GuardDuty - Threat Detection

**Purpose:** Continuous monitoring for malicious activity and unauthorized behavior.

**Implementation Steps:**

```bash
# Enable GuardDuty in production account
aws guardduty create-detector \
    --enable \
    --finding-publishing-frequency FIFTEEN_MINUTES \
    --region ap-southeast-2

# Get detector ID
DETECTOR_ID=$(aws guardduty list-detectors \
    --region ap-southeast-2 \
    --query 'DetectorIds[0]' \
    --output text)

# Configure threat intelligence sets (optional)
aws guardduty create-threat-intel-set \
    --detector-id $DETECTOR_ID \
    --name "CustomThreatList" \
    --format TXT \
    --location s3://ohmycoins-security/threat-intel.txt \
    --activate \
    --region ap-southeast-2
```

**Notification Setup:**

```bash
# Create SNS topic for GuardDuty findings
aws sns create-topic \
    --name guardduty-findings \
    --region ap-southeast-2

# Subscribe email to topic (CUSTOMIZE: Replace with your actual security email)
aws sns subscribe \
    --topic-arn arn:aws:sns:ap-southeast-2:220711411889:guardduty-findings \
    --protocol email \
    --notification-endpoint security@ohmycoins.com  # REPLACE: Use your actual security email

# Create EventBridge rule to forward findings to SNS
aws events put-rule \
    --name guardduty-findings-rule \
    --event-pattern '{
      "source": ["aws.guardduty"],
      "detail-type": ["GuardDuty Finding"]
    }' \
    --region ap-southeast-2

# Add SNS as target
aws events put-targets \
    --rule guardduty-findings-rule \
    --targets "Id"="1","Arn"="arn:aws:sns:ap-southeast-2:220711411889:guardduty-findings" \
    --region ap-southeast-2
```

**Monitoring:**
- High and Critical findings require immediate investigation
- Review findings daily in AWS Console or CloudWatch
- Configure automated response for known threat patterns

### 2. AWS CloudTrail - Audit Logging

**Purpose:** Track all API activity for security analysis, compliance, and troubleshooting.

**Implementation Steps:**

```bash
# Create S3 bucket for CloudTrail logs
aws s3api create-bucket \
    --bucket ohmycoins-cloudtrail-logs \
    --region ap-southeast-2 \
    --create-bucket-configuration LocationConstraint=ap-southeast-2

# Enable versioning
aws s3api put-bucket-versioning \
    --bucket ohmycoins-cloudtrail-logs \
    --versioning-configuration Status=Enabled

# Apply bucket policy for CloudTrail
aws s3api put-bucket-policy \
    --bucket ohmycoins-cloudtrail-logs \
    --policy file://cloudtrail-bucket-policy.json

# Enable encryption
aws s3api put-bucket-encryption \
    --bucket ohmycoins-cloudtrail-logs \
    --server-side-encryption-configuration '{
      "Rules": [{
        "ApplyServerSideEncryptionByDefault": {
          "SSEAlgorithm": "AES256"
        }
      }]
    }'

# Create CloudTrail
aws cloudtrail create-trail \
    --name ohmycoins-production \
    --s3-bucket-name ohmycoins-cloudtrail-logs \
    --is-multi-region-trail \
    --enable-log-file-validation \
    --region ap-southeast-2

# Start logging
aws cloudtrail start-logging \
    --name ohmycoins-production \
    --region ap-southeast-2

# Enable CloudWatch Logs integration
aws cloudtrail update-trail \
    --name ohmycoins-production \
    --cloud-watch-logs-log-group-arn arn:aws:logs:ap-southeast-2:220711411889:log-group:cloudtrail \
    --cloud-watch-logs-role-arn arn:aws:iam::220711411889:role/CloudTrailCloudWatchLogsRole
```

**CloudTrail Bucket Policy (cloudtrail-bucket-policy.json):**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AWSCloudTrailAclCheck",
      "Effect": "Allow",
      "Principal": {
        "Service": "cloudtrail.amazonaws.com"
      },
      "Action": "s3:GetBucketAcl",
      "Resource": "arn:aws:s3:::ohmycoins-cloudtrail-logs"
    },
    {
      "Sid": "AWSCloudTrailWrite",
      "Effect": "Allow",
      "Principal": {
        "Service": "cloudtrail.amazonaws.com"
      },
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::ohmycoins-cloudtrail-logs/AWSLogs/220711411889/*",
      "Condition": {
        "StringEquals": {
          "s3:x-amz-acl": "bucket-owner-full-control"
        }
      }
    }
  ]
}
```

**Monitoring:**
- Review CloudTrail logs for suspicious API calls
- Set up CloudWatch alarms for critical events
- Retain logs for at least 90 days (compliance requirement)

### 3. AWS Config - Compliance Monitoring

**Purpose:** Assess, audit, and evaluate AWS resource configurations for compliance.

**Implementation Steps:**

```bash
# Create S3 bucket for Config
aws s3api create-bucket \
    --bucket ohmycoins-config-logs \
    --region ap-southeast-2 \
    --create-bucket-configuration LocationConstraint=ap-southeast-2

# Create IAM role for AWS Config
aws iam create-role \
    --role-name AWSConfigRole \
    --assume-role-policy-document '{
      "Version": "2012-10-17",
      "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "config.amazonaws.com"},
        "Action": "sts:AssumeRole"
      }]
    }'

# Attach managed policy
aws iam attach-role-policy \
    --role-name AWSConfigRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/ConfigRole

# Enable AWS Config
aws configservice put-configuration-recorder \
    --configuration-recorder name=default,roleARN=arn:aws:iam::220711411889:role/AWSConfigRole \
    --recording-group allSupported=true,includeGlobalResourceTypes=true

aws configservice put-delivery-channel \
    --delivery-channel name=default,s3BucketName=ohmycoins-config-logs

aws configservice start-configuration-recorder \
    --configuration-recorder-name default
```

**Recommended Config Rules:**

```bash
# Ensure encrypted volumes
aws configservice put-config-rule \
    --config-rule '{
      "ConfigRuleName": "encrypted-volumes",
      "Source": {
        "Owner": "AWS",
        "SourceIdentifier": "ENCRYPTED_VOLUMES"
      }
    }'

# Ensure RDS is encrypted
aws configservice put-config-rule \
    --config-rule '{
      "ConfigRuleName": "rds-storage-encrypted",
      "Source": {
        "Owner": "AWS",
        "SourceIdentifier": "RDS_STORAGE_ENCRYPTED"
      }
    }'

# Ensure security groups don't allow 0.0.0.0/0 on high-risk ports
aws configservice put-config-rule \
    --config-rule '{
      "ConfigRuleName": "restricted-ssh",
      "Source": {
        "Owner": "AWS",
        "SourceIdentifier": "INCOMING_SSH_DISABLED"
      }
    }'

# Ensure S3 buckets have encryption
aws configservice put-config-rule \
    --config-rule '{
      "ConfigRuleName": "s3-bucket-server-side-encryption-enabled",
      "Source": {
        "Owner": "AWS",
        "SourceIdentifier": "S3_BUCKET_SERVER_SIDE_ENCRYPTION_ENABLED"
      }
    }'
```

---

## Web Application Firewall (WAF)

### WAF Configuration for Production ALB

**Purpose:** Protect web applications from common web exploits and DDoS attacks.

**Implementation:**

```bash
# Create WAF Web ACL
aws wafv2 create-web-acl \
    --name ohmycoins-production-waf \
    --scope REGIONAL \
    --region ap-southeast-2 \
    --default-action Allow={} \
    --rules file://waf-rules.json \
    --visibility-config SampledRequestsEnabled=true,CloudWatchMetricsEnabled=true,MetricName=ohmycoins-waf

# Associate with ALB
aws wafv2 associate-web-acl \
    --web-acl-arn arn:aws:wafv2:ap-southeast-2:220711411889:regional/webacl/ohmycoins-production-waf/... \
    --resource-arn arn:aws:elasticloadbalancing:ap-southeast-2:220711411889:loadbalancer/app/ohmycoins-prod-alb/...
```

**WAF Rules (waf-rules.json):**

```json
[
  {
    "Name": "AWSManagedRulesCommonRuleSet",
    "Priority": 1,
    "Statement": {
      "ManagedRuleGroupStatement": {
        "VendorName": "AWS",
        "Name": "AWSManagedRulesCommonRuleSet"
      }
    },
    "OverrideAction": {"None": {}},
    "VisibilityConfig": {
      "SampledRequestsEnabled": true,
      "CloudWatchMetricsEnabled": true,
      "MetricName": "AWSManagedRulesCommonRuleSetMetric"
    }
  },
  {
    "Name": "AWSManagedRulesKnownBadInputsRuleSet",
    "Priority": 2,
    "Statement": {
      "ManagedRuleGroupStatement": {
        "VendorName": "AWS",
        "Name": "AWSManagedRulesKnownBadInputsRuleSet"
      }
    },
    "OverrideAction": {"None": {}},
    "VisibilityConfig": {
      "SampledRequestsEnabled": true,
      "CloudWatchMetricsEnabled": true,
      "MetricName": "AWSManagedRulesKnownBadInputsRuleSetMetric"
    }
  },
  {
    "Name": "RateLimitRule",
    "Priority": 3,
    "Statement": {
      "RateBasedStatement": {
        "Limit": 2000,
        "AggregateKeyType": "IP"
      }
    },
    "Action": {"Block": {}},
    "VisibilityConfig": {
      "SampledRequestsEnabled": true,
      "CloudWatchMetricsEnabled": true,
      "MetricName": "RateLimitRuleMetric"
    }
  }
]
```

**Testing WAF Rules:**

```bash
# Test rate limiting
for i in {1..2100}; do
  curl -s https://api.ohmycoins.com/api/v1/health > /dev/null
done
# Should start getting 403 Forbidden after 2000 requests

# Monitor WAF metrics
aws cloudwatch get-metric-statistics \
    --namespace AWS/WAFV2 \
    --metric-name BlockedRequests \
    --dimensions Name=Region,Value=ap-southeast-2 Name=Rule,Value=ALL \
    --start-time 2025-11-20T00:00:00Z \
    --end-time 2025-11-20T23:59:59Z \
    --period 3600 \
    --statistics Sum
```

---

## Network Security

### 1. Kubernetes Network Policies

**Implementation:**

```bash
# Apply network policies
kubectl apply -f infrastructure/aws/eks/security/network-policies.yml

# Verify policies
kubectl get networkpolicies -A

# Test connectivity (should be blocked)
kubectl run test-pod --image=busybox --rm -it --restart=Never -- sh
# Inside pod:
wget -O- http://backend:8000/api/v1/health
# Should timeout if not allowed by policy
```

### 2. Security Group Hardening

**Review and Update Security Groups:**

```bash
# List all security groups
aws ec2 describe-security-groups \
    --filters "Name=tag:Environment,Values=production" \
    --region ap-southeast-2

# Review rules for each security group
# Ensure:
# - No 0.0.0.0/0 on sensitive ports (except 80/443 for ALB)
# - Minimal egress rules
# - Clear descriptions for each rule
```

**Example Security Group Review Checklist:**

- [ ] ALB Security Group: Allow 80/443 from 0.0.0.0/0, egress to ECS tasks only
- [ ] ECS Security Group: Allow traffic from ALB only, egress to RDS/Redis/Internet
- [ ] RDS Security Group: Allow 5432 from ECS only, no egress
- [ ] Redis Security Group: Allow 6379 from ECS only, no egress
- [ ] EKS Node Security Group: Allow required Kubernetes ports, minimal egress

---

## Backup and Disaster Recovery

### 1. RDS Automated Backups

**Verify Backup Configuration:**

```bash
# Check RDS backup settings
aws rds describe-db-instances \
    --db-instance-identifier ohmycoins-prod \
    --query 'DBInstances[0].{BackupRetention:BackupRetentionPeriod,Window:PreferredBackupWindow,MultiAZ:MultiAZ}' \
    --region ap-southeast-2

# Expected output:
# {
#   "BackupRetention": 30,
#   "Window": "03:00-04:00",
#   "MultiAZ": true
# }
```

**Manual Snapshot:**

```bash
# Create manual snapshot
aws rds create-db-snapshot \
    --db-instance-identifier ohmycoins-prod \
    --db-snapshot-identifier ohmycoins-prod-manual-snapshot-$(date +%Y%m%d) \
    --region ap-southeast-2
```

### 2. Disaster Recovery Testing

**Test RDS Restore (in non-production):**

```bash
# Restore from snapshot to test instance
aws rds restore-db-instance-from-db-snapshot \
    --db-instance-identifier ohmycoins-dr-test \
    --db-snapshot-identifier ohmycoins-prod-manual-snapshot-20251120 \
    --db-instance-class db.t3.small \
    --region ap-southeast-2

# Verify data integrity
# Connect to restored instance and run data validation queries

# Delete test instance after validation
aws rds delete-db-instance \
    --db-instance-identifier ohmycoins-dr-test \
    --skip-final-snapshot \
    --region ap-southeast-2
```

**Document Recovery Procedures:**

- Recovery Time Objective (RTO): 4 hours
- Recovery Point Objective (RPO): 24 hours
- Backup testing schedule: Monthly
- Full DR drill: Quarterly

---

## Security Audit Checklist

### Pre-Production Security Audit

**Infrastructure:**
- [ ] All resources tagged appropriately
- [ ] Deletion protection enabled on critical resources (RDS, ALB)
- [ ] All data encrypted at rest (RDS, Redis, S3, EBS)
- [ ] All data encrypted in transit (TLS everywhere)
- [ ] VPC Flow Logs enabled
- [ ] Security groups follow least privilege
- [ ] Network policies implemented in Kubernetes
- [ ] No public subnets for application/database resources

**IAM and Access:**
- [ ] Root account MFA enabled
- [ ] No long-lived IAM credentials in code
- [ ] IAM roles use least privilege policies
- [ ] OIDC authentication for GitHub Actions
- [ ] Secrets stored in AWS Secrets Manager
- [ ] Regular credential rotation policy

**Monitoring and Logging:**
- [ ] GuardDuty enabled
- [ ] CloudTrail enabled with log file validation
- [ ] AWS Config enabled with compliance rules
- [ ] CloudWatch alarms configured for critical metrics
- [ ] Prometheus/Grafana monitoring operational
- [ ] Log retention policies configured (90+ days)

**Application Security:**
- [ ] WAF enabled on production ALB
- [ ] Rate limiting configured
- [ ] CORS properly configured
- [ ] Input validation on all API endpoints
- [ ] No sensitive data in logs
- [ ] Dependency vulnerability scanning enabled

**Backup and DR:**
- [ ] RDS automated backups configured (30 days)
- [ ] Manual snapshots taken before major changes
- [ ] Disaster recovery procedures documented
- [ ] Recovery testing completed successfully
- [ ] Cross-region backup replication considered

**Compliance:**
- [ ] All audit requirements met
- [ ] Security documentation up to date
- [ ] Incident response plan documented
- [ ] Security contact information configured

---

## Compliance and Monitoring

### Ongoing Security Monitoring

**Daily:**
- Review GuardDuty findings
- Check CloudWatch alarms
- Monitor WAF blocked requests

**Weekly:**
- Review AWS Config compliance dashboard
- Analyze CloudTrail logs for suspicious activity
- Review security group changes

**Monthly:**
- Security patch review and application
- Access review (IAM users/roles)
- Test disaster recovery procedures
- Review and update security documentation

**Quarterly:**
- Full security audit
- Penetration testing (if applicable)
- Full disaster recovery drill
- Security training for team

---

## Emergency Response

### Incident Response Procedures

**1. Detect:**
- GuardDuty alerts
- CloudWatch alarms
- Manual discovery

**2. Assess:**
- Severity: Critical, High, Medium, Low
- Impact: Data breach, service disruption, unauthorized access
- Scope: Affected resources

**3. Contain:**
- Isolate affected resources (modify security groups)
- Disable compromised credentials
- Enable additional logging

**4. Investigate:**
- Review CloudTrail logs
- Analyze GuardDuty findings
- Check application logs

**5. Remediate:**
- Remove malicious resources
- Patch vulnerabilities
- Restore from clean backups if needed

**6. Recover:**
- Verify system integrity
- Restore normal operations
- Monitor for recurrence

**7. Post-Incident:**
- Document incident
- Update runbooks
- Implement preventive measures

**Emergency Contacts:**
- Security Team: security@ohmycoins.com
- On-Call Engineer: [PagerDuty/Phone]
- AWS Support: [Support Plan Contact]

---

## Appendix: Security Tools and Commands

### Useful Security Commands

```bash
# Check for exposed secrets
git secrets --scan

# Scan dependencies for vulnerabilities
npm audit
pip-audit

# Check Docker image for vulnerabilities
trivy image ghcr.io/marklimmage/ohmycoins-backend:latest

# Review IAM permissions
aws iam get-account-authorization-details

# List all public S3 buckets
aws s3api list-buckets --query 'Buckets[*].Name' | \
  xargs -I {} aws s3api get-bucket-acl --bucket {}

# Check for unused security groups
aws ec2 describe-security-groups --query 'SecurityGroups[?IpPermissions==`[]`]'
```

---

**Last Updated:** 2025-11-20  
**Next Review:** 2025-12-20  
**Owner:** Developer C (Infrastructure & DevOps)
