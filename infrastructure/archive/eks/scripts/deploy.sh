#!/bin/bash
# Deploy script for OMC applications to EKS
# Usage: ./deploy.sh [staging|production] [all|backend|collectors|agents|monitoring]

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

if [[ ! "$COMPONENT" =~ ^(all|backend|collectors|agents|monitoring)$ ]]; then
    echo_error "Invalid component: $COMPONENT"
    exit 1
fi

echo_info "Deploying to $ENVIRONMENT environment"
echo_info "Component: $COMPONENT"

# Update kubeconfig
echo_info "Updating kubeconfig for cluster $EKS_CLUSTER..."
aws eks update-kubeconfig --region $AWS_REGION --name $EKS_CLUSTER

# Verify cluster access
echo_info "Verifying cluster access..."
kubectl cluster-info >/dev/null 2>&1 || {
    echo_error "Cannot access Kubernetes cluster"
    exit 1
}

# Create namespace if it doesn't exist
echo_info "Creating namespace $NAMESPACE..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Function to deploy monitoring
deploy_monitoring() {
    echo_info "Deploying monitoring stack..."
    
    kubectl apply -f infrastructure/aws/eks/monitoring/prometheus-operator.yml
    kubectl apply -f infrastructure/aws/eks/monitoring/grafana.yml
    kubectl apply -f infrastructure/aws/eks/monitoring/loki-stack.yml
    kubectl apply -f infrastructure/aws/eks/monitoring/alertmanager-config.yml
    kubectl apply -f infrastructure/aws/eks/monitoring/alert-rules.yml
    
    echo_info "Waiting for monitoring components to be ready..."
    kubectl wait --for=condition=ready pod -l app=prometheus -n monitoring --timeout=300s || echo_warn "Prometheus not ready"
    kubectl wait --for=condition=ready pod -l app=grafana -n monitoring --timeout=300s || echo_warn "Grafana not ready"
    kubectl wait --for=condition=ready pod -l app=loki -n monitoring --timeout=300s || echo_warn "Loki not ready"
    
    echo_info "Getting Grafana URL..."
    sleep 30
    GRAFANA_URL=$(kubectl get svc grafana -n monitoring -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "Pending...")
    echo_info "Grafana URL: http://$GRAFANA_URL"
    echo_info "Default credentials: admin / admin"
}

# Function to deploy backend
deploy_backend() {
    echo_info "Deploying backend..."
    
    # Get latest image from ECR
    IMAGE_TAG=$(aws ecr describe-images \
        --repository-name omc-backend \
        --region $AWS_REGION \
        --query 'sort_by(imageDetails,& imagePushedAt)[-1].imageTags[0]' \
        --output text 2>/dev/null || echo "latest")
    
    echo_info "Using backend image tag: $IMAGE_TAG"
    
    # Apply manifests
    kubectl apply -f infrastructure/aws/eks/applications/backend/deployment.yml -n $NAMESPACE
    kubectl apply -f infrastructure/aws/eks/applications/backend/ingress.yml -n $NAMESPACE
    
    echo_info "Waiting for backend rollout..."
    kubectl rollout status deployment/backend -n $NAMESPACE --timeout=300s
    
    echo_info "Getting backend URL..."
    sleep 30
    BACKEND_URL=$(kubectl get ingress backend-ingress -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "Pending...")
    echo_info "Backend URL: http://$BACKEND_URL"
}

# Function to deploy collectors
deploy_collectors() {
    echo_info "Deploying collectors..."
    
    kubectl apply -f infrastructure/aws/eks/applications/collectors/cronjobs.yml -n $NAMESPACE
    
    echo_info "Collector CronJobs and Deployments:"
    kubectl get cronjobs -n $NAMESPACE
    kubectl get deployments -n $NAMESPACE -l app=collectors
}

# Function to deploy agents
deploy_agents() {
    echo_info "Deploying agentic system..."
    
    kubectl apply -f infrastructure/aws/eks/applications/agents/deployment.yml -n $NAMESPACE
    
    echo_info "Waiting for agents rollout..."
    kubectl rollout status deployment/agents -n $NAMESPACE --timeout=300s
    
    echo_info "Agent pods:"
    kubectl get pods -n $NAMESPACE -l app=agents
}

# Deploy based on component selection
case $COMPONENT in
    all)
        deploy_monitoring
        deploy_backend
        deploy_collectors
        deploy_agents
        kubectl apply -f infrastructure/aws/eks/applications/servicemonitor.yml -n $NAMESPACE
        ;;
    monitoring)
        deploy_monitoring
        ;;
    backend)
        deploy_backend
        kubectl apply -f infrastructure/aws/eks/applications/servicemonitor.yml -n $NAMESPACE
        ;;
    collectors)
        deploy_collectors
        kubectl apply -f infrastructure/aws/eks/applications/servicemonitor.yml -n $NAMESPACE
        ;;
    agents)
        deploy_agents
        kubectl apply -f infrastructure/aws/eks/applications/servicemonitor.yml -n $NAMESPACE
        ;;
esac

echo_info "✅ Deployment completed successfully!"
echo_info ""
echo_info "Useful commands:"
echo_info "  kubectl get pods -n $NAMESPACE"
echo_info "  kubectl logs -n $NAMESPACE -l app=backend"
echo_info "  kubectl get svc -n monitoring"
echo_info "  kubectl port-forward -n monitoring svc/grafana 3000:80"
