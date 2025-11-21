# Security Configuration for Oh My Coins EKS Cluster
**Last Updated:** 2025-11-20  
**Sprint:** Weeks 9-10  
**Owner:** Developer C (Infrastructure & DevOps)

---

## Overview

This directory contains security configuration files and documentation for hardening the Oh My Coins Kubernetes cluster and AWS infrastructure.

**Security Approach:**
- Defense-in-depth with multiple security layers
- Principle of least privilege for all access
- Continuous monitoring and threat detection
- Automated compliance checking
- Comprehensive audit logging

---

## Directory Contents

### Configuration Files

| File | Purpose | Apply When |
|------|---------|------------|
| `network-policies.yml` | Kubernetes network policies implementing micro-segmentation | After deploying applications |

### Documentation

| File | Purpose | Target Audience |
|------|---------|----------------|
| `SECURITY_HARDENING.md` | Comprehensive security hardening guide | DevOps, Security Team |
| `README.md` | This file - security overview | All team members |

---

## Quick Start

### 1. Apply Network Policies

```bash
# After deploying applications to the cluster
kubectl apply -f network-policies.yml

# Verify policies are active
kubectl get networkpolicies -A

# Test connectivity (optional)
kubectl run test-pod --image=busybox --rm -it --restart=Never -- sh
# Inside pod, test: wget -O- http://backend:8000/api/v1/health
```

### 2. Implement AWS Security Services

Follow the steps in `SECURITY_HARDENING.md` to enable:
- AWS GuardDuty (threat detection)
- AWS CloudTrail (audit logging)
- AWS Config (compliance monitoring)
- AWS WAF (web application firewall)

### 3. Verify Security Posture

```bash
# Check network policies
kubectl get networkpolicies -A
kubectl describe networkpolicy backend-api-policy -n default

# Verify GuardDuty is enabled
aws guardduty list-detectors --region ap-southeast-2

# Verify CloudTrail is logging
aws cloudtrail get-trail-status --name ohmycoins-production

# Check WAF is protecting ALB
aws wafv2 list-web-acls --scope REGIONAL --region ap-southeast-2
```

---

## Security Layers

### Layer 1: Network Security

**Kubernetes Network Policies:**
- Default deny all ingress traffic
- Explicit allow rules for necessary communication
- Separate policies for backend, collectors, and agents
- Monitoring namespace policies for Prometheus/Grafana

**AWS Security Groups:**
- Least privilege rules
- No 0.0.0.0/0 access except ALB (80/443)
- Minimal egress rules
- Clear descriptions for each rule

**Reference:** `network-policies.yml`

### Layer 2: Application Security

**Web Application Firewall (WAF):**
- OWASP Top 10 protection
- Known bad inputs detection
- Rate limiting (2000 req/min per IP)
- Custom rules for application-specific threats

**API Security:**
- HTTPS/TLS everywhere
- JWT authentication
- CORS properly configured
- Input validation on all endpoints

**Reference:** `SECURITY_HARDENING.md` - WAF section

### Layer 3: Data Security

**Encryption at Rest:**
- RDS PostgreSQL with KMS encryption
- ElastiCache Redis with encryption
- EBS volumes encrypted
- S3 buckets with server-side encryption

**Encryption in Transit:**
- TLS 1.2+ for all connections
- mTLS between microservices (optional)
- VPN or PrivateLink for admin access

**Reference:** Production Terraform configuration

### Layer 4: Access Control

**IAM Policies:**
- Least privilege roles
- No long-lived credentials
- OIDC for GitHub Actions
- Regular access reviews

**Kubernetes RBAC:**
- Namespace isolation
- Role-based access control
- Service account tokens
- Pod security policies

**Reference:** Terraform IAM module

### Layer 5: Monitoring and Detection

**Threat Detection:**
- AWS GuardDuty for continuous threat monitoring
- Anomaly detection on logs and metrics
- Real-time alerting for critical threats

**Audit Logging:**
- AWS CloudTrail for all API calls
- VPC Flow Logs for network traffic
- Application logs aggregated in Loki
- 90-day retention minimum

**Compliance Monitoring:**
- AWS Config for resource compliance
- Automated compliance checks
- Regular security audits
- Compliance dashboards

**Reference:** `SECURITY_HARDENING.md` - Monitoring section

---

## Security Checklist

### Pre-Production Security Audit

**Infrastructure Security:**
- [ ] All data encrypted at rest
- [ ] All data encrypted in transit (TLS)
- [ ] VPC Flow Logs enabled
- [ ] Security groups follow least privilege
- [ ] Network policies applied
- [ ] Deletion protection on critical resources

**Access Control:**
- [ ] Root account MFA enabled
- [ ] No long-lived credentials in code
- [ ] IAM roles use least privilege
- [ ] OIDC authentication for CI/CD
- [ ] Secrets in AWS Secrets Manager

**Monitoring:**
- [ ] GuardDuty enabled and configured
- [ ] CloudTrail enabled with validation
- [ ] AWS Config enabled with rules
- [ ] CloudWatch alarms configured
- [ ] Prometheus/Grafana operational

**Application Security:**
- [ ] WAF enabled on ALB
- [ ] Rate limiting configured
- [ ] CORS properly configured
- [ ] Input validation implemented
- [ ] Dependencies scanned for vulnerabilities

**Backup and DR:**
- [ ] Automated backups configured (30 days)
- [ ] Manual snapshots before changes
- [ ] DR procedures documented and tested
- [ ] Recovery time objective (RTO) met
- [ ] Recovery point objective (RPO) met

---

## Common Security Tasks

### Adding a New Application

1. Create deployment manifest with security context
2. Update network policies to allow necessary traffic
3. Add ServiceMonitor for Prometheus
4. Configure resource limits
5. Enable security scanning in CI/CD

### Investigating Security Alerts

1. Check GuardDuty findings in AWS Console
2. Review CloudTrail logs for suspicious API calls
3. Check application logs in Loki
4. Analyze network traffic in VPC Flow Logs
5. Follow incident response procedures

### Regular Security Maintenance

**Daily:**
- Review GuardDuty findings
- Check CloudWatch alarms
- Monitor WAF blocked requests

**Weekly:**
- Review AWS Config compliance
- Analyze CloudTrail for anomalies
- Review security group changes

**Monthly:**
- Update security patches
- Access review (IAM users/roles)
- Test disaster recovery
- Update security documentation

**Quarterly:**
- Full security audit
- Penetration testing
- DR drill (full restore)
- Security training

---

## Security Incident Response

### Severity Levels

**Critical:**
- Active data breach
- Root account compromise
- Ransomware/crypto-mining detected
- **Response:** Immediate (<15 min)

**High:**
- Unauthorized access attempts
- Suspicious API calls
- GuardDuty High severity findings
- **Response:** Within 1 hour

**Medium:**
- GuardDuty Medium severity findings
- Unusual traffic patterns
- Failed authentication attempts
- **Response:** Within 4 hours

**Low:**
- GuardDuty Low severity findings
- Minor policy violations
- **Response:** Within 24 hours

### Response Procedures

1. **Detect** - GuardDuty alert, CloudWatch alarm, manual discovery
2. **Assess** - Severity, impact, scope
3. **Contain** - Isolate affected resources, disable credentials
4. **Investigate** - Review logs, analyze behavior
5. **Remediate** - Remove threats, patch vulnerabilities
6. **Recover** - Restore normal operations, monitor
7. **Post-Incident** - Document, update runbooks, prevent recurrence

**Reference:** `SECURITY_HARDENING.md` - Emergency Response section

---

## Security Contacts

**Security Team:** security@ohmycoins.com  
**On-Call Engineer:** [PagerDuty/Phone]  
**AWS Support:** [Support Plan Contact]  
**Emergency Escalation:** [Management Contact]

---

## Additional Resources

### Internal Documentation
- `SECURITY_HARDENING.md` - Detailed hardening procedures
- `../PRODUCTION_DEPLOYMENT_RUNBOOK.md` - Production deployment
- `../../terraform/OPERATIONS_RUNBOOK.md` - Day-to-day operations
- `../../terraform/TROUBLESHOOTING.md` - Common issues

### External Resources
- [AWS Well-Architected Framework - Security Pillar](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/)
- [Kubernetes Security Best Practices](https://kubernetes.io/docs/concepts/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks)

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-11-20 | Initial security configuration created | Developer C |
| 2025-11-20 | Network policies implemented | Developer C |
| 2025-11-20 | Security hardening guide created | Developer C |

---

**Last Updated:** 2025-11-20  
**Next Review:** 2025-12-20  
**Owner:** Developer C (Infrastructure & DevOps)
