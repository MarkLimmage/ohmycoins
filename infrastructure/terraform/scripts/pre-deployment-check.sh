#!/bin/bash
# Pre-Deployment Checklist Script
# Validates all prerequisites before deploying to AWS

set -e

echo "========================================="
echo "Oh My Coins - Pre-Deployment Checklist"
echo "========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

CHECKLIST_PASSED=true
WARNINGS=0

# Function to check and report
check_item() {
    local description=$1
    local command=$2
    local required=${3:-true}
    
    echo -n "Checking $description... "
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        if [ "$required" = true ]; then
            echo -e "${RED}✗ FAILED${NC}"
            CHECKLIST_PASSED=false
            return 1
        else
            echo -e "${YELLOW}⚠ WARNING${NC}"
            WARNINGS=$((WARNINGS + 1))
            return 0
        fi
    fi
}

# Environment check
if [ $# -eq 0 ]; then
    ENVIRONMENT="staging"
    echo -e "${BLUE}No environment specified, defaulting to: staging${NC}"
else
    ENVIRONMENT=$1
fi

echo -e "${BLUE}Environment: $ENVIRONMENT${NC}"
echo ""

# Section 1: Local Tools
echo "1. Local Development Tools"
echo "----------------------------"

check_item "AWS CLI installed" "which aws"
check_item "Terraform installed" "which terraform"
check_item "Git installed" "which git"
check_item "jq installed" "which jq" false

# Check versions
if command -v terraform &> /dev/null; then
    TF_VERSION=$(terraform version -json 2>/dev/null | jq -r '.terraform_version' 2>/dev/null || terraform version | head -1 | cut -d 'v' -f 2)
    if [ ! -z "$TF_VERSION" ]; then
        echo "  Terraform version: $TF_VERSION"
    fi
fi

echo ""

# Section 2: AWS Credentials
echo "2. AWS Credentials & Access"
echo "----------------------------"

check_item "AWS credentials configured" "aws sts get-caller-identity"

if aws sts get-caller-identity > /dev/null 2>&1; then
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    echo "  AWS Account ID: $ACCOUNT_ID"
    
    CURRENT_REGION=$(aws configure get region)
    echo "  Current Region: $CURRENT_REGION"
    
    if [ "$CURRENT_REGION" != "ap-southeast-2" ]; then
        echo -e "  ${YELLOW}⚠ Warning: Region should be ap-southeast-2${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
fi

echo ""

# Section 3: S3 Backend
echo "3. Terraform Backend (S3)"
echo "-------------------------"

check_item "S3 state bucket exists" "aws s3 ls s3://ohmycoins-terraform-state"
check_item "S3 bucket versioning enabled" \
    "aws s3api get-bucket-versioning --bucket ohmycoins-terraform-state | grep -q Enabled"
check_item "S3 bucket encryption enabled" \
    "aws s3api get-bucket-encryption --bucket ohmycoins-terraform-state | grep -q AES256"

echo ""

# Section 4: DynamoDB Lock
echo "4. Terraform State Locking (DynamoDB)"
echo "--------------------------------------"

check_item "DynamoDB lock table exists" \
    "aws dynamodb describe-table --table-name ohmycoins-terraform-locks"

# Check for stale locks
if aws dynamodb scan --table-name ohmycoins-terraform-locks --query 'Items' --output json 2>/dev/null | grep -q "LockID"; then
    echo -e "  ${YELLOW}⚠ Warning: State lock may be held${NC}"
    echo "    Run: aws dynamodb scan --table-name ohmycoins-terraform-locks"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "  ${GREEN}No active locks${NC}"
fi

echo ""

# Section 5: Terraform Configuration
echo "5. Terraform Configuration"
echo "--------------------------"

TERRAFORM_DIR="infrastructure/terraform/environments/$ENVIRONMENT"

if [ -d "$TERRAFORM_DIR" ]; then
    check_item "Terraform directory exists" "test -d $TERRAFORM_DIR"
    check_item "main.tf exists" "test -f $TERRAFORM_DIR/main.tf"
    check_item "variables.tf exists" "test -f $TERRAFORM_DIR/variables.tf"
    check_item "terraform.tfvars exists" "test -f $TERRAFORM_DIR/terraform.tfvars" false
    
    if [ ! -f "$TERRAFORM_DIR/terraform.tfvars" ]; then
        echo -e "  ${YELLOW}Note: Copy terraform.tfvars.example to terraform.tfvars${NC}"
        echo "    cd $TERRAFORM_DIR"
        echo "    cp terraform.tfvars.example terraform.tfvars"
    fi
else
    echo -e "${RED}✗ Terraform directory not found: $TERRAFORM_DIR${NC}"
    CHECKLIST_PASSED=false
fi

echo ""

# Section 6: Required Variables
echo "6. Required Environment Variables"
echo "----------------------------------"

if [ -f "$TERRAFORM_DIR/terraform.tfvars" ]; then
    # Check for critical variables
    if grep -q "aws_region.*=" "$TERRAFORM_DIR/terraform.tfvars" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} aws_region configured"
    else
        echo -e "${YELLOW}⚠${NC} aws_region not found in terraform.tfvars"
        WARNINGS=$((WARNINGS + 1))
    fi
    
    if grep -q "vpc_cidr.*=" "$TERRAFORM_DIR/terraform.tfvars" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} vpc_cidr configured"
    else
        echo -e "${YELLOW}⚠${NC} vpc_cidr not found in terraform.tfvars"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo -e "${YELLOW}⚠ terraform.tfvars not found, skipping variable checks${NC}"
fi

echo ""

# Section 7: AWS Service Quotas (optional but recommended)
echo "7. AWS Service Quotas (Warnings Only)"
echo "--------------------------------------"

# Check VPC quota
VPC_QUOTA=$(aws service-quotas get-service-quota \
    --service-code vpc \
    --quota-code L-F678F1CE 2>/dev/null | jq -r '.Quota.Value' 2>/dev/null || echo "unknown")

if [ "$VPC_QUOTA" != "unknown" ]; then
    echo "  VPC limit: $VPC_QUOTA"
    if [ "$VPC_QUOTA" -lt 5 ]; then
        echo -e "  ${YELLOW}⚠ Low VPC quota${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
fi

# Check EIP quota (for NAT Gateway)
EIP_QUOTA=$(aws service-quotas get-service-quota \
    --service-code ec2 \
    --quota-code L-0263D0A3 2>/dev/null | jq -r '.Quota.Value' 2>/dev/null || echo "unknown")

if [ "$EIP_QUOTA" != "unknown" ]; then
    echo "  Elastic IP limit: $EIP_QUOTA"
    if [ "$EIP_QUOTA" -lt 5 ]; then
        echo -e "  ${YELLOW}⚠ Low Elastic IP quota${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
fi

echo ""

# Section 8: Docker Images (for ECS)
echo "8. Container Images (Optional)"
echo "------------------------------"

# Check if ECR repositories exist
check_item "ECR backend repository exists" \
    "aws ecr describe-repositories --repository-names ohmycoins-backend" false

check_item "ECR frontend repository exists" \
    "aws ecr describe-repositories --repository-names ohmycoins-frontend" false

if ! aws ecr describe-repositories --repository-names ohmycoins-backend &>/dev/null; then
    echo -e "  ${YELLOW}Note: Create ECR repositories before deploying ECS${NC}"
    echo "    aws ecr create-repository --repository-name ohmycoins-backend"
    echo "    aws ecr create-repository --repository-name ohmycoins-frontend"
fi

echo ""

# Section 9: SSL Certificate (for production)
if [ "$ENVIRONMENT" = "production" ]; then
    echo "9. SSL Certificate (Production Only)"
    echo "------------------------------------"
    
    check_item "ACM certificate exists" \
        "aws acm list-certificates --region ap-southeast-2 | grep -q CertificateArn" false
    
    if ! aws acm list-certificates --region ap-southeast-2 | grep -q CertificateArn; then
        echo -e "  ${YELLOW}Note: Request ACM certificate for production HTTPS${NC}"
        echo "    aws acm request-certificate \\"
        echo "      --domain-name ohmycoins.example.com \\"
        echo "      --validation-method DNS"
    fi
    
    echo ""
fi

# Final Summary
echo "========================================="
echo "Checklist Summary"
echo "========================================="
echo ""

if [ "$CHECKLIST_PASSED" = true ]; then
    echo -e "${GREEN}✓ All critical checks passed!${NC}"
    
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠ $WARNINGS warning(s) found (non-critical)${NC}"
        echo ""
        echo "You can proceed with deployment, but review warnings above."
    else
        echo ""
        echo "You are ready to deploy!"
    fi
    
    echo ""
    echo "Next steps:"
    echo "  1. Review terraform.tfvars configuration"
    echo "  2. Run: cd $TERRAFORM_DIR"
    echo "  3. Run: terraform init"
    echo "  4. Run: terraform plan"
    echo "  5. Run: terraform apply"
    
    exit 0
else
    echo -e "${RED}✗ Checklist failed!${NC}"
    echo ""
    echo "Please fix the errors above before deploying."
    echo "See TROUBLESHOOTING.md for help."
    
    exit 1
fi
