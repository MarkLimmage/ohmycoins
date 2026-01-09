# AWS EKS Infrastructure - Quick Reference

## 📋 Documentation Index

| Document | Purpose | Estimated Time |
|----------|---------|---------------|
| [README.md](./README.md) | Complete overview and architecture | 10 min read |
| [STEP0_CREATE_CLUSTER.md](./STEP0_CREATE_CLUSTER.md) | Create EKS cluster with new VPC | 20 min setup |
| [STEP1_INSTALL_ARC.md](./STEP1_INSTALL_ARC.md) | Install Actions Runner Controller | 10 min setup |
| [STEP2_UPDATE_WORKFLOWS.md](./STEP2_UPDATE_WORKFLOWS.md) | Update workflows for self-hosted runners | 30 min setup |

## 🚀 Quick Start Commands

### Create EKS Cluster
```bash
cd infrastructure/aws/eks
eksctl create cluster -f eks-cluster-new-vpc.yml
# Wait ~20 minutes
kubectl get nodes
```

### Install Actions Runner Controller
```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.3/cert-manager.yaml

# Install ARC via Helm
helm repo add actions-runner-controller https://actions-runner-controller.github.io/actions-runner-controller
helm repo update
helm install arc --namespace actions-runner-system --create-namespace actions-runner-controller/actions-runner-controller

# Create GitHub auth secret (replace YOUR_TOKEN)
kubectl create namespace actions-runner-system
kubectl create secret generic github-auth \
  --namespace=actions-runner-system \
  --from-literal=github_token=YOUR_GITHUB_PAT

# Deploy runners
kubectl apply -f arc-manifests/runner-deployment.yaml
kubectl apply -f arc-manifests/runner-autoscaler.yaml
```

### Verify Setup
```bash
# Run health check script
./check-health.sh

# Check runners in Kubernetes
kubectl get pods -n actions-runner-system
kubectl get runnerdeployment -n actions-runner-system

# Check runners in GitHub
# Go to: https://github.com/MarkLimmage/ohmycoins/settings/actions/runners
```

## 📁 File Reference

### Configuration Files

| File | Description |
|------|-------------|
| `eks-cluster-new-vpc.yml` | EKS cluster configuration with auto-created VPC |
| `arc-manifests/runner-deployment.yaml` | Base runner deployment (test environment) |
| `arc-manifests/runner-deployment-staging.yaml` | Staging runner deployment |
| `arc-manifests/runner-deployment-production.yaml` | Production runner deployment |
| `arc-manifests/runner-autoscaler.yaml` | Autoscaling for test runners |
| `arc-manifests/runner-autoscaler-staging.yaml` | Autoscaling for staging runners |
| `arc-manifests/runner-autoscaler-production.yaml` | Autoscaling for production runners |
| `arc-manifests/github-auth-secret.yaml.template` | Template for GitHub authentication |

### Scripts

| Script | Purpose |
|--------|---------|
| `check-health.sh` | Health check script for cluster and runners |

### Workflows

| Workflow | Purpose |
|----------|---------|
| `.github/workflows/test-self-hosted-runner.yml` | Test self-hosted runner functionality |

## 🏷️ Runner Labels

Use these labels in your workflow `runs-on` configuration:

| Environment | Labels | Use Case |
|------------|--------|----------|
| Test | `[self-hosted, eks, test]` | Development and testing |
| Staging | `[self-hosted, eks, staging]` | Staging deployments |
| Production | `[self-hosted, eks, production]` | Production deployments |

Example workflow:
```yaml
jobs:
  test:
    runs-on: [self-hosted, eks, test]
  deploy-staging:
    runs-on: [self-hosted, eks, staging]
  deploy-prod:
    runs-on: [self-hosted, eks, production]
```

## 🔧 Common Commands

### Cluster Management
```bash
# View cluster info
eksctl get cluster --name copilot-test-cluster --region us-west-2

# Update cluster
eksctl upgrade cluster --name copilot-test-cluster --region us-west-2 --approve

# Delete cluster
eksctl delete cluster --name copilot-test-cluster --region us-west-2
```

### Runner Management
```bash
# View runner deployments
kubectl get runnerdeployment -n actions-runner-system

# View runner pods
kubectl get pods -n actions-runner-system

# View runner logs
kubectl logs -n actions-runner-system -l app.kubernetes.io/component=runner --tail=50

# Scale runners manually
kubectl scale runnerdeployment ohmycoins-runners --replicas=3 -n actions-runner-system

# Delete runners
kubectl delete runnerdeployment ohmycoins-runners -n actions-runner-system
```

### Troubleshooting
```bash
# Check node status
kubectl get nodes
kubectl describe node <node-name>

# Check pod status
kubectl get pods -n actions-runner-system
kubectl describe pod <pod-name> -n actions-runner-system

# Check logs
kubectl logs -n actions-runner-system deployment/arc-actions-runner-controller
kubectl logs -n actions-runner-system <runner-pod-name>

# Check events
kubectl get events -n actions-runner-system --sort-by='.lastTimestamp'

# Check resource usage
kubectl top nodes
kubectl top pods -n actions-runner-system
```

## 💰 Cost Management

### Monitor Costs
```bash
# Check running resources
aws ec2 describe-instances --filters "Name=tag:alpha.eksctl.io/cluster-name,Values=copilot-test-cluster" --region us-west-2
aws ec2 describe-nat-gateways --filter "Name=tag:alpha.eksctl.io/cluster-name,Values=copilot-test-cluster" --region us-west-2
```

### Cost Optimization
- Scale runners to 0 when not in use: `kubectl scale runnerdeployment ohmycoins-runners --replicas=0 -n actions-runner-system`
- Delete cluster when not needed: `eksctl delete cluster --name copilot-test-cluster --region us-west-2`
- Use Spot instances for test/staging: Modify `eks-cluster-new-vpc.yml` with `instancesDistribution`

## 🔐 Security Checklist

- [ ] GitHub PAT has minimal required permissions
- [ ] IMDSv2 enabled (already configured)
- [ ] Ephemeral runners enabled (already configured)
- [ ] Network policies configured (if needed)
- [ ] VPC Flow Logs enabled
- [ ] EKS audit logging enabled
- [ ] Secrets stored in AWS Secrets Manager or Kubernetes secrets
- [ ] Regular security updates applied

## 📊 Monitoring

### Key Metrics to Track
- Runner pod count and status
- CPU and memory utilization
- Workflow queue time
- Job success/failure rate
- Network traffic and costs

### Set Up Alerts For
- Runner pod failures
- High CPU/memory usage
- Autoscaling events
- Authentication failures
- Cost threshold breaches

## 🆘 Emergency Procedures

### Runners Not Working
1. Check runner pods: `kubectl get pods -n actions-runner-system`
2. Check controller logs: `kubectl logs -n actions-runner-system deployment/arc-actions-runner-controller`
3. Verify GitHub secret: `kubectl get secret github-auth -n actions-runner-system`
4. Restart ARC: `kubectl rollout restart deployment arc-actions-runner-controller -n actions-runner-system`

### High Costs
1. Scale down runners: `kubectl scale runnerdeployment --all --replicas=0 -n actions-runner-system`
2. Check for runaway pods: `kubectl get pods --all-namespaces`
3. Review AWS Cost Explorer for unexpected charges

### Cluster Issues
1. Check CloudFormation stacks in AWS console
2. Review CloudWatch logs for EKS control plane
3. Contact AWS Support if needed

## 📚 Additional Resources

- [AWS EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
- [Actions Runner Controller Docs](https://github.com/actions/actions-runner-controller)
- [GitHub Actions Security](https://docs.github.com/en/actions/security-guides)
- [eksctl Documentation](https://eksctl.io/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)

## 🤝 Support

- **Infrastructure Issues**: Check documentation in this directory
- **GitHub Actions Issues**: See [STEP2_UPDATE_WORKFLOWS.md](./STEP2_UPDATE_WORKFLOWS.md)
- **AWS Issues**: Contact AWS Support
- **General Questions**: Open an issue in the repository

---

**Last Updated**: 2024  
**Maintained By**: Oh My Coins Development Team
