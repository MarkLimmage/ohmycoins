# Step 1: Install Actions Runner Controller (ARC)

This guide walks through installing and configuring the Actions Runner Controller in your EKS cluster.

## Prerequisites

- Completed [Step 0: Create EKS Cluster](./STEP0_CREATE_CLUSTER.md)
- kubectl configured and able to access the cluster
- Helm 3.x installed
- GitHub Personal Access Token (PAT) or GitHub App credentials

## Overview

Actions Runner Controller (ARC) is a Kubernetes operator that orchestrates and scales self-hosted GitHub Actions runners. It automatically creates and manages runner pods based on workflow demand.

## Step 1.1: Install cert-manager

ARC requires cert-manager for webhook certificate management.

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.3/cert-manager.yaml

# Wait for cert-manager pods to be ready
kubectl wait --for=condition=Available --timeout=300s -n cert-manager deployment/cert-manager
kubectl wait --for=condition=Available --timeout=300s -n cert-manager deployment/cert-manager-webhook
kubectl wait --for=condition=Available --timeout=300s -n cert-manager deployment/cert-manager-cainjector

# Verify installation
kubectl get pods -n cert-manager
```

Expected output:
```
NAME                                      READY   STATUS    RESTARTS   AGE
cert-manager-xxxxxxxxxx-xxxxx             1/1     Running   0          1m
cert-manager-cainjector-xxxxxxxxxx-xxxxx  1/1     Running   0          1m
cert-manager-webhook-xxxxxxxxxx-xxxxx     1/1     Running   0          1m
```

## Step 1.2: Create GitHub Authentication

You need to authenticate ARC with GitHub. You have two options:

### Option A: GitHub Personal Access Token (Recommended for testing)

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token with these permissions:
   - `repo` (Full control of private repositories)
   - `admin:org` (if deploying org-level runners)
   - `admin:repo_hook` (for repository webhooks)
   
3. Create Kubernetes secret:
   ```bash
   kubectl create namespace actions-runner-system
   
   kubectl create secret generic github-auth \
     --namespace=actions-runner-system \
     --from-literal=github_token=ghp_YOUR_TOKEN_HERE
   ```

### Option B: GitHub App (Recommended for production)

See [GitHub's documentation](https://docs.github.com/en/developers/apps/building-github-apps/creating-a-github-app) for creating a GitHub App.

Required permissions:
- Repository permissions:
  - Administration: Read and Write
  - Checks: Read and Write
  - Contents: Read and Write
  - Metadata: Read-only
  - Pull requests: Read and Write
- Organization permissions (if org-level):
  - Self-hosted runners: Read and Write

## Step 1.3: Add ARC Helm Repository

```bash
# Add the ARC Helm repository
helm repo add actions-runner-controller https://actions-runner-controller.github.io/actions-runner-controller

# Update repository
helm repo update
```

## Step 1.4: Install ARC Controller

```bash
# Install ARC in the actions-runner-system namespace
helm install arc \
  --namespace actions-runner-system \
  --create-namespace \
  actions-runner-controller/actions-runner-controller \
  --set syncPeriod=1m

# Wait for controller to be ready
kubectl wait --for=condition=Available --timeout=300s -n actions-runner-system deployment/arc-actions-runner-controller

# Verify installation
kubectl get pods -n actions-runner-system
```

Expected output:
```
NAME                                              READY   STATUS    RESTARTS   AGE
arc-actions-runner-controller-xxxxxxxxxx-xxxxx    1/1     Running   0          30s
```

## Step 1.5: Configure Runner Deployment

Create a runner deployment manifest. Save this as `infrastructure/aws/eks/arc-manifests/runner-deployment.yaml`:

```yaml
apiVersion: actions.summerwind.dev/v1alpha1
kind: RunnerDeployment
metadata:
  name: ohmycoins-runners
  namespace: actions-runner-system
spec:
  replicas: 1
  template:
    spec:
      repository: MarkLimmage/ohmycoins
      # Optional: Add labels to runners
      labels:
        - self-hosted
        - eks
        - test
      # Runner pod resource requests and limits
      resources:
        limits:
          cpu: "2.0"
          memory: "4Gi"
        requests:
          cpu: "1.0"
          memory: "2Gi"
      # Use Kubernetes Docker-in-Docker
      dockerdWithinRunnerContainer: true
      # Ephemeral runners (destroyed after each job)
      ephemeral: true
```

Apply the manifest:
```bash
kubectl apply -f infrastructure/aws/eks/arc-manifests/runner-deployment.yaml
```

## Step 1.6: Configure Autoscaling (Optional but Recommended)

Create a Horizontal Runner Autoscaler to scale runners based on workflow demand:

Save as `infrastructure/aws/eks/arc-manifests/runner-autoscaler.yaml`:

```yaml
apiVersion: actions.summerwind.dev/v1alpha1
kind: HorizontalRunnerAutoscaler
metadata:
  name: ohmycoins-runners-autoscaler
  namespace: actions-runner-system
spec:
  scaleTargetRef:
    name: ohmycoins-runners
  minReplicas: 1
  maxReplicas: 5
  metrics:
  - type: PercentageRunnersBusy
    scaleUpThreshold: '0.75'
    scaleDownThreshold: '0.25'
    scaleUpFactor: '2'
    scaleDownFactor: '0.5'
  # Scale down delay to prevent thrashing
  scaleDownDelaySecondsAfterScaleOut: 300
```

Apply the autoscaler:
```bash
kubectl apply -f infrastructure/aws/eks/arc-manifests/runner-autoscaler.yaml
```

## Step 1.7: Verify Runners

Check that runners are registered with GitHub:

```bash
# Check runner pods
kubectl get pods -n actions-runner-system -l app.kubernetes.io/component=runner

# Check runner logs
kubectl logs -n actions-runner-system -l app.kubernetes.io/component=runner --tail=50

# Check runner deployment status
kubectl get runnerdeployment -n actions-runner-system
kubectl describe runnerdeployment ohmycoins-runners -n actions-runner-system
```

Verify in GitHub:
1. Go to your repository: https://github.com/MarkLimmage/ohmycoins
2. Navigate to Settings → Actions → Runners
3. You should see your self-hosted runner(s) listed with status "Idle"

## Troubleshooting

### Runners Not Appearing in GitHub

1. Check authentication secret:
   ```bash
   kubectl get secret github-auth -n actions-runner-system
   ```

2. Check controller logs:
   ```bash
   kubectl logs -n actions-runner-system deployment/arc-actions-runner-controller
   ```

3. Verify runner deployment:
   ```bash
   kubectl describe runnerdeployment ohmycoins-runners -n actions-runner-system
   ```

### Runner Pods Failing

Check pod events and logs:
```bash
kubectl describe pod -n actions-runner-system <pod-name>
kubectl logs -n actions-runner-system <pod-name>
```

Common issues:
- Insufficient resources (CPU/memory)
- Image pull errors (check network connectivity)
- Authentication failures (check secret)

### Networking Issues

If runners can't access GitHub:
```bash
# Test DNS resolution from a runner pod
kubectl run -n actions-runner-system test-dns --image=busybox --rm -it -- nslookup github.com

# Test connectivity
kubectl run -n actions-runner-system test-curl --image=curlimages/curl --rm -it -- curl -I https://api.github.com
```

## Security Considerations

1. **Limit Runner Permissions**: Use dedicated GitHub tokens/apps with minimal required permissions
2. **Network Policies**: Implement Kubernetes NetworkPolicies to restrict runner pod traffic
3. **Resource Limits**: Always set CPU and memory limits on runner pods
4. **Ephemeral Runners**: Use ephemeral mode (already configured) to ensure clean state for each job
5. **Private Repositories**: Consider using VPC endpoints for GitHub if dealing with sensitive code

## Monitoring

Monitor your runners:

```bash
# Watch runner pods
kubectl get pods -n actions-runner-system -w

# Check autoscaler status
kubectl get hra -n actions-runner-system

# View metrics
kubectl top pods -n actions-runner-system
```

Set up alerts for:
- Runner pod failures
- High resource utilization
- Autoscaling events
- Authentication failures

## Next Steps

After successfully installing ARC, proceed to:
- **Step 2**: Update GitHub Actions workflows to use self-hosted runners
- **Step 3**: Configure workflow security and permissions
- **Step 4**: Set up monitoring and logging

See [STEP2_UPDATE_WORKFLOWS.md](./STEP2_UPDATE_WORKFLOWS.md) for next steps.

## Cleanup

To remove ARC:

```bash
# Delete runner deployment and autoscaler
kubectl delete -f infrastructure/aws/eks/arc-manifests/

# Uninstall ARC controller
helm uninstall arc -n actions-runner-system

# Remove namespace (optional)
kubectl delete namespace actions-runner-system

# Remove cert-manager (if no longer needed)
kubectl delete -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.3/cert-manager.yaml
```

## References

- [Actions Runner Controller Documentation](https://github.com/actions/actions-runner-controller)
- [GitHub Self-hosted Runners](https://docs.github.com/en/actions/hosting-your-own-runners)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
