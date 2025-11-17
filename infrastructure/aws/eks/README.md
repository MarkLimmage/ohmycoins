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
│                  AWS EKS Cluster: OMC-test                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │    System Nodes (Always-On)                          │   │
│  │    - 1× t3.medium instance                           │   │
│  │    - Taint: CriticalAddonsOnly=true                  │   │
│  │    ┌────────────┐  ┌────────────┐  ┌────────────┐   │   │
│  │    │  CoreDNS   │  │    ARC     │  │  Cluster   │   │   │
│  │    │            │  │ Controller │  │ Autoscaler │   │   │
│  │    └────────────┘  └────────────┘  └────────────┘   │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │    Runner Nodes (Scale-to-Zero)                      │   │
│  │    - 0-10× t3.large instances                        │   │
│  │    - Taint: github-runners=true                      │   │
│  │    ┌────────────┐  ┌────────────┐  ┌────────────┐   │   │
│  │    │  Runner 1  │  │  Runner 2  │  │  Runner N  │   │   │
│  │    │ (ephemeral)│  │ (ephemeral)│  │ (ephemeral)│   │   │
│  │    └────────────┘  └────────────┘  └────────────┘   │   │
│  │    Scales automatically: 0 → N when jobs run         │   │
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

### Architecture Highlights

**Two-Node-Group Strategy:**
- **system-nodes**: Always-on group (1 node) hosting critical Kubernetes components
- **arc-runner-nodes**: Scalable group (0-10 nodes) dedicated to GitHub Actions runners

**Cost Optimization:**
- Runner nodes scale to zero when no workflows are active
- Cluster Autoscaler provisions nodes on-demand when jobs are queued
- Estimated 40-60% cost savings compared to always-on configuration

**Workload Isolation:**
- Taints and tolerations ensure clean separation between system and runner workloads
- System components never compete with runners for resources
- Runner pods exclusively use dedicated runner nodes

## Directory Structure

```
infrastructure/aws/eks/
├── README.md                          # This file - overview and quick start
├── STEP0_CREATE_CLUSTER.md            # EKS cluster setup guide
├── STEP1_INSTALL_ARC.md               # Actions Runner Controller setup
├── STEP2_UPDATE_WORKFLOWS.md          # Workflow migration guide
├── EKS_AUTOSCALING_CONFIGURATION.md   # Autoscaling architecture and troubleshooting
├── QUICK_REFERENCE.md                 # Quick command reference
├── eks-cluster-new-vpc.yml            # EKS cluster configuration (two node groups)
└── arc-manifests/                     # Kubernetes manifests for ARC
    ├── runner-deployment.yaml         # Runner deployment with tolerations
    ├── cluster-autoscaler.yaml        # Cluster Autoscaler with RBAC
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

### Configuration Options

### Cluster Configuration

Edit `eks-cluster-new-vpc.yml` to customize:

- **Region**: `ap-southeast-2` (current setting)
- **Cluster Name**: `OMC-test` (current setting)
- **System Nodes**:
  - Instance Type: `t3.medium` (for critical components)
  - Capacity: `minSize: 1`, `maxSize: 2` (always-on)
  - Taint: `CriticalAddonsOnly=true:NoSchedule`
- **Runner Nodes**:
  - Instance Type: `t3.large` (for CI/CD workloads)
  - Capacity: `minSize: 0`, `maxSize: 10` (scale-to-zero)
  - Taint: `github-runners=true:NoSchedule`

### Runner Configuration

Edit `arc-manifests/runner-deployment.yaml` to customize:

- **Repository**: `MarkLimmage/ohmycoins` (current setting)
- **Labels**: `[self-hosted, eks, test]` for workflow targeting
- **Tolerations**: Must include `github-runners=true:NoSchedule`
- **Resources**: Adjust CPU/memory limits for runner pods

### Cluster Autoscaler Configuration

The Cluster Autoscaler is configured in `arc-manifests/cluster-autoscaler.yaml`:

- **Auto-Discovery**: Uses ASG tags to find node groups automatically
- **Expander**: `least-waste` strategy for cost optimization
- **IAM Permissions**: Attached to system-nodes role
- **Toleration**: `CriticalAddonsOnly=true:NoSchedule` (runs on system-nodes)

**No manual configuration needed** - autoscaling works out of the box!

## Cost Estimation

Estimated monthly costs (ap-southeast-2, current configuration):

| Resource | Cost | Notes |
|----------|------|-------|
| EKS Control Plane | $73 | Fixed cost |
| EC2 t3.medium (system-nodes, 1 always-on) | $30 | ~$0.0416/hour |
| EC2 t3.large (runner-nodes, on-demand) | Variable | ~$0.0832/hour × hours active |
| NAT Gateway | $32 | ~$0.045/hour |
| EBS Storage (20GB × nodes) | $10-50 | Depends on node count |
| Data Transfer | Variable | Depends on usage |
| **Baseline (0 runners)** | **~$135-145/month** | With no active workflows |
| **With runners (10% utilization)** | **~$155-170/month** | ~75 hours/month of runner activity |
| **With runners (50% utilization)** | **~$225-250/month** | ~365 hours/month of runner activity |

### Cost Comparison

| Configuration | Monthly Cost | Notes |
|---------------|--------------|-------|
| **Before (single node group)** | $175-200 | 1× t3.large always running |
| **After (two node groups)** | $135-170 | Scale-to-zero enabled, 10% utilization |
| **Savings** | 15-30% | Additional savings at lower utilization |

### Cost Optimization Tips

1. **Scale to Zero**: Runner nodes automatically scale to 0 when idle (✅ implemented)
2. **Spot Instances**: Use EC2 Spot for runner nodes (potential 60-80% savings)
3. **Right-sizing**: Monitor usage and adjust instance types
4. **Delete When Unused**: Delete cluster during extended idle periods
5. **VPC Sharing**: Share VPC with other workloads to split NAT Gateway costs
6. **Reduce Runner Node Max**: Lower maxSize if <10 parallel jobs are needed

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
| Pods stuck in Pending | Check taints/tolerations and Cluster Autoscaler logs |
| Runner pods on wrong nodes | Verify toleration in runner-deployment.yaml |
| Cluster Autoscaler not scaling | Check IAM permissions and ASG auto-discovery tags |
| AccessDenied errors in CA logs | Attach OMC-ClusterAutoscalerPolicy to system-nodes role |
| Network connectivity issues | Verify NAT Gateway and security groups |
| Workflow job not picking up runner | Verify runner labels match workflow `runs-on` |
| High costs | Check node count, review autoscaling, consider spot instances |

**For detailed troubleshooting**, see [EKS_AUTOSCALING_CONFIGURATION.md](./EKS_AUTOSCALING_CONFIGURATION.md)

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
kubectl delete -f arc-manifests/runner-deployment.yaml

# Delete Cluster Autoscaler
kubectl delete -f arc-manifests/cluster-autoscaler.yaml

# Uninstall ARC
helm uninstall arc -n actions-runner-system

# Delete cert-manager (if no longer needed)
kubectl delete -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.3/cert-manager.yaml

# Delete cluster (this deletes both node groups, VPC, and all resources)
eksctl delete cluster --name OMC-test --region ap-southeast-2
```

**Warning**: This is irreversible and will delete all data. Ensure you have backups.

### Cleanup Verification

```bash
# Verify cluster is deleted
eksctl get cluster --name OMC-test --region ap-southeast-2

# Check for remaining EC2 instances
aws ec2 describe-instances --filters "Name=tag:eks:cluster-name,Values=OMC-test" --region ap-southeast-2

# Verify IAM policy removal (optional)
aws iam delete-policy --policy-arn arn:aws:iam::220711411889:policy/OMC-ClusterAutoscalerPolicy
```

## Support and Resources

- **Issues**: Report issues in the GitHub repository
- **Documentation**: See step-by-step guides in this directory
- **AWS Support**: Use AWS Support for infrastructure issues
- **Community**: GitHub Actions and eksctl communities

## References

- [eksctl Documentation](https://eksctl.io/)
- [Actions Runner Controller](https://github.com/actions/actions-runner-controller)
- [AWS EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
- [Cluster Autoscaler on AWS](https://github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler/cloudprovider/aws)
- [Kubernetes Taints and Tolerations](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/)
- [GitHub Actions Self-hosted Runners](https://docs.github.com/en/actions/hosting-your-own-runners)
- [Kubernetes Documentation](https://kubernetes.io/docs/)

## Current Status

**Cluster:** OMC-test (ap-southeast-2)  
**Kubernetes Version:** 1.32  
**Implementation Status:** ✅ Complete and Operational  
**Node Groups:**
- system-nodes: 1× t3.medium (always-on)
- arc-runner-nodes: 0-10× t3.large (scale-to-zero)

**Last Updated:** November 17, 2025

## License

This infrastructure configuration is part of the Oh My Coins project.  
Copyright © 2025 Mark Limmage. All rights reserved.
