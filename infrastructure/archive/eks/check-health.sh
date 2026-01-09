#!/bin/bash
# EKS Runner Health Check Script
# This script verifies that the EKS cluster and GitHub Actions runners are properly configured

set -e

CLUSTER_NAME="${CLUSTER_NAME:-copilot-test-cluster}"
REGION="${REGION:-us-west-2}"
NAMESPACE="actions-runner-system"

echo "================================"
echo "EKS Runner Health Check"
echo "================================"
echo ""
echo "Cluster: $CLUSTER_NAME"
echo "Region: $REGION"
echo "Namespace: $NAMESPACE"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check functions
check_command() {
    if command -v "$1" &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 is installed"
        return 0
    else
        echo -e "${RED}✗${NC} $1 is not installed"
        return 1
    fi
}

check_cluster() {
    echo "Checking EKS cluster..."
    if eksctl get cluster --name "$CLUSTER_NAME" --region "$REGION" &> /dev/null; then
        echo -e "${GREEN}✓${NC} Cluster $CLUSTER_NAME exists"
        return 0
    else
        echo -e "${RED}✗${NC} Cluster $CLUSTER_NAME not found"
        return 1
    fi
}

check_nodes() {
    echo "Checking cluster nodes..."
    NODE_COUNT=$(kubectl get nodes --no-headers 2>/dev/null | wc -l)
    if [ "$NODE_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✓${NC} Found $NODE_COUNT node(s)"
        kubectl get nodes
        return 0
    else
        echo -e "${RED}✗${NC} No nodes found"
        return 1
    fi
}

check_namespace() {
    echo "Checking namespace..."
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        echo -e "${GREEN}✓${NC} Namespace $NAMESPACE exists"
        return 0
    else
        echo -e "${YELLOW}⚠${NC} Namespace $NAMESPACE not found (ARC not installed yet)"
        return 1
    fi
}

check_cert_manager() {
    echo "Checking cert-manager..."
    if kubectl get namespace cert-manager &> /dev/null; then
        CERT_PODS=$(kubectl get pods -n cert-manager --no-headers 2>/dev/null | grep -c "Running" || echo "0")
        if [ "$CERT_PODS" -ge 3 ]; then
            echo -e "${GREEN}✓${NC} cert-manager is running ($CERT_PODS/3 pods)"
            return 0
        else
            echo -e "${YELLOW}⚠${NC} cert-manager pods not ready ($CERT_PODS/3)"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠${NC} cert-manager not installed"
        return 1
    fi
}

check_arc_controller() {
    echo "Checking Actions Runner Controller..."
    if kubectl get deployment -n "$NAMESPACE" arc-actions-runner-controller &> /dev/null; then
        ARC_STATUS=$(kubectl get deployment -n "$NAMESPACE" arc-actions-runner-controller -o jsonpath='{.status.conditions[?(@.type=="Available")].status}')
        if [ "$ARC_STATUS" == "True" ]; then
            echo -e "${GREEN}✓${NC} ARC controller is running"
            return 0
        else
            echo -e "${YELLOW}⚠${NC} ARC controller not ready"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠${NC} ARC controller not installed"
        return 1
    fi
}

check_runners() {
    echo "Checking runner deployments..."
    RUNNER_COUNT=$(kubectl get runnerdeployment -n "$NAMESPACE" --no-headers 2>/dev/null | wc -l)
    if [ "$RUNNER_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✓${NC} Found $RUNNER_COUNT runner deployment(s)"
        kubectl get runnerdeployment -n "$NAMESPACE"
        echo ""
        echo "Runner pods:"
        kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/component=runner
        return 0
    else
        echo -e "${YELLOW}⚠${NC} No runner deployments found"
        return 1
    fi
}

check_github_secret() {
    echo "Checking GitHub authentication secret..."
    if kubectl get secret github-auth -n "$NAMESPACE" &> /dev/null; then
        echo -e "${GREEN}✓${NC} GitHub authentication secret exists"
        return 0
    else
        echo -e "${YELLOW}⚠${NC} GitHub authentication secret not found"
        echo "  Create it with: kubectl create secret generic github-auth --namespace=$NAMESPACE --from-literal=github_token=YOUR_TOKEN"
        return 1
    fi
}

# Main execution
echo "=== Prerequisites Check ==="
PREREQ_OK=true
check_command kubectl || PREREQ_OK=false
check_command eksctl || PREREQ_OK=false
check_command helm || PREREQ_OK=false
check_command aws || PREREQ_OK=false
echo ""

if [ "$PREREQ_OK" = false ]; then
    echo -e "${RED}Missing required tools. Please install them before proceeding.${NC}"
    exit 1
fi

echo "=== Cluster Check ==="
if ! check_cluster; then
    echo ""
    echo -e "${YELLOW}Cluster not found. Create it with:${NC}"
    echo "  cd infrastructure/aws/eks"
    echo "  eksctl create cluster -f eks-cluster-new-vpc.yml"
    exit 1
fi
echo ""

echo "=== Node Check ==="
check_nodes
echo ""

echo "=== ARC Installation Check ==="
NAMESPACE_EXISTS=false
check_namespace && NAMESPACE_EXISTS=true
echo ""

if [ "$NAMESPACE_EXISTS" = true ]; then
    check_cert_manager
    echo ""
    
    check_arc_controller
    echo ""
    
    check_github_secret
    echo ""
    
    check_runners
    echo ""
else
    echo -e "${YELLOW}ARC not installed yet. Follow the installation guide:${NC}"
    echo "  See: infrastructure/aws/eks/STEP1_INSTALL_ARC.md"
    echo ""
fi

echo "=== Resource Usage ==="
echo "Node resource usage:"
kubectl top nodes 2>/dev/null || echo "Metrics server not available"
echo ""
if [ "$NAMESPACE_EXISTS" = true ]; then
    echo "Runner pod resource usage:"
    kubectl top pods -n "$NAMESPACE" 2>/dev/null || echo "No pods or metrics not available"
fi
echo ""

echo "=== Summary ==="
echo "Health check complete!"
echo ""
echo "Next steps:"
if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
    echo "1. Install cert-manager and ARC (see STEP1_INSTALL_ARC.md)"
    echo "2. Create GitHub authentication secret"
    echo "3. Deploy runner manifests"
elif ! kubectl get runnerdeployment -n "$NAMESPACE" &> /dev/null 2>&1; then
    echo "1. Deploy runner manifests:"
    echo "   kubectl apply -f infrastructure/aws/eks/arc-manifests/runner-deployment.yaml"
    echo "   kubectl apply -f infrastructure/aws/eks/arc-manifests/runner-autoscaler.yaml"
else
    echo "✓ Infrastructure is set up!"
    echo "  - Verify runners appear in GitHub: Settings → Actions → Runners"
    echo "  - Test with: .github/workflows/test-self-hosted-runner.yml"
fi
echo ""
echo "For detailed documentation, see: infrastructure/aws/eks/README.md"
