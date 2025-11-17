#!/bin/bash
# Terraform Validation Script
# Validates all Terraform configurations before deployment

set -e

echo "========================================="
echo "Oh My Coins - Terraform Validation"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TERRAFORM_ROOT="$SCRIPT_DIR/.."

# Track validation status
VALIDATION_PASSED=true

# Function to validate a Terraform directory
validate_directory() {
    local dir=$1
    local name=$2
    
    echo "Validating $name..."
    
    cd "$dir"
    
    # Check if terraform files exist
    if [ ! -f "main.tf" ] && [ ! -f "*.tf" ]; then
        echo -e "${RED}✗${NC} No Terraform files found in $name"
        VALIDATION_PASSED=false
        return 1
    fi
    
    # Terraform format check
    if ! terraform fmt -check -recursive > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠${NC} $name has formatting issues (non-critical)"
        echo "  Run: terraform fmt -recursive"
    fi
    
    # Terraform init (suppress output)
    if ! terraform init -backend=false > /dev/null 2>&1; then
        echo -e "${RED}✗${NC} $name failed to initialize"
        VALIDATION_PASSED=false
        return 1
    fi
    
    # Terraform validate
    if ! terraform validate > /dev/null 2>&1; then
        echo -e "${RED}✗${NC} $name validation failed"
        terraform validate
        VALIDATION_PASSED=false
        return 1
    fi
    
    echo -e "${GREEN}✓${NC} $name validated successfully"
    return 0
}

# Validate modules
echo "Step 1: Validating Terraform Modules"
echo "-------------------------------------"

MODULES=(
    "vpc"
    "rds"
    "redis"
    "security"
    "iam"
    "alb"
    "ecs"
)

for module in "${MODULES[@]}"; do
    validate_directory "$TERRAFORM_ROOT/modules/$module" "Module: $module"
done

echo ""

# Validate environments
echo "Step 2: Validating Environments"
echo "--------------------------------"

ENVIRONMENTS=(
    "staging"
    "production"
)

for env in "${ENVIRONMENTS[@]}"; do
    validate_directory "$TERRAFORM_ROOT/environments/$env" "Environment: $env"
done

echo ""
echo "========================================="

# Final result
if [ "$VALIDATION_PASSED" = true ]; then
    echo -e "${GREEN}✓ All Terraform configurations are valid!${NC}"
    exit 0
else
    echo -e "${RED}✗ Validation failed. Please fix the errors above.${NC}"
    exit 1
fi
