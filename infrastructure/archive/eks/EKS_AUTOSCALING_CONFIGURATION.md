# EKS Cluster Autoscaling Configuration for GitHub Actions Runner Controller

## Overview

This document describes the EKS cluster configuration changes implemented to enable cost-efficient autoscaling of GitHub Actions runners. The primary goal was to allow the Actions Runner Controller (ARC) node group to scale to zero when inactive, thereby minimizing AWS costs.

## Problem Statement

The original single-node-group configuration could not scale to zero because:
- Critical system pods (CoreDNS, kube-proxy, etc.) must always run
- The ARC controller pod itself needs a node to run on
- Kubernetes cannot run without these essential components

## Solution: Two-Node-Group Strategy

### Architecture

The cluster was reconfigured from a single node group into two specialized groups:

#### 1. `system-nodes` (Always-On Group)

**Purpose:** Hosts critical cluster components and the ARC controller pod

**Configuration:**
- `minSize: 1` - Always maintains at least one node
- `desiredCapacity: 1` - Normal state is one node
- `maxSize: 3` - Can scale up if needed (though rarely necessary)
- `instanceType: t3.medium` - Smaller, cost-effective instance

**Taint Applied:**
```yaml
taints:
  - key: CriticalAddonsOnly
    value: "true"
    effect: NoSchedule
```

**Why This Taint?**
- Prevents regular pods (like runner pods) from being scheduled on system nodes
- Only pods with explicit tolerations can run here
- System pods automatically tolerate this taint
- Ensures system nodes remain available for critical workloads

#### 2. `arc-runner-nodes` (Scalable Runner Group)

**Purpose:** Exclusively dedicated to running GitHub Actions runner pods

**Configuration:**
- `minSize: 0` - Can scale down to zero nodes
- `desiredCapacity: 0` - Starts with zero nodes (cost savings)
- `maxSize: 10` - Can scale up to 10 nodes for parallel jobs
- `instanceType: t3.large` - More powerful for build/test workloads

**Taint Applied:**
```yaml
taints:
  - key: github-runners
    value: "true"
    effect: NoSchedule
```

**Why This Taint?**
- Ensures only runner pods can be scheduled on these nodes
- Prevents system pods from landing here (allowing scale-to-zero)
- Acts as a dedicated "reservation" for GitHub Actions workloads

**Auto-Discovery Tags:**
```yaml
tags:
  k8s.io/cluster-autoscaler/enabled: "true"
  k8s.io/cluster-autoscaler/OMC-test: "owned"
```

## Kubernetes Scheduling Configuration

### Taints and Tolerations System

**What are Taints?**
- Taints are like "repellants" applied to nodes
- They prevent pods from being scheduled unless they have a matching toleration
- Format: `key=value:effect`

**What are Tolerations?**
- Tolerations are like "passes" that allow pods to ignore specific taints
- Applied in pod specifications
- Must match the taint key, value, and effect

### RunnerDeployment Configuration

The `runner-deployment.yaml` file was updated to include:

```yaml
spec:
  template:
    spec:
      tolerations:
        - key: github-runners
          operator: Equal
          value: "true"
          effect: NoSchedule
```

**Why This Matters:**
- Runner pods can now be scheduled on `arc-runner-nodes` (matching toleration)
- Runner pods are blocked from `system-nodes` (no CriticalAddonsOnly toleration)
- Ensures clean separation of workloads

## Cluster Autoscaler (CA) Integration

### Why Cluster Autoscaler is Essential

The Kubernetes Cluster Autoscaler is required because:
1. **Manual Scaling Limitation:** A node group at zero nodes cannot self-provision
2. **Pending Pod Detection:** CA watches for pods stuck in `Pending` state
3. **Automatic Provisioning:** When a runner pod appears, CA provisions a node in `arc-runner-nodes`
4. **Scale-Down:** After jobs complete and nodes are idle, CA scales back to zero

### Installation

The Cluster Autoscaler was deployed using a Kubernetes manifest with proper RBAC configuration:

```bash
kubectl apply -f infrastructure/aws/eks/arc-manifests/cluster-autoscaler.yaml
```

**Why Not EKS Add-On?**
- The EKS add-on for Cluster Autoscaler requires additional IAM service account configuration
- Manifest-based deployment provides more direct control over RBAC and tolerations
- Easier to version control and customize for specific cluster needs

### IAM Permissions Configuration

The Cluster Autoscaler requires AWS IAM permissions to interact with Auto Scaling Groups. These were configured as follows:

#### 1. Created IAM Policy

Policy Document (`OMC-ClusterAutoscalerPolicy`):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "autoscaling:DescribeAutoScalingGroups",
        "autoscaling:DescribeAutoScalingInstances",
        "autoscaling:DescribeLaunchConfigurations",
        "autoscaling:DescribeScalingActivities",
        "autoscaling:DescribeTags",
        "ec2:DescribeImages",
        "ec2:DescribeInstanceTypes",
        "ec2:DescribeLaunchTemplateVersions",
        "ec2:GetInstanceTypesFromInstanceRequirements",
        "eks:DescribeNodegroup"
      ],
      "Resource": ["*"]
    },
    {
      "Effect": "Allow",
      "Action": [
        "autoscaling:SetDesiredCapacity",
        "autoscaling:TerminateInstanceInAutoScalingGroup"
      ],
      "Resource": ["*"]
    }
  ]
}
```

#### 2. Attached Policy to System Nodes IAM Role

The policy was attached to the system-nodes IAM role because:
- The Cluster Autoscaler pod runs on system-nodes (due to CriticalAddonsOnly taint)
- Pods inherit IAM permissions from the EC2 instance role
- No IRSA (IAM Roles for Service Accounts) configuration needed

```bash
# Created the policy
aws iam create-policy \
  --policy-name OMC-ClusterAutoscalerPolicy \
  --policy-document file:///tmp/cluster-autoscaler-policy.json

# Attached to system-nodes role
aws iam attach-role-policy \
  --role-name eksctl-OMC-test-nodegroup-system-n-NodeInstanceRole-8oAwzToybyzO \
  --policy-arn arn:aws:iam::220711411889:policy/OMC-ClusterAutoscalerPolicy
```

**Key IAM Role:** `eksctl-OMC-test-nodegroup-system-n-NodeInstanceRole-8oAwzToybyzO`

**Attached Policies:**
1. `AmazonEKSWorkerNodePolicy` - Standard EKS worker node permissions
2. `AmazonEKS_CNI_Policy` - VPC CNI plugin permissions
3. `AmazonEC2ContainerRegistryPullOnly` - Pull container images
4. `AmazonSSMManagedInstanceCore` - SSM access (optional)
5. `OMC-ClusterAutoscalerPolicy` - Autoscaling permissions (custom)

### Cluster Autoscaler Deployment Details

**Manifest Location:** `infrastructure/aws/eks/arc-manifests/cluster-autoscaler.yaml`

**Key Configuration:**

1. **ServiceAccount:** `cluster-autoscaler` in `kube-system` namespace
2. **ClusterRole:** Permissions to watch/list/update nodes and pods
3. **Deployment:** Single replica with node group auto-discovery

**Auto-Discovery Configuration:**
```yaml
command:
  - ./cluster-autoscaler
  - --v=4
  - --stderrthreshold=info
  - --cloud-provider=aws
  - --skip-nodes-with-local-storage=false
  - --expander=least-waste
  - --node-group-auto-discovery=asg:tag=k8s.io/cluster-autoscaler/enabled,k8s.io/cluster-autoscaler/OMC-test
```

**Toleration Applied:**
```yaml
tolerations:
  - key: CriticalAddonsOnly
    operator: Equal
    value: "true"
    effect: NoSchedule
```

This ensures the Cluster Autoscaler pod can run on system-nodes alongside other critical components.

### How It Works

1. **GitHub Actions Job Triggered:**
   - A workflow run starts
   - ARC controller detects the job

2. **Runner Pod Created:**
   - ARC controller creates a runner pod
   - Pod has `github-runners` toleration

3. **Pending State:**
   - Pod cannot be scheduled (no nodes in `arc-runner-nodes`)
   - Pod enters `Pending` state

4. **CA Intervention:**
   - CA detects pending pod
   - CA checks node group auto-discovery tags
   - CA finds `arc-runner-nodes` group
   - CA provisions a new EC2 instance

5. **Job Execution:**
   - Node becomes ready
   - Pod is scheduled and runs the job
   - Job completes

6. **Scale-Down:**
   - After idle period (default: 10 minutes)
   - CA marks node as unneeded
   - CA terminates the EC2 instance
   - Node group returns to zero nodes

## Cost Implications

### Before (Single Node Group)

- **Minimum Nodes:** 1 always running
- **Instance Type:** t3.large
- **Monthly Cost:** ~$60-70 USD (assuming 730 hours)

### After (Two Node Groups)

- **system-nodes:** 1 × t3.medium always running (~$30/month)
- **arc-runner-nodes:** 0 nodes when idle (no cost)
- **Active Time:** Only pays for runner nodes during job execution
- **Estimated Savings:** 40-60% depending on CI/CD usage patterns

## Implementation Timeline

### Phase 1: Cluster Configuration (November 2025)
1. Updated `eks-cluster-new-vpc.yml` with two node groups
2. Added taints to both node groups:
   - `system-nodes`: `CriticalAddonsOnly=true:NoSchedule`
   - `arc-runner-nodes`: `github-runners=true:NoSchedule`
3. Added auto-discovery tags to `arc-runner-nodes`:
   - `k8s.io/cluster-autoscaler/enabled: "true"`
   - `k8s.io/cluster-autoscaler/OMC-test: "owned"`

### Phase 2: Node Group Creation
```bash
# Created system-nodes first (hosts critical components)
eksctl create nodegroup --config-file=eks-cluster-new-vpc.yml --include=system-nodes

# Created arc-runner-nodes (scalable runner group)
eksctl create nodegroup --config-file=eks-cluster-new-vpc.yml --include=arc-runner-nodes
```

### Phase 3: ARC Controller Configuration
```bash
# Patched ARC controller to tolerate CriticalAddonsOnly taint
kubectl patch deployment arc-actions-runner-controller \
  -n actions-runner-system \
  --type='json' \
  -p='[{"op": "add", "path": "/spec/template/spec/tolerations", "value": [{"key": "CriticalAddonsOnly", "operator": "Equal", "value": "true", "effect": "NoSchedule"}]}]'
```

**Why This Was Needed:**
- The ARC controller pod was stuck in `Pending` state after system-nodes creation
- System-nodes had `CriticalAddonsOnly` taint that blocked the pod
- Added toleration to allow ARC controller to schedule on system-nodes

### Phase 4: Runner Deployment Update
```bash
# Updated runner-deployment.yaml with github-runners toleration
kubectl apply -f infrastructure/aws/eks/arc-manifests/runner-deployment.yaml
```

**Configuration Added:**
```yaml
spec:
  template:
    spec:
      tolerations:
        - key: github-runners
          operator: Equal
          value: "true"
          effect: NoSchedule
```

### Phase 5: Cluster Autoscaler Deployment

#### Step 5.1: Create Manifest
Created `infrastructure/aws/eks/arc-manifests/cluster-autoscaler.yaml` with:
- ServiceAccount, ClusterRole, Role, and bindings
- Deployment with auto-discovery configuration
- Toleration for `CriticalAddonsOnly` taint

#### Step 5.2: Create IAM Policy
```bash
# Created policy document
cat > /tmp/cluster-autoscaler-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "autoscaling:DescribeAutoScalingGroups",
        "autoscaling:DescribeAutoScalingInstances",
        "autoscaling:DescribeLaunchConfigurations",
        "autoscaling:DescribeScalingActivities",
        "autoscaling:DescribeTags",
        "ec2:DescribeImages",
        "ec2:DescribeInstanceTypes",
        "ec2:DescribeLaunchTemplateVersions",
        "ec2:GetInstanceTypesFromInstanceRequirements",
        "eks:DescribeNodegroup"
      ],
      "Resource": ["*"]
    },
    {
      "Effect": "Allow",
      "Action": [
        "autoscaling:SetDesiredCapacity",
        "autoscaling:TerminateInstanceInAutoScalingGroup"
      ],
      "Resource": ["*"]
    }
  ]
}
EOF

# Created IAM policy
aws iam create-policy \
  --policy-name OMC-ClusterAutoscalerPolicy \
  --policy-document file:///tmp/cluster-autoscaler-policy.json
```

#### Step 5.3: Attach Policy to System Nodes Role
```bash
# Attached policy to system-nodes IAM role
aws iam attach-role-policy \
  --role-name eksctl-OMC-test-nodegroup-system-n-NodeInstanceRole-8oAwzToybyzO \
  --policy-arn arn:aws:iam::220711411889:policy/OMC-ClusterAutoscalerPolicy
```

**Critical Finding:**
- Initial deployment failed with `AccessDenied` errors
- Investigation revealed autoscaling permissions were missing
- Policy was created and attached to correct IAM role
- Pod restart picked up new permissions automatically

#### Step 5.4: Deploy Cluster Autoscaler
```bash
# Applied manifest
kubectl apply -f infrastructure/aws/eks/arc-manifests/cluster-autoscaler.yaml

# Restarted pod to pick up IAM permissions
kubectl delete pod -n kube-system -l app=cluster-autoscaler
```

### Phase 6: Verification and Testing

#### Test 1: Verify ASG Configuration
```bash
aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names \
    "eks-arc-runner-nodes-f4cd48a7-4b6a-18d3-12bf-e92f28b737ba" \
    "eks-system-nodes-3ecd48a8-f71f-0de0-2ad0-4731366e9ff4" \
  --query "AutoScalingGroups[*].{Name:AutoScalingGroupName, Min:MinSize, Max:MaxSize, Desired:DesiredCapacity, Instances:length(Instances)}"
```

**Results:**
- ✅ arc-runner-nodes: Min=0, Max=5, Desired=0 (scale-to-zero enabled)
- ✅ system-nodes: Min=1, Max=2, Desired=1 (always-on)

#### Test 2: Trigger Workflow to Test Autoscaling
```bash
# Made code change to trigger workflow
cd /home/mark/omc/ohmycoins
echo "# Test autoscaling - $(date)" >> README.md
git add README.md
git commit -m "test: trigger workflow to verify EKS autoscaling"
git push origin main
```

**Observed Behavior:**
1. GitHub Actions workflow triggered
2. ARC controller created runner pod
3. Runner pod entered `Pending` state (no nodes available)
4. Cluster Autoscaler detected pending pod
5. CA scaled arc-runner-nodes from 0 → 1
6. New node provisioned (ip-192-168-12-40)
7. Runner pod scheduled and executed workflow
8. ✅ End-to-end autoscaling verified!

#### Test 3: Monitor Cluster Autoscaler Logs
```bash
kubectl logs -n kube-system -l app=cluster-autoscaler --tail=50
```

**Key Log Messages:**
- ✅ Successfully discovered both node groups
- ✅ Evaluated scale-up for pending pods
- ✅ Triggered scale-up on arc-runner-nodes
- ✅ No permission errors after IAM policy attachment

## Verification Commands

### Check Node Group Status
```bash
# List all node groups
eksctl get nodegroup --cluster=OMC-test --region=ap-southeast-2

# Check ASG configuration
aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names \
    "eks-arc-runner-nodes-f4cd48a7-4b6a-18d3-12bf-e92f28b737ba" \
    "eks-system-nodes-3ecd48a8-f71f-0de0-2ad0-4731366e9ff4" \
  --query "AutoScalingGroups[*].{Name:AutoScalingGroupName, Min:MinSize, Max:MaxSize, Desired:DesiredCapacity, Instances:length(Instances)}" \
  --output table
```

### Check Nodes and Taints
```bash
# List all nodes with taints
kubectl get nodes -o custom-columns=NAME:.metadata.name,TAINTS:.spec.taints

# Detailed node information
kubectl describe nodes
```

### Check Cluster Autoscaler Status
```bash
# Check CA deployment
kubectl get deployment -n kube-system cluster-autoscaler

# Check CA pod status
kubectl get pods -n kube-system -l app=cluster-autoscaler

# View CA logs (last 50 lines)
kubectl logs -n kube-system -l app=cluster-autoscaler --tail=50

# Monitor CA decisions in real-time
kubectl logs -n kube-system -l app=cluster-autoscaler -f
```

### Check IAM Permissions
```bash
# List IAM roles for EKS
aws iam list-roles --query 'Roles[?contains(RoleName, `OMC-test`)].RoleName' --output text

# Check attached policies on system-nodes role
aws iam list-attached-role-policies \
  --role-name eksctl-OMC-test-nodegroup-system-n-NodeInstanceRole-8oAwzToybyzO

# Verify custom autoscaling policy exists
aws iam get-policy --policy-arn arn:aws:iam::220711411889:policy/OMC-ClusterAutoscalerPolicy
```

### Monitor Autoscaling Events
```bash
# Watch for autoscaling events
kubectl get events --all-namespaces --sort-by='.lastTimestamp' | grep -i autoscal

# Check pod events
kubectl get events -n arc-runners --sort-by='.lastTimestamp'

# Watch events in real-time
kubectl get events --all-namespaces --watch
```

### Check Runner Pod Status
```bash
# List runner pods
kubectl get pods -n arc-runners

# Check runner system pods
kubectl get pods -n actions-runner-system

# Describe specific runner pod
kubectl describe pod <pod-name> -n arc-runners

# Check pod placement
kubectl get pods -n arc-runners -o wide
```

### Verify Auto-Discovery Tags
```bash
# Check tags on arc-runner-nodes ASG
aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names eks-arc-runner-nodes-f4cd48a7-4b6a-18d3-12bf-e92f28b737ba \
  --query 'AutoScalingGroups[0].Tags[?contains(Key, `cluster-autoscaler`)]'
```

### Test Autoscaling Manually
```bash
# Trigger a workflow to test scale-up
cd /home/mark/omc/ohmycoins
echo "# Test autoscaling - $(date)" >> README.md
git add README.md
git commit -m "test: verify autoscaling"
git push origin main

# Watch for runner pod creation
kubectl get pods -n arc-runners -w

# Monitor node scaling
watch -n 5 'kubectl get nodes'
```

## Troubleshooting

### Issue 1: ARC Controller Pod Stuck in Pending

**Symptom:** 
```
Events:
  Warning  FailedScheduling  pod/arc-actions-runner-controller-xxx
  0/1 nodes are available: 1 node(s) had untolerated taint {CriticalAddonsOnly: true}
```

**Root Cause:** The ARC controller pod lacks toleration for system-nodes taint

**Solution:**
```bash
kubectl patch deployment arc-actions-runner-controller \
  -n actions-runner-system \
  --type='json' \
  -p='[{"op": "add", "path": "/spec/template/spec/tolerations", "value": [{"key": "CriticalAddonsOnly", "operator": "Equal", "value": "true", "effect": "NoSchedule"}]}]'
```

### Issue 2: Cluster Autoscaler AccessDenied Errors

**Symptom:**
```
Failed to list Auto Scaling Groups: AccessDenied: User is not authorized to perform: autoscaling:DescribeAutoScalingGroups
```

**Root Cause:** Missing IAM permissions on system-nodes role

**Solution:**
1. Create IAM policy with autoscaling permissions (see Phase 5.2)
2. Attach policy to system-nodes IAM role
3. Restart Cluster Autoscaler pod to pick up new permissions

**Verification:**
```bash
# List attached policies
aws iam list-attached-role-policies \
  --role-name eksctl-OMC-test-nodegroup-system-n-NodeInstanceRole-8oAwzToybyzO

# Check logs for successful ASG discovery
kubectl logs -n kube-system -l app=cluster-autoscaler --tail=50
```

### Issue 3: Runners Not Scaling Up

**Symptom:** Pods stuck in `Pending` state indefinitely

**Check:**
1. Verify CA is running: `kubectl get pods -n kube-system | grep cluster-autoscaler`
2. Check CA logs for errors: `kubectl logs -n kube-system -l app=cluster-autoscaler`
3. Verify auto-discovery tags on node group:
   ```bash
   aws autoscaling describe-auto-scaling-groups \
     --auto-scaling-group-names eks-arc-runner-nodes-* \
     --query 'AutoScalingGroups[0].Tags'
   ```
4. Ensure IAM permissions are attached (see Issue 2)

### Issue 4: Nodes Not Scaling Down

**Symptom:** Nodes remain running after jobs complete

**Check:**
1. CA scale-down delay (default: 10 minutes) - this is normal behavior
2. Pods preventing scale-down: `kubectl describe node <node-name>`
3. Check for local storage or daemonsets blocking termination
4. Review CA logs for scale-down decisions:
   ```bash
   kubectl logs -n kube-system -l app=cluster-autoscaler | grep -i "scale down"
   ```

### Issue 5: Runner Pods on Wrong Nodes

**Symptom:** Runners scheduled on system nodes instead of arc-runner-nodes

**Check:**
1. Verify taints on nodes: 
   ```bash
   kubectl get nodes -o custom-columns=NAME:.metadata.name,TAINTS:.spec.taints
   ```
2. Verify tolerations in runner deployment: 
   ```bash
   kubectl get runnerdeployment ohmycoins-runners -n arc-runners -o yaml | grep -A 5 tolerations
   ```
3. Ensure runner deployment was reapplied after adding tolerations

### Issue 6: VolumeAttachment Permission Warnings

**Symptom:**
```
Error: volumeattachments.storage.k8s.io is forbidden: User "system:serviceaccount:kube-system:cluster-autoscaler" cannot list resource "volumeattachments"
```

**Impact:** Non-critical - CA can still function normally

**Solution (Optional):**
Add `volumeattachments` to ClusterRole in `cluster-autoscaler.yaml`:
```yaml
- apiGroups: ["storage.k8s.io"]
  resources: ["storageclasses", "csinodes", "csidrivers", "csistoragecapacities", "volumeattachments"]
  verbs: ["watch", "list", "get"]
```

## Best Practices

1. **Monitor Costs:** Use AWS Cost Explorer to track EC2 costs by tag
2. **Set Autoscaling Limits:** Adjust `maxSize` based on parallel job requirements
3. **Tune Scale-Down Delay:** Balance responsiveness vs. cost (longer delay = less thrashing)
4. **Use Spot Instances:** Consider using spot instances for runner nodes (additional savings)
5. **Resource Requests:** Set appropriate CPU/memory requests on runner pods for efficient bin-packing

## Related Files

- `eks-cluster-new-vpc.yml` - Main EKS cluster configuration with two node groups
- `arc-manifests/runner-deployment.yaml` - ARC runner deployment with github-runners toleration
- `arc-manifests/cluster-autoscaler.yaml` - Cluster Autoscaler manifest with RBAC and auto-discovery
- `QUICK_REFERENCE.md` - Quick command reference for cluster operations

## Key Decisions and Rationale

### Why Two Node Groups Instead of One?

**Decision:** Split cluster into system-nodes (always-on) and arc-runner-nodes (scalable)

**Rationale:**
- Kubernetes requires system pods (CoreDNS, kube-proxy) to always run
- Cannot scale a node group to zero if it hosts critical components
- Separation allows cost optimization without compromising cluster stability
- Each group can be independently configured for its workload type

### Why Use Taints Instead of Node Selectors?

**Decision:** Use taints/tolerations rather than node selectors

**Rationale:**
- **Prevention vs. Selection:** Taints actively prevent scheduling, node selectors only prefer
- **System Pod Protection:** System pods automatically tolerate certain taints
- **Explicit Opt-In:** Pods must explicitly declare tolerance, preventing accidental misplacement
- **Bi-directional Control:** Nodes repel pods, and pods must have permission

### Why Manifest-Based Cluster Autoscaler Instead of EKS Add-On?

**Decision:** Deploy CA using Kubernetes manifest rather than EKS managed add-on

**Rationale:**
- **IRSA Complexity:** EKS add-on requires IAM Roles for Service Accounts (IRSA) setup
- **Version Control:** Manifest can be tracked in git alongside other infrastructure
- **Customization:** Direct control over RBAC, tolerations, and configuration
- **Simpler IAM:** Uses EC2 instance role instead of IRSA, fewer moving parts
- **Troubleshooting:** Easier to debug and modify when issues arise

### Why Attach IAM Policy to System-Nodes Role?

**Decision:** Attach autoscaling policy to EC2 instance role instead of using IRSA

**Rationale:**
- **Pod Location:** CA pod runs on system-nodes, inherits that node's IAM role
- **Simplicity:** No need to create OIDC provider or configure service account annotations
- **Automatic Pickup:** Pods get permissions via instance metadata service
- **Fewer Dependencies:** No additional AWS resources or configurations needed

### Why These Specific Instance Types?

**Decision:** t3.medium for system-nodes, t3.large for arc-runner-nodes

**Rationale:**
- **system-nodes (t3.medium):**
  - CPU: 2 vCPUs, RAM: 4 GiB
  - Sufficient for lightweight system pods (CoreDNS, ARC controller, CA)
  - Cost-effective for always-on workload (~$30/month)
  
- **arc-runner-nodes (t3.large):**
  - CPU: 2 vCPUs, RAM: 8 GiB
  - More resources for CI/CD workloads (builds, tests, Docker operations)
  - Can handle parallel job execution
  - Only pay when actually running jobs

### Why MinSize=0 for Runner Nodes?

**Decision:** Set arc-runner-nodes minSize to 0

**Rationale:**
- **Cost Optimization:** Zero nodes when no workflows are running
- **On-Demand Scaling:** Cluster Autoscaler provisions nodes only when needed
- **Estimated Savings:** 40-60% reduction in baseline compute costs
- **No Impact on Availability:** Jobs may wait 2-3 minutes for node provisioning, acceptable for CI/CD

### Why MaxSize=10 for Runner Nodes?

**Decision:** Set arc-runner-nodes maxSize to 10

**Rationale:**
- **Parallel Jobs:** Support multiple concurrent workflow runs
- **Safety Limit:** Prevent runaway costs from misconfigured workflows
- **Scaling Headroom:** Allows burst capacity for high-activity periods
- **Adjustable:** Can be increased if more parallelism is needed

## Current Configuration Summary

### Cluster Details
- **Name:** OMC-test
- **Region:** ap-southeast-2
- **Kubernetes Version:** 1.32

### Node Groups

#### system-nodes
- **Auto Scaling Group:** eks-system-nodes-3ecd48a8-f71f-0de0-2ad0-4731366e9ff4
- **Instance Type:** t3.medium (2 vCPU, 4 GiB RAM)
- **Min:** 1 | **Desired:** 1 | **Max:** 2
- **Current Instances:** 1
- **Taint:** `CriticalAddonsOnly=true:NoSchedule`
- **IAM Role:** eksctl-OMC-test-nodegroup-system-n-NodeInstanceRole-8oAwzToybyzO
- **Workloads:** CoreDNS, kube-proxy, ARC controller, Cluster Autoscaler

#### arc-runner-nodes
- **Auto Scaling Group:** eks-arc-runner-nodes-f4cd48a7-4b6a-18d3-12bf-e92f28b737ba
- **Instance Type:** t3.large (2 vCPU, 8 GiB RAM)
- **Min:** 0 | **Desired:** 0 | **Max:** 5
- **Current Instances:** 0 (scales to 1 when workflows run)
- **Taint:** `github-runners=true:NoSchedule`
- **IAM Role:** eksctl-OMC-test-nodegroup-arc-runn-NodeInstanceRole-L4g9RzI3scwc
- **Workloads:** GitHub Actions runner pods (ephemeral)

### IAM Configuration

**System Nodes Role:** `eksctl-OMC-test-nodegroup-system-n-NodeInstanceRole-8oAwzToybyzO`

**Attached Policies:**
1. `AmazonEKSWorkerNodePolicy` (AWS managed)
2. `AmazonEKS_CNI_Policy` (AWS managed)
3. `AmazonEC2ContainerRegistryPullOnly` (AWS managed)
4. `AmazonSSMManagedInstanceCore` (AWS managed)
5. `OMC-ClusterAutoscalerPolicy` (Custom - arn:aws:iam::220711411889:policy/OMC-ClusterAutoscalerPolicy)

### Deployed Components

1. **Actions Runner Controller (ARC)**
   - Namespace: `actions-runner-system`
   - Toleration: `CriticalAddonsOnly=true:NoSchedule`
   - Runs on: system-nodes

2. **Runner Deployment**
   - Namespace: `arc-runners`
   - Toleration: `github-runners=true:NoSchedule`
   - Runs on: arc-runner-nodes

3. **Cluster Autoscaler**
   - Namespace: `kube-system`
   - Toleration: `CriticalAddonsOnly=true:NoSchedule`
   - Runs on: system-nodes
   - Auto-Discovery: Enabled via ASG tags

## Related Files

- `eks-cluster-new-vpc.yml` - Main EKS cluster configuration with two node groups
- `arc-manifests/runner-deployment.yaml` - ARC runner deployment with github-runners toleration
- `arc-manifests/cluster-autoscaler.yaml` - Cluster Autoscaler manifest with RBAC and auto-discovery
- `QUICK_REFERENCE.md` - Quick command reference for cluster operations

## References

- [EKS Cluster Autoscaler Documentation](https://docs.aws.amazon.com/eks/latest/userguide/autoscaling.html)
- [Kubernetes Taints and Tolerations](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/)
- [Actions Runner Controller Documentation](https://github.com/actions/actions-runner-controller)

---

**Last Updated:** November 17, 2025  
**Cluster Name:** OMC-test  
**Region:** ap-southeast-2  
**Kubernetes Version:** 1.32  
**Implementation Status:** ✅ Complete and Operational  
**Maintained By:** OMC Infrastructure Team

## Implementation Results

### ✅ Successfully Implemented
- Two-node-group architecture (system-nodes + arc-runner-nodes)
- Taints and tolerations for workload isolation
- Cluster Autoscaler with auto-discovery
- IAM permissions for autoscaling operations
- Runner pods with proper toleration configuration
- Scale-to-zero capability for runner nodes
- End-to-end workflow triggering and autoscaling

### ✅ Verified Behaviors
- Runner nodes scale from 0 to 1 when workflow triggered
- New EC2 instance provisions in ~2-3 minutes
- Runner pod schedules successfully on new node
- Workflow executes without errors
- System nodes remain stable at 1 instance
- Cluster Autoscaler operates without permission errors

### 💰 Cost Impact
- **Before:** 1 × t3.large always running (~$60-70/month)
- **After:** 1 × t3.medium always running (~$30/month) + on-demand runner nodes
- **Estimated Savings:** 40-60% depending on CI/CD usage patterns
- **Additional Benefit:** Can scale to 10 nodes for burst capacity

### 📊 System Health
- All pods running and healthy
- No CrashLoopBackOff or pending pods
- IAM permissions correctly configured
- Auto-discovery working properly
- Autoscaling responding to workflow triggers
