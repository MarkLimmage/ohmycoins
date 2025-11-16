# AWS EKS Infrastructure for GitHub Actions Runners

This directory contains infrastructure-as-code and documentation for setting up a self-hosted GitHub Actions runner environment on AWS EKS.

## Overview

The Oh My Coins project uses GitHub Actions for CI/CD. This infrastructure enables running workflows on self-hosted runners in AWS EKS, providing:

- **Controlled Environment**: Run builds and tests in a managed Kubernetes cluster
- **AWS Integration**: Direct access to AWS resources (databases, services, etc.)
- **Cost Control**: Scale runners based on demand, scale to zero when idle
- **Enhanced Security**: Isolated network environment with security groups and IAM
- **Better Performance**: Larger instance types and dedicated resources

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     GitHub Repository                        │
│                   MarkLimmage/ohmycoins                      │
└─────────────────────┬───────────────────────────────────────┘
                      │ Workflow Triggers
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  AWS EKS Cluster                             │
│              copilot-test-cluster                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │    Actions Runner Controller (ARC)                   │   │
│  │    - Watches for workflow jobs                       │   │
│  │    - Creates/scales runner pods                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │    Runner Pods (Managed Node Group)                  │   │
│  │    ┌────────────┐  ┌────────────┐  ┌────────────┐   │   │
│  │    │  Runner 1  │  │  Runner 2  │  │  Runner N  │   │   │
│  │    │  (t3.large)│  │  (t3.large)│  │  (t3.large)│   │   │
│  │    └────────────┘  └────────────┘  └────────────┘   │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │    VPC (Auto-created by eksctl)                      │   │
│  │    - Public Subnets (NAT, Load Balancers)           │   │
│  │    - Private Subnets (Runner Pods)                  │   │
│  │    - Internet Gateway + NAT Gateway                  │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
infrastructure/aws/eks/
├── README.md                          # This file
├── STEP0_CREATE_CLUSTER.md            # EKS cluster setup guide
├── STEP1_INSTALL_ARC.md               # Actions Runner Controller setup
├── STEP2_UPDATE_WORKFLOWS.md          # Workflow migration guide
├── eks-cluster-new-vpc.yml            # EKS cluster configuration
└── arc-manifests/                     # Kubernetes manifests for ARC
    ├── runner-deployment.yaml         # Base runner deployment
    ├── runner-autoscaler.yaml         # Horizontal autoscaler
    └── github-auth-secret.yaml.template  # Authentication secret template
```

## Quick Start

Follow these steps in order:

### Step 0: Create EKS Cluster
Create the EKS cluster with a new VPC. This sets up all networking and compute resources.

**Time**: ~20 minutes  
**Doc**: [STEP0_CREATE_CLUSTER.md](./STEP0_CREATE_CLUSTER.md)

```bash
cd infrastructure/aws/eks
eksctl create cluster -f eks-cluster-new-vpc.yml
```

### Step 1: Install Actions Runner Controller
Install ARC to manage GitHub Actions runners in your cluster.

**Time**: ~10 minutes  
**Doc**: [STEP1_INSTALL_ARC.md](./STEP1_INSTALL_ARC.md)

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.3/cert-manager.yaml

# Install ARC via Helm
helm repo add actions-runner-controller https://actions-runner-controller.github.io/actions-runner-controller
helm repo update
helm install arc --namespace actions-runner-system --create-namespace actions-runner-controller/actions-runner-controller

# Deploy runners
kubectl apply -f arc-manifests/runner-deployment.yaml
kubectl apply -f arc-manifests/runner-autoscaler.yaml
```

### Step 2: Update GitHub Actions Workflows
Update your workflows to use the self-hosted runners.

**Time**: ~30 minutes  
**Doc**: [STEP2_UPDATE_WORKFLOWS.md](./STEP2_UPDATE_WORKFLOWS.md)

```yaml
# In .github/workflows/*.yml
jobs:
  my-job:
    runs-on: [self-hosted, eks, test]  # Changed from ubuntu-latest
```

## Prerequisites

Before starting, ensure you have:

- **AWS Account** with appropriate permissions
- **AWS CLI** configured (`aws configure`)
- **eksctl** v0.150.0+ ([install guide](https://eksctl.io/installation/))
- **kubectl** v1.28+ ([install guide](https://kubernetes.io/docs/tasks/tools/))
- **Helm** v3.x ([install guide](https://helm.sh/docs/intro/install/))
- **GitHub Personal Access Token** or GitHub App credentials

## Configuration Options

### Cluster Configuration

Edit `eks-cluster-new-vpc.yml` to customize:

- **Region**: Change `us-west-2` to your preferred region
- **Instance Type**: Adjust `t3.large` for more/less resources
- **Capacity**: Modify `minSize`, `maxSize`, `desiredCapacity`
- **Cluster Name**: Change `copilot-test-cluster`

### Runner Configuration

Edit `arc-manifests/runner-deployment.yaml` to customize:

- **Repository**: Change `MarkLimmage/ohmycoins`
- **Labels**: Add custom labels for workflow targeting
- **Resources**: Adjust CPU/memory limits
- **Replicas**: Set initial runner count

### Autoscaling Configuration

Edit `arc-manifests/runner-autoscaler.yaml` to customize:

- **minReplicas/maxReplicas**: Set scaling boundaries
- **scaleUpThreshold**: Adjust when to add runners
- **scaleDownThreshold**: Adjust when to remove runners

## Cost Estimation

Estimated monthly costs (us-west-2):

| Resource | Cost | Notes |
|----------|------|-------|
| EKS Control Plane | $73 | Fixed cost |
| EC2 t3.large (1 node) | $60 | ~$0.0832/hour |
| NAT Gateway | $32 | ~$0.045/hour |
| EBS Storage (20GB) | $10 | Per node |
| Data Transfer | Variable | Depends on usage |
| **Total** | **~$175-200/month** | For minimal setup |

### Cost Optimization Tips

1. **Scale to Zero**: Configure autoscaler to scale down to 0 when idle
2. **Spot Instances**: Use EC2 Spot for non-critical workloads (60-80% savings)
3. **Right-sizing**: Monitor usage and adjust instance types
4. **Delete When Unused**: Delete cluster during extended idle periods
5. **VPC Sharing**: Share VPC with other workloads

## Security Best Practices

1. **IAM Least Privilege**: Grant minimal required permissions
2. **Network Policies**: Restrict pod-to-pod communication
3. **Secrets Management**: Use AWS Secrets Manager or Kubernetes secrets
4. **Image Scanning**: Scan runner images for vulnerabilities
5. **Audit Logging**: Enable EKS control plane logging
6. **VPC Flow Logs**: Monitor network traffic
7. **IMDSv2**: Use IMDSv2 for instance metadata (already configured)
8. **Ephemeral Runners**: Use ephemeral mode (already configured)

## Monitoring and Troubleshooting

### Check Cluster Health
```bash
# Cluster status
eksctl get cluster --name copilot-test-cluster --region us-west-2

# Node status
kubectl get nodes

# All pods
kubectl get pods --all-namespaces
```

### Check Runners
```bash
# Runner pods
kubectl get pods -n actions-runner-system

# Runner logs
kubectl logs -n actions-runner-system -l app.kubernetes.io/component=runner

# Runner deployment status
kubectl get runnerdeployment -n actions-runner-system
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Runners not appearing in GitHub | Check authentication secret and controller logs |
| Pods failing to start | Check resource limits and node capacity |
| Network connectivity issues | Verify NAT Gateway and security groups |
| Workflow job not picking up runner | Verify runner labels match workflow `runs-on` |
| High costs | Check node count and autoscaling configuration |

## Maintenance

### Update EKS Cluster
```bash
eksctl upgrade cluster --name copilot-test-cluster --region us-west-2 --approve
```

### Update Node Group AMI
```bash
eksctl upgrade nodegroup --cluster=copilot-test-cluster --name=arc-runner-nodes --region=us-west-2
```

### Update ARC
```bash
helm upgrade arc --namespace actions-runner-system actions-runner-controller/actions-runner-controller
```

## Cleanup

To completely remove all resources:

```bash
# Delete runner deployments
kubectl delete -f arc-manifests/

# Uninstall ARC
helm uninstall arc -n actions-runner-system

# Delete cluster (this deletes VPC and all resources)
eksctl delete cluster --name copilot-test-cluster --region us-west-2
```

**Warning**: This is irreversible and will delete all data. Ensure you have backups.

## Support and Resources

- **Issues**: Report issues in the GitHub repository
- **Documentation**: See step-by-step guides in this directory
- **AWS Support**: Use AWS Support for infrastructure issues
- **Community**: GitHub Actions and eksctl communities

## References

- [eksctl Documentation](https://eksctl.io/)
- [Actions Runner Controller](https://github.com/actions/actions-runner-controller)
- [AWS EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
- [GitHub Actions Self-hosted Runners](https://docs.github.com/en/actions/hosting-your-own-runners)
- [Kubernetes Documentation](https://kubernetes.io/docs/)

## License

This infrastructure configuration is part of the Oh My Coins project.  
Copyright © 2025 Mark Limmage. All rights reserved.
