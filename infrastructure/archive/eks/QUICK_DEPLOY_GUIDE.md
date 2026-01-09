# Quick Deploy Guide for OMC Staging Environment (EKS/Kubernetes)

> **⚠️ IMPORTANT NOTE:** This guide is for **future EKS/Kubernetes deployment**. The current production infrastructure uses **ECS (Elastic Container Service)** managed via **Terraform**.
> 
> **For current deployments, see:** `infrastructure/terraform/README.md`
> 
> This guide should be used only if:
> - You are migrating from ECS to EKS
> - You are setting up a separate EKS-based deployment
> - You have explicitly chosen Kubernetes over ECS

**Purpose:** Step-by-step deployment instructions for someone with kubectl access to an EKS cluster  
**Target Audience:** DevOps engineers planning EKS deployment  
**Prerequisites:** EKS cluster deployed, kubectl access, AWS CLI configured  
**Estimated Time:** 3-4 hours for complete deployment

## Current Infrastructure Status

**Primary Deployment (ECS via Terraform):**
- ✅ Fully operational
- ✅ VPC, RDS, Redis, ECS, ALB deployed
- ✅ Managed via Terraform in `infrastructure/terraform/`

**EKS/Kubernetes Deployment (This Guide):**
- 📝 Manifests created but not deployed
- ⏸️ Requires EKS cluster setup first
- 🔮 Future migration path or alternative deployment option

---

## Table of Contents

1. [Prerequisites Verification](#prerequisites-verification)
2. [Week 9: Deploy Monitoring Stack](#week-9-deploy-monitoring-stack)
3. [Week 10: Deploy Applications](#week-10-deploy-applications)
4. [Verification & Testing](#verification--testing)
5. [Troubleshooting](#troubleshooting)

---

## Prerequisites Verification

Before starting, verify you have the necessary access and tools.

### Step 1: Verify kubectl Access

```bash
# Check current context
kubectl config current-context

# Expected output: Should show EKS cluster ARN or context name containing "OMC-test"

# List nodes
kubectl get nodes

# Expected output: At least 1 node in Ready state
# NAME                                         STATUS   ROLES    AGE   VERSION
# ip-192-168-xx-xx.ap-southeast-2.compute...   Ready    <none>   Xd    v1.28.x
```

**✅ Checkpoint:** If you can see nodes, you have kubectl access. Proceed to next step.

**❌ Troubleshooting:** If kubectl is not configured:
```bash
# Update kubeconfig for OMC-test cluster
aws eks update-kubeconfig \
  --region ap-southeast-2 \
  --name OMC-test

# Verify again
kubectl get nodes
```

### Step 2: Verify AWS CLI Access

```bash
# Check AWS identity
aws sts get-caller-identity

# Expected output: Should show your AWS account ID and IAM role/user

# Check region
aws configure get region

# Expected output: ap-southeast-2 (or your configured region)
```

**✅ Checkpoint:** If you see your AWS account details, you have AWS CLI access.

### Step 3: Clone Repository (if needed)

```bash
# Clone the repository (if not already done)
git clone https://github.com/MarkLimmage/ohmycoins.git
cd ohmycoins

# Verify you're in the right directory
ls -la infrastructure/aws/eks/

# Expected output: Should see monitoring/, applications/, scripts/ directories
```

### Step 4: Gather Required Information

You'll need the following endpoints. Retrieve them now:

**RDS Database Endpoint:**
```bash
aws rds describe-db-instances \
  --db-instance-identifier omc-staging-db \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text

# Save this value for later: _________________________________
```

**ElastiCache Redis Endpoint:**
```bash
aws elasticache describe-cache-clusters \
  --cache-cluster-id omc-staging-redis \
  --show-cache-node-info \
  --query 'CacheClusters[0].CacheNodes[0].Endpoint.Address' \
  --output text

# Save this value for later: _________________________________
```

**ECR Repository URI (for backend image):**
```bash
aws ecr describe-repositories \
  --repository-names ohmycoins/backend \
  --query 'repositories[0].repositoryUri' \
  --output text

# Save this value for later: _________________________________
```

**Latest Image Tag:**
```bash
aws ecr describe-images \
  --repository-name ohmycoins/backend \
  --query 'sort_by(imageDetails,& imagePushedAt)[-1].imageTags[0]' \
  --output text

# Save this value for later: _________________________________
```

**✅ Checkpoint:** You have all four values saved. You're ready to deploy!

---

## Week 9: Deploy Monitoring Stack

**Estimated Time:** 1-2 hours  
**Goal:** Deploy Prometheus, Grafana, Loki, and AlertManager for observability

### Step 1: Create Monitoring Namespace (2 minutes)

```bash
# Navigate to the monitoring directory
cd infrastructure/aws/eks/monitoring

# Create monitoring namespace
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# Verify namespace creation
kubectl get namespace monitoring

# Expected output:
# NAME         STATUS   AGE
# monitoring   Active   Xs
```

**✅ Checkpoint:** Monitoring namespace is Active.

### Step 2: Deploy Prometheus Operator (5 minutes)

```bash
# Deploy Prometheus Operator
kubectl apply -f prometheus-operator.yml

# Wait for Prometheus to be ready (this may take 2-3 minutes)
kubectl wait --for=condition=ready pod -l app=prometheus -n monitoring --timeout=300s

# Verify Prometheus deployment
kubectl get pods -n monitoring -l app=prometheus

# Expected output:
# NAME                          READY   STATUS    RESTARTS   AGE
# prometheus-xxxxxxxxxx-xxxxx   1/1     Running   0          2m
```

**✅ Checkpoint:** Prometheus pod is Running (1/1 Ready).

**🔍 Troubleshooting (if pod not ready):**
```bash
# Check pod status
kubectl describe pod -n monitoring -l app=prometheus

# Check logs
kubectl logs -n monitoring -l app=prometheus --tail=50

# Common issues:
# - Resource constraints: Check node resources
# - RBAC issues: Verify ClusterRole prometheus exists
# - Image pull issues: Verify internet connectivity
```

### Step 3: Deploy Grafana (5 minutes)

```bash
# Deploy Grafana
kubectl apply -f grafana.yml

# Wait for Grafana to be ready
kubectl wait --for=condition=ready pod -l app=grafana -n monitoring --timeout=300s

# Check Grafana service (LoadBalancer type)
kubectl get svc grafana -n monitoring

# Expected output:
# NAME      TYPE           CLUSTER-IP      EXTERNAL-IP                        PORT(S)        AGE
# grafana   LoadBalancer   10.100.x.x      xxxxx.ap-southeast-2.elb.amazonaws.com   80:xxxxx/TCP   2m

# Wait for LoadBalancer to provision (may take 2-5 minutes)
kubectl get svc grafana -n monitoring -w

# Press Ctrl+C once EXTERNAL-IP is assigned (not <pending>)
```

**✅ Checkpoint:** Grafana has an EXTERNAL-IP assigned.

**Save Grafana URL:**
```bash
# Get Grafana URL
GRAFANA_URL=$(kubectl get svc grafana -n monitoring -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo "Grafana URL: http://$GRAFANA_URL"

# Save this URL: _________________________________
```

**Access Grafana:**
```bash
# Open in browser
# URL: http://<EXTERNAL-IP>
# Default credentials: admin / admin
# You'll be prompted to change the password on first login
```

**✅ Checkpoint:** You can access Grafana in your browser and login.

### Step 4: Deploy Loki and Promtail (5 minutes)

```bash
# Deploy Loki stack (Loki + Promtail)
kubectl apply -f loki-stack.yml

# Wait for Loki to be ready
kubectl wait --for=condition=ready pod -l app=loki -n monitoring --timeout=300s

# Verify Promtail DaemonSet (should have 1 pod per node)
kubectl get daemonset promtail -n monitoring
kubectl get pods -n monitoring -l app=promtail

# Expected output:
# NAME             DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR   AGE
# promtail         N         N         N       N            N           <none>          2m
#
# NAME                   READY   STATUS    RESTARTS   AGE
# promtail-xxxxx         1/1     Running   0          2m
# promtail-yyyyy         1/1     Running   0          2m (if multiple nodes)
```

**✅ Checkpoint:** Loki pod is Running, Promtail pods running on all nodes.

**Verify Loki Datasource in Grafana:**
1. Open Grafana (http://<GRAFANA-URL>)
2. Go to Configuration (gear icon) → Data Sources
3. You should see "Loki" datasource configured
4. Click "Test" - should show "Data source is working"

### Step 5: Deploy AlertManager (5 minutes)

```bash
# Deploy AlertManager
kubectl apply -f alertmanager-config.yml

# Wait for AlertManager to be ready
kubectl wait --for=condition=ready pod -l app=alertmanager -n monitoring --timeout=300s

# Verify AlertManager
kubectl get pods -n monitoring -l app=alertmanager
kubectl get svc -n monitoring -l app=alertmanager

# Expected output:
# NAME                           READY   STATUS    RESTARTS   AGE
# alertmanager-xxxxxxxxxx-xxxxx  1/1     Running   0          2m
```

**✅ Checkpoint:** AlertManager pod is Running.

### Step 6: Apply Alert Rules (2 minutes)

```bash
# Apply alert rules
kubectl apply -f alert-rules.yml

# Verify PrometheusRule created
kubectl get prometheusrules -n monitoring

# Expected output:
# NAME                   AGE
# omc-alert-rules        10s
```

**Verify in Prometheus:**
```bash
# Port-forward to Prometheus
kubectl port-forward -n monitoring svc/prometheus 9090:9090 &

# Open browser to http://localhost:9090/alerts
# You should see alert rules loaded (may be in "Inactive" state initially)

# Stop port-forward
kill %1
```

**✅ Checkpoint:** Alert rules are visible in Prometheus UI.

### Step 7: Verify Monitoring Stack (5 minutes)

**Run comprehensive verification:**

```bash
# Check all pods in monitoring namespace
kubectl get pods -n monitoring

# Expected output: All pods should be Running (1/1 Ready)
# - prometheus-xxx
# - grafana-xxx
# - loki-xxx
# - promtail-xxx (one per node)
# - alertmanager-xxx

# Check all services
kubectl get svc -n monitoring

# Expected output: Services created for all components
```

**Test Prometheus:**
```bash
# Port-forward to Prometheus
kubectl port-forward -n monitoring svc/prometheus 9090:9090 &

# Open browser to http://localhost:9090
# Go to Status → Targets
# You should see targets (may be limited before applications are deployed)

# Stop port-forward
kill %1
```

**✅ Checkpoint:** All monitoring components are Running and healthy.

**📝 Week 9 Complete!** Monitoring stack is operational.

---

## Week 10: Deploy Applications

**Estimated Time:** 2-3 hours  
**Goal:** Deploy backend API, collectors, and agentic system to staging

### Step 1: Create Application Namespace (2 minutes)

```bash
# Navigate to applications directory
cd ../applications

# Create omc-staging namespace
kubectl create namespace omc-staging --dry-run=client -o yaml | kubectl apply -f -

# Verify namespace
kubectl get namespace omc-staging

# Expected output:
# NAME           STATUS   AGE
# omc-staging    Active   Xs
```

**✅ Checkpoint:** omc-staging namespace is Active.

### Step 2: Update Backend Configuration (5 minutes)

**IMPORTANT:** You must update the configuration with actual AWS resource endpoints.

```bash
# Make a backup of the original deployment file
cp backend/deployment.yml backend/deployment.yml.backup

# Edit the deployment file
nano backend/deployment.yml
# OR
vim backend/deployment.yml
# OR use your preferred editor
```

**Update the following values in backend/deployment.yml:**

**Lines 21-28 (ConfigMap data):**
```yaml
# Line 21: Update with your RDS endpoint
POSTGRES_SERVER: "<YOUR-RDS-ENDPOINT>"  # e.g., omc-staging-db.xxxxx.ap-southeast-2.rds.amazonaws.com

# Line 25: Update with your Redis endpoint  
REDIS_HOST: "<YOUR-REDIS-ENDPOINT>"  # e.g., omc-staging-redis.xxxxx.cache.amazonaws.com
```

**Lines 38-44 (Secret data):**

Generate secure values:
```bash
# Generate SECRET_KEY (32+ character random string)
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate ENCRYPTION_KEY (Fernet key for credential encryption)
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Update in deployment.yml:
```yaml
# Line 40: Update with secure random password
POSTGRES_PASSWORD: "<SECURE-PASSWORD>"  # Generate: openssl rand -base64 32

# Line 42: Update admin password
FIRST_SUPERUSER_PASSWORD: "<ADMIN-PASSWORD>"  # Generate: openssl rand -base64 24

# Line 43: Update with generated SECRET_KEY
SECRET_KEY: "<YOUR-SECRET-KEY>"  # From python command above

# Line 44: Update with generated ENCRYPTION_KEY
ENCRYPTION_KEY: "<YOUR-ENCRYPTION-KEY>"  # From python command above
```

**Save the file** and verify your changes:
```bash
# Verify ConfigMap values
grep -A 15 "kind: ConfigMap" backend/deployment.yml | grep -E "POSTGRES_SERVER|REDIS_HOST"

# Verify Secret values (should NOT show 'changeme')
grep -A 10 "kind: Secret" backend/deployment.yml | grep -E "POSTGRES_PASSWORD|SECRET_KEY"
```

**✅ Checkpoint:** Configuration file updated with actual endpoints and secure secrets.

### Step 3: Deploy Backend API (10 minutes)

```bash
# Deploy backend (includes ConfigMap, Secret, Deployment, Service, HPA)
kubectl apply -f backend/deployment.yml

# Watch deployment progress
kubectl get pods -n omc-staging -l app=backend -w

# Wait for pods to be Ready (may take 2-3 minutes)
# Press Ctrl+C once pods show 1/1 Ready

# Expected output:
# NAME                       READY   STATUS    RESTARTS   AGE
# backend-xxxxxxxxxx-xxxxx   1/1     Running   0          2m
# backend-xxxxxxxxxx-yyyyy   1/1     Running   0          2m
```

**Verify backend connectivity:**
```bash
# Port-forward to backend service
kubectl port-forward -n omc-staging svc/backend 8000:8000 &

# Test health endpoint (in another terminal or use curl)
curl http://localhost:8000/api/v1/health

# Expected output: {"status":"healthy"} or similar

# Test API docs
curl http://localhost:8000/docs

# Expected: HTML response (OpenAPI/Swagger UI)

# Stop port-forward
kill %1
```

**✅ Checkpoint:** Backend pods are Running and health endpoint responds.

**🔍 Troubleshooting (if pods not ready):**
```bash
# Check pod status
kubectl describe pod -n omc-staging -l app=backend

# Check logs
kubectl logs -n omc-staging -l app=backend --tail=50

# Common issues:
# - Database connection failed: Verify RDS endpoint and credentials
# - Redis connection failed: Verify Redis endpoint
# - Image pull errors: Verify ECR image exists and permissions
# - CrashLoopBackOff: Check application logs for errors
```

### Step 4: Deploy Backend Ingress (10 minutes)

```bash
# Deploy ALB Ingress
kubectl apply -f backend/ingress.yml

# Wait for Ingress to be created
kubectl get ingress -n omc-staging

# Expected output:
# NAME              CLASS   HOSTS   ADDRESS   PORTS   AGE
# backend-ingress   alb     *                 80      10s

# Wait for ALB to provision (this takes 5-10 minutes)
kubectl get ingress backend-ingress -n omc-staging -w

# Press Ctrl+C once ADDRESS is populated (not empty)
```

**Get ALB URL:**
```bash
# Get ALB hostname
ALB_URL=$(kubectl get ingress backend-ingress -n omc-staging -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo "Backend ALB URL: http://$ALB_URL"

# Save this URL: _________________________________

# Wait 2-3 minutes for ALB health checks to pass
sleep 180

# Test via ALB
curl http://$ALB_URL/api/v1/health

# Expected output: {"status":"healthy"}
```

**✅ Checkpoint:** Backend is accessible via ALB.

### Step 5: Deploy Phase 2.5 Collectors (10 minutes)

**Update collector image URIs (if needed):**
```bash
# Check current image URI in cronjobs.yml
grep "image:" collectors/cronjobs.yml

# If you need to update the image URI, edit the file
nano collectors/cronjobs.yml

# Update all occurrences of image URI to your ECR repository
# Find: image: <ACCOUNT>.dkr.ecr.ap-southeast-2.amazonaws.com/ohmycoins/backend:latest
# Replace with your actual ECR URI
```

**Deploy collectors:**
```bash
# Deploy all collectors (3 CronJobs + 2 Deployments)
kubectl apply -f collectors/cronjobs.yml

# Verify CronJobs created
kubectl get cronjobs -n omc-staging

# Expected output:
# NAME                         SCHEDULE      SUSPEND   ACTIVE   LAST SCHEDULE   AGE
# defillama-collector          0 2 * * *     False     0        <none>          10s
# sec-api-collector            0 3 * * *     False     0        <none>          10s
# coinspot-announcements       0 * * * *     False     0        <none>          10s

# Verify Deployments created
kubectl get deployments -n omc-staging | grep collector

# Expected output:
# reddit-collector          1/1     1            1           10s
# cryptopanic-collector     1/1     1            1           10s

# Check collector pods
kubectl get pods -n omc-staging -l component=collector

# Expected output: 2 pods Running (reddit and cryptopanic)
```

**Test a collector (optional but recommended):**
```bash
# Manually trigger DeFiLlama collector for testing
kubectl create job --from=cronjob/defillama-collector test-defillama -n omc-staging

# Watch job completion
kubectl get jobs -n omc-staging test-defillama -w

# Press Ctrl+C once COMPLETIONS shows 1/1

# Check job logs
kubectl logs -n omc-staging job/test-defillama

# Expected: Logs showing data collection (no errors)

# Clean up test job
kubectl delete job test-defillama -n omc-staging
```

**✅ Checkpoint:** All 5 collectors are deployed. CronJobs scheduled, continuous collectors running.

### Step 6: Deploy Phase 3 Agentic System (15 minutes)

**Create agent secrets (LLM API keys):**

**IMPORTANT:** You need OpenAI and/or Anthropic API keys.

```bash
# Create agent secrets
kubectl create secret generic agent-secrets \
  --from-literal=OPENAI_API_KEY="sk-your-openai-api-key-here" \
  --from-literal=ANTHROPIC_API_KEY="sk-ant-your-anthropic-key-here" \
  -n omc-staging \
  --dry-run=client -o yaml | kubectl apply -f -

# Verify secret created
kubectl get secret agent-secrets -n omc-staging

# Expected output:
# NAME            TYPE     DATA   AGE
# agent-secrets   Opaque   2      10s
```

**Check storage class for PVC:**
```bash
# Check available storage classes
kubectl get storageclass

# Expected output: At least one storage class available (e.g., gp2, gp3, ebs-sc)

# If needed, update agents/deployment.yml line with storageClassName
# Default is usually fine (uses cluster default storage class)
```

**Deploy agentic system:**
```bash
# Deploy agents
kubectl apply -f agents/deployment.yml

# Watch deployment progress
kubectl get pods -n omc-staging -l app=agents -w

# Wait for pods to be Ready (may take 2-3 minutes)
# Press Ctrl+C once pods show 1/1 Ready

# Verify PVC created and bound
kubectl get pvc -n omc-staging -l app=agents

# Expected output:
# NAME          STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
# agent-data    Bound    pvc-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx   10Gi       RWO            gp2            2m
```

**Test agentic system:**
```bash
# Port-forward to agent service
kubectl port-forward -n omc-staging svc/agents 8001:8000 &

# Test agent health
curl http://localhost:8001/api/v1/health

# Expected output: {"status":"healthy"}

# Test agent session creation (optional)
curl -X POST http://localhost:8001/api/v1/lab/agent/sessions \
  -H "Content-Type: application/json" \
  -d '{"goal": "Analyze BTC price trends for the past week"}'

# Expected: JSON response with session_id

# Stop port-forward
kill %1
```

**✅ Checkpoint:** Agentic system is deployed, PVC bound, pods running, health check passes.

**🔍 Troubleshooting (if pods not ready):**
```bash
# Check pod status
kubectl describe pod -n omc-staging -l app=agents

# Check logs
kubectl logs -n omc-staging -l app=agents --tail=50

# Common issues:
# - PVC not binding: Check storage class availability
# - API key errors: Verify agent-secrets exist and have valid keys
# - Database errors: Verify backend database connection
```

### Step 7: Configure ServiceMonitors (5 minutes)

```bash
# Deploy ServiceMonitors for Prometheus integration
kubectl apply -f servicemonitor.yml

# Verify ServiceMonitors created
kubectl get servicemonitors -n omc-staging

# Expected output:
# NAME                        AGE
# backend-servicemonitor      10s
# agents-servicemonitor       10s
# collectors-podmonitor       10s (may show as PodMonitor)
```

**Verify Prometheus is scraping targets:**
```bash
# Port-forward to Prometheus
kubectl port-forward -n monitoring svc/prometheus 9090:9090 &

# Open browser to http://localhost:9090/targets
# Look for targets in "omc-staging" namespace
# Expected: backend, agents showing "UP" status
# collectors may not show if CronJobs haven't run yet

# Stop port-forward
kill %1
```

**✅ Checkpoint:** ServiceMonitors created, Prometheus scraping application metrics.

### Step 8: Create Application Dashboards in Grafana (10 minutes)

**Create Backend API Dashboard:**

1. Open Grafana: http://<GRAFANA-URL>
2. Click "+" → Create → Dashboard
3. Click "Add new panel"
4. Configure panel:
   - **Query:** `rate(http_requests_total{namespace="omc-staging", app="backend"}[5m])`
   - **Title:** Backend Request Rate
   - **Panel type:** Time series
5. Add more panels:
   - Response time: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`
   - Error rate: `rate(http_requests_total{namespace="omc-staging", app="backend", status=~"5.."}[5m])`
6. Save dashboard as "Backend API Dashboard"

**Create Collectors Dashboard:**

1. Create new dashboard
2. Add panels:
   - **Collection success rate:** `rate(collector_runs_total{namespace="omc-staging", status="success"}[1h])`
   - **Records collected:** `increase(collector_records_total{namespace="omc-staging"}[1h])`
   - **Collection latency:** `collector_duration_seconds{namespace="omc-staging"}`
3. Save dashboard as "Data Collectors Dashboard"

**Create Agentic System Dashboard:**

1. Create new dashboard
2. Add panels:
   - **Active sessions:** `agent_sessions_active{namespace="omc-staging"}`
   - **Workflow completion rate:** `rate(agent_workflows_total{namespace="omc-staging", status="completed"}[1h])`
   - **LLM API latency:** `agent_llm_api_duration_seconds{namespace="omc-staging"}`
3. Save dashboard as "Agentic System Dashboard"

**Note:** Exact metric names depend on application instrumentation. Adjust queries based on available metrics.

**✅ Checkpoint:** Grafana dashboards created and showing data.

### Step 9: End-to-End Verification (10 minutes)

**Verify complete system integration:**

**1. Check all pods are running:**
```bash
# Get all pods in omc-staging
kubectl get pods -n omc-staging

# Expected output: All pods Running (1/1 Ready)
# - backend-xxx (2 pods)
# - reddit-collector-xxx
# - cryptopanic-collector-xxx
# - agents-xxx (2 pods)
```

**2. Verify data flow:**
```bash
# Check collector logs (should show data collection)
kubectl logs -n omc-staging -l component=collector --tail=20

# Check backend logs (should show API requests)
kubectl logs -n omc-staging -l app=backend --tail=20

# Check agent logs (should show initialization)
kubectl logs -n omc-staging -l app=agents --tail=20
```

**3. Test end-to-end data flow:**
```bash
# Test data collection → database → API
curl http://$ALB_URL/api/v1/coins

# Expected: JSON array of coins (may be empty initially)

# Test agentic system can access data
curl -X POST http://localhost:8001/api/v1/lab/agent/sessions \
  -H "Content-Type: application/json" \
  -d '{"goal": "List available coins in the database"}'

# Expected: Session created successfully
```

**4. Check Grafana dashboards:**
- Open Grafana
- Navigate to each dashboard
- Verify metrics are being collected
- Verify no errors in logs panel (if configured)

**5. Check Prometheus targets:**
```bash
# Port-forward to Prometheus
kubectl port-forward -n monitoring svc/prometheus 9090:9090 &

# Open http://localhost:9090/targets
# Verify all targets are "UP":
# - backend (2 endpoints)
# - agents (2 endpoints)
# - collectors (as jobs run)

# Stop port-forward
kill %1
```

**✅ Final Checkpoint:** All applications deployed and operational!

**📝 Week 10 Complete!** All applications are running on staging.

---

## Verification & Testing

### Quick Health Check Script

Create a simple health check script:

```bash
#!/bin/bash
# health-check.sh

echo "=== OMC Staging Health Check ==="
echo ""

echo "1. Monitoring Namespace:"
kubectl get pods -n monitoring --no-headers | wc -l
echo "   Pods running in monitoring namespace"
echo ""

echo "2. Application Namespace:"
kubectl get pods -n omc-staging --no-headers | wc -l
echo "   Pods running in omc-staging namespace"
echo ""

echo "3. Backend API:"
ALB_URL=$(kubectl get ingress backend-ingress -n omc-staging -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
curl -s http://$ALB_URL/api/v1/health || echo "   Backend not accessible"
echo ""

echo "4. Grafana:"
GRAFANA_URL=$(kubectl get svc grafana -n monitoring -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo "   Grafana URL: http://$GRAFANA_URL"
curl -s -o /dev/null -w "   HTTP Status: %{http_code}\n" http://$GRAFANA_URL/api/health
echo ""

echo "5. Prometheus Targets:"
echo "   Run: kubectl port-forward -n monitoring svc/prometheus 9090:9090"
echo "   Then visit: http://localhost:9090/targets"
echo ""

echo "=== Health Check Complete ==="
```

Run the health check:
```bash
chmod +x health-check.sh
./health-check.sh
```

### Performance Testing (Optional)

**Simple load test on backend:**
```bash
# Install hey (HTTP load generator) if not already installed
# macOS: brew install hey
# Linux: go install github.com/rakyll/hey@latest

# Run load test (100 requests, 10 concurrent)
hey -n 100 -c 10 http://$ALB_URL/api/v1/health

# Check results in Grafana dashboard
# Should see spike in request rate
```

### Monitoring Alerts Test

**Trigger a test alert:**
```bash
# Scale backend to 0 (will trigger ApplicationDown alert)
kubectl scale deployment backend --replicas=0 -n omc-staging

# Wait 2 minutes for alert to fire

# Check Prometheus alerts
kubectl port-forward -n monitoring svc/prometheus 9090:9090 &
# Open http://localhost:9090/alerts
# Should see ApplicationDown alert in "Pending" or "Firing" state

# Restore backend
kubectl scale deployment backend --replicas=2 -n omc-staging

# Stop port-forward
kill %1
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: Pods in CrashLoopBackOff

**Symptoms:**
```bash
kubectl get pods -n omc-staging
# NAME                       READY   STATUS             RESTARTS   AGE
# backend-xxx                0/1     CrashLoopBackOff   5          5m
```

**Diagnosis:**
```bash
# Check pod logs
kubectl logs -n omc-staging backend-xxx --tail=100

# Check pod events
kubectl describe pod -n omc-staging backend-xxx
```

**Common causes:**
1. **Database connection failed:** Verify RDS endpoint and credentials
2. **Redis connection failed:** Verify Redis endpoint
3. **Missing environment variables:** Check ConfigMap and Secrets
4. **Application error:** Review application logs

**Solution:**
```bash
# If configuration issue, update deployment.yml and reapply
kubectl apply -f backend/deployment.yml

# If application issue, check backend code

# Force restart pods
kubectl rollout restart deployment/backend -n omc-staging
```

#### Issue 2: Ingress Not Getting External IP

**Symptoms:**
```bash
kubectl get ingress -n omc-staging
# NAME              CLASS   HOSTS   ADDRESS   PORTS   AGE
# backend-ingress   alb     *                 80      10m
# ADDRESS is empty even after 10 minutes
```

**Diagnosis:**
```bash
# Check Ingress events
kubectl describe ingress backend-ingress -n omc-staging

# Check AWS Load Balancer Controller
kubectl get pods -n kube-system | grep aws-load-balancer-controller
```

**Common causes:**
1. **ALB Controller not installed:** Need to install AWS Load Balancer Controller
2. **IAM permissions missing:** Controller needs IAM permissions
3. **Subnet tags missing:** Public subnets need specific tags

**Solution:**
```bash
# Check if ALB controller exists
kubectl get deployment -n kube-system aws-load-balancer-controller

# If not found, install AWS Load Balancer Controller
# (Follow AWS documentation for installation)

# Verify IAM policy and subnet tags
```

#### Issue 3: PVC Not Binding

**Symptoms:**
```bash
kubectl get pvc -n omc-staging
# NAME         STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS   AGE
# agent-data   Pending                                                     5m
```

**Diagnosis:**
```bash
# Check PVC events
kubectl describe pvc agent-data -n omc-staging

# Check storage classes
kubectl get storageclass
```

**Common causes:**
1. **No storage class available:** Need to create or configure storage class
2. **Capacity issue:** Not enough storage
3. **Zone mismatch:** PVC in different AZ than nodes

**Solution:**
```bash
# If no storage class, create one
kubectl apply -f - <<EOF
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp2
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp2
  fsType: ext4
EOF

# Update PVC to use specific storage class
# Edit agents/deployment.yml and add:
# storageClassName: gp2
```

#### Issue 4: Prometheus Not Scraping Targets

**Symptoms:**
- Prometheus UI shows targets as "DOWN"
- No metrics in Grafana

**Diagnosis:**
```bash
# Check ServiceMonitor
kubectl get servicemonitors -n omc-staging

# Check if labels match
kubectl get svc -n omc-staging --show-labels

# Check Prometheus logs
kubectl logs -n monitoring -l app=prometheus --tail=50
```

**Common causes:**
1. **Label mismatch:** ServiceMonitor selector doesn't match service labels
2. **Network policy:** Prometheus can't reach target pods
3. **Port mismatch:** ServiceMonitor port doesn't match service port

**Solution:**
```bash
# Verify service labels match ServiceMonitor selector
kubectl get svc backend -n omc-staging -o yaml | grep -A 5 labels
kubectl get servicemonitor backend-servicemonitor -n omc-staging -o yaml | grep -A 5 selector

# If mismatch, update servicemonitor.yml and reapply
kubectl apply -f servicemonitor.yml
```

#### Issue 5: Collector Jobs Failing

**Symptoms:**
```bash
kubectl get jobs -n omc-staging
# NAME                       COMPLETIONS   DURATION   AGE
# defillama-collector-xxx    0/1           5m         5m
```

**Diagnosis:**
```bash
# Check job logs
kubectl logs -n omc-staging job/defillama-collector-xxx

# Check CronJob configuration
kubectl get cronjob defillama-collector -n omc-staging -o yaml
```

**Common causes:**
1. **API rate limit:** External API rate limiting
2. **Network issue:** Can't reach external API
3. **Database error:** Can't write to database
4. **Authentication:** Missing API keys or credentials

**Solution:**
```bash
# If API rate limit, adjust schedule in collectors/cronjobs.yml

# If database error, verify backend-secrets

# If network issue, check NAT Gateway and security groups

# Manual retry
kubectl create job --from=cronjob/defillama-collector retry-defillama -n omc-staging
```

### Getting Help

**Check logs:**
```bash
# Monitoring logs
kubectl logs -n monitoring -l app=prometheus --tail=100
kubectl logs -n monitoring -l app=grafana --tail=100
kubectl logs -n monitoring -l app=loki --tail=100

# Application logs
kubectl logs -n omc-staging -l app=backend --tail=100
kubectl logs -n omc-staging -l app=agents --tail=100
kubectl logs -n omc-staging -l component=collector --tail=100
```

**Check events:**
```bash
# All events in namespace
kubectl get events -n omc-staging --sort-by='.lastTimestamp'
kubectl get events -n monitoring --sort-by='.lastTimestamp'
```

**Check resource usage:**
```bash
# Pod resource usage
kubectl top pods -n omc-staging
kubectl top pods -n monitoring

# Node resource usage
kubectl top nodes
```

**Useful commands:**
```bash
# Get all resources in namespace
kubectl get all -n omc-staging
kubectl get all -n monitoring

# Restart a deployment
kubectl rollout restart deployment/<name> -n omc-staging

# Scale a deployment
kubectl scale deployment/<name> --replicas=<N> -n omc-staging

# Delete and recreate a pod
kubectl delete pod <pod-name> -n omc-staging
```

---

## Post-Deployment Checklist

After completing the deployment, verify the following:

### Monitoring Stack
- [ ] Prometheus pod running and healthy
- [ ] Grafana accessible via LoadBalancer URL
- [ ] Loki collecting logs from all pods
- [ ] Promtail DaemonSet running on all nodes
- [ ] AlertManager pod running
- [ ] Alert rules loaded in Prometheus
- [ ] Grafana dashboards created (infrastructure, backend, collectors, agents)

### Applications
- [ ] Backend API pods running (2/2)
- [ ] Backend accessible via ALB Ingress
- [ ] Backend health endpoint returns 200
- [ ] API documentation accessible (/docs)
- [ ] DeFiLlama CronJob scheduled
- [ ] SEC API CronJob scheduled
- [ ] CoinSpot Announcements CronJob scheduled
- [ ] Reddit collector deployment running
- [ ] CryptoPanic collector deployment running
- [ ] Agentic system pods running (2/2)
- [ ] Agent PVC bound and ready
- [ ] Agent health endpoint returns 200

### Monitoring Integration
- [ ] ServiceMonitors created for backend and agents
- [ ] Prometheus scraping all application targets
- [ ] Metrics visible in Prometheus UI
- [ ] Grafana dashboards showing real-time data
- [ ] Loki showing application logs
- [ ] Alerts configured and testable

### Documentation
- [ ] Grafana URL documented
- [ ] ALB URL documented
- [ ] Grafana admin password changed and saved securely
- [ ] All endpoints documented
- [ ] Deployment notes updated

### Security
- [ ] Backend secrets contain strong passwords
- [ ] Agent secrets contain valid API keys
- [ ] No "changeme" values in production
- [ ] Sensitive data not committed to git

### Next Steps
- [ ] Configure DNS for ALB (api.staging.ohmycoins.com)
- [ ] Set up SSL certificate (ACM)
- [ ] Enable HTTPS on Ingress
- [ ] Configure backup for PVCs
- [ ] Set up alerting notifications (email/Slack)
- [ ] Run integration tests
- [ ] Performance testing
- [ ] Production environment preparation

---

## Quick Reference

### Important URLs

Save these URLs after deployment:

```bash
# Grafana
kubectl get svc grafana -n monitoring -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'

# Backend API
kubectl get ingress backend-ingress -n omc-staging -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

**Grafana:** http://<GRAFANA-URL>  
**Backend API:** http://<ALB-URL>  
**API Docs:** http://<ALB-URL>/docs  
**Prometheus:** Port-forward to http://localhost:9090  

### Useful Commands

```bash
# Quick status check
kubectl get pods --all-namespaces | grep -v Running

# Check all services
kubectl get svc --all-namespaces

# Check all ingresses
kubectl get ingress --all-namespaces

# View logs
kubectl logs -f -n <namespace> <pod-name>

# Execute command in pod
kubectl exec -it -n <namespace> <pod-name> -- /bin/bash

# Port forward
kubectl port-forward -n <namespace> svc/<service-name> <local-port>:<remote-port>

# Restart deployment
kubectl rollout restart deployment/<name> -n <namespace>

# Scale deployment
kubectl scale deployment/<name> --replicas=<N> -n <namespace>
```

### Default Credentials

**Grafana:**
- Username: `admin`
- Password: `admin` (change on first login)

**Backend Admin:**
- Email: Configured in backend-secrets (FIRST_SUPERUSER)
- Password: Configured in backend-secrets (FIRST_SUPERUSER_PASSWORD)

---

## Summary

You have successfully deployed:
- ✅ Complete monitoring stack (Prometheus, Grafana, Loki, AlertManager)
- ✅ Backend API with ALB Ingress
- ✅ 5 data collectors (3 CronJobs + 2 Deployments)
- ✅ Agentic system with persistent storage
- ✅ ServiceMonitors for Prometheus integration
- ✅ Grafana dashboards for visualization

**Estimated time spent:** 3-4 hours

**Next recommended steps:**
1. Configure DNS and SSL for production-ready URLs
2. Set up backup for persistent volumes
3. Configure alerting notifications (Slack/email)
4. Run integration and performance tests
5. Begin production environment preparation

For detailed week-by-week deployment procedures, see:
- `infrastructure/aws/eks/DEPLOYMENT_CHECKLIST_WEEKS_9-12.md`

For troubleshooting and operations, see:
- `infrastructure/aws/eks/monitoring/README.md`
- `infrastructure/aws/eks/applications/README.md`

---

**Deployment Complete!** 🎉

If you encounter any issues, refer to the [Troubleshooting](#troubleshooting) section or check the comprehensive deployment checklist.
