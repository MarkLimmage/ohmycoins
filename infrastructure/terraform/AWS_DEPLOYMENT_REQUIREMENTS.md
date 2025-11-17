# AWS Deployment Requirements - Oh My Coins Infrastructure

**Purpose:** Complete checklist of AWS credentials, resources, and configurations required to deploy the Oh My Coins infrastructure from this sandboxed environment or any deployment environment.

**Date:** 2025-11-17  
**Maintained By:** Developer C (Infrastructure & DevOps Specialist)

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [AWS Account Requirements](#aws-account-requirements)
4. [Required AWS Resources](#required-aws-resources)
5. [Required GitHub Secrets](#required-github-secrets)
6. [Required Environment Variables](#required-environment-variables)
7. [AWS Permissions Required](#aws-permissions-required)
8. [Setup Instructions](#setup-instructions)
9. [Validation Checklist](#validation-checklist)
10. [Troubleshooting](#troubleshooting)

---

## Overview

This document provides a complete list of AWS credentials, resources, and configurations that must be provided to enable deployment of the Oh My Coins infrastructure. These requirements are not available in the sandboxed development environment and must be provisioned separately.

### Why This Is Needed

The sandboxed environment where development occurs:
- ❌ Does NOT have AWS credentials
- ❌ Does NOT have access to AWS APIs
- ❌ Does NOT have Terraform state backend configured
- ❌ Does NOT have GitHub repository secrets configured
- ❌ Cannot create or manage AWS resources

To deploy infrastructure, the following must be provided externally.

---

## Prerequisites

### Local Development Tools

If deploying locally (not via GitHub Actions), ensure these tools are installed:

```bash
# Check if tools are installed
aws --version          # AWS CLI v2.x or higher
terraform --version    # Terraform v1.5.0 or higher
kubectl version        # kubectl v1.27 or higher
helm version          # Helm v3.x or higher
git --version         # Git v2.x or higher
jq --version          # jq v1.6 or higher (optional but recommended)
```

**Installation Commands:**

```bash
# AWS CLI (Linux/macOS)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Terraform
wget https://releases.hashicorp.com/terraform/1.5.0/terraform_1.5.0_linux_amd64.zip
unzip terraform_1.5.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

---

## AWS Account Requirements

### 1. AWS Account

**Required:**
- Active AWS account with billing enabled
- Account must be in good standing (no payment issues)
- Recommended: Separate AWS accounts for staging and production

**Account IDs Needed:**
- AWS Account ID: `XXXXXXXXXXXX` (12-digit number)

**How to Find:**
```bash
aws sts get-caller-identity --query "Account" --output text
```

### 2. AWS Region

**Recommended Region:** `ap-southeast-2` (Sydney)

**Alternative Regions:**
- `us-east-1` (N. Virginia) - Cheapest, most services
- `us-west-2` (Oregon) - Good balance
- `eu-west-1` (Ireland) - European customers

**Configuration:**
```bash
# Set default region
aws configure set region ap-southeast-2

# Or via environment variable
export AWS_REGION=ap-southeast-2
```

### 3. AWS Service Quotas

Ensure these service limits are sufficient:

| Service | Quota Type | Required Minimum | Check Command |
|---------|------------|------------------|---------------|
| VPC | VPCs per region | 1 | `aws ec2 describe-account-attributes --attribute-names max-vpcs` |
| EC2 | Running On-Demand instances | 5+ | `aws service-quotas get-service-quota --service-code ec2 --quota-code L-1216C47A` |
| RDS | DB instances | 1+ | `aws service-quotas get-service-quota --service-code rds --quota-code L-7B6409FD` |
| ElastiCache | Nodes per region | 2+ | `aws service-quotas get-service-quota --service-code elasticache --quota-code L-47A85A6E` |
| ECS | Tasks per service | 10+ | `aws service-quotas get-service-quota --service-code ecs --quota-code L-9CD9B152` |
| ALB | Application Load Balancers | 1+ | `aws service-quotas get-service-quota --service-code elasticloadbalancing --quota-code L-53DA6B97` |

**Request Quota Increases:**
```bash
aws service-quotas request-service-quota-increase \
  --service-code ec2 \
  --quota-code L-1216C47A \
  --desired-value 10
```

---

## Required AWS Resources

### 1. S3 Bucket for Terraform State

**Purpose:** Store Terraform state files centrally and enable state locking

**Requirements:**
- Bucket name: `ohmycoins-terraform-state` (or similar, must be globally unique)
- Region: Same as deployment region (e.g., `ap-southeast-2`)
- Versioning: Enabled (required for state recovery)
- Encryption: Enabled with AES-256 or KMS
- Public access: Blocked (required for security)

**Creation Commands:**

```bash
# Set variables
BUCKET_NAME="ohmycoins-terraform-state"
AWS_REGION="ap-southeast-2"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)

# Create S3 bucket
aws s3api create-bucket \
  --bucket $BUCKET_NAME \
  --region $AWS_REGION \
  --create-bucket-configuration LocationConstraint=$AWS_REGION

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket $BUCKET_NAME \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket $BUCKET_NAME \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'

# Block public access
aws s3api put-public-access-block \
  --bucket $BUCKET_NAME \
  --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

# Verify bucket
aws s3api head-bucket --bucket $BUCKET_NAME && echo "✅ Bucket created successfully"
```

**Bucket Policy (Optional but Recommended):**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::ohmycoins-terraform-state",
        "arn:aws:s3:::ohmycoins-terraform-state/*"
      ],
      "Condition": {
        "Bool": {
          "aws:SecureTransport": "false"
        }
      }
    }
  ]
}
```

Apply policy:
```bash
aws s3api put-bucket-policy \
  --bucket $BUCKET_NAME \
  --policy file://bucket-policy.json
```

### 2. DynamoDB Table for State Locking

**Purpose:** Prevent concurrent Terraform operations from corrupting state

**Requirements:**
- Table name: `terraform-lock-table`
- Region: Same as S3 bucket
- Partition key: `LockID` (String)
- Billing mode: PAY_PER_REQUEST (or PROVISIONED with 5 RCU, 5 WCU)
- Encryption: Enabled

**Creation Commands:**

```bash
# Create DynamoDB table
aws dynamodb create-table \
  --table-name terraform-lock-table \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region $AWS_REGION

# Wait for table to be active
aws dynamodb wait table-exists --table-name terraform-lock-table

# Verify table
aws dynamodb describe-table \
  --table-name terraform-lock-table \
  --query "Table.TableStatus" \
  --output text
```

### 3. IAM Role for GitHub Actions OIDC

**Purpose:** Allow GitHub Actions to authenticate to AWS without long-lived credentials

**Requirements:**
- Role name: `GitHubActionsRole` (or similar)
- Trust policy: GitHub OIDC provider
- Permissions: Full deployment permissions (see Permissions section)

**Creation Commands:**

```bash
# Step 1: Create OIDC provider for GitHub (if not exists)
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1

# Get provider ARN
OIDC_PROVIDER_ARN=$(aws iam list-open-id-connect-providers \
  --query "OpenIDConnectProviderList[?contains(Arn, 'token.actions.githubusercontent.com')].Arn" \
  --output text)

echo "OIDC Provider ARN: $OIDC_PROVIDER_ARN"

# Step 2: Create trust policy document
cat > trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "$OIDC_PROVIDER_ARN"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:MarkLimmage/ohmycoins:*"
        }
      }
    }
  ]
}
EOF

# Step 3: Create IAM role
aws iam create-role \
  --role-name GitHubActionsRole \
  --assume-role-policy-document file://trust-policy.json \
  --description "Role for GitHub Actions to deploy infrastructure"

# Get role ARN
ROLE_ARN=$(aws iam get-role --role-name GitHubActionsRole --query 'Role.Arn' --output text)
echo "Role ARN: $ROLE_ARN"
echo "⚠️  Save this ARN for GitHub Secrets: AWS_ROLE_ARN=$ROLE_ARN"

# Step 4: Attach managed policies (or create custom policy - see Permissions section)
aws iam attach-role-policy \
  --role-name GitHubActionsRole \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

# Note: AdministratorAccess is convenient for testing but too permissive for production
# See "AWS Permissions Required" section for a least-privilege policy
```

### 4. ECR Repositories for Docker Images

**Purpose:** Store Docker images for backend and frontend

**Requirements:**
- Repository names: `ohmycoins-backend`, `ohmycoins-frontend`
- Region: Same as deployment region
- Image scanning: Enabled
- Tag immutability: Optional (recommended for production)

**Creation Commands:**

```bash
# Create backend repository
aws ecr create-repository \
  --repository-name ohmycoins-backend \
  --region $AWS_REGION \
  --image-scanning-configuration scanOnPush=true

# Create frontend repository
aws ecr create-repository \
  --repository-name ohmycoins-frontend \
  --region $AWS_REGION \
  --image-scanning-configuration scanOnPush=true

# Get repository URIs
BACKEND_REPO_URI=$(aws ecr describe-repositories \
  --repository-names ohmycoins-backend \
  --query 'repositories[0].repositoryUri' \
  --output text)

FRONTEND_REPO_URI=$(aws ecr describe-repositories \
  --repository-names ohmycoins-frontend \
  --query 'repositories[0].repositoryUri' \
  --output text)

echo "Backend ECR: $BACKEND_REPO_URI"
echo "Frontend ECR: $FRONTEND_REPO_URI"

# Test login
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $BACKEND_REPO_URI
```

### 5. Secrets Manager Secrets

**Purpose:** Store sensitive configuration securely

**Required Secrets:**
- Database master password
- Redis auth token
- API keys (OpenAI, Anthropic, CoinGecko, etc.)

**Creation Commands:**

```bash
# Generate secure password
DB_PASSWORD=$(openssl rand -base64 32)

# Create database password secret
aws secretsmanager create-secret \
  --name ohmycoins/staging/db-password \
  --description "RDS master password for staging" \
  --secret-string "$DB_PASSWORD" \
  --region $AWS_REGION

# Create API keys secret
cat > api-keys.json <<EOF
{
  "openai_api_key": "sk-...",
  "anthropic_api_key": "sk-ant-...",
  "coingecko_api_key": "CG-...",
  "sec_api_key": "...",
  "reddit_client_id": "...",
  "reddit_client_secret": "..."
}
EOF

aws secretsmanager create-secret \
  --name ohmycoins/staging/api-keys \
  --description "API keys for external services" \
  --secret-string file://api-keys.json \
  --region $AWS_REGION

# Retrieve secret (for verification)
aws secretsmanager get-secret-value \
  --secret-id ohmycoins/staging/db-password \
  --query 'SecretString' \
  --output text
```

### 6. ACM Certificate for HTTPS (Production Only)

**Purpose:** Enable HTTPS on Application Load Balancer

**Requirements:**
- Domain name: e.g., `ohmycoins.example.com`
- DNS validation or email validation
- Region: Same as deployment region

**Creation Commands:**

```bash
# Request certificate
CERTIFICATE_ARN=$(aws acm request-certificate \
  --domain-name ohmycoins.example.com \
  --subject-alternative-names '*.ohmycoins.example.com' \
  --validation-method DNS \
  --region $AWS_REGION \
  --query 'CertificateArn' \
  --output text)

echo "Certificate ARN: $CERTIFICATE_ARN"

# Get DNS validation records
aws acm describe-certificate \
  --certificate-arn $CERTIFICATE_ARN \
  --region $AWS_REGION \
  --query 'Certificate.DomainValidationOptions[0].ResourceRecord'

# Add the CNAME records to your DNS provider
# Wait for validation
aws acm wait certificate-validated \
  --certificate-arn $CERTIFICATE_ARN \
  --region $AWS_REGION

echo "✅ Certificate validated"
```

---

## Required GitHub Secrets

These secrets must be configured in the GitHub repository settings:

**Location:** `Settings → Secrets and variables → Actions → New repository secret`

### Mandatory Secrets

| Secret Name | Description | How to Obtain | Example Value |
|-------------|-------------|---------------|---------------|
| `AWS_ROLE_ARN` | IAM role ARN for OIDC | From Step 3 above | `arn:aws:iam::123456789012:role/GitHubActionsRole` |
| `DB_MASTER_PASSWORD` | RDS master password | Generate securely | `SuperSecureP@ssw0rd123!` |

### Optional but Recommended Secrets

| Secret Name | Description | How to Obtain | Example Value |
|-------------|-------------|---------------|---------------|
| `REDIS_AUTH_TOKEN` | Redis authentication token | Generate securely | `redis-auth-token-12345` |
| `ACM_CERTIFICATE_ARN` | SSL certificate ARN | From Step 6 above | `arn:aws:acm:ap-southeast-2:123456789012:certificate/...` |
| `OPENAI_API_KEY` | OpenAI API key | https://platform.openai.com | `sk-...` |
| `ANTHROPIC_API_KEY` | Anthropic API key | https://console.anthropic.com | `sk-ant-...` |
| `COINGECKO_API_KEY` | CoinGecko API key | https://www.coingecko.com/en/api | `CG-...` |

**How to Add Secrets:**

```bash
# Via GitHub CLI
gh secret set AWS_ROLE_ARN --body "arn:aws:iam::123456789012:role/GitHubActionsRole"
gh secret set DB_MASTER_PASSWORD --body "$(openssl rand -base64 32)"

# Or manually via GitHub UI:
# 1. Go to repository on GitHub
# 2. Settings → Secrets and variables → Actions
# 3. Click "New repository secret"
# 4. Enter name and value
# 5. Click "Add secret"
```

---

## Required Environment Variables

These must be configured in Terraform variable files:

### Staging: `infrastructure/terraform/environments/staging/terraform.tfvars`

```hcl
# Basic Configuration
project_name = "ohmycoins"
environment  = "staging"
region       = "ap-southeast-2"

# Network Configuration
vpc_cidr = "10.0.0.0/16"
availability_zones = [
  "ap-southeast-2a",
  "ap-southeast-2b"
]

# Database Configuration
db_instance_class         = "db.t3.micro"
db_allocated_storage      = 20
db_max_allocated_storage  = 100
db_multi_az               = false
db_backup_retention_days  = 3
db_deletion_protection    = false

# Redis Configuration
redis_node_type         = "cache.t3.micro"
redis_num_cache_nodes   = 1

# ECS Configuration
backend_cpu    = 512
backend_memory = 1024
backend_desired_count = 1

frontend_cpu    = 256
frontend_memory = 512
frontend_desired_count = 1

# Auto-scaling Configuration
backend_min_tasks  = 1
backend_max_tasks  = 3
frontend_min_tasks = 1
frontend_max_tasks = 3

# Domain Configuration (optional for staging)
domain_name = ""  # Leave empty for staging
certificate_arn = ""  # Leave empty for staging

# Tags
tags = {
  Project     = "ohmycoins"
  Environment = "staging"
  ManagedBy   = "terraform"
  Developer   = "Developer-C"
}
```

### Production: `infrastructure/terraform/environments/production/terraform.tfvars`

```hcl
# Basic Configuration
project_name = "ohmycoins"
environment  = "production"
region       = "ap-southeast-2"

# Network Configuration
vpc_cidr = "10.1.0.0/16"
availability_zones = [
  "ap-southeast-2a",
  "ap-southeast-2b",
  "ap-southeast-2c"
]
multi_az_nat_gateway = true

# Database Configuration
db_instance_class         = "db.t3.small"
db_allocated_storage      = 50
db_max_allocated_storage  = 500
db_multi_az               = true
db_backup_retention_days  = 30
db_deletion_protection    = true
create_read_replica       = true

# Redis Configuration
redis_node_type         = "cache.t3.small"
redis_num_cache_nodes   = 2

# ECS Configuration
backend_cpu    = 1024
backend_memory = 2048
backend_desired_count = 2

frontend_cpu    = 512
frontend_memory = 1024
frontend_desired_count = 2

# Auto-scaling Configuration
backend_min_tasks  = 2
backend_max_tasks  = 10
frontend_min_tasks = 2
frontend_max_tasks = 10

# Domain Configuration
domain_name = "ohmycoins.example.com"
certificate_arn = "arn:aws:acm:ap-southeast-2:123456789012:certificate/..."

# Tags
tags = {
  Project     = "ohmycoins"
  Environment = "production"
  ManagedBy   = "terraform"
  CostCenter  = "engineering"
  Compliance  = "required"
}
```

**Create Variable Files:**

```bash
# Copy example files
cd infrastructure/terraform/environments/staging
cp terraform.tfvars.example terraform.tfvars
# Edit with your values

cd ../production
cp terraform.tfvars.example terraform.tfvars
# Edit with your values
```

---

## AWS Permissions Required

### Least-Privilege IAM Policy

Instead of using `AdministratorAccess`, create a custom policy with only required permissions:

**Policy Name:** `OhMyCoinsDeploymentPolicy`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:*",
        "ecs:*",
        "ecr:*",
        "elasticloadbalancing:*",
        "rds:*",
        "elasticache:*",
        "s3:*",
        "dynamodb:*",
        "iam:GetRole",
        "iam:PassRole",
        "iam:CreateRole",
        "iam:AttachRolePolicy",
        "iam:PutRolePolicy",
        "iam:GetRolePolicy",
        "iam:ListRolePolicies",
        "iam:ListAttachedRolePolicies",
        "logs:*",
        "cloudwatch:*",
        "secretsmanager:*",
        "kms:*",
        "acm:*",
        "route53:*"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::ohmycoins-terraform-state/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:DeleteItem"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/terraform-lock-table"
    }
  ]
}
```

**Create and Attach Policy:**

```bash
# Create policy
aws iam create-policy \
  --policy-name OhMyCoinsDeploymentPolicy \
  --policy-document file://deployment-policy.json

# Get policy ARN
POLICY_ARN=$(aws iam list-policies \
  --query "Policies[?PolicyName=='OhMyCoinsDeploymentPolicy'].Arn" \
  --output text)

# Attach to role
aws iam attach-role-policy \
  --role-name GitHubActionsRole \
  --policy-arn $POLICY_ARN

# Remove AdministratorAccess if previously attached
aws iam detach-role-policy \
  --role-name GitHubActionsRole \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess
```

---

## Setup Instructions

### Complete Setup Checklist

Execute these steps in order to prepare for deployment:

#### Step 1: Prepare AWS Account

```bash
# 1.1 Configure AWS CLI
aws configure
# Enter:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region: ap-southeast-2
# - Default output format: json

# 1.2 Verify access
aws sts get-caller-identity

# 1.3 Save account details
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
echo "AWS Account ID: $AWS_ACCOUNT_ID"
```

#### Step 2: Create Backend Resources

```bash
# 2.1 Set variables
export BUCKET_NAME="ohmycoins-terraform-state"
export AWS_REGION="ap-southeast-2"
export TABLE_NAME="terraform-lock-table"

# 2.2 Create S3 bucket (see detailed commands in "Required AWS Resources" section)
./infrastructure/terraform/scripts/setup-backend.sh  # If you create this script

# Or manually:
aws s3api create-bucket \
  --bucket $BUCKET_NAME \
  --region $AWS_REGION \
  --create-bucket-configuration LocationConstraint=$AWS_REGION

aws s3api put-bucket-versioning \
  --bucket $BUCKET_NAME \
  --versioning-configuration Status=Enabled

# 2.3 Create DynamoDB table
aws dynamodb create-table \
  --table-name $TABLE_NAME \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region $AWS_REGION

# 2.4 Verify
aws s3 ls s3://$BUCKET_NAME
aws dynamodb describe-table --table-name $TABLE_NAME
```

#### Step 3: Configure OIDC for GitHub Actions

```bash
# 3.1 Create OIDC provider
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1

# 3.2 Create IAM role with trust policy (see detailed commands above)
# Save the trust-policy.json file
# Create role
# Attach policies

# 3.3 Save Role ARN
ROLE_ARN=$(aws iam get-role --role-name GitHubActionsRole --query 'Role.Arn' --output text)
echo "AWS_ROLE_ARN=$ROLE_ARN"
```

#### Step 4: Create ECR Repositories

```bash
# 4.1 Create repositories
aws ecr create-repository --repository-name ohmycoins-backend --region $AWS_REGION
aws ecr create-repository --repository-name ohmycoins-frontend --region $AWS_REGION

# 4.2 Get URIs
aws ecr describe-repositories \
  --repository-names ohmycoins-backend ohmycoins-frontend \
  --query 'repositories[*].[repositoryName,repositoryUri]' \
  --output table
```

#### Step 5: Create Secrets

```bash
# 5.1 Generate database password
DB_PASSWORD=$(openssl rand -base64 32)

# 5.2 Create secret in Secrets Manager
aws secretsmanager create-secret \
  --name ohmycoins/staging/db-password \
  --secret-string "$DB_PASSWORD" \
  --region $AWS_REGION

# 5.3 Save password for GitHub Secret
echo "DB_MASTER_PASSWORD=$DB_PASSWORD"
```

#### Step 6: Configure GitHub Secrets

```bash
# 6.1 Add secrets via GitHub CLI
gh secret set AWS_ROLE_ARN --body "$ROLE_ARN"
gh secret set DB_MASTER_PASSWORD --body "$DB_PASSWORD"

# Or manually via GitHub UI
echo "Add these secrets to GitHub:"
echo "AWS_ROLE_ARN=$ROLE_ARN"
echo "DB_MASTER_PASSWORD=$DB_PASSWORD"
```

#### Step 7: Configure Terraform Variables

```bash
# 7.1 Create terraform.tfvars files
cd infrastructure/terraform/environments/staging
cp terraform.tfvars.example terraform.tfvars

# 7.2 Edit variables
nano terraform.tfvars
# Update with your values

# 7.3 Configure backend
cat > backend.tf <<EOF
terraform {
  backend "s3" {
    bucket         = "$BUCKET_NAME"
    key            = "staging/terraform.tfstate"
    region         = "$AWS_REGION"
    dynamodb_table = "$TABLE_NAME"
    encrypt        = true
  }
}
EOF
```

#### Step 8: Validate Setup

```bash
# 8.1 Run pre-deployment check
cd infrastructure/terraform
./scripts/pre-deployment-check.sh staging

# 8.2 Run validation
./scripts/validate-terraform.sh

# 8.3 Check GitHub Actions
# Go to: Actions → Test Infrastructure → Run workflow
```

---

## Validation Checklist

Use this checklist to verify all requirements are met:

### AWS Account Setup

- [ ] AWS account active and accessible
- [ ] AWS CLI configured with credentials
- [ ] Correct AWS region selected (ap-southeast-2)
- [ ] Service quotas sufficient for deployment
- [ ] Billing alarms configured (recommended)

### AWS Backend Resources

- [ ] S3 bucket created: `ohmycoins-terraform-state`
- [ ] S3 versioning enabled
- [ ] S3 encryption enabled
- [ ] S3 public access blocked
- [ ] DynamoDB table created: `terraform-lock-table`
- [ ] DynamoDB table has correct partition key: `LockID`

### IAM and Authentication

- [ ] GitHub OIDC provider created
- [ ] IAM role created: `GitHubActionsRole`
- [ ] Role has trust policy for GitHub Actions
- [ ] Role has deployment permissions attached
- [ ] Role ARN saved for GitHub Secret

### Container Repositories

- [ ] ECR repository created: `ohmycoins-backend`
- [ ] ECR repository created: `ohmycoins-frontend`
- [ ] Image scanning enabled
- [ ] Repository URIs documented

### Secrets and Configuration

- [ ] Database password generated and stored
- [ ] Database password added to Secrets Manager
- [ ] Database password added to GitHub Secrets
- [ ] API keys obtained (if needed)
- [ ] API keys added to Secrets Manager

### GitHub Configuration

- [ ] GitHub Secret: `AWS_ROLE_ARN` configured
- [ ] GitHub Secret: `DB_MASTER_PASSWORD` configured
- [ ] GitHub Secret: `ACM_CERTIFICATE_ARN` (if using HTTPS)
- [ ] GitHub repository has OIDC permissions
- [ ] Self-hosted runners configured (optional but recommended)

### Terraform Configuration

- [ ] `terraform.tfvars` created for staging
- [ ] `terraform.tfvars` created for production
- [ ] Backend configuration updated with S3 bucket name
- [ ] Backend configuration updated with DynamoDB table name
- [ ] All required variables populated

### Production-Only (Optional for Staging)

- [ ] Domain name registered
- [ ] DNS hosted zone created in Route53
- [ ] ACM certificate requested
- [ ] ACM certificate validated
- [ ] Certificate ARN saved

### Testing

- [ ] Pre-deployment check script runs successfully
- [ ] Terraform validation passes
- [ ] Cost estimation script runs
- [ ] GitHub Actions test workflow passes

---

## Troubleshooting

### Issue: AWS CLI Not Configured

**Symptom:**
```
Unable to locate credentials. You can configure credentials by running "aws configure"
```

**Solution:**
```bash
aws configure
# Or set environment variables:
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_REGION="ap-southeast-2"
```

### Issue: S3 Bucket Already Exists

**Symptom:**
```
An error occurred (BucketAlreadyExists) when calling the CreateBucket operation
```

**Solution:**
```bash
# Choose a different bucket name (must be globally unique)
BUCKET_NAME="ohmycoins-terraform-state-$(aws sts get-caller-identity --query Account --output text)"
```

### Issue: Insufficient IAM Permissions

**Symptom:**
```
An error occurred (AccessDenied) when calling the CreateBucket operation
```

**Solution:**
```bash
# Verify your IAM user has sufficient permissions
aws iam get-user
aws iam list-attached-user-policies --user-name YOUR_USERNAME

# Contact AWS administrator to grant required permissions
```

### Issue: OIDC Provider Already Exists

**Symptom:**
```
EntityAlreadyExists: Provider with url https://token.actions.githubusercontent.com already exists
```

**Solution:**
```bash
# This is OK - provider already exists, skip creation
# Just get the ARN:
OIDC_PROVIDER_ARN=$(aws iam list-open-id-connect-providers \
  --query "OpenIDConnectProviderList[?contains(Arn, 'token.actions.githubusercontent.com')].Arn" \
  --output text)
```

### Issue: GitHub Actions Cannot Assume Role

**Symptom:**
```
Error: User: ... is not authorized to perform: sts:AssumeRoleWithWebIdentity
```

**Solution:**
```bash
# Verify trust policy is correct
aws iam get-role --role-name GitHubActionsRole --query 'Role.AssumeRolePolicyDocument'

# Verify repository name matches in trust policy
# Should be: "token.actions.githubusercontent.com:sub": "repo:MarkLimmage/ohmycoins:*"
```

### Issue: Terraform State Lock Timeout

**Symptom:**
```
Error locking state: Error acquiring the state lock
```

**Solution:**
```bash
# Check if lock exists
aws dynamodb get-item \
  --table-name terraform-lock-table \
  --key '{"LockID": {"S": "ohmycoins-staging/terraform.tfstate-md5"}}'

# If stale, force unlock
cd infrastructure/terraform/environments/staging
terraform force-unlock <lock-id>
```

---

## Quick Start Script

Save this as `infrastructure/terraform/scripts/setup-aws-deployment.sh`:

```bash
#!/bin/bash
# Quick setup script for AWS deployment requirements

set -e

echo "========================================="
echo "Oh My Coins - AWS Deployment Setup"
echo "========================================="
echo ""

# Variables
BUCKET_NAME="ohmycoins-terraform-state"
TABLE_NAME="terraform-lock-table"
AWS_REGION="ap-southeast-2"
ROLE_NAME="GitHubActionsRole"

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
echo "AWS Account ID: $AWS_ACCOUNT_ID"
echo ""

# Create S3 bucket
echo "Creating S3 bucket: $BUCKET_NAME..."
aws s3api create-bucket \
  --bucket $BUCKET_NAME \
  --region $AWS_REGION \
  --create-bucket-configuration LocationConstraint=$AWS_REGION || echo "Bucket may already exist"

aws s3api put-bucket-versioning \
  --bucket $BUCKET_NAME \
  --versioning-configuration Status=Enabled

aws s3api put-bucket-encryption \
  --bucket $BUCKET_NAME \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'

echo "✅ S3 bucket configured"
echo ""

# Create DynamoDB table
echo "Creating DynamoDB table: $TABLE_NAME..."
aws dynamodb create-table \
  --table-name $TABLE_NAME \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region $AWS_REGION || echo "Table may already exist"

echo "✅ DynamoDB table created"
echo ""

# Create ECR repositories
echo "Creating ECR repositories..."
aws ecr create-repository \
  --repository-name ohmycoins-backend \
  --region $AWS_REGION || echo "Backend repo may already exist"

aws ecr create-repository \
  --repository-name ohmycoins-frontend \
  --region $AWS_REGION || echo "Frontend repo may already exist"

echo "✅ ECR repositories created"
echo ""

# Generate database password
DB_PASSWORD=$(openssl rand -base64 32)

# Create secret
echo "Creating Secrets Manager secret..."
aws secretsmanager create-secret \
  --name ohmycoins/staging/db-password \
  --secret-string "$DB_PASSWORD" \
  --region $AWS_REGION || echo "Secret may already exist"

echo "✅ Secrets created"
echo ""

# Output summary
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Configure GitHub Secrets:"
echo "   AWS_ROLE_ARN: (see IAM console for GitHubActionsRole ARN)"
echo "   DB_MASTER_PASSWORD: $DB_PASSWORD"
echo ""
echo "2. Update terraform.tfvars files in environments/"
echo ""
echo "3. Run pre-deployment check:"
echo "   ./scripts/pre-deployment-check.sh staging"
echo ""
```

Make it executable:
```bash
chmod +x infrastructure/terraform/scripts/setup-aws-deployment.sh
```

---

## Summary

This document provides a complete checklist of AWS credentials, resources, and configurations required for deploying the Oh My Coins infrastructure. All requirements have been documented with:

- ✅ Step-by-step creation commands
- ✅ Verification commands
- ✅ Troubleshooting guidance
- ✅ Quick start script
- ✅ Validation checklist

**To facilitate AWS deployment for testing, provide:**

1. **AWS Credentials** with appropriate permissions
2. **S3 Bucket** for Terraform state: `ohmycoins-terraform-state`
3. **DynamoDB Table** for state locking: `terraform-lock-table`
4. **IAM Role ARN** for GitHub Actions OIDC
5. **Database Password** for RDS
6. **ECR Repository URIs** for Docker images
7. **GitHub Secrets** configured with the above values

Once these are in place, the infrastructure can be deployed using:
- GitHub Actions workflows (recommended)
- Manual Terraform commands (for testing)
- AWS EKS self-hosted runners (for realistic testing)

---

**Document Version:** 1.0  
**Last Updated:** 2025-11-17  
**Maintained By:** Developer C (Infrastructure & DevOps Specialist)
