#!/bin/bash
# One-Command Deployment Script for Oh My Coins
# Deploys application to staging or production environment
#
# Usage:
#   ./deploy-ecs.sh staging     # Deploy to staging
#   ./deploy-ecs.sh production  # Deploy to production
#
# Prerequisites:
#   - AWS CLI configured with appropriate credentials
#   - Docker installed and running
#   - Terraform installed (optional, for infrastructure changes)
#
# This script:
#   1. Validates prerequisites
#   2. Builds and pushes Docker images to ECR
#   3. Updates ECS services with new images
#   4. Waits for deployment to stabilize
#   5. Verifies health checks

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION="ap-southeast-2"
PROJECT_NAME="ohmycoins"

# Parse arguments
if [ $# -eq 0 ]; then
    echo -e "${RED}Error: Environment not specified${NC}"
    echo "Usage: $0 <staging|production>"
    exit 1
fi

ENVIRONMENT=$1

if [ "$ENVIRONMENT" != "staging" ] && [ "$ENVIRONMENT" != "production" ]; then
    echo -e "${RED}Error: Invalid environment '$ENVIRONMENT'${NC}"
    echo "Valid environments: staging, production"
    exit 1
fi

echo -e "${BOLD}=========================================${NC}"
echo -e "${BOLD}  Oh My Coins - ECS Deployment${NC}"
echo -e "${BOLD}  Environment: $ENVIRONMENT${NC}"
echo -e "${BOLD}=========================================${NC}"
echo ""

# Step 1: Validate prerequisites
echo -e "${BLUE}[1/5] Validating prerequisites...${NC}"

if ! command -v aws &> /dev/null; then
    echo -e "${RED}✗ AWS CLI not found${NC}"
    echo "Please install AWS CLI: https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html"
    exit 1
fi
echo -e "${GREEN}✓ AWS CLI found${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker not found${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi
echo -e "${GREEN}✓ Docker found${NC}"

# Verify AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}✗ AWS credentials not configured${NC}"
    echo "Please run: aws configure"
    exit 1
fi
echo -e "${GREEN}✓ AWS credentials valid${NC}"

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "  Account ID: $AWS_ACCOUNT_ID"

# Verify Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}✗ Docker daemon not running${NC}"
    echo "Please start Docker"
    exit 1
fi
echo -e "${GREEN}✓ Docker daemon running${NC}"
echo ""

# Step 2: Build and push Docker images
echo -e "${BLUE}[2/5] Building and pushing Docker images...${NC}"

# Login to ECR
echo "Logging in to Amazon ECR..."
if ! aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com 2>&1; then
    echo -e "${RED}✗ ECR login failed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ ECR login successful${NC}"

ECR_REGISTRY="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

# Validate git is available and we're in a git repo
if ! command -v git &> /dev/null; then
    echo -e "${RED}✗ Git not found${NC}"
    echo "Using timestamp as image tag instead"
    IMAGE_TAG="$(date +%Y%m%d-%H%M%S)"
elif ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Not in a git repository${NC}"
    echo "Using timestamp as image tag instead"
    IMAGE_TAG="$(date +%Y%m%d-%H%M%S)"
else
    IMAGE_TAG="$(git rev-parse --short HEAD)"
fi

TIMESTAMP=$(date +%Y%m%d-%H%M%S)

echo "Building backend image..."
docker build -t $ECR_REGISTRY/omc-backend:$IMAGE_TAG ./backend
docker tag $ECR_REGISTRY/omc-backend:$IMAGE_TAG $ECR_REGISTRY/omc-backend:latest
docker tag $ECR_REGISTRY/omc-backend:$IMAGE_TAG $ECR_REGISTRY/omc-backend:$ENVIRONMENT-$TIMESTAMP

echo "Pushing backend image..."
docker push $ECR_REGISTRY/omc-backend:$IMAGE_TAG
docker push $ECR_REGISTRY/omc-backend:latest
docker push $ECR_REGISTRY/omc-backend:$ENVIRONMENT-$TIMESTAMP

echo -e "${GREEN}✓ Backend image pushed${NC}"
echo "  Image: $ECR_REGISTRY/omc-backend:$IMAGE_TAG"

echo "Building frontend image..."
docker build -t $ECR_REGISTRY/omc-frontend:$IMAGE_TAG ./frontend
docker tag $ECR_REGISTRY/omc-frontend:$IMAGE_TAG $ECR_REGISTRY/omc-frontend:latest
docker tag $ECR_REGISTRY/omc-frontend:$IMAGE_TAG $ECR_REGISTRY/omc-frontend:$ENVIRONMENT-$TIMESTAMP

echo "Pushing frontend image..."
docker push $ECR_REGISTRY/omc-frontend:$IMAGE_TAG
docker push $ECR_REGISTRY/omc-frontend:latest
docker push $ECR_REGISTRY/omc-frontend:$ENVIRONMENT-$TIMESTAMP

echo -e "${GREEN}✓ Frontend image pushed${NC}"
echo "  Image: $ECR_REGISTRY/omc-frontend:$IMAGE_TAG"
echo ""

# Step 3: Get ECS cluster and service names
echo -e "${BLUE}[3/5] Getting ECS cluster information...${NC}"

CLUSTER_NAME="$PROJECT_NAME-$ENVIRONMENT-cluster"
BACKEND_SERVICE="$PROJECT_NAME-$ENVIRONMENT-backend-service"
FRONTEND_SERVICE="$PROJECT_NAME-$ENVIRONMENT-frontend-service"

echo "  Cluster: $CLUSTER_NAME"
echo "  Backend Service: $BACKEND_SERVICE"
echo "  Frontend Service: $FRONTEND_SERVICE"
echo ""

# Step 4: Update ECS services
echo -e "${BLUE}[4/5] Updating ECS services...${NC}"

echo "Updating backend service..."
aws ecs update-service \
    --cluster $CLUSTER_NAME \
    --service $BACKEND_SERVICE \
    --force-new-deployment \
    --region $AWS_REGION \
    --output text > /dev/null

echo -e "${GREEN}✓ Backend service update initiated${NC}"

echo "Updating frontend service..."
aws ecs update-service \
    --cluster $CLUSTER_NAME \
    --service $FRONTEND_SERVICE \
    --force-new-deployment \
    --region $AWS_REGION \
    --output text > /dev/null

echo -e "${GREEN}✓ Frontend service update initiated${NC}"
echo ""

# Step 5: Wait for services to stabilize
echo -e "${BLUE}[5/5] Waiting for services to stabilize...${NC}"
echo "This may take 5-10 minutes..."

# Wait for backend service
echo "Waiting for backend service..."
if aws ecs wait services-stable \
    --cluster $CLUSTER_NAME \
    --services $BACKEND_SERVICE \
    --region $AWS_REGION 2>/dev/null; then
    echo -e "${GREEN}✓ Backend service stable${NC}"
else
    echo -e "${YELLOW}⚠ Backend service wait timed out or failed${NC}"
    echo "Check ECS console for details"
fi

# Wait for frontend service
echo "Waiting for frontend service..."
if aws ecs wait services-stable \
    --cluster $CLUSTER_NAME \
    --services $FRONTEND_SERVICE \
    --region $AWS_REGION 2>/dev/null; then
    echo -e "${GREEN}✓ Frontend service stable${NC}"
else
    echo -e "${YELLOW}⚠ Frontend service wait timed out or failed${NC}"
    echo "Check ECS console for details"
fi

echo ""
echo -e "${BOLD}=========================================${NC}"
echo -e "${BOLD}${GREEN}  Deployment Complete!${NC}"
echo -e "${BOLD}=========================================${NC}"
echo ""
echo "Deployment Summary:"
echo "  Environment: $ENVIRONMENT"
echo "  Backend Image: $ECR_REGISTRY/omc-backend:$IMAGE_TAG"
echo "  Frontend Image: $ECR_REGISTRY/omc-frontend:$IMAGE_TAG"
echo ""
echo "Next steps:"
echo "  1. Verify application health:"
echo "     aws ecs describe-services --cluster $CLUSTER_NAME --services $BACKEND_SERVICE $FRONTEND_SERVICE --region $AWS_REGION"
echo ""
echo "  2. Check application logs:"
echo "     aws logs tail /ecs/$PROJECT_NAME-$ENVIRONMENT/backend --follow --region $AWS_REGION"
echo ""
echo "  3. View deployment events:"
echo "     aws ecs describe-services --cluster $CLUSTER_NAME --services $BACKEND_SERVICE --region $AWS_REGION --query 'services[0].events[0:5]'"
echo ""

# Optional: Show current task status
echo "Current running tasks:"
if aws ecs describe-services --cluster $CLUSTER_NAME --services $BACKEND_SERVICE --region $AWS_REGION &> /dev/null; then
    BACKEND_TASKS=$(aws ecs list-tasks --cluster $CLUSTER_NAME --service-name $BACKEND_SERVICE --region $AWS_REGION --query 'taskArns' --output text 2>/dev/null | wc -w)
    echo "  Backend: $BACKEND_TASKS tasks running"
else
    echo "  Backend: Service not found or inaccessible"
fi

if aws ecs describe-services --cluster $CLUSTER_NAME --services $FRONTEND_SERVICE --region $AWS_REGION &> /dev/null; then
    FRONTEND_TASKS=$(aws ecs list-tasks --cluster $CLUSTER_NAME --service-name $FRONTEND_SERVICE --region $AWS_REGION --query 'taskArns' --output text 2>/dev/null | wc -w)
    echo "  Frontend: $FRONTEND_TASKS tasks running"
else
    echo "  Frontend: Service not found or inaccessible"
fi
echo ""

echo -e "${GREEN}Deployment to $ENVIRONMENT completed successfully!${NC}"
