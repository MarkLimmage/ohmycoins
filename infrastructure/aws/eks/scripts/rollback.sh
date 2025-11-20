#!/bin/bash
# Rollback script for OMC applications on EKS
# Usage: ./rollback.sh [staging|production] [backend|agents|all]

set -e

# Configuration
ENVIRONMENT=${1:-staging}
COMPONENT=${2:-all}
AWS_REGION="ap-southeast-2"
EKS_CLUSTER="OMC-test"
NAMESPACE="omc-${ENVIRONMENT}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validate inputs
if [[ ! "$ENVIRONMENT" =~ ^(staging|production)$ ]]; then
    echo_error "Invalid environment: $ENVIRONMENT. Must be 'staging' or 'production'"
    exit 1
fi

if [[ ! "$COMPONENT" =~ ^(all|backend|agents)$ ]]; then
    echo_error "Invalid component: $COMPONENT. Must be 'all', 'backend', or 'agents'"
    exit 1
fi

echo_warn "⚠️  ROLLBACK WARNING ⚠️"
echo_warn "This will rollback deployments in $ENVIRONMENT environment"
echo_warn "Component: $COMPONENT"
echo_warn ""
read -p "Are you sure you want to proceed? (yes/no): " CONFIRM

if [[ "$CONFIRM" != "yes" ]]; then
    echo_info "Rollback cancelled"
    exit 0
fi

# Update kubeconfig
echo_info "Updating kubeconfig for cluster $EKS_CLUSTER..."
aws eks update-kubeconfig --region $AWS_REGION --name $EKS_CLUSTER

# Verify cluster access
echo_info "Verifying cluster access..."
kubectl cluster-info >/dev/null 2>&1 || {
    echo_error "Cannot access Kubernetes cluster"
    exit 1
}

# Function to rollback a deployment
rollback_deployment() {
    local DEPLOYMENT=$1
    
    echo_info "Rolling back deployment: $DEPLOYMENT"
    
    # Check if deployment exists
    if ! kubectl get deployment $DEPLOYMENT -n $NAMESPACE >/dev/null 2>&1; then
        echo_warn "Deployment $DEPLOYMENT not found, skipping"
        return
    fi
    
    # Get rollout history
    echo_info "Rollout history for $DEPLOYMENT:"
    kubectl rollout history deployment/$DEPLOYMENT -n $NAMESPACE
    
    # Rollback to previous revision
    kubectl rollout undo deployment/$DEPLOYMENT -n $NAMESPACE
    
    # Wait for rollback to complete
    echo_info "Waiting for rollback to complete..."
    kubectl rollout status deployment/$DEPLOYMENT -n $NAMESPACE --timeout=300s
    
    echo_info "✅ Rollback completed for $DEPLOYMENT"
}

# Perform rollback based on component
case $COMPONENT in
    all)
        rollback_deployment "backend"
        rollback_deployment "agents"
        rollback_deployment "reddit-collector"
        rollback_deployment "cryptopanic-collector"
        ;;
    backend)
        rollback_deployment "backend"
        ;;
    agents)
        rollback_deployment "agents"
        ;;
esac

# Show current pod status
echo_info ""
echo_info "Current pod status:"
kubectl get pods -n $NAMESPACE

echo_info ""
echo_info "✅ Rollback operation completed!"
echo_info ""
echo_info "To verify the rollback:"
echo_info "  kubectl get pods -n $NAMESPACE"
echo_info "  kubectl describe deployment backend -n $NAMESPACE"
echo_info "  kubectl logs -n $NAMESPACE deployment/backend"
