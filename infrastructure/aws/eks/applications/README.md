# OMC Application Deployments for EKS

## Overview

This directory contains Kubernetes manifests for deploying the OMC (Oh My Coins) application stack to AWS EKS. The deployment includes:

- **Backend API**: FastAPI service for the OMC platform
- **Data Collectors**: Phase 2.5 data collection services (5 collectors)
- **Agentic System**: Phase 3 LangGraph-based autonomous algorithm development
- **Monitoring**: Prometheus, Grafana, Loki stack for observability

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         AWS EKS Cluster                          │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Namespace: omc-staging                   │ │
│  │                                                              │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │ │
│  │  │   Backend    │  │  Collectors  │  │     Agents      │  │ │
│  │  │  (2-10 pods) │  │  (CronJobs + │  │   (2-5 pods)    │  │ │
│  │  │              │  │  Deployments)│  │                 │  │ │
│  │  └──────┬───────┘  └──────┬───────┘  └────────┬────────┘  │ │
│  │         │                  │                    │           │ │
│  │         └──────────────────┴────────────────────┘           │ │
│  │                            │                                │ │
│  │                            ▼                                │ │
│  │         ┌──────────────────────────────────┐               │ │
│  │         │     ServiceMonitors              │               │ │
│  │         │  (Prometheus metric collection)  │               │ │
│  │         └──────────────────────────────────┘               │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │                  Namespace: monitoring                    │ │
│  │                                                            │ │
│  │  ┌────────────┐  ┌──────────┐  ┌──────────────────────┐ │ │
│  │  │ Prometheus │  │ Grafana  │  │  Loki + Promtail     │ │ │
│  │  └────────────┘  └──────────┘  └──────────────────────┘ │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │                   External Services                       │ │
│  │                                                            │ │
│  │  RDS PostgreSQL  │  ElastiCache Redis  │  S3/EFS Storage │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
applications/
├── backend/
│   ├── deployment.yml    # Backend API deployment with HPA
│   └── ingress.yml       # ALB Ingress for external access
├── collectors/
│   └── cronjobs.yml      # All 5 data collectors (CronJobs + Deployments)
├── agents/
│   └── deployment.yml    # Agentic system with HPA and PVC
└── servicemonitor.yml    # Prometheus monitoring integration
```

## Prerequisites

1. **EKS Cluster**: OMC-test cluster running in ap-southeast-2
2. **AWS Resources**:
   - RDS PostgreSQL database
   - ElastiCache Redis cluster
   - ECR repositories for container images
   - IAM roles for service accounts
3. **kubectl**: Configured to access the EKS cluster
4. **AWS CLI**: Configured with appropriate credentials

## Configuration

### Environment Variables

All applications use ConfigMaps and Secrets for configuration:

**ConfigMap (backend-config):**
- Database connection strings
- Redis connection strings
- Application settings

**Secrets (backend-secrets):**
- Database credentials
- Encryption keys
- Admin credentials

**Secrets (agent-secrets):**
- OpenAI API key
- Anthropic API key

### Update Configuration

Before deploying, update the following in the manifests:

1. **Backend deployment.yml**:
   - `POSTGRES_SERVER`: RDS endpoint
   - `REDIS_HOST`: ElastiCache endpoint

2. **Backend secrets**:
   - Update all passwords and keys
   - Use AWS Secrets Manager in production

3. **Agent secrets**:
   - Add your LLM API keys

4. **Ingress**:
   - Update SSL certificate ARN (optional)
   - Update domain names

## Deployment

### Quick Start

Deploy everything:

```bash
# Deploy monitoring stack
kubectl apply -f ../monitoring/

# Deploy all applications
kubectl apply -f backend/
kubectl apply -f collectors/
kubectl apply -f agents/
kubectl apply -f servicemonitor.yml
```

### Using the Deploy Script

```bash
# Deploy all components to staging
../scripts/deploy.sh staging all

# Deploy only backend to staging
../scripts/deploy.sh staging backend

# Deploy only collectors
../scripts/deploy.sh staging collectors

# Deploy only monitoring
../scripts/deploy.sh staging monitoring
```

### Manual Deployment

#### 1. Deploy Backend

```bash
# Create namespace
kubectl create namespace omc-staging

# Deploy backend
kubectl apply -f backend/deployment.yml
kubectl apply -f backend/ingress.yml

# Wait for rollout
kubectl rollout status deployment/backend -n omc-staging

# Check pods
kubectl get pods -n omc-staging -l app=backend
```

#### 2. Deploy Collectors

```bash
# Deploy all collectors
kubectl apply -f collectors/cronjobs.yml

# Verify CronJobs
kubectl get cronjobs -n omc-staging

# Verify continuous collectors
kubectl get deployments -n omc-staging -l app=collectors
```

#### 3. Deploy Agents

```bash
# Deploy agentic system
kubectl apply -f agents/deployment.yml

# Wait for rollout
kubectl rollout status deployment/agents -n omc-staging

# Check pods
kubectl get pods -n omc-staging -l app=agents
```

#### 4. Deploy Monitoring Integration

```bash
# Deploy ServiceMonitors for Prometheus
kubectl apply -f servicemonitor.yml
```

## Verification

### Check Deployment Status

```bash
# All pods
kubectl get pods -n omc-staging

# Deployments
kubectl get deployments -n omc-staging

# Services
kubectl get svc -n omc-staging

# Ingresses
kubectl get ingress -n omc-staging

# CronJobs
kubectl get cronjobs -n omc-staging
```

### Check Logs

```bash
# Backend logs
kubectl logs -n omc-staging deployment/backend --tail=50 -f

# Agent logs
kubectl logs -n omc-staging deployment/agents --tail=50 -f

# Collector logs (last job run)
kubectl logs -n omc-staging job/defillama-collector-<job-id>
```

### Test Endpoints

```bash
# Get backend URL
BACKEND_URL=$(kubectl get ingress backend-ingress -n omc-staging -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Test health endpoint
curl http://$BACKEND_URL/api/v1/health

# Test API docs
curl http://$BACKEND_URL/docs
```

### Check Metrics

```bash
# Port-forward Grafana
kubectl port-forward -n monitoring svc/grafana 3000:80

# Open http://localhost:3000
# Default credentials: admin / admin
```

## Scaling

### Manual Scaling

```bash
# Scale backend
kubectl scale deployment backend -n omc-staging --replicas=5

# Scale agents
kubectl scale deployment agents -n omc-staging --replicas=3
```

### Auto-Scaling (HPA)

Both backend and agents have Horizontal Pod Autoscalers configured:

**Backend HPA:**
- Min replicas: 2
- Max replicas: 10
- Target CPU: 70%
- Target Memory: 80%

**Agents HPA:**
- Min replicas: 2
- Max replicas: 5
- Target CPU: 75%
- Target Memory: 85%

View HPA status:

```bash
kubectl get hpa -n omc-staging
kubectl describe hpa backend-hpa -n omc-staging
```

## Collectors

### CronJob Schedule

- **DeFiLlama**: Daily at 2 AM UTC (`0 2 * * *`)
- **SEC API**: Daily at 3 AM UTC (`0 3 * * *`)
- **CoinSpot Announcements**: Hourly (`0 * * * *`)

### Continuous Collectors (Deployments)

- **Reddit**: Runs continuously, collects every 15 minutes
- **CryptoPanic**: Runs continuously, collects every 5 minutes

### Manually Trigger CronJob

```bash
# Create a job from CronJob
kubectl create job --from=cronjob/defillama-collector manual-run-1 -n omc-staging

# Watch job
kubectl get jobs -n omc-staging -w
```

## Rollback

### Using the Rollback Script

```bash
# Rollback all deployments
../scripts/rollback.sh staging all

# Rollback only backend
../scripts/rollback.sh staging backend

# Rollback only agents
../scripts/rollback.sh staging agents
```

### Manual Rollback

```bash
# View rollout history
kubectl rollout history deployment/backend -n omc-staging

# Rollback to previous version
kubectl rollout undo deployment/backend -n omc-staging

# Rollback to specific revision
kubectl rollout undo deployment/backend --to-revision=2 -n omc-staging

# Check status
kubectl rollout status deployment/backend -n omc-staging
```

## Troubleshooting

### Pod Not Starting

```bash
# Describe pod
kubectl describe pod <pod-name> -n omc-staging

# Check events
kubectl get events -n omc-staging --sort-by='.lastTimestamp'

# Check logs
kubectl logs <pod-name> -n omc-staging
```

### Database Connection Issues

```bash
# Test database connectivity
kubectl run -it --rm debug --image=postgres:16 --restart=Never -n omc-staging -- \
  psql -h <rds-endpoint> -U omc_user -d omc

# Check secrets
kubectl get secret backend-secrets -n omc-staging -o yaml
```

### Redis Connection Issues

```bash
# Test Redis connectivity
kubectl run -it --rm debug --image=redis:7 --restart=Never -n omc-staging -- \
  redis-cli -h <elasticache-endpoint> ping
```

### Ingress Not Working

```bash
# Check ingress
kubectl describe ingress backend-ingress -n omc-staging

# Check ALB controller logs
kubectl logs -n kube-system deployment/aws-load-balancer-controller

# Verify security groups
aws ec2 describe-security-groups --filters "Name=tag:elbv2.k8s.aws/cluster,Values=OMC-test"
```

### CronJob Not Running

```bash
# Check CronJob status
kubectl get cronjob defillama-collector -n omc-staging

# Check job history
kubectl get jobs -n omc-staging

# Check job logs
kubectl logs job/defillama-collector-<timestamp> -n omc-staging
```

## Monitoring

All applications expose metrics on `/metrics` endpoint and are automatically scraped by Prometheus via ServiceMonitors.

**Available Metrics:**
- Request count and latency
- Error rates
- Database connection pool stats
- Custom business metrics

**Dashboards:**
Access Grafana to view:
- Application performance
- Collector job success rates
- Agent system metrics
- Infrastructure health

## Security

### Network Policies (Recommended)

Apply network policies to restrict pod-to-pod communication:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-network-policy
  namespace: omc-staging
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: ingress-controller
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: database
```

### Pod Security Standards

All deployments follow restricted pod security standards:
- No privileged containers
- Run as non-root user
- Read-only root filesystem where possible
- Resource limits enforced

### Secrets Management

For production, use AWS Secrets Manager with External Secrets Operator:

1. Store secrets in AWS Secrets Manager
2. Install External Secrets Operator
3. Create ExternalSecret resources to sync secrets

## Cost Optimization

### Resource Requests and Limits

All pods have defined resource requests and limits:

**Backend:**
- Requests: 500m CPU, 512Mi memory
- Limits: 1000m CPU, 1Gi memory

**Agents:**
- Requests: 1000m CPU, 2Gi memory
- Limits: 2000m CPU, 4Gi memory

**Collectors:**
- Requests: 100m CPU, 256Mi memory
- Limits: 500m CPU, 512Mi memory

### HPA Optimization

HPAs ensure optimal resource usage:
- Scale up during high load
- Scale down during low usage
- Maintain minimum replicas for availability

## CI/CD Integration

GitHub Actions workflows automate deployment:

**Build Workflow** (`.github/workflows/build-push-ecr.yml`):
1. Build Docker images
2. Run security scans (Trivy)
3. Push to ECR

**Deploy Workflow** (`.github/workflows/deploy-to-eks.yml`):
1. Update kubeconfig
2. Deploy to EKS
3. Run smoke tests
4. Notify team

### Manual Trigger

```bash
# Trigger deployment via GitHub Actions
gh workflow run deploy-to-eks.yml \
  -f environment=staging \
  -f component=backend
```

## Next Steps

1. **Production Deployment**: Replicate setup for production environment
2. **Service Mesh**: Consider Istio or Linkerd for advanced traffic management
3. **GitOps**: Implement ArgoCD or Flux for declarative deployments
4. **Backup Strategy**: Implement Velero for cluster backups
5. **Cost Monitoring**: Set up AWS Cost Explorer dashboards

## Support

For issues or questions:
- Check Grafana dashboards
- Review application logs
- Consult team documentation
- Contact DevOps team
