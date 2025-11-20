# OMC Monitoring Stack Documentation

## Overview

The OMC monitoring stack provides comprehensive observability for the staging environment, including:

- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visualization and dashboards
- **Loki**: Log aggregation
- **Promtail**: Log collection agent
- **AlertManager**: Alert routing and notification

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     EKS Cluster                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │  Backend   │  │ Collectors │  │   Agents   │            │
│  │    Pods    │  │    Pods    │  │    Pods    │            │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘            │
│        │                │                │                   │
│        │  Metrics       │  Metrics       │  Metrics          │
│        │  Logs          │  Logs          │  Logs             │
│        └────────────────┴────────────────┘                   │
│                         │                                     │
│                         ▼                                     │
│        ┌────────────────────────────────┐                    │
│        │  Promtail (DaemonSet)          │                    │
│        │  - Collects logs from all pods │                    │
│        └────────────┬───────────────────┘                    │
│                     │                                         │
│        ┌────────────▼─────────┐  ┌─────────────────┐        │
│        │    Prometheus         │  │      Loki       │        │
│        │  - Metrics storage    │  │  - Log storage  │        │
│        │  - Alert evaluation   │  │                 │        │
│        └────────────┬──────────┘  └────────┬────────┘        │
│                     │                       │                 │
│                     ├───────────────────────┘                 │
│                     │                                         │
│                     ▼                                         │
│        ┌────────────────────────┐                            │
│        │      Grafana           │                            │
│        │  - Visualization       │                            │
│        │  - Dashboards          │                            │
│        └────────────────────────┘                            │
│                                                               │
│        ┌────────────────────────┐                            │
│        │    AlertManager        │                            │
│        │  - Alert routing       │                            │
│        │  - Notifications       │                            │
│        └────────────────────────┘                            │
└─────────────────────────────────────────────────────────────┘
```

## Deployment

### Prerequisites

1. EKS cluster running (OMC-test)
2. `kubectl` configured to access the cluster
3. Helm installed (optional, for easier deployment)

### Quick Start

Deploy all monitoring components:

```bash
# Create monitoring namespace
kubectl apply -f monitoring/prometheus-operator.yml

# Deploy Grafana
kubectl apply -f monitoring/grafana.yml

# Deploy Loki and Promtail
kubectl apply -f monitoring/loki-stack.yml

# Deploy AlertManager
kubectl apply -f monitoring/alertmanager-config.yml

# Apply alert rules
kubectl apply -f monitoring/alert-rules.yml
```

### Verify Deployment

```bash
# Check all pods in monitoring namespace
kubectl get pods -n monitoring

# Expected output:
# NAME                            READY   STATUS    RESTARTS   AGE
# prometheus-xxxxx                1/1     Running   0          5m
# grafana-xxxxx                   1/1     Running   0          5m
# loki-xxxxx                      1/1     Running   0          5m
# promtail-xxxxx                  1/1     Running   0          5m
# alertmanager-xxxxx              1/1     Running   0          5m
```

### Access Grafana

Get Grafana LoadBalancer URL:

```bash
kubectl get svc grafana -n monitoring
```

Default credentials:
- Username: `admin`
- Password: `admin` (change on first login!)

## Configuration

### Prometheus

Configuration in `monitoring/prometheus-operator.yml`:

- **Scrape interval**: 15 seconds
- **Retention**: 15 days
- **Target discovery**: Kubernetes service discovery
- **Alert rules**: Defined in `monitoring/alert-rules.yml`

### Grafana

Datasources automatically configured:
- **Prometheus**: Default datasource for metrics
- **Loki**: For log queries

### Loki

Configuration in `monitoring/loki-stack.yml`:

- **Retention**: 7 days (168 hours)
- **Storage**: Local filesystem (ephemeral)
- **Ingestion rate**: 10MB/s
- **Burst size**: 20MB

**Note**: For production, configure S3 backend for log storage.

### AlertManager

Configuration in `monitoring/alertmanager-config.yml`:

- **Default receiver**: webhook (configure as needed)
- **Grouping**: By alertname, cluster, service
- **Repeat interval**: 12 hours

**To configure notifications**, edit the AlertManager ConfigMap and add:
- Slack webhook
- Email settings
- PagerDuty integration
- Other notification channels

## Alert Rules

### Infrastructure Alerts

- **HighNodeCPU**: Node CPU > 80% for 5 minutes
- **HighNodeMemory**: Node memory > 85% for 5 minutes
- **LowDiskSpace**: Disk space < 15%

### Pod Alerts

- **PodRestarting**: Pod restarting frequently
- **PodCrashLooping**: Pod in crash loop
- **PodNotReady**: Pod not ready for 10 minutes

### Application Alerts

- **HighErrorRate**: HTTP 5xx error rate > 5%
- **ApplicationDown**: Application endpoint unreachable
- **DatabaseConnectionFailures**: Database connection errors

### Collector Alerts

- **CollectorJobFailed**: Collector CronJob failed
- **CollectorMissedRun**: Collector hasn't run in 2 hours

See `monitoring/alert-rules.yml` for complete list.

## Dashboards

Grafana comes with pre-configured datasources. Import dashboards:

1. **Kubernetes Cluster Dashboard**: ID 7249
2. **Kubernetes Pods Dashboard**: ID 6417
3. **Node Exporter Full**: ID 1860
4. **Loki Dashboard**: ID 13639

Custom dashboards will be added for:
- Backend API metrics
- Collector job metrics
- Agent system metrics
- Database performance

## Troubleshooting

### Prometheus not scraping

Check ServiceMonitor configuration:

```bash
kubectl get servicemonitor -n omc-staging
kubectl describe servicemonitor backend-monitor -n omc-staging
```

Verify Prometheus targets:

```bash
# Port-forward Prometheus
kubectl port-forward svc/prometheus -n monitoring 9090:9090

# Open http://localhost:9090/targets
```

### Grafana can't connect to datasources

Check Grafana logs:

```bash
kubectl logs deployment/grafana -n monitoring
```

Verify Prometheus and Loki services are running:

```bash
kubectl get svc -n monitoring
```

### Loki not receiving logs

Check Promtail status:

```bash
kubectl get pods -n monitoring -l app=promtail
kubectl logs -n monitoring -l app=promtail --tail=50
```

Verify Promtail can reach Loki:

```bash
kubectl exec -n monitoring <promtail-pod> -- wget -O- http://loki:3100/ready
```

### Alerts not firing

Check AlertManager:

```bash
# Port-forward AlertManager
kubectl port-forward svc/alertmanager -n monitoring 9093:9093

# Open http://localhost:9093
```

Verify alert rules loaded:

```bash
# Port-forward Prometheus
kubectl port-forward svc/prometheus -n monitoring 9090:9090

# Open http://localhost:9090/rules
```

## Metrics

### Application Metrics

Applications should expose metrics on `/metrics` endpoint:

- **Backend API**: Port 8000
- **Agents**: Port 8001
- **Collectors**: Via job completion metrics

### Custom Metrics

To add custom metrics to your application:

1. Install Prometheus client library
2. Create metrics in your code
3. Expose `/metrics` endpoint
4. Add ServiceMonitor or PodMonitor

Example Python (FastAPI):

```python
from prometheus_client import Counter, Histogram, generate_latest

# Define metrics
request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## Maintenance

### Updating Alert Rules

1. Edit `monitoring/alert-rules.yml`
2. Apply changes:
   ```bash
   kubectl apply -f monitoring/alert-rules.yml
   ```
3. Reload Prometheus configuration:
   ```bash
   kubectl exec -n monitoring deployment/prometheus -- kill -HUP 1
   ```

### Scaling

Increase Prometheus storage:

```yaml
# In prometheus-operator.yml
volumeMounts:
  - name: prometheus-storage
    mountPath: /prometheus
volumes:
  - name: prometheus-storage
    persistentVolumeClaim:
      claimName: prometheus-storage  # Use PVC instead of emptyDir
```

Increase Grafana replicas:

```bash
kubectl scale deployment grafana -n monitoring --replicas=2
```

## Security

### Securing Grafana

1. Change default admin password immediately
2. Enable HTTPS (configure Ingress with TLS)
3. Set up OAuth or LDAP authentication
4. Restrict dashboard editing permissions

### Securing Prometheus

1. Enable authentication (use sidecar proxy)
2. Restrict API access
3. Use NetworkPolicies to limit access

### Secrets Management

For production:

1. Use AWS Secrets Manager for API keys
2. Use External Secrets Operator to sync secrets
3. Rotate credentials regularly

## Cost Optimization

Current configuration uses ephemeral storage (emptyDir):
- **Pros**: No additional costs
- **Cons**: Data lost on pod restart

For production:

1. Use EBS volumes for Prometheus (persistent metrics)
2. Use S3 for Loki (long-term log storage)
3. Configure appropriate retention periods
4. Use Grafana Cloud for dashboards (optional)

## Support

For issues or questions:

1. Check Grafana dashboards for system health
2. Review Prometheus alerts
3. Check application logs via Loki
4. Consult team documentation in `infrastructure/terraform/OPERATIONS_RUNBOOK.md`

## Next Steps

1. Configure notification channels in AlertManager
2. Create custom dashboards for OMC applications
3. Set up log-based alerts in Loki
4. Implement distributed tracing (Jaeger/Tempo)
5. Add business metrics to applications
