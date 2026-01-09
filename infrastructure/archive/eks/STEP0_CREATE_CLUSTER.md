# AWS EKS Test Server Setup Guide

This guide walks through setting up an AWS EKS cluster with GitHub Actions self-hosted runners for the Oh My Coins project.

## Overview

This infrastructure enables running GitHub Actions workflows on self-hosted runners in AWS EKS, providing a more permissive and controlled environment for CI/CD operations.

## Prerequisites

Before starting, ensure you have:

1. **AWS CLI** installed and configured with appropriate credentials
   ```bash
   aws --version
   aws configure
   ```

2. **eksctl** installed (v0.150.0 or later recommended)
   ```bash
   # macOS
   brew install eksctl
   
   # Linux
   curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
   sudo mv /tmp/eksctl /usr/local/bin
   
   # Verify installation
   eksctl version
   ```

3. **kubectl** installed (v1.28 or later recommended)
   ```bash
   # macOS
   brew install kubectl
   
   # Linux
   curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
   sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
   
   # Verify installation
   kubectl version --client
   ```

4. **Helm** (v3.x) for installing Actions Runner Controller
   ```bash
   # macOS
   brew install helm
   
   # Linux
   curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
   
   # Verify installation
   helm version
   ```

5. **AWS IAM Permissions** - Your AWS user/role needs permissions to:
   - Create VPCs, subnets, route tables, internet gateways, NAT gateways
   - Create EKS clusters and managed node groups
   - Create IAM roles and policies
   - Create security groups
   - Create CloudFormation stacks (eksctl uses this)

## Step 0: Create EKS Cluster with New VPC

This step creates a complete, production-ready infrastructure including:
- A new high-availability VPC
- Public and private subnets across multiple availability zones
- Internet Gateway for public subnet access
- NAT Gateway for private subnet internet access (e.g., pulling container images)
- All necessary route tables
- EKS cluster with managed node group
- Required IAM roles and OIDC provider

### 1. Review the Cluster Configuration

The configuration file is located at: `infrastructure/aws/eks/eks-cluster-new-vpc.yml`

Key parameters:
- **Cluster Name**: `copilot-test-cluster`
- **Region**: `us-west-2` (modify as needed)
- **Instance Type**: `t3.large` (2 vCPU, 8 GiB RAM)
- **Node Capacity**: 1 node (can scale 1-5)

### 2. Deploy the EKS Cluster

Run the following command from the repository root:

```bash
cd infrastructure/aws/eks
eksctl create cluster -f eks-cluster-new-vpc.yml
```

**Expected Duration**: 15-20 minutes

The command will:
1. Create a CloudFormation stack for the VPC and networking
2. Create the EKS cluster control plane
3. Create managed node group with EC2 instances
4. Configure kubectl context automatically

### 3. Verify Cluster Creation

After deployment completes, verify the cluster is ready:

```bash
# Check cluster status
eksctl get cluster --name copilot-test-cluster --region us-west-2

# Check nodes are ready
kubectl get nodes

# Expected output:
# NAME                                           STATUS   ROLES    AGE   VERSION
# ip-192-168-x-x.us-west-2.compute.internal     Ready    <none>   2m    v1.28.x
```

### 4. Verify Networking Components

Check that all networking resources were created:

```bash
# List VPC
aws ec2 describe-vpcs --filters "Name=tag:alpha.eksctl.io/cluster-name,Values=copilot-test-cluster" --region us-west-2

# List subnets
aws ec2 describe-subnets --filters "Name=tag:alpha.eksctl.io/cluster-name,Values=copilot-test-cluster" --region us-west-2

# List NAT gateways
aws ec2 describe-nat-gateways --filter "Name=tag:alpha.eksctl.io/cluster-name,Values=copilot-test-cluster" --region us-west-2
```

## What Gets Created

### Network Infrastructure
- **VPC**: New VPC with CIDR block (automatically assigned)
- **Public Subnets**: 2-3 subnets across availability zones (for load balancers)
- **Private Subnets**: 2-3 subnets across availability zones (for runner pods)
- **Internet Gateway**: Enables public subnet internet access
- **NAT Gateway**: Enables private subnet outbound internet access
- **Route Tables**: Proper routing configuration for all subnets

### Compute Resources
- **EKS Cluster**: Kubernetes control plane (managed by AWS)
- **Managed Node Group**: EC2 instances running Kubernetes workers
- **Security Groups**: Network security for cluster and nodes

### IAM Resources
- **Cluster IAM Role**: Permissions for EKS control plane
- **Node Instance IAM Role**: Permissions for EC2 worker nodes
- **OIDC Provider**: Enables IAM roles for service accounts (IRSA)
- **VPC CNI IAM Role**: Required for pod networking

## Cost Considerations

Estimated monthly costs (us-west-2, as of 2024):
- **EKS Cluster**: ~$73/month (control plane)
- **EC2 t3.large**: ~$60/month per node (1 node minimum)
- **NAT Gateway**: ~$32/month + data transfer costs
- **EBS Volumes**: ~$10/month (20GB per node)
- **Data Transfer**: Variable based on usage

**Total Estimated**: ~$175-200/month for minimal setup

To minimize costs:
- Use Spot Instances for non-production workloads
- Scale down to 0 nodes when not in use
- Delete the cluster when not needed: `eksctl delete cluster --name copilot-test-cluster --region us-west-2`

## Troubleshooting

### Cluster Creation Fails

If cluster creation fails:

```bash
# Check CloudFormation stack events
aws cloudformation describe-stack-events --stack-name eksctl-copilot-test-cluster-cluster --region us-west-2

# Delete failed cluster and retry
eksctl delete cluster --name copilot-test-cluster --region us-west-2
```

### Insufficient Permissions

Error: "User is not authorized to perform..."

Solution: Ensure your AWS credentials have the required IAM permissions listed in Prerequisites.

### Nodes Not Ready

If nodes show "NotReady" status:

```bash
# Check node details
kubectl describe node <node-name>

# Check system pods
kubectl get pods -n kube-system
```

Common causes:
- VPC CNI plugin not running
- Security group misconfiguration
- Instance metadata service (IMDS) issues

## Next Steps

After successfully creating the cluster, proceed to:
- **Step 1**: Install Actions Runner Controller (ARC)
- **Step 2**: Configure GitHub App for runner authentication
- **Step 3**: Deploy runner pods
- **Step 4**: Update GitHub Actions workflows

See [STEP1_INSTALL_ARC.md](./STEP1_INSTALL_ARC.md) for next steps.

## Cleanup

To completely remove the EKS cluster and all resources:

```bash
# Delete the cluster (this will also delete the VPC and all resources)
eksctl delete cluster --name copilot-test-cluster --region us-west-2
```

This command will:
1. Delete the managed node group
2. Delete the EKS cluster
3. Delete the CloudFormation stacks
4. Delete the VPC and all networking resources

**Note**: This is irreversible. Ensure you've backed up any necessary data before proceeding.

## Security Best Practices

1. **Enable VPC Flow Logs**: Monitor network traffic
   ```bash
   aws ec2 create-flow-logs --resource-type VPC --resource-ids <vpc-id> --traffic-type ALL --log-destination-type cloud-watch-logs --log-group-name /aws/vpc/copilot-test-cluster
   ```

2. **Enable EKS Audit Logging**: Track API calls
   ```bash
   aws eks update-cluster-config --name copilot-test-cluster --logging '{"clusterLogging":[{"types":["api","audit","authenticator","controllerManager","scheduler"],"enabled":true}]}' --region us-west-2
   ```

3. **Use IMDSv2**: Already configured in the cluster configuration (httpTokens: required)

4. **Implement Pod Security Standards**: Apply security contexts to runner pods

5. **Regular Updates**: Keep EKS and node AMIs updated
   ```bash
   eksctl upgrade cluster --name copilot-test-cluster --region us-west-2 --approve
   ```

## References

- [eksctl Documentation](https://eksctl.io/)
- [EKS Best Practices Guide](https://aws.github.io/aws-eks-best-practices/)
- [Actions Runner Controller](https://github.com/actions/actions-runner-controller)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
