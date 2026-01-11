# Step-by-Step AWS Deployment Guide for Oh My Coins

**Purpose:** Walk through deploying Oh My Coins infrastructure to AWS staging environment  
**Estimated Time:** 60-90 minutes (first deployment)  
**Target Audience:** DevOps engineers, developers with AWS access  
**Prerequisites:** AWS account with billing enabled

---

## 📋 Before You Begin

### What You'll Need

**Required Tools:**
- [ ] AWS account with admin or PowerUser access
- [ ] Credit card on file with AWS (infrastructure will cost ~$50-100/month for staging)
- [ ] Computer with Linux, macOS, or Windows (WSL2)
- [ ] Terminal/command line access
- [ ] Text editor (VS Code, vim, nano, etc.)

**Time Allocation:**
- Initial setup: 20-30 minutes
- Infrastructure deployment: 15-20 minutes  
- Application deployment: 10-15 minutes
- Validation: 10-15 minutes

### Cost Estimate

**Monthly AWS Costs (Staging):**
- RDS PostgreSQL (db.t3.micro): ~$15
- ElastiCache Redis (cache.t3.micro): ~$12
- ECS Fargate (2 tasks, 1GB each): ~$15
- NAT Gateway: ~$32
- Application Load Balancer: ~$18
- CloudWatch/Secrets Manager: ~$5
- **Total: ~$97/month**

> 💡 **Tip:** You can reduce costs by stopping the environment when not in use (stop ECS tasks).

---

## Step 1: Install Required Tools (15 minutes)

### 1.1 Install AWS CLI

**macOS (using Homebrew):**
```bash
brew install awscli
```

**Linux:**
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

**Windows (using MSI installer):**
1. Download from: https://awscli.amazonaws.com/AWSCLIV2.msi
2. Run the installer
3. Open PowerShell or Command Prompt

**Verify Installation:**
```bash
aws --version
# Expected output: aws-cli/2.x.x Python/3.x.x ...
```

### 1.2 Install Terraform

**macOS (using Homebrew):**
```bash
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
```

**Linux:**
```bash
wget https://releases.hashicorp.com/terraform/1.7.0/terraform_1.7.0_linux_amd64.zip
unzip terraform_1.7.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
```

**Windows (using Chocolatey):**
```bash
choco install terraform
```

**Verify Installation:**
```bash
terraform version
# Expected output: Terraform v1.7.0 or higher
```

### 1.3 Install Docker

**macOS/Windows:**
1. Download Docker Desktop: https://www.docker.com/products/docker-desktop
2. Install and start Docker Desktop
3. Verify Docker is running

**Linux:**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Log out and back in for group changes to take effect
```

**Verify Installation:**
```bash
docker --version
# Expected output: Docker version 24.x.x or higher

docker ps
# Should not show any errors
```

---

## Step 2: Configure AWS Credentials (10 minutes)

### 2.1 Create AWS IAM User

1. **Log into AWS Console:** https://console.aws.amazon.com
2. **Navigate to IAM:** Services → IAM → Users → Add users
3. **Create user:**
   - Username: `ohmycoins-deployer`
   - Access type: ✅ Programmatic access
   - Click "Next: Permissions"
4. **Attach policies:**
   - ✅ AdministratorAccess (for initial setup)
   - Click "Next: Tags" → "Next: Review" → "Create user"
5. **Save credentials:**
   - ⚠️ **Copy Access Key ID and Secret Access Key NOW**
   - You won't be able to see the secret key again
   - Save them in a secure password manager

### 2.2 Configure AWS CLI

```bash
# Configure AWS credentials
aws configure

# You'll be prompted for:
AWS Access Key ID [None]: <paste your access key>
AWS Secret Access Key [None]: <paste your secret key>
Default region name [None]: ap-southeast-2
Default output format [None]: json
```

**Verify Configuration:**
```bash
# Test AWS credentials
aws sts get-caller-identity

# Expected output:
# {
#     "UserId": "AIDAXXXXXXXXXXXXXXXXX",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/ohmycoins-deployer"
# }

# Save your account ID for later
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "Your AWS Account ID: $AWS_ACCOUNT_ID"
```

---

## Step 3: Clone Repository and Prepare Environment (5 minutes)

### 3.1 Clone Repository

```bash
# Clone the repository
git clone https://github.com/MarkLimmage/ohmycoins.git
cd ohmycoins

# Verify you're in the right place
ls -la
# Should see: backend/ frontend/ infrastructure/ docs/ etc.
```

### 3.2 Navigate to Infrastructure Directory

```bash
cd infrastructure/terraform/environments/staging

# List files
ls -la
# Should see: main.tf, variables.tf, terraform.tfvars.example, outputs.tf
```

---

## Step 4: Set Up Terraform Backend (10 minutes)

### 4.1 Create S3 Bucket for Terraform State

```bash
# Set variables
export AWS_REGION="ap-southeast-2"
export STATE_BUCKET="ohmycoins-terraform-state"
export LOCK_TABLE="ohmycoins-terraform-locks"

# Create S3 bucket
aws s3api create-bucket \
    --bucket $STATE_BUCKET \
    --region $AWS_REGION \
    --create-bucket-configuration LocationConstraint=$AWS_REGION

# Enable versioning (important for rollback capability)
aws s3api put-bucket-versioning \
    --bucket $STATE_BUCKET \
    --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
    --bucket $STATE_BUCKET \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            },
            "BucketKeyEnabled": true
        }]
    }'

# Block public access (security best practice)
aws s3api put-public-access-block \
    --bucket $STATE_BUCKET \
    --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

echo "✓ S3 bucket created: $STATE_BUCKET"
```

### 4.2 Create DynamoDB Table for State Locking

```bash
# Create DynamoDB table
aws dynamodb create-table \
    --table-name $LOCK_TABLE \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region $AWS_REGION

# Wait for table to be active
aws dynamodb wait table-exists --table-name $LOCK_TABLE --region $AWS_REGION

echo "✓ DynamoDB table created: $LOCK_TABLE"
```

### 4.3 Verify Backend Resources

```bash
# Verify S3 bucket
aws s3 ls $STATE_BUCKET
# Should show empty output (no error)

# Verify DynamoDB table
aws dynamodb describe-table \
    --table-name $LOCK_TABLE \
    --region $AWS_REGION \
    --query 'Table.TableStatus' \
    --output text
# Should output: ACTIVE

echo "✓ Terraform backend ready"
```

---

## Step 5: Configure Terraform Variables (10 minutes)

### 5.1 Generate Secure Passwords

```bash
# Generate RDS-compatible database password (no /, @, ", or space characters)
export DB_PASSWORD=$(openssl rand -base64 32 | tr -d '/+=' | head -c 32)

# Generate other secure credentials
export APP_SECRET_KEY=$(openssl rand -base64 32)
export ADMIN_PASSWORD=$(openssl rand -base64 16)

echo "=== SAVE THESE CREDENTIALS ==="
echo "Database Password: $DB_PASSWORD"
echo "App Secret Key: $APP_SECRET_KEY"
echo "Admin Password: $ADMIN_PASSWORD"
echo "=============================="
echo ""
echo "⚠️  IMPORTANT: Save these in a password manager NOW!"
echo "Note: DB password excludes /+= characters (RDS requirement)"
echo "Press Enter to continue after saving..."
read
```
echo ""
echo "⚠️  IMPORTANT: Save these in a password manager NOW!"
echo "Press Enter to continue after saving..."
read
```

### 5.2 Create terraform.tfvars File

```bash
# Create terraform.tfvars from template
cp terraform.tfvars.example terraform.tfvars

# Edit the file (use your preferred editor)
nano terraform.tfvars
```

**Replace the following values in `terraform.tfvars`:**

```hcl
aws_region = "ap-southeast-2"

# Database password - USE THE GENERATED PASSWORD ABOVE
master_password = "<PASTE_DB_PASSWORD_HERE>"

# Domain configuration - MODIFY THESE if you have custom domains
# Or leave as-is to use ALB DNS name
domain              = "staging.ohmycoins.com"
backend_domain      = "api.staging.ohmycoins.com"
frontend_host       = "https://dashboard.staging.ohmycoins.com"
backend_cors_origins = "https://dashboard.staging.ohmycoins.com,http://localhost:5173"

# ACM Certificate ARN - LEAVE EMPTY for HTTP-only staging
# certificate_arn = ""

# GitHub configuration
github_repo                = "MarkLimmage/ohmycoins"
create_github_oidc_provider = true

# Container images - USE THESE DEFAULT VALUES
backend_image      = "ghcr.io/marklimmage/ohmycoins-backend"
backend_image_tag  = "latest"
frontend_image     = "ghcr.io/marklimmage/ohmycoins-frontend"
frontend_image_tag = "latest"
```

**Save and close the file** (Ctrl+X, then Y, then Enter if using nano)

### 5.3 Verify Configuration

```bash
# Validate terraform.tfvars syntax
terraform fmt terraform.tfvars

# Check that password was set (not the placeholder)
grep -q "<PASTE_DB_PASSWORD_HERE>" terraform.tfvars && echo "⚠️  ERROR: Update master_password!" || echo "✓ Password configured"

# Validate password doesn't contain invalid characters for RDS
if grep "master_password" terraform.tfvars | grep -q "[/@\" ]"; then
    echo "⚠️  ERROR: Password contains invalid characters (/, @, \", or space)"
    echo "Regenerate with: openssl rand -base64 32 | tr -d '/+=' | head -c 32"
else
    echo "✓ Password is RDS-compatible"
fi
```

---

## Step 6: Deploy Infrastructure with Terraform (20 minutes)

### 6.1 Initialize Terraform

```bash
# Make sure you're in the staging directory
pwd
# Should end with: /infrastructure/terraform/environments/staging

# Initialize Terraform
terraform init

# Expected output:
# Initializing modules...
# Initializing the backend...
# Initializing provider plugins...
# Terraform has been successfully initialized!
```

**If you see errors:**
- Check that S3 bucket and DynamoDB table exist
- Verify AWS credentials are configured correctly
- Ensure you have internet access to download providers

### 6.2 Validate Configuration

```bash
# Validate Terraform configuration
terraform validate

# Expected output:
# Success! The configuration is valid.
```

### 6.3 Plan Deployment

```bash
# Generate deployment plan
terraform plan -out=tfplan

# This will:
# 1. Show all resources to be created (~73 resources)
# 2. Save the plan to a file (tfplan)
# 3. Take 1-2 minutes to complete

# Review the output carefully:
# - Look for "Plan: XX to add, 0 to change, 0 to destroy"
# - Verify resource names start with "ohmycoins-staging"
# - Check that database password is not visible in output
```

**Expected Resources:**
- VPC and networking: ~15 resources
- RDS PostgreSQL: ~5 resources  
- ElastiCache Redis: ~5 resources
- ECS cluster and services: ~20 resources
- ALB and target groups: ~10 resources
- IAM roles and policies: ~10 resources
- Secrets Manager: ~2 resources
- Security groups: ~6 resources
- **Total: ~73 resources**

### 6.4 Apply Infrastructure

```bash
# Apply the plan
terraform apply tfplan

# This will:
# 1. Create all AWS resources
# 2. Take 10-15 minutes (RDS creation is the slowest)
# 3. Show progress as resources are created

# You'll see output like:
# module.vpc.aws_vpc.main: Creating...
# module.vpc.aws_vpc.main: Creation complete after 3s
# ...
# Apply complete! Resources: 73 added, 0 changed, 0 destroyed.
```

**⏱️ Grab a coffee! This takes 10-15 minutes.**

**Watch for:**
- ✅ Green text: Resources created successfully
- ⚠️ Yellow text: Warnings (usually safe to ignore)
- ❌ Red text: Errors (stop and troubleshoot)

### 6.5 Save Terraform Outputs

```bash
# After successful apply, save outputs
terraform output > outputs.txt

# Display key outputs
echo "=== DEPLOYMENT OUTPUTS ==="
terraform output alb_dns_name
terraform output ecs_cluster_name
terraform output db_instance_address
terraform output redis_primary_endpoint_address
terraform output app_secrets_arn
echo "=========================="

# Save these for later reference
```

---

## Step 7: Configure Application Secrets (10 minutes)

### 7.1 Prepare Secrets JSON

```bash
# Get output values
export SECRET_ARN=$(terraform output -raw app_secrets_arn)
export DB_HOST=$(terraform output -raw db_instance_address)
export REDIS_HOST=$(terraform output -raw redis_primary_endpoint_address)
export ALB_DNS=$(terraform output -raw alb_dns_name)

# Create secrets JSON file
cat > /tmp/staging-secrets.json << EOF
{
  "SECRET_KEY": "$APP_SECRET_KEY",
  "FIRST_SUPERUSER": "admin@ohmycoins.com",
  "FIRST_SUPERUSER_PASSWORD": "$ADMIN_PASSWORD",
  "POSTGRES_SERVER": "$DB_HOST",
  "POSTGRES_PORT": "5432",
  "POSTGRES_DB": "ohmycoins",
  "POSTGRES_USER": "postgres",
  "POSTGRES_PASSWORD": "$DB_PASSWORD",
  "REDIS_HOST": "$REDIS_HOST",
  "REDIS_PORT": "6379",
  "OPENAI_API_KEY": "",
  "OPENAI_MODEL": "gpt-4-turbo-preview",
  "LLM_PROVIDER": "openai",
  "ENVIRONMENT": "staging",
  "FRONTEND_HOST": "http://$ALB_DNS",
  "SMTP_HOST": "",
  "SMTP_USER": "",
  "SMTP_PASSWORD": "",
  "SMTP_TLS": "True",
  "SMTP_SSL": "False",
  "SMTP_PORT": "587",
  "EMAILS_FROM_EMAIL": "noreply@ohmycoins.com"
}
EOF

echo "✓ Secrets file created at /tmp/staging-secrets.json"
```

### 7.2 Update Secrets in AWS

```bash
# Upload secrets to AWS Secrets Manager
aws secretsmanager put-secret-value \
    --secret-id $SECRET_ARN \
    --secret-string file:///tmp/staging-secrets.json \
    --region ap-southeast-2

# Verify secret was updated
aws secretsmanager describe-secret \
    --secret-id $SECRET_ARN \
    --region ap-southeast-2 \
    --query '[Name,LastChangedDate]' \
    --output table

# Clean up temporary file
rm /tmp/staging-secrets.json

echo "✓ Application secrets configured"
```

### 7.3 Add OpenAI API Key (Optional)

If you have an OpenAI API key for the agentic AI features:

```bash
# Get current secret value
CURRENT_SECRET=$(aws secretsmanager get-secret-value \
    --secret-id $SECRET_ARN \
    --region ap-southeast-2 \
    --query SecretString \
    --output text)

# Update with your OpenAI key (replace with your actual key)
echo "$CURRENT_SECRET" | jq '.OPENAI_API_KEY = "sk-your-openai-key-here"' > /tmp/updated-secret.json

# Update secret
aws secretsmanager put-secret-value \
    --secret-id $SECRET_ARN \
    --secret-string file:///tmp/updated-secret.json \
    --region ap-southeast-2

rm /tmp/updated-secret.json

echo "✓ OpenAI API key added"
```

---

## Step 8: Deploy Application Services (15 minutes)

### 8.1 Build and Push Docker Images

**Option A: Use Existing Images (Recommended for First Deployment)**

The Terraform configuration uses pre-built images from GitHub Container Registry. Skip to section 8.2.

**Option B: Build Your Own Images (Advanced)**

```bash
# Navigate to project root
cd ../../../../

# Login to AWS ECR
aws ecr get-login-password --region ap-southeast-2 | \
    docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.ap-southeast-2.amazonaws.com

# Create ECR repositories
aws ecr create-repository --repository-name ohmycoins/backend --region ap-southeast-2
aws ecr create-repository --repository-name ohmycoins/frontend --region ap-southeast-2

# Build and push backend
docker build -t ohmycoins-backend:latest ./backend
docker tag ohmycoins-backend:latest $AWS_ACCOUNT_ID.dkr.ecr.ap-southeast-2.amazonaws.com/ohmycoins/backend:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.ap-southeast-2.amazonaws.com/ohmycoins/backend:latest

# Build and push frontend
docker build -t ohmycoins-frontend:latest ./frontend
docker tag ohmycoins-frontend:latest $AWS_ACCOUNT_ID.dkr.ecr.ap-southeast-2.amazonaws.com/ohmycoins/frontend:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.ap-southeast-2.amazonaws.com/ohmycoins/frontend:latest
```

### 8.2 Deploy Services to ECS

```bash
# Get cluster name
export CLUSTER_NAME=$(cd infrastructure/terraform/environments/staging && terraform output -raw ecs_cluster_name)

echo "Deploying to cluster: $CLUSTER_NAME"

# Trigger new deployment of backend service
aws ecs update-service \
    --cluster $CLUSTER_NAME \
    --service ohmycoins-staging-backend-service \
    --force-new-deployment \
    --region ap-southeast-2

# Trigger new deployment of frontend service
aws ecs update-service \
    --cluster $CLUSTER_NAME \
    --service ohmycoins-staging-frontend-service \
    --force-new-deployment \
    --region ap-southeast-2

echo "✓ Deployment initiated"
echo "⏱️  Waiting for services to stabilize (5-10 minutes)..."
```

### 8.3 Wait for Deployment

```bash
# Wait for services to become stable
aws ecs wait services-stable \
    --cluster $CLUSTER_NAME \
    --services ohmycoins-staging-backend-service ohmycoins-staging-frontend-service \
    --region ap-southeast-2

echo "✓ Services are stable and running"
```

### 8.4 Verify Service Status

```bash
# Check service status
aws ecs describe-services \
    --cluster $CLUSTER_NAME \
    --services ohmycoins-staging-backend-service ohmycoins-staging-frontend-service \
    --region ap-southeast-2 \
    --query 'services[*].[serviceName,status,runningCount,desiredCount,deployments[0].rolloutState]' \
    --output table

# Expected output:
# ----------------------------------------------------------------
# |                      DescribeServices                        |
# +-------------------------------+--------+----------+----------+
# | ohmycoins-staging-backend-svc | ACTIVE |    1     |    1     | COMPLETED |
# | ohmycoins-staging-frontend-svc| ACTIVE |    1     |    1     | COMPLETED |
# +-------------------------------+--------+----------+----------+
```

---

## Step 9: Validate Deployment (10 minutes)

### 9.1 Get Application URL

```bash
# Get ALB DNS name
export ALB_DNS=$(cd infrastructure/terraform/environments/staging && terraform output -raw alb_dns_name)

echo "==================================="
echo "Application URLs:"
echo "Backend API:  http://$ALB_DNS"
echo "API Docs:     http://$ALB_DNS/docs"
echo "Frontend:     http://$ALB_DNS/"
echo "Health Check: http://$ALB_DNS/health"
echo "==================================="
```

### 9.2 Test Health Endpoints

```bash
# Test backend health
echo "Testing backend health..."
curl -f http://$ALB_DNS/health && echo "✓ Backend healthy" || echo "❌ Backend unhealthy"

# Test API documentation
echo "Testing API docs..."
curl -s -o /dev/null -w "%{http_code}" http://$ALB_DNS/docs | grep -q "200" && echo "✓ API docs accessible" || echo "❌ API docs not accessible"

# Test frontend
echo "Testing frontend..."
curl -s -o /dev/null -w "%{http_code}" http://$ALB_DNS/ | grep -q "200" && echo "✓ Frontend accessible" || echo "❌ Frontend not accessible"
```

### 9.3 Check ALB Target Health

```bash
# Get backend target group ARN
export TG_ARN=$(cd infrastructure/terraform/environments/staging && terraform output -raw backend_target_group_arn)

# Check target health
aws elbv2 describe-target-health \
    --target-group-arn $TG_ARN \
    --region ap-southeast-2 \
    --query 'TargetHealthDescriptions[*].[Target.Id,TargetHealth.State,TargetHealth.Reason]' \
    --output table

# Expected: State = healthy
```

### 9.4 View Application Logs

```bash
# View backend logs (last 10 minutes)
aws logs tail /ecs/ohmycoins-staging-backend \
    --since 10m \
    --region ap-southeast-2

# Press Ctrl+C to stop tailing logs

# Check for errors
echo "Checking for errors in logs..."
ERROR_COUNT=$(aws logs filter-log-events \
    --log-group-name /ecs/ohmycoins-staging-backend \
    --filter-pattern "ERROR" \
    --start-time $(date -u -d '10 minutes ago' +%s)000 \
    --region ap-southeast-2 \
    --query 'events' \
    --output json | jq 'length')

echo "Errors in last 10 minutes: $ERROR_COUNT"
```

### 9.5 Test API Endpoint

```bash
# Test a simple API endpoint
echo "Testing API endpoint..."
curl -X GET "http://$ALB_DNS/api/v1/health" -H "accept: application/json"

# You should see JSON response with health status
```

---

## Step 10: Configure Monitoring (5 minutes)

### 10.1 Access CloudWatch Dashboard

```bash
# Get dashboard URL
echo "CloudWatch Dashboard URL:"
echo "https://console.aws.amazon.com/cloudwatch/home?region=ap-southeast-2#dashboards:name=ohmycoins-staging-infrastructure"
```

**Manual Steps:**
1. Open the URL in your browser
2. Log into AWS Console if prompted
3. Verify dashboard shows 6 widgets with metrics

### 10.2 Configure Email Alerts

```bash
# Get SNS topic ARN
export SNS_TOPIC_ARN=$(cd infrastructure/terraform/environments/staging && terraform output -raw monitoring_sns_topic_arn)

# Subscribe your email to alerts
aws sns subscribe \
    --topic-arn $SNS_TOPIC_ARN \
    --protocol email \
    --notification-endpoint your-email@example.com \
    --region ap-southeast-2

echo "✓ Subscription request sent to your-email@example.com"
echo "⚠️  Check your email and confirm the subscription!"
```

### 10.3 Test Alert System

```bash
# Send test notification
aws sns publish \
    --topic-arn $SNS_TOPIC_ARN \
    --message "Test alert from Oh My Coins staging environment - Deployment successful!" \
    --subject "✓ Oh My Coins Staging - Test Alert" \
    --region ap-southeast-2

echo "✓ Test notification sent. Check your email."
```

### 10.4 View CloudWatch Alarms

```bash
# List all alarms
aws cloudwatch describe-alarms \
    --alarm-name-prefix ohmycoins-staging \
    --region ap-southeast-2 \
    --query 'MetricAlarms[*].[AlarmName,StateValue]' \
    --output table

# All alarms should show "OK" state
```

---

## Step 11: Create Superuser Account (5 minutes)

### 11.1 Run Database Migrations

```bash
# Get a task ARN
export TASK_ARN=$(aws ecs list-tasks \
    --cluster $CLUSTER_NAME \
    --service-name ohmycoins-staging-backend-service \
    --region ap-southeast-2 \
    --query 'taskArns[0]' \
    --output text)

echo "Task ARN: $TASK_ARN"

# Execute database migrations via ECS exec
# Note: This requires ECS exec to be enabled (it is in our Terraform config)
aws ecs execute-command \
    --cluster $CLUSTER_NAME \
    --task $TASK_ARN \
    --container backend \
    --command "alembic upgrade head" \
    --interactive \
    --region ap-southeast-2
```

**If ECS exec doesn't work (common on first deployment):**

```bash
# Alternative: Check if migrations ran automatically
# The backend container should run migrations on startup

# View logs to confirm
aws logs tail /ecs/ohmycoins-staging-backend \
    --since 10m \
    --region ap-southeast-2 \
    | grep -i "migration\|alembic"
```

### 11.2 Verify Superuser Creation

The superuser should be created automatically on first startup using the credentials in Secrets Manager.

```bash
# Check logs for superuser creation
aws logs filter-log-events \
    --log-group-name /ecs/ohmycoins-staging-backend \
    --filter-pattern "superuser" \
    --start-time $(date -u -d '30 minutes ago' +%s)000 \
    --region ap-southeast-2 \
    --query 'events[*].message' \
    --output text
```

---

## Step 12: Final Validation Checklist

Run through this checklist to ensure everything is working:

### Infrastructure Checklist

```bash
# 1. VPC and Networking
aws ec2 describe-vpcs \
    --filters "Name=tag:Project,Values=Oh My Coins" \
    --region ap-southeast-2 \
    --query 'Vpcs[*].[VpcId,State]' \
    --output table
# ✅ Should show: available

# 2. RDS Database
aws rds describe-db-instances \
    --db-instance-identifier ohmycoins-staging \
    --region ap-southeast-2 \
    --query 'DBInstances[*].[DBInstanceIdentifier,DBInstanceStatus]' \
    --output table
# ✅ Should show: available

# 3. ElastiCache Redis
aws elasticache describe-cache-clusters \
    --cache-cluster-id ohmycoins-staging \
    --region ap-southeast-2 \
    --query 'CacheClusters[*].[CacheClusterId,CacheClusterStatus]' \
    --output table
# ✅ Should show: available

# 4. ECS Cluster
aws ecs describe-clusters \
    --clusters $CLUSTER_NAME \
    --region ap-southeast-2 \
    --query 'clusters[*].[clusterName,status,registeredContainerInstancesCount,runningTasksCount]' \
    --output table
# ✅ Should show: ACTIVE, 0 instances (Fargate), 2 running tasks

# 5. Load Balancer
aws elbv2 describe-load-balancers \
    --names ohmycoins-staging-alb \
    --region ap-southeast-2 \
    --query 'LoadBalancers[*].[LoadBalancerName,State.Code]' \
    --output table
# ✅ Should show: active

# 6. Secrets Manager
aws secretsmanager describe-secret \
    --secret-id $SECRET_ARN \
    --region ap-southeast-2 \
    --query '[Name,LastChangedDate]' \
    --output table
# ✅ Should show your secret name and recent date
```

### Application Checklist

- [ ] Backend health check returns 200: `curl http://$ALB_DNS/health`
- [ ] API docs accessible: `curl http://$ALB_DNS/docs`
- [ ] Frontend loads: `curl http://$ALB_DNS/`
- [ ] Database migrations completed
- [ ] Superuser account created
- [ ] No error logs in CloudWatch
- [ ] All ECS tasks running (2/2)

### Monitoring Checklist

- [ ] CloudWatch dashboard visible and showing metrics
- [ ] 8 CloudWatch alarms in "OK" state
- [ ] SNS email subscription confirmed
- [ ] Test notification received

---

## Step 13: Save Important Information

Create a file to save all your deployment information:

```bash
# Create deployment info file
cat > ~/ohmycoins-staging-deployment.txt << EOF
=== Oh My Coins Staging Deployment ===
Deployment Date: $(date)
AWS Account ID: $AWS_ACCOUNT_ID
AWS Region: ap-southeast-2

=== URLs ===
Application URL: http://$ALB_DNS
API Docs: http://$ALB_DNS/docs
Health Check: http://$ALB_DNS/health
CloudWatch Dashboard: https://console.aws.amazon.com/cloudwatch/home?region=ap-southeast-2#dashboards:name=ohmycoins-staging-infrastructure

=== Resources ===
ECS Cluster: $CLUSTER_NAME
VPC ID: $(cd infrastructure/terraform/environments/staging && terraform output -raw vpc_id)
Database Endpoint: $(cd infrastructure/terraform/environments/staging && terraform output -raw db_instance_address)
Redis Endpoint: $(cd infrastructure/terraform/environments/staging && terraform output -raw redis_primary_endpoint_address)
Secrets ARN: $SECRET_ARN
SNS Topic ARN: $SNS_TOPIC_ARN

=== Credentials ===
Admin Email: admin@ohmycoins.com
Admin Password: $ADMIN_PASSWORD
Database User: postgres
Database Name: ohmycoins

⚠️  KEEP THIS FILE SECURE - IT CONTAINS SENSITIVE INFORMATION!

=== Next Steps ===
1. Configure custom domain (optional)
2. Set up HTTPS with ACM certificate
3. Configure GitHub Actions for CI/CD
4. Enable CloudWatch Container Insights
5. Set up automated backups
6. Configure secret rotation
7. Review security groups and permissions
8. Set up monitoring alerts (PagerDuty, Slack)

=== Useful Commands ===
# View logs
aws logs tail /ecs/ohmycoins-staging-backend --follow --region ap-southeast-2

# Update service (redeploy)
aws ecs update-service --cluster $CLUSTER_NAME --service ohmycoins-staging-backend-service --force-new-deployment --region ap-southeast-2

# View running tasks
aws ecs list-tasks --cluster $CLUSTER_NAME --region ap-southeast-2

# Check alarm status
aws cloudwatch describe-alarms --alarm-name-prefix ohmycoins-staging --region ap-southeast-2

# SSH into running task (troubleshooting)
aws ecs execute-command --cluster $CLUSTER_NAME --task <TASK_ARN> --container backend --command "/bin/bash" --interactive --region ap-southeast-2
EOF

echo "✓ Deployment information saved to: ~/ohmycoins-staging-deployment.txt"
cat ~/ohmycoins-staging-deployment.txt
```

---

## 🎉 Deployment Complete!

Congratulations! You've successfully deployed Oh My Coins to AWS staging environment.

### What You've Accomplished

✅ Installed AWS CLI, Terraform, and Docker  
✅ Configured AWS credentials  
✅ Created Terraform backend (S3 + DynamoDB)  
✅ Deployed infrastructure (VPC, RDS, Redis, ECS, ALB, IAM)  
✅ Configured application secrets  
✅ Deployed backend and frontend services  
✅ Set up CloudWatch monitoring and alarms  
✅ Validated deployment health  

### Your Application is Running At

**URL:** http://<ALB_DNS_NAME>  
**API Docs:** http://<ALB_DNS_NAME>/docs  
**Admin Email:** admin@ohmycoins.com  
**Admin Password:** <saved in deployment file>

---

## Next Steps

### Immediate (Day 1)
1. **Test the Application**
   - Log into the frontend with admin credentials
   - Explore the API documentation
   - Test basic functionality

2. **Monitor Health**
   - Check CloudWatch dashboard regularly
   - Confirm alarm emails are being received
   - Review application logs for errors

### Short Term (Week 1)
3. **Configure Custom Domain (Optional)**
   - Set up Route53 hosted zone
   - Request ACM certificate
   - Update ALB listener to use HTTPS

4. **Enhance Monitoring**
   - Add Slack notifications
   - Set up PagerDuty integration
   - Configure log aggregation

### Medium Term (Month 1)
5. **Set Up CI/CD**
   - Configure GitHub Actions
   - Automate deployments
   - Add deployment gates

6. **Implement Security Best Practices**
   - Enable CloudTrail logging
   - Set up AWS Config
   - Configure VPC Flow Logs
   - Enable GuardDuty

7. **Optimize Costs**
   - Review RDS instance sizing
   - Consider Reserved Instances
   - Set up billing alerts

---

## Troubleshooting Common Issues

### Issue: Terraform Apply Fails

**Symptoms:** Error messages during `terraform apply`

**Solutions:**
```bash
# Check AWS credentials
aws sts get-caller-identity

# Verify permissions
aws iam get-user

# Check for resource limits
aws service-quotas list-service-quotas --service-code vpc

# Re-run with detailed logs
TF_LOG=DEBUG terraform apply tfplan
```

### Issue: ECS Tasks Not Starting

**Symptoms:** Tasks stuck in PROVISIONING or immediately failing

**Solutions:**
```bash
# Check task logs
aws logs tail /ecs/ohmycoins-staging-backend --since 30m --region ap-southeast-2

# Describe stopped tasks
aws ecs describe-tasks \
    --cluster $CLUSTER_NAME \
    --tasks $(aws ecs list-tasks --cluster $CLUSTER_NAME --desired-status STOPPED --region ap-southeast-2 --query 'taskArns[0]' --output text) \
    --region ap-southeast-2

# Common causes:
# - Invalid secrets ARN
# - Database not accessible (security group)
# - Container image not found
# - Insufficient memory/CPU
```

### Issue: Health Checks Failing

**Symptoms:** `curl` commands return errors

**Solutions:**
```bash
# Check target group health
aws elbv2 describe-target-health --target-group-arn $TG_ARN --region ap-southeast-2

# Check security groups
# - ALB security group: Allow inbound 80/443
# - ECS security group: Allow inbound from ALB
# - RDS security group: Allow inbound from ECS

# View detailed logs
aws logs tail /ecs/ohmycoins-staging-backend --follow --region ap-southeast-2
```

### Issue: Database Connection Failed

**Symptoms:** Backend logs show database connection errors

**Solutions:**
```bash
# Verify database is running
aws rds describe-db-instances \
    --db-instance-identifier ohmycoins-staging \
    --region ap-southeast-2 \
    --query 'DBInstances[0].DBInstanceStatus'

# Check security group allows ECS
# - RDS security group should allow port 5432 from ECS security group

# Verify secrets are correct
aws secretsmanager get-secret-value \
    --secret-id $SECRET_ARN \
    --region ap-southeast-2 \
    --query SecretString \
    --output text | jq .
```

---

## Cost Management

### Monitor Costs

```bash
# Get current month costs
aws ce get-cost-and-usage \
    --time-period Start=$(date -u -d '1 month ago' +%Y-%m-01),End=$(date -u +%Y-%m-%d) \
    --granularity MONTHLY \
    --metrics UnblendedCost \
    --group-by Type=TAG,Key=Project

# Set up billing alert (one-time)
aws cloudwatch put-metric-alarm \
    --alarm-name ohmycoins-staging-billing-alert \
    --alarm-description "Alert when staging costs exceed $150/month" \
    --metric-name EstimatedCharges \
    --namespace AWS/Billing \
    --statistic Maximum \
    --period 86400 \
    --evaluation-periods 1 \
    --threshold 150 \
    --comparison-operator GreaterThanThreshold \
    --alarm-actions $SNS_TOPIC_ARN
```

### Reduce Costs

```bash
# Stop ECS tasks when not in use (saves ~$15/month)
aws ecs update-service \
    --cluster $CLUSTER_NAME \
    --service ohmycoins-staging-backend-service \
    --desired-count 0 \
    --region ap-southeast-2

aws ecs update-service \
    --cluster $CLUSTER_NAME \
    --service ohmycoins-staging-frontend-service \
    --desired-count 0 \
    --region ap-southeast-2

# Restart when needed
aws ecs update-service \
    --cluster $CLUSTER_NAME \
    --service ohmycoins-staging-backend-service \
    --desired-count 1 \
    --region ap-southeast-2
```

---

## Destroying the Environment

**⚠️ WARNING: This will delete all resources and data!**

```bash
# Navigate to staging directory
cd infrastructure/terraform/environments/staging

# Plan destruction
terraform plan -destroy

# Review carefully - this cannot be undone!

# Destroy infrastructure
terraform destroy

# Confirm by typing: yes

# Clean up Terraform backend (optional)
aws s3 rm s3://ohmycoins-terraform-state --recursive
aws s3api delete-bucket --bucket ohmycoins-terraform-state --region ap-southeast-2
aws dynamodb delete-table --table-name ohmycoins-terraform-locks --region ap-southeast-2
```

---

## Getting Help

### Resources
- **Documentation:** `/infrastructure/terraform/OPERATIONS_RUNBOOK.md`
- **Terraform Docs:** https://registry.terraform.io/providers/hashicorp/aws/latest/docs
- **AWS Support:** https://console.aws.amazon.com/support/home

### Support Contacts
- **GitHub Issues:** https://github.com/MarkLimmage/ohmycoins/issues
- **DevOps Engineer:** (Configure your contact info here)

---

**Document Version:** 1.0  
**Last Updated:** January 10, 2026  
**Author:** OMC-DevOps-Engineer (Developer C)  
**Sprint:** 2.7
