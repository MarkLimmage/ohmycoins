#!/bin/bash
set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="$PROJECT_ROOT/infrastructure/terraform/environments/staging"
DOC_FILE="$PROJECT_ROOT/docs/DEPLOYMENT_STATUS.md"

echo "⚠️  WARNING: This script will destroy all AWS Staging Infrastructure."
echo "     - Resources: RDS, ElastiCache, ECS, VPC, NAT Gateway, etc."
echo "     - Purpose: Cost saving during development pause."
echo

# Check for terraform
if ! command -v terraform &> /dev/null; then
  echo "❌ Terraform not found. Please install terraform."
  exit 1
fi

echo "🚀 Initiating Terraform Destroy..."
cd "$TERRAFORM_DIR"

# Run destroy
terraform destroy -auto-approve -var-file="terraform.tfvars"

echo "✅ Terraform destroy completed successfully."

# Update documentation
echo "📝 Updating Deployment Status..."
sed -i 's/✅ Deployed (Sleeping)/🔴 Decommissioned (Cost Saving)/g' "$DOC_FILE"
sed -i 's/Verified [0-9-]*/Teardown: '$(date +%Y-%m-%d)'/g' "$DOC_FILE"

echo "🎉 AWS Staging Environment has been completely torn down."
