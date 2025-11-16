# Step 2: Update GitHub Actions Workflows

This guide explains how to update your GitHub Actions workflows to use the self-hosted runners in your EKS cluster.

## Prerequisites

- Completed [Step 0: Create EKS Cluster](./STEP0_CREATE_CLUSTER.md)
- Completed [Step 1: Install Actions Runner Controller](./STEP1_INSTALL_ARC.md)
- Verified runners are registered and showing as "Idle" in GitHub

## Overview

The project currently uses GitHub-hosted runners (`ubuntu-latest`) for most workflows. With self-hosted runners, you can:
- Run workflows in a more permissive environment
- Access private AWS resources (VPCs, databases, etc.)
- Customize runner environment and tools
- Reduce costs for high-volume CI/CD
- Control compute resources and scaling

## Understanding Runner Labels

Your self-hosted runners have these labels:
- `self-hosted` - Identifies as a self-hosted runner
- `eks` - Indicates it's running in EKS
- `test` - Environment identifier

Workflows target specific runners using the `runs-on` key.

## Workflow Update Strategies

### Strategy 1: Hybrid Approach (Recommended)

Use GitHub-hosted runners for simple tasks and self-hosted for complex/resource-intensive tasks:

**Example: Current build.yml workflow**
```yaml
jobs:
  build-backend:
    runs-on: ubuntu-latest  # Keep for simple builds
    
  integration-tests:
    runs-on: [self-hosted, eks, test]  # Use self-hosted for heavy tests
```

### Strategy 2: Full Migration

Migrate all workflows to self-hosted runners:

```yaml
jobs:
  test-backend:
    runs-on: [self-hosted, eks, test]
```

### Strategy 3: Environment-Based Selection

Use different runners based on branch/environment:

```yaml
jobs:
  deploy:
    runs-on: ${{ github.ref == 'refs/heads/main' && 'ubuntu-latest' || '[self-hosted, eks, test]' }}
```

## Current Workflows to Update

Based on the repository structure, here are the workflows that may benefit from self-hosted runners:

### 1. test-backend.yml
**Current**: Uses `ubuntu-latest`
**Recommended**: Migrate to self-hosted for faster database access

```yaml
jobs:
  test-backend:
    runs-on: [self-hosted, eks, test]
    # ... rest of configuration
```

**Benefits**:
- Faster docker-compose operations
- Potential to connect to persistent test database in AWS
- More control over Python environment

### 2. build.yml
**Current**: Uses `ubuntu-latest`
**Recommended**: Keep GitHub-hosted or hybrid

```yaml
jobs:
  build-backend:
    runs-on: ubuntu-latest  # Light build, keep on GitHub runners
    
  build-frontend:
    runs-on: ubuntu-latest  # Light build, keep on GitHub runners
```

**Rationale**: Docker builds work well on GitHub-hosted runners and benefit from GitHub's cache infrastructure.

### 3. deploy-staging.yml
**Current**: Uses `[self-hosted, staging]`
**Recommended**: Update to use EKS runners

```yaml
jobs:
  deploy:
    runs-on: [self-hosted, eks, staging]  # Add 'eks' label
    # ... rest of configuration
```

**Note**: You'll need to update runner-deployment.yaml to add a 'staging' label.

### 4. deploy-production.yml
**Current**: Uses `[self-hosted, production]`
**Recommended**: Keep as-is initially, migrate after testing

Production deployments should remain stable. Consider:
- Testing EKS runners thoroughly with staging first
- Creating a separate production runner pool
- Implementing additional security controls

## Updating Runner Deployment for Multiple Environments

To support different environments (staging, production), create multiple runner deployments:

### Staging Runners
```yaml
# infrastructure/aws/eks/arc-manifests/runner-deployment-staging.yaml
apiVersion: actions.summerwind.dev/v1alpha1
kind: RunnerDeployment
metadata:
  name: ohmycoins-runners-staging
  namespace: actions-runner-system
spec:
  replicas: 1
  template:
    spec:
      repository: MarkLimmage/ohmycoins
      labels:
        - self-hosted
        - eks
        - staging
      resources:
        limits:
          cpu: "2.0"
          memory: "4Gi"
        requests:
          cpu: "1.0"
          memory: "2Gi"
      dockerdWithinRunnerContainer: true
      ephemeral: true
```

### Production Runners
```yaml
# infrastructure/aws/eks/arc-manifests/runner-deployment-production.yaml
apiVersion: actions.summerwind.dev/v1alpha1
kind: RunnerDeployment
metadata:
  name: ohmycoins-runners-production
  namespace: actions-runner-system
spec:
  replicas: 2  # More replicas for production
  template:
    spec:
      repository: MarkLimmage/ohmycoins
      labels:
        - self-hosted
        - eks
        - production
      resources:
        limits:
          cpu: "4.0"
          memory: "8Gi"
        requests:
          cpu: "2.0"
          memory: "4Gi"
      dockerdWithinRunnerContainer: true
      ephemeral: true
```

Apply these:
```bash
kubectl apply -f infrastructure/aws/eks/arc-manifests/runner-deployment-staging.yaml
kubectl apply -f infrastructure/aws/eks/arc-manifests/runner-deployment-production.yaml
```

## Testing Workflow Changes

Before migrating all workflows:

1. **Create a Test Workflow**

Create `.github/workflows/test-self-hosted.yml`:
```yaml
name: Test Self-Hosted Runner

on:
  workflow_dispatch:

jobs:
  test:
    runs-on: [self-hosted, eks, test]
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Verify environment
        run: |
          echo "Runner name: $RUNNER_NAME"
          echo "Runner OS: $RUNNER_OS"
          echo "Available CPU: $(nproc)"
          echo "Available memory: $(free -h)"
          uname -a
      
      - name: Test Docker
        run: |
          docker --version
          docker ps
      
      - name: Test network
        run: |
          curl -I https://api.github.com
          curl -I https://github.com
```

2. **Run the Test Workflow**
   - Go to Actions tab in GitHub
   - Select "Test Self-Hosted Runner"
   - Click "Run workflow"

3. **Verify Results**
   - Check that the workflow runs on your self-hosted runner
   - Review the output to ensure all tools are available
   - Verify Docker-in-Docker works correctly

## Common Issues and Solutions

### Issue: Runner can't pull Docker images

**Solution**: Ensure NAT Gateway is working and runner pods can access internet:
```bash
kubectl run -n actions-runner-system test-curl --image=curlimages/curl --rm -it -- curl -I https://ghcr.io
```

### Issue: Workflow fails with "No runner available"

**Solutions**:
1. Check runner status: `kubectl get pods -n actions-runner-system`
2. Verify runner labels match workflow `runs-on`
3. Check runner logs: `kubectl logs -n actions-runner-system <pod-name>`

### Issue: Docker-in-Docker permission errors

**Solution**: Ensure runner deployment has `dockerdWithinRunnerContainer: true`

### Issue: Workflow timeout or hangs

**Solution**: 
- Check resource limits on runner pods
- Increase timeout in workflow: `timeout-minutes: 30`
- Check pod CPU/memory usage: `kubectl top pods -n actions-runner-system`

## Security Considerations

When using self-hosted runners:

1. **Secrets Management**: Self-hosted runners have access to repository secrets
   - Use separate runners for public repositories
   - Implement least-privilege access
   - Rotate secrets regularly

2. **Network Security**: Runners in EKS can access AWS resources
   - Use security groups to limit access
   - Implement Kubernetes NetworkPolicies
   - Enable VPC Flow Logs

3. **Resource Isolation**: Use ephemeral runners (already configured)
   - Each job gets a fresh runner
   - No state persists between jobs
   - Reduces security risks

4. **Code Execution**: Self-hosted runners execute untrusted code
   - Review PRs carefully before running workflows
   - Consider using `pull_request_target` carefully
   - Implement approval workflows for external contributors

## Monitoring and Logging

Monitor workflow performance:

```bash
# Watch runner pods during workflow execution
kubectl get pods -n actions-runner-system -w

# Check resource usage
kubectl top pods -n actions-runner-system

# View workflow logs
kubectl logs -n actions-runner-system -l app.kubernetes.io/component=runner --tail=100
```

Set up CloudWatch for:
- Workflow execution metrics
- Runner pod resource usage
- Failed job alerts

## Rollback Plan

If issues occur with self-hosted runners:

1. **Quick Rollback**: Change workflow `runs-on` back to `ubuntu-latest`
2. **Partial Rollback**: Keep critical workflows on GitHub-hosted runners
3. **Full Rollback**: Delete runner deployments:
   ```bash
   kubectl delete runnerdeployment -n actions-runner-system --all
   ```

## Best Practices

1. **Start Small**: Migrate one workflow at a time
2. **Test Thoroughly**: Use test workflows before production changes
3. **Monitor Costs**: Track EC2 and data transfer costs
4. **Scale Appropriately**: Adjust min/max replicas based on usage
5. **Update Regularly**: Keep runner images and ARC controller updated
6. **Document Changes**: Update workflow documentation when migrating

## Next Steps

After updating workflows:
- Monitor workflow execution and performance
- Optimize runner resource allocation
- Set up alerting for runner failures
- Plan for production runner deployment
- Consider implementing workflow job matrices for parallel execution

## References

- [GitHub Actions: Hosting your own runners](https://docs.github.com/en/actions/hosting-your-own-runners)
- [Actions Runner Controller Autoscaling](https://github.com/actions/actions-runner-controller/blob/master/docs/automatically-scaling-runners.md)
- [GitHub Actions Security Hardening](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
