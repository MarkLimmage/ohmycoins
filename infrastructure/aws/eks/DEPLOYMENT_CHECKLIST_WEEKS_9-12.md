# Deployment Checklist - Weeks 9-12
# Developer C: Application Deployment & Production Preparation

**Sprint Duration:** Weeks 9-12 (4 weeks)  
**Objective:** Deploy all applications to staging, prepare production environment, implement security hardening  
**Last Updated:** 2025-11-21

---

## Overview

This checklist provides a step-by-step guide for completing Weeks 9-12 of the infrastructure track. All manifests, scripts, and documentation have been prepared in Weeks 7-8. This sprint focuses on actual deployment and production preparation.

## Prerequisites

Before starting this sprint, verify the following:

- [x] Weeks 1-8 complete (infrastructure, manifests, scripts, documentation)
- [ ] AWS credentials configured with appropriate permissions
- [ ] kubectl configured to access OMC-test EKS cluster
- [ ] Helm installed (version 3.x)
- [ ] Docker images built and pushed to ECR
- [ ] Database and Redis endpoints available

---

## Week 9: Monitoring Stack Deployment

### 9.1 Pre-Deployment Verification (Day 1)

```bash
# Verify EKS cluster access
kubectl cluster-info
kubectl get nodes

# Expected: 1+ nodes in Ready state
# Expected: OMC-test cluster information
```

**Checklist:**
- [ ] EKS cluster accessible
- [ ] At least 1 node in Ready state
- [ ] kubectl context set to OMC-test cluster
- [ ] Cluster version compatible (1.28+)

### 9.2 Create Monitoring Namespace (Day 1)

```bash
# Create monitoring namespace (if not exists)
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# Verify namespace creation
kubectl get namespace monitoring
```

**Checklist:**
- [ ] Monitoring namespace created
- [ ] Namespace is Active

### 9.3 Deploy Prometheus Operator (Day 1-2)

```bash
# Deploy Prometheus Operator
kubectl apply -f infrastructure/aws/eks/monitoring/prometheus-operator.yml

# Wait for Prometheus to be ready
kubectl wait --for=condition=ready pod -l app=prometheus -n monitoring --timeout=300s

# Verify Prometheus deployment
kubectl get pods -n monitoring -l app=prometheus
kubectl get svc -n monitoring -l app=prometheus
```

**Checklist:**
- [ ] Prometheus pod running (1/1 Ready)
- [ ] Prometheus service created
- [ ] Prometheus metrics endpoint accessible
- [ ] Prometheus discovering targets

**Troubleshooting:**
- If pod not ready, check logs: `kubectl logs -n monitoring -l app=prometheus`
- If service discovery issues, verify RBAC: `kubectl get clusterrole prometheus -o yaml`

### 9.4 Deploy Grafana (Day 2)

```bash
# Deploy Grafana
kubectl apply -f infrastructure/aws/eks/monitoring/grafana.yml

# Wait for Grafana to be ready
kubectl wait --for=condition=ready pod -l app=grafana -n monitoring --timeout=300s

# Get Grafana LoadBalancer URL
kubectl get svc grafana -n monitoring

# Wait for external IP (may take 2-5 minutes)
kubectl get svc grafana -n monitoring -w
```

**Checklist:**
- [ ] Grafana pod running (1/1 Ready)
- [ ] Grafana LoadBalancer service created
- [ ] External hostname/IP assigned
- [ ] Grafana accessible at http://<EXTERNAL-IP>
- [ ] Default credentials work (admin/admin)
- [ ] Prometheus datasource configured

**Important:**
- Save Grafana URL: `_____________________`
- Change default password immediately
- Document new admin credentials in secure location

### 9.5 Deploy Loki and Promtail (Day 2-3)

```bash
# Deploy Loki stack (Loki + Promtail)
kubectl apply -f infrastructure/aws/eks/monitoring/loki-stack.yml

# Wait for Loki to be ready
kubectl wait --for=condition=ready pod -l app=loki -n monitoring --timeout=300s

# Verify Promtail DaemonSet
kubectl get daemonset promtail -n monitoring
kubectl get pods -n monitoring -l app=promtail
```

**Checklist:**
- [ ] Loki pod running (1/1 Ready)
- [ ] Promtail DaemonSet created
- [ ] Promtail pods running on all nodes
- [ ] Loki service accessible
- [ ] Logs being ingested (check Loki datasource in Grafana)

**Verification:**
```bash
# Test log query in Grafana
# Query: {namespace="monitoring"}
# Should return logs from monitoring namespace
```

### 9.6 Deploy AlertManager (Day 3)

```bash
# Deploy AlertManager configuration
kubectl apply -f infrastructure/aws/eks/monitoring/alertmanager-config.yml

# Wait for AlertManager to be ready
kubectl wait --for=condition=ready pod -l app=alertmanager -n monitoring --timeout=300s

# Verify AlertManager
kubectl get pods -n monitoring -l app=alertmanager
kubectl get svc -n monitoring -l app=alertmanager
```

**Checklist:**
- [ ] AlertManager pod running (1/1 Ready)
- [ ] AlertManager service created
- [ ] AlertManager accessible (port-forward if needed)
- [ ] Alert routing configured

### 9.7 Apply Alert Rules (Day 3)

```bash
# Apply alert rules
kubectl apply -f infrastructure/aws/eks/monitoring/alert-rules.yml

# Verify PrometheusRule created
kubectl get prometheusrules -n monitoring
```

**Checklist:**
- [ ] PrometheusRule resource created
- [ ] 15+ alert rules loaded
- [ ] Rules visible in Prometheus UI (Alerts tab)
- [ ] Test alerts firing (check /alerts endpoint)

### 9.8 Create Monitoring Dashboards (Day 3-4)

**Manual Steps in Grafana:**

1. **Import Infrastructure Dashboard**
   - Go to Dashboards > Import
   - Upload: `infrastructure/aws/eks/monitoring/dashboards/infrastructure-dashboard.json` (if exists)
   - Or create dashboard with:
     - Node CPU usage
     - Node memory usage
     - Pod status
     - Network I/O

2. **Create Application Dashboards** (to be created in Week 10 after apps deployed)
   - Backend API dashboard
   - Collectors dashboard
   - Agents dashboard

**Checklist:**
- [ ] Infrastructure dashboard created
- [ ] Dashboard shows real-time metrics
- [ ] Dashboard saved and persisted

### 9.9 Week 9 Verification (Day 4-5)

**Final Verification:**

```bash
# Check all monitoring components
kubectl get all -n monitoring

# Expected:
# - 1 Prometheus pod
# - 1 Grafana pod
# - 1 Loki pod
# - N Promtail pods (one per node)
# - 1 AlertManager pod
# - All services created
```

**Checklist:**
- [ ] All monitoring pods running
- [ ] All services created
- [ ] Grafana accessible via LoadBalancer
- [ ] Prometheus collecting metrics
- [ ] Loki collecting logs
- [ ] AlertManager receiving alerts
- [ ] Documentation updated with endpoints

**Week 9 Deliverables:**
- [ ] Monitoring stack fully operational
- [ ] Grafana URL documented
- [ ] Admin credentials changed and documented
- [ ] Alert rules verified
- [ ] Monitoring README updated

---

## Week 10: Application Deployment

### 10.1 Pre-Deployment Preparation (Day 1)

**Gather Required Information:**

1. **RDS Database Endpoint:**
   ```bash
   aws rds describe-db-instances \
     --db-instance-identifier omc-staging-db \
     --query 'DBInstances[0].Endpoint.Address' \
     --output text
   ```
   Save: `_____________________`

2. **ElastiCache Redis Endpoint:**
   ```bash
   aws elasticache describe-cache-clusters \
     --cache-cluster-id omc-staging-redis \
     --show-cache-node-info \
     --query 'CacheClusters[0].CacheNodes[0].Endpoint.Address' \
     --output text
   ```
   Save: `_____________________`

3. **ECR Image URIs:**
   ```bash
   # Backend image
   aws ecr describe-repositories --repository-names ohmycoins/backend --query 'repositories[0].repositoryUri'
   
   # Get latest tag
   aws ecr describe-images --repository-name ohmycoins/backend --query 'sort_by(imageDetails,& imagePushedAt)[-1].imageTags[0]'
   ```
   Save: `_____________________:_____`

**Checklist:**
- [ ] RDS endpoint obtained
- [ ] Redis endpoint obtained
- [ ] ECR images available
- [ ] Image tags identified

### 10.2 Update Configuration Files (Day 1)

**Backend ConfigMap:**

Edit `infrastructure/aws/eks/applications/backend/deployment.yml`:

```yaml
# Line 21: Update POSTGRES_SERVER
POSTGRES_SERVER: "<YOUR-RDS-ENDPOINT>"

# Line 25: Update REDIS_HOST  
REDIS_HOST: "<YOUR-REDIS-ENDPOINT>"
```

**Backend Secrets:**

```yaml
# Generate secure keys
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Update lines 40-44 with generated values
```

**Checklist:**
- [ ] RDS endpoint updated in ConfigMap
- [ ] Redis endpoint updated in ConfigMap
- [ ] Secure passwords generated
- [ ] SECRET_KEY generated (32+ characters)
- [ ] ENCRYPTION_KEY generated (Fernet key)
- [ ] Changes saved

### 10.3 Create Application Namespace (Day 1)

```bash
# Create namespace
kubectl create namespace omc-staging --dry-run=client -o yaml | kubectl apply -f -

# Verify
kubectl get namespace omc-staging
```

**Checklist:**
- [ ] omc-staging namespace created
- [ ] Namespace is Active

### 10.4 Deploy Backend API (Day 1-2)

```bash
# Deploy backend (includes namespace, configmap, secrets, deployment, service, HPA)
kubectl apply -f infrastructure/aws/eks/applications/backend/deployment.yml

# Wait for backend to be ready
kubectl wait --for=condition=ready pod -l app=backend -n omc-staging --timeout=300s

# Check deployment status
kubectl get pods -n omc-staging -l app=backend
kubectl get svc -n omc-staging -l app=backend
kubectl get hpa -n omc-staging -l app=backend
```

**Checklist:**
- [ ] Backend pod running (2/2 Ready by default)
- [ ] Backend service created
- [ ] HPA created and monitoring
- [ ] Pods can connect to database
- [ ] Pods can connect to Redis

**Verification:**

```bash
# Port-forward to backend
kubectl port-forward -n omc-staging svc/backend 8000:8000

# Test health endpoint (in another terminal)
curl http://localhost:8000/api/v1/health

# Expected: {"status": "healthy"}
```

### 10.5 Deploy Backend Ingress (Day 2)

```bash
# Deploy ALB Ingress
kubectl apply -f infrastructure/aws/eks/applications/backend/ingress.yml

# Wait for ALB to provision (5-10 minutes)
kubectl get ingress -n omc-staging -w

# Get ALB hostname
kubectl get ingress backend-ingress -n omc-staging -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

**Checklist:**
- [ ] Ingress resource created
- [ ] ALB provisioned (check AWS console)
- [ ] External hostname assigned
- [ ] Health checks passing
- [ ] API accessible via ALB

**Save ALB URL:** `_____________________`

### 10.6 Deploy Phase 2.5 Collectors (Day 2-3)

**Update Collector ConfigMap (if needed):**

Edit `infrastructure/aws/eks/applications/collectors/cronjobs.yml`:
- Verify image URIs
- Verify schedules

**Deploy Collectors:**

```bash
# Deploy all collectors (3 CronJobs + 2 Deployments)
kubectl apply -f infrastructure/aws/eks/applications/collectors/cronjobs.yml

# Verify CronJobs
kubectl get cronjobs -n omc-staging

# Verify Deployments
kubectl get deployments -n omc-staging | grep collector

# Check pods
kubectl get pods -n omc-staging -l component=collector
```

**Checklist:**
- [ ] DeFiLlama CronJob created (schedule: `0 2 * * *`)
- [ ] SEC API CronJob created (schedule: `0 3 * * *`)
- [ ] CoinSpot Announcements CronJob created (schedule: `0 * * * *`)
- [ ] Reddit Deployment created (1/1 Ready)
- [ ] CryptoPanic Deployment created (1/1 Ready)

**Test Collectors:**

```bash
# Manually trigger a CronJob to test
kubectl create job --from=cronjob/defillama-collector test-defillama -n omc-staging

# Watch job completion
kubectl get jobs -n omc-staging -w

# Check job logs
kubectl logs -n omc-staging job/test-defillama

# Clean up test job
kubectl delete job test-defillama -n omc-staging
```

**Verification:**
- [ ] Test job completed successfully
- [ ] Logs show data collection
- [ ] Data written to database
- [ ] No errors in logs

### 10.7 Deploy Phase 3 Agentic System (Day 3-4)

**Update Agent Configuration:**

Edit `infrastructure/aws/eks/applications/agents/deployment.yml`:
- Verify image URI
- Verify resource limits
- Ensure PVC storage class available

**Create Agent Secrets:**

```yaml
# Add OpenAI and Anthropic API keys to agent-secrets
# Either edit the file or create from command line:

kubectl create secret generic agent-secrets \
  --from-literal=OPENAI_API_KEY="sk-..." \
  --from-literal=ANTHROPIC_API_KEY="sk-ant-..." \
  -n omc-staging \
  --dry-run=client -o yaml | kubectl apply -f -
```

**Deploy Agents:**

```bash
# Deploy agentic system
kubectl apply -f infrastructure/aws/eks/applications/agents/deployment.yml

# Wait for agents to be ready
kubectl wait --for=condition=ready pod -l app=agents -n omc-staging --timeout=300s

# Check deployment
kubectl get pods -n omc-staging -l app=agents
kubectl get svc -n omc-staging -l app=agents
kubectl get pvc -n omc-staging -l app=agents
kubectl get hpa -n omc-staging -l app=agents
```

**Checklist:**
- [ ] Agent pods running (2/2 Ready by default)
- [ ] Agent service created
- [ ] PVC created and bound
- [ ] HPA created and monitoring
- [ ] Pods can access LLM APIs
- [ ] Pods can connect to database and Redis

**Test Agents:**

```bash
# Port-forward to agent service
kubectl port-forward -n omc-staging svc/agents 8001:8000

# Test agent health (in another terminal)
curl http://localhost:8001/api/v1/health

# Test agent session creation
curl -X POST http://localhost:8001/api/v1/lab/agent/sessions \
  -H "Content-Type: application/json" \
  -d '{"goal": "Analyze BTC price trends"}'
```

### 10.8 Configure ServiceMonitors (Day 4)

```bash
# Deploy ServiceMonitors for Prometheus integration
kubectl apply -f infrastructure/aws/eks/applications/servicemonitor.yml

# Verify ServiceMonitors
kubectl get servicemonitors -n omc-staging

# Check Prometheus targets (port-forward Prometheus and visit /targets)
kubectl port-forward -n monitoring svc/prometheus 9090:9090

# Visit http://localhost:9090/targets
# Expected: backend, collectors, agents targets showing "UP"
```

**Checklist:**
- [ ] ServiceMonitors created
- [ ] Prometheus scraping targets
- [ ] Metrics visible in Prometheus
- [ ] All targets showing "UP" status

### 10.9 Create Application Dashboards (Day 4-5)

**In Grafana, create dashboards for:**

1. **Backend API Dashboard:**
   - Request rate (requests/sec)
   - Response time (p50, p95, p99)
   - Error rate (%)
   - Active connections
   - Database query performance

2. **Collectors Dashboard:**
   - Collection job success rate
   - Records collected per collector
   - Collection latency
   - Failed collections (alerts)

3. **Agentic System Dashboard:**
   - Active agent sessions
   - Workflow completion rate
   - Agent tool execution metrics
   - LLM API usage and latency

**Checklist:**
- [ ] Backend API dashboard created
- [ ] Collectors dashboard created
- [ ] Agentic system dashboard created
- [ ] Dashboards showing real-time data

### 10.10 Week 10 Verification (Day 5)

**End-to-End Integration Test:**

1. **Data Collection:**
   ```bash
   # Check collector pods are running
   kubectl get pods -n omc-staging -l component=collector
   
   # Check recent data in database (requires database access)
   # Or check logs
   kubectl logs -n omc-staging -l component=collector --tail=50
   ```

2. **Backend API:**
   ```bash
   # Test data retrieval via API
   curl http://<ALB-URL>/api/v1/health
   curl http://<ALB-URL>/api/v1/coins
   ```

3. **Agentic System:**
   ```bash
   # Test agent session creation and execution
   # (Use Postman or curl)
   ```

**Final Checklist:**
- [ ] All pods running (backend, collectors, agents)
- [ ] All services accessible
- [ ] Data flowing: Collectors → Database → Backend API
- [ ] Agents can access data and execute workflows
- [ ] Monitoring capturing all metrics
- [ ] Logs aggregated in Loki
- [ ] Dashboards showing data
- [ ] No critical errors in any pods

**Week 10 Deliverables:**
- [ ] Backend API deployed and accessible
- [ ] All 5 collectors operational
- [ ] Agentic system deployed and functional
- [ ] ServiceMonitors configured
- [ ] Application dashboards created
- [ ] Integration testing passed
- [ ] Documentation updated

---

## Week 11: Production Environment Preparation

### 11.1 Production Infrastructure Deployment (Day 1-2)

**Update Production Terraform Variables:**

Edit `infrastructure/terraform/environments/production/terraform.tfvars`:

```hcl
# Verify all settings for production:
# - Multi-AZ deployment
# - Larger instance sizes
# - Automated backups enabled
# - Enhanced monitoring
```

**Deploy Production Infrastructure:**

```bash
cd infrastructure/terraform/environments/production

# Initialize Terraform
terraform init

# Plan deployment
terraform plan -out=production.tfplan

# Review plan carefully!
# Verify:
# - RDS is Multi-AZ
# - Redis has replication
# - NAT Gateways in multiple AZs
# - Appropriate instance sizes

# Apply plan
terraform apply production.tfplan

# Wait for completion (~20-30 minutes)
```

**Checklist:**
- [ ] Production tfvars reviewed
- [ ] Terraform plan reviewed
- [ ] Production infrastructure deployed
- [ ] RDS endpoint obtained
- [ ] Redis endpoint obtained
- [ ] ALB endpoint obtained
- [ ] All resources tagged correctly

**Save Production Endpoints:**
- RDS: `_____________________`
- Redis: `_____________________`
- ALB: `_____________________`

### 11.2 DNS Configuration (Day 2)

**Route53 Setup:**

```bash
# Create hosted zone (if not exists)
aws route53 create-hosted-zone \
  --name ohmycoins.com \
  --caller-reference $(date +%s)

# Create A record for API (alias to ALB)
# (Use AWS Console or Terraform for Route53 records)
```

**DNS Records to Create:**
- `api.ohmycoins.com` → Production ALB
- `app.ohmycoins.com` → Production Frontend (future)
- `grafana.ohmycoins.com` → Grafana LoadBalancer (optional)

**Checklist:**
- [ ] Hosted zone created/verified
- [ ] DNS records created
- [ ] DNS propagation verified (dig/nslookup)
- [ ] TTL set appropriately

### 11.3 SSL Certificate Setup (Day 2-3)

**Request ACM Certificate:**

```bash
# Request certificate via AWS Certificate Manager
aws acm request-certificate \
  --domain-name ohmycoins.com \
  --subject-alternative-names "*.ohmycoins.com" \
  --validation-method DNS \
  --region ap-southeast-2

# Note the CertificateArn
```

**Validate Certificate:**

```bash
# Get validation records
aws acm describe-certificate \
  --certificate-arn <ARN> \
  --region ap-southeast-2

# Add CNAME validation records to Route53
# (Use AWS Console for easier validation)
```

**Update ALB Ingress:**

Edit production ingress manifest to use HTTPS with ACM certificate:

```yaml
metadata:
  annotations:
    alb.ingress.kubernetes.io/certificate-arn: <CERTIFICATE-ARN>
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'
    alb.ingress.kubernetes.io/ssl-redirect: '443'
```

**Checklist:**
- [ ] SSL certificate requested
- [ ] DNS validation completed
- [ ] Certificate issued
- [ ] Certificate ARN documented
- [ ] Ingress updated with certificate

### 11.4 WAF Configuration (Day 3)

**Create WAF Web ACL:**

```bash
# Use AWS Console to create WAF Web ACL
# Or use AWS CLI:

aws wafv2 create-web-acl \
  --name omc-production-waf \
  --scope REGIONAL \
  --region ap-southeast-2 \
  --default-action Block={} \
  --rules file://waf-rules.json
```

**WAF Rules to Include:**
1. AWS Managed Rules - Core Rule Set
2. AWS Managed Rules - Known Bad Inputs
3. Rate limiting (1000 requests per 5 minutes per IP)
4. Geo-blocking (if needed)

**Associate WAF with ALB:**

```bash
# Get ALB ARN
aws elbv2 describe-load-balancers \
  --names omc-production-alb \
  --query 'LoadBalancers[0].LoadBalancerArn'

# Associate WAF
aws wafv2 associate-web-acl \
  --web-acl-arn <WAF-ACL-ARN> \
  --resource-arn <ALB-ARN> \
  --region ap-southeast-2
```

**Checklist:**
- [ ] WAF Web ACL created
- [ ] Core rule set enabled
- [ ] Rate limiting configured
- [ ] WAF associated with production ALB
- [ ] WAF metrics visible in CloudWatch

### 11.5 Backup Configuration (Day 3-4)

**RDS Automated Backups:**

Verify in Terraform or AWS Console:
- Backup retention: 7 days (staging) / 30 days (production)
- Backup window: Off-peak hours
- Maintenance window: Off-peak hours
- Point-in-time recovery enabled

**Manual Snapshot:**

```bash
# Create manual snapshot for baseline
aws rds create-db-snapshot \
  --db-instance-identifier omc-production-db \
  --db-snapshot-identifier omc-production-baseline-$(date +%Y%m%d)
```

**EBS Snapshots (for PVCs):**

```bash
# If using EBS-backed PVCs, configure snapshot lifecycle
# (Can use AWS Data Lifecycle Manager)
```

**Checklist:**
- [ ] RDS automated backups configured
- [ ] Backup retention appropriate (7/30 days)
- [ ] Backup window set to off-peak hours
- [ ] Manual baseline snapshot created
- [ ] Snapshot lifecycle policy configured (if needed)

### 11.6 Disaster Recovery Procedures (Day 4)

**Create DR Runbook:**

Document procedures for:

1. **RDS Restore:**
   ```bash
   # Restore from automated backup
   aws rds restore-db-instance-to-point-in-time \
     --source-db-instance-identifier omc-production-db \
     --target-db-instance-identifier omc-production-db-restored \
     --restore-time <TIMESTAMP>
   ```

2. **Application Rollback:**
   ```bash
   # Using rollback script
   cd infrastructure/aws/eks/scripts
   ./rollback.sh production all
   ```

3. **Infrastructure Recreation:**
   - Terraform state backup location
   - Terraform apply from backup
   - DNS failover procedures

**Test DR Procedures (Optional but Recommended):**

- [ ] Test RDS restore to new instance
- [ ] Test application rollback
- [ ] Verify Terraform state backup
- [ ] Document recovery time objectives (RTO)

**Checklist:**
- [ ] DR runbook created
- [ ] RDS restore procedure documented
- [ ] Application rollback procedure documented
- [ ] Infrastructure recreation procedure documented
- [ ] DR contacts and escalation documented

### 11.7 Production Deployment Runbook (Day 4-5)

**Create Comprehensive Deployment Runbook:**

**File:** `infrastructure/aws/eks/PRODUCTION_DEPLOYMENT_RUNBOOK.md`

**Sections:**
1. Prerequisites checklist
2. Pre-deployment verification
3. Step-by-step deployment procedure
4. Post-deployment verification
5. Rollback procedure
6. Troubleshooting guide

**Key Procedures to Document:**
- Database migration process
- Zero-downtime deployment strategy
- Smoke testing procedure
- Monitoring validation
- Performance baseline

**Checklist:**
- [ ] Deployment runbook created
- [ ] Pre-deployment checklist complete
- [ ] Deployment steps documented
- [ ] Post-deployment verification documented
- [ ] Rollback steps documented
- [ ] Runbook reviewed by team

### 11.8 Production Access Procedures (Day 5)

**Document Access Control:**

1. **kubectl Access:**
   - How to update kubeconfig for production
   - RBAC roles and permissions
   - Access request procedure

2. **Database Access:**
   - Bastion host setup (if using)
   - Port-forwarding procedure
   - Read-only vs read-write access

3. **Monitoring Access:**
   - Grafana URL and credentials
   - Prometheus access
   - CloudWatch access

4. **AWS Console Access:**
   - IAM roles and policies
   - Access request procedure
   - MFA requirements

**Checklist:**
- [ ] kubectl access documented
- [ ] Database access documented
- [ ] Monitoring access documented
- [ ] AWS Console access documented
- [ ] Access request process documented

### 11.9 Week 11 Verification (Day 5)

**Production Readiness Checklist:**

**Infrastructure:**
- [ ] All Terraform modules deployed
- [ ] Multi-AZ RDS operational
- [ ] Multi-AZ Redis operational
- [ ] ALB operational with HTTPS
- [ ] DNS configured and validated
- [ ] SSL certificate issued and applied
- [ ] WAF configured and enabled

**Security:**
- [ ] Encryption at rest enabled (RDS, Redis)
- [ ] Encryption in transit enabled (TLS)
- [ ] Security groups configured (least privilege)
- [ ] IAM roles configured (least privilege)
- [ ] Secrets managed securely

**Backup & DR:**
- [ ] Automated backups configured
- [ ] Manual baseline snapshot created
- [ ] DR procedures documented
- [ ] Recovery tested (optional but recommended)

**Documentation:**
- [ ] Deployment runbook created
- [ ] Access procedures documented
- [ ] DR procedures documented
- [ ] All endpoints and credentials documented

**Week 11 Deliverables:**
- [ ] Production infrastructure deployed
- [ ] DNS and SSL configured
- [ ] WAF enabled
- [ ] Backups configured
- [ ] DR procedures documented
- [ ] Deployment runbook complete

---

## Week 12: Security Hardening & Finalization

### 12.1 AWS Config Setup (Day 1)

**Enable AWS Config:**

```bash
# Create S3 bucket for Config
aws s3 mb s3://omc-aws-config-<ACCOUNT-ID> --region ap-southeast-2

# Enable AWS Config
aws configservice put-configuration-recorder \
  --configuration-recorder name=omc-config-recorder,roleARN=<CONFIG-ROLE-ARN> \
  --recording-group allSupported=true,includeGlobalResourceTypes=true

# Start recorder
aws configservice start-configuration-recorder \
  --configuration-recorder-name omc-config-recorder
```

**Configure Config Rules:**

Rules to enable:
1. `rds-encryption-enabled` - Verify RDS encryption
2. `s3-bucket-public-read-prohibited` - No public S3 buckets
3. `iam-password-policy` - Strong password policy
4. `vpc-default-security-group-closed` - Default SG has no rules
5. `ec2-security-group-attached-to-eni` - All SGs attached
6. `elasticsearch-encrypted-at-rest` - ElastiCache encryption

**Checklist:**
- [ ] AWS Config enabled
- [ ] Config S3 bucket created
- [ ] Configuration recorder started
- [ ] 10+ Config rules enabled
- [ ] Compliance dashboard reviewed

### 12.2 GuardDuty Setup (Day 1)

**Enable GuardDuty:**

```bash
# Enable GuardDuty
aws guardduty create-detector \
  --enable \
  --finding-publishing-frequency FIFTEEN_MINUTES \
  --region ap-southeast-2
```

**Configure Findings Export:**

```bash
# Create S3 bucket for findings
aws s3 mb s3://omc-guardduty-findings-<ACCOUNT-ID>

# Configure export
aws guardduty create-publishing-destination \
  --detector-id <DETECTOR-ID> \
  --destination-type S3 \
  --destination-properties DestinationArn=arn:aws:s3:::omc-guardduty-findings-<ACCOUNT-ID>
```

**Set Up Alerts:**

Create SNS topic and CloudWatch Events rule to alert on GuardDuty findings:

```bash
# Create SNS topic
aws sns create-topic --name guardduty-alerts

# Create EventBridge rule (use AWS Console for easier setup)
```

**Checklist:**
- [ ] GuardDuty enabled
- [ ] Findings export configured
- [ ] SNS topic for alerts created
- [ ] EventBridge rule for high-severity findings
- [ ] Initial findings reviewed (expect some for new account)

### 12.3 CloudTrail Setup (Day 2)

**Enable CloudTrail:**

```bash
# Create S3 bucket for CloudTrail
aws s3 mb s3://omc-cloudtrail-<ACCOUNT-ID>

# Create CloudTrail
aws cloudtrail create-trail \
  --name omc-audit-trail \
  --s3-bucket-name omc-cloudtrail-<ACCOUNT-ID> \
  --is-multi-region-trail

# Enable logging
aws cloudtrail start-logging --name omc-audit-trail
```

**Configure CloudWatch Logs Integration:**

```bash
# Create CloudWatch log group
aws logs create-log-group --log-group-name /aws/cloudtrail/omc

# Update trail to send to CloudWatch
aws cloudtrail update-trail \
  --name omc-audit-trail \
  --cloud-watch-logs-log-group-arn <LOG-GROUP-ARN> \
  --cloud-watch-logs-role-arn <CLOUDTRAIL-ROLE-ARN>
```

**Create Metric Filters:**

Create filters for:
- Unauthorized API calls
- Root account usage
- IAM policy changes
- Security group changes
- Network ACL changes

**Checklist:**
- [ ] CloudTrail enabled
- [ ] Multi-region trail configured
- [ ] S3 bucket for logs created
- [ ] CloudWatch Logs integration enabled
- [ ] Metric filters created
- [ ] Alarms created for critical events

### 12.4 Kubernetes Network Policies (Day 2-3)

**Create Network Policies:**

**File:** `infrastructure/aws/eks/network-policies.yml`

```yaml
---
# Deny all ingress by default
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: omc-staging
spec:
  podSelector: {}
  policyTypes:
  - Ingress

---
# Allow backend to database and Redis
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-egress
  namespace: omc-staging
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Egress
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres  # If DB in cluster
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - podSelector:
        matchLabels:
          app: redis  # If Redis in cluster
    ports:
    - protocol: TCP
      port: 6379
  - to:  # Allow external access (RDS, ElastiCache, Internet)
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 5432
    - protocol: TCP
      port: 6379
    - protocol: TCP
      port: 443

---
# Additional policies for collectors and agents
# (Allow database and Redis access, deny pod-to-pod communication)
```

**Apply Network Policies:**

```bash
kubectl apply -f infrastructure/aws/eks/network-policies.yml

# Verify policies
kubectl get networkpolicies -n omc-staging

# Test policies (verify pods can still access DB/Redis but not each other)
```

**Checklist:**
- [ ] Default deny-all ingress policy created
- [ ] Backend egress policy created
- [ ] Collector egress policies created
- [ ] Agent egress policies created
- [ ] Policies tested and verified
- [ ] No unintended connectivity blocked

### 12.5 Security Audit (Day 3-4)

**Conduct Comprehensive Security Review:**

1. **Infrastructure Security:**
   - [ ] All databases have encryption at rest
   - [ ] All data in transit uses TLS
   - [ ] Security groups follow least privilege
   - [ ] IAM roles follow least privilege
   - [ ] No public S3 buckets
   - [ ] VPC Flow Logs enabled

2. **Application Security:**
   - [ ] Secrets managed via Kubernetes Secrets (or AWS Secrets Manager)
   - [ ] No hardcoded credentials in code
   - [ ] API authentication enabled
   - [ ] CORS configured correctly
   - [ ] Input validation in place
   - [ ] SQL injection protection (parameterized queries)

3. **Kubernetes Security:**
   - [ ] RBAC configured (least privilege)
   - [ ] Network policies in place
   - [ ] Pod Security Standards enforced
   - [ ] Container images scanned for vulnerabilities (Trivy)
   - [ ] No privileged containers
   - [ ] Resource limits set on all pods

4. **Monitoring & Logging:**
   - [ ] CloudTrail enabled
   - [ ] GuardDuty enabled
   - [ ] AWS Config enabled
   - [ ] Application logs aggregated
   - [ ] Security alerts configured
   - [ ] Log retention policies set

**Security Audit Checklist:**
- [ ] Infrastructure security review complete
- [ ] Application security review complete
- [ ] Kubernetes security review complete
- [ ] Monitoring & logging review complete
- [ ] No critical security issues found
- [ ] Medium/low issues documented and planned

### 12.6 Backup & Restore Testing (Day 4)

**Test RDS Backup Restore:**

```bash
# Restore RDS to test instance
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier omc-test-restore \
  --db-snapshot-identifier <SNAPSHOT-ID> \
  --db-instance-class db.t3.micro \
  --no-publicly-accessible

# Verify data integrity
# Connect to restored instance and verify data

# Clean up test instance
aws rds delete-db-instance \
  --db-instance-identifier omc-test-restore \
  --skip-final-snapshot
```

**Test Application Rollback:**

```bash
# Deploy test version
kubectl set image deployment/backend backend=<OLD-IMAGE> -n omc-staging

# Verify rollback
kubectl rollout status deployment/backend -n omc-staging

# Roll back to current version
kubectl rollout undo deployment/backend -n omc-staging
```

**Checklist:**
- [ ] RDS snapshot restore tested
- [ ] Restored data verified
- [ ] Application rollback tested
- [ ] Rollback time measured (RTO)
- [ ] Test resources cleaned up

### 12.7 Documentation Update (Day 4-5)

**Update All Documentation:**

1. **infrastructure/aws/eks/applications/README.md:**
   - Add actual endpoints (RDS, Redis, ALB)
   - Update configuration examples
   - Add troubleshooting section

2. **infrastructure/aws/eks/monitoring/README.md:**
   - Add Grafana URL
   - Add dashboard links
   - Update access procedures

3. **infrastructure/terraform/README.md:**
   - Add production deployment notes
   - Update cost estimates
   - Add architecture diagrams

4. **Create PRODUCTION_DEPLOYMENT_RUNBOOK.md:**
   - Complete deployment procedure
   - Include all checklists
   - Add rollback procedures

5. **Update DEVELOPER_C_SUMMARY.md:**
   - Add Weeks 9-12 summary
   - Document all deliverables
   - Update current status

**Checklist:**
- [ ] All README files updated
- [ ] Production runbook complete
- [ ] DEVELOPER_C_SUMMARY.md updated
- [ ] Architecture diagrams updated (if needed)
- [ ] All endpoints and credentials documented

### 12.8 Handoff Documentation (Day 5)

**Create Handoff Package:**

**File:** `infrastructure/HANDOFF_DOCUMENTATION.md`

**Contents:**
1. **System Overview:**
   - Architecture diagram
   - Component inventory
   - Technology stack

2. **Access Information:**
   - AWS Console access
   - kubectl access
   - Database access
   - Monitoring URLs

3. **Operational Procedures:**
   - Daily operations checklist
   - Weekly maintenance tasks
   - Monthly review tasks
   - Incident response procedures

4. **Contacts & Escalation:**
   - Team members and roles
   - On-call rotation
   - Escalation procedures
   - Vendor contacts

5. **Known Issues & Roadmap:**
   - Current limitations
   - Planned improvements
   - Technical debt
   - Future phases

**Checklist:**
- [ ] Handoff documentation created
- [ ] System overview complete
- [ ] Access information documented
- [ ] Operational procedures documented
- [ ] Contacts and escalation documented
- [ ] Known issues and roadmap documented

### 12.9 Final Sprint Review (Day 5)

**Complete Sprint Retrospective:**

**What Went Well:**
- Manifests created in Week 7-8 were production-ready
- Deployment scripts worked as expected
- Monitoring stack deployed smoothly
- Applications deployed successfully
- Production environment ready

**Challenges:**
- Configuration management (RDS/Redis endpoints)
- Secret management (need AWS Secrets Manager)
- Testing with limited staging resources
- Documentation updates time-consuming

**Lessons Learned:**
- Infrastructure-as-code saves time
- Comprehensive testing framework essential
- Documentation must be maintained throughout
- Automation reduces errors

**Future Improvements:**
- Implement AWS Secrets Manager
- Add GitOps workflow (ArgoCD/Flux)
- Implement service mesh (Istio/Linkerd)
- Multi-region deployment
- Advanced observability (tracing)

**Checklist:**
- [ ] Sprint retrospective completed
- [ ] Lessons learned documented
- [ ] Future improvements identified
- [ ] Feedback provided to team

### 12.10 Week 12 Final Verification

**Complete Infrastructure Audit:**

```bash
# Verify all components
kubectl get all --all-namespaces
kubectl get pvc --all-namespaces
kubectl get ingress --all-namespaces

# Check AWS resources
aws rds describe-db-instances
aws elasticache describe-cache-clusters
aws elbv2 describe-load-balancers

# Verify monitoring
# Access Grafana and check all dashboards

# Verify security
aws guardduty list-findings
aws config get-compliance-summary-by-resource-type
```

**Final Checklist:**

**Infrastructure:**
- [ ] Staging environment fully operational
- [ ] Production environment deployed and ready
- [ ] All services accessible
- [ ] DNS configured and working
- [ ] SSL certificates issued and applied

**Security:**
- [ ] AWS Config enabled and compliant
- [ ] GuardDuty enabled and monitoring
- [ ] CloudTrail enabled and logging
- [ ] Network policies in place
- [ ] Security audit completed (no critical issues)

**Monitoring:**
- [ ] Prometheus collecting metrics
- [ ] Grafana showing all dashboards
- [ ] Loki aggregating logs
- [ ] Alerts configured and tested
- [ ] All applications monitored

**Applications:**
- [ ] Backend API operational
- [ ] All 5 collectors running
- [ ] Agentic system functional
- [ ] End-to-end integration working

**Documentation:**
- [ ] All README files updated
- [ ] Deployment runbook complete
- [ ] DR procedures documented
- [ ] Handoff documentation complete
- [ ] DEVELOPER_C_SUMMARY.md updated

**Backup & DR:**
- [ ] Automated backups configured
- [ ] Backup restore tested
- [ ] DR procedures tested
- [ ] RTO/RPO documented

**Week 12 Deliverables:**
- [ ] Security hardening complete
- [ ] Backup/restore tested
- [ ] All documentation updated
- [ ] Handoff package complete
- [ ] Sprint completed successfully

---

## Sprint Summary

### Completion Metrics

**Week 9:**
- Monitoring stack deployed (5 components)
- All monitoring operational
- Grafana dashboards created

**Week 10:**
- Backend API deployed
- 5 collectors deployed and operational
- Agentic system deployed
- End-to-end integration verified

**Week 11:**
- Production infrastructure deployed
- DNS and SSL configured
- WAF enabled
- Backup and DR configured

**Week 12:**
- AWS Config enabled
- GuardDuty enabled
- CloudTrail enabled
- Network policies implemented
- Security audit completed
- All documentation updated

### Total Deliverables (Weeks 9-12)

**Infrastructure:**
- Monitoring stack (5 components)
- Backend API deployment
- 5 collector deployments
- Agentic system deployment
- Production environment (full stack)

**Security:**
- AWS Config (10+ rules)
- GuardDuty threat detection
- CloudTrail audit logging
- Network policies (Kubernetes)
- WAF (production ALB)

**Documentation:**
- Updated README files (5+)
- Production deployment runbook
- DR procedures
- Handoff documentation
- Updated DEVELOPER_C_SUMMARY.md

### Success Metrics

- ✅ All applications deployed to staging
- ✅ Monitoring operational
- ✅ Production environment ready
- ✅ Security hardening complete
- ✅ Documentation comprehensive
- ✅ Zero critical security issues
- ✅ Backup/restore tested
- ✅ Team handoff prepared

### Next Steps (Future Sprints)

**High Priority:**
1. Implement AWS Secrets Manager integration
2. Set up GitOps workflow (ArgoCD)
3. Production deployment and go-live
4. Performance optimization

**Medium Priority:**
1. Implement service mesh
2. Add tracing (Jaeger/Tempo)
3. Multi-region deployment
4. Chaos engineering

**Low Priority:**
1. Advanced dashboards
2. Cost optimization
3. Advanced security features
4. Developer tooling enhancements

---

## Appendix

### Useful Commands

**Check All Pods:**
```bash
kubectl get pods --all-namespaces
```

**Check Services:**
```bash
kubectl get svc --all-namespaces
```

**Get Logs:**
```bash
kubectl logs -n <namespace> <pod-name> --tail=100 -f
```

**Port Forward:**
```bash
kubectl port-forward -n <namespace> svc/<service-name> <local-port>:<remote-port>
```

**Describe Resource:**
```bash
kubectl describe pod -n <namespace> <pod-name>
```

**Get Events:**
```bash
kubectl get events -n <namespace> --sort-by='.lastTimestamp'
```

### Troubleshooting Guide

**Pod Not Starting:**
1. Check pod description: `kubectl describe pod <pod-name> -n <namespace>`
2. Check events: `kubectl get events -n <namespace>`
3. Check logs: `kubectl logs <pod-name> -n <namespace>`
4. Check resource limits
5. Check image pull secrets

**Service Not Accessible:**
1. Check service: `kubectl get svc -n <namespace>`
2. Check endpoints: `kubectl get endpoints -n <namespace>`
3. Check pod selectors
4. Check network policies
5. Test with port-forward

**Database Connection Issues:**
1. Verify RDS endpoint
2. Check security groups
3. Test connectivity from pod: `kubectl exec -it <pod> -- nc -zv <rds-endpoint> 5432`
4. Verify credentials in secrets
5. Check database logs

**Monitoring Not Working:**
1. Check Prometheus targets: Port-forward and visit `/targets`
2. Verify ServiceMonitor selectors
3. Check RBAC permissions
4. Verify network connectivity
5. Check Prometheus logs

---

**End of Deployment Checklist**

**Last Updated:** 2025-11-21  
**Maintained by:** Developer C (Infrastructure & DevOps)  
**Version:** 1.0
