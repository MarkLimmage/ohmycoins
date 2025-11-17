# Quick Setup Guide for AWS Infrastructure

This guide will help you deploy Oh My Coins to AWS using Terraform.

## Prerequisites

1. **AWS Account** with administrator access
2. **AWS CLI** installed and configured
3. **Terraform** v1.5+ installed
4. **GitHub repository** set up with necessary secrets

## Step 1: Set Up AWS

### 1.1 Create S3 Bucket for Terraform State

```bash
aws s3api create-bucket \
    --bucket ohmycoins-terraform-state \
    --region ap-southeast-2 \
    --create-bucket-configuration LocationConstraint=ap-southeast-2

aws s3api put-bucket-versioning \
    --bucket ohmycoins-terraform-state \
    --versioning-configuration Status=Enabled

aws s3api put-bucket-encryption \
    --bucket ohmycoins-terraform-state \
    --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
```

### 1.2 Create DynamoDB Table for State Locking

```bash
aws dynamodb create-table \
    --table-name ohmycoins-terraform-locks \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region ap-southeast-2
```

## Step 2: Configure Terraform Variables

### 2.1 Copy Example Variables

```bash
cd infrastructure/terraform/environments/staging
cp terraform.tfvars.example terraform.tfvars
```

### 2.2 Edit terraform.tfvars

```hcl
# Update these values in terraform.tfvars

aws_region = "ap-southeast-2"

# IMPORTANT: Use a strong password
master_password = "YOUR_SECURE_PASSWORD_HERE"

# Update with your actual domains (or use defaults for testing)
domain              = "staging.ohmycoins.com"
backend_domain      = "api.staging.ohmycoins.com"
frontend_host       = "https://dashboard.staging.ohmycoins.com"

# For development/testing without a domain, you can use ALB DNS:
# Leave certificate_arn empty for HTTP-only deployment
certificate_arn = ""

# GitHub configuration
github_repo = "MarkLimmage/ohmycoins"
```

## Step 3: Deploy Infrastructure

### 3.1 Initialize Terraform

```bash
cd infrastructure/terraform/environments/staging
terraform init
```

### 3.2 Plan Deployment

```bash
terraform plan
```

Review the plan carefully to ensure all resources are correct.

### 3.3 Apply Infrastructure

```bash
terraform apply
```

Type `yes` when prompted. This will create:
- VPC with public and private subnets
- RDS PostgreSQL database
- ElastiCache Redis cluster
- Application Load Balancer
- ECS Fargate cluster
- IAM roles and security groups

**Note:** This will take 10-15 minutes to complete.

### 3.4 Get Outputs

```bash
terraform output
```

Save these outputs - you'll need them for the next steps.

## Step 4: Configure Application Secrets

### 4.1 Create Secrets JSON File

Create a file `secrets.json` with your application secrets:

```json
{
  "SECRET_KEY": "your-secret-key-here",
  "FIRST_SUPERUSER": "admin@example.com",
  "FIRST_SUPERUSER_PASSWORD": "secure-admin-password",
  "POSTGRES_PASSWORD": "same-as-terraform-tfvars",
  "SMTP_HOST": "smtp.example.com",
  "SMTP_USER": "smtp-user",
  "SMTP_PASSWORD": "smtp-password",
  "EMAILS_FROM_EMAIL": "noreply@example.com",
  "OPENAI_API_KEY": "your-openai-key",
  "SENTRY_DSN": ""
}
```

### 4.2 Upload Secrets to AWS

```bash
# Get the secret ARN from Terraform output
SECRET_ARN=$(terraform output -raw secrets_manager_secret_arn)

# Upload secrets
aws secretsmanager put-secret-value \
    --secret-id "$SECRET_ARN" \
    --secret-string file://secrets.json \
    --region ap-southeast-2
```

**Important:** Delete the `secrets.json` file after uploading:
```bash
rm secrets.json
```

## Step 5: Set Up GitHub Actions (Optional)

### 5.1 Configure GitHub Secrets

In your GitHub repository, go to Settings → Secrets and variables → Actions, and add:

1. `AWS_ROLE_ARN`: The GitHub Actions role ARN from Terraform output
   ```
   terraform output -raw github_actions_role_arn
   ```

2. `DB_MASTER_PASSWORD`: Your database master password

### 5.2 Create ECR Repositories

```bash
# Create ECR repositories for Docker images
aws ecr create-repository \
    --repository-name ohmycoins-backend \
    --region ap-southeast-2

aws ecr create-repository \
    --repository-name ohmycoins-frontend \
    --region ap-southeast-2
```

## Step 6: Deploy Application

### Option A: Using GitHub Actions

Push your code to the `main` branch, and the `deploy-aws.yml` workflow will:
1. Build Docker images
2. Push to ECR
3. Deploy to ECS

### Option B: Manual Deployment

```bash
# Login to ECR
aws ecr get-login-password --region ap-southeast-2 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.ap-southeast-2.amazonaws.com

# Build and push backend
docker build -t <account-id>.dkr.ecr.ap-southeast-2.amazonaws.com/ohmycoins-backend:latest ./backend
docker push <account-id>.dkr.ecr.ap-southeast-2.amazonaws.com/ohmycoins-backend:latest

# Build and push frontend
docker build -t <account-id>.dkr.ecr.ap-southeast-2.amazonaws.com/ohmycoins-frontend:latest ./frontend
docker push <account-id>.dkr.ecr.ap-southeast-2.amazonaws.com/ohmycoins-frontend:latest

# Update ECS services
CLUSTER_NAME=$(terraform output -raw ecs_cluster_name)
BACKEND_SERVICE=$(terraform output -raw backend_service_name)
FRONTEND_SERVICE=$(terraform output -raw frontend_service_name)

aws ecs update-service \
    --cluster "$CLUSTER_NAME" \
    --service "$BACKEND_SERVICE" \
    --force-new-deployment \
    --region ap-southeast-2

aws ecs update-service \
    --cluster "$CLUSTER_NAME" \
    --service "$FRONTEND_SERVICE" \
    --force-new-deployment \
    --region ap-southeast-2
```

## Step 7: Access Your Application

### 7.1 Get ALB DNS Name

```bash
terraform output alb_dns_name
```

### 7.2 Access the Application

- **Frontend:** http://<alb-dns-name>
- **Backend API:** http://<alb-dns-name>/api/v1/docs

### 7.3 Set Up DNS (Optional)

If you have a domain, create CNAME records:
- `dashboard.staging.ohmycoins.com` → ALB DNS name
- `api.staging.ohmycoins.com` → ALB DNS name

## Step 8: Set Up SSL Certificate (Optional)

### 8.1 Request Certificate in ACM

```bash
aws acm request-certificate \
    --domain-name "*.staging.ohmycoins.com" \
    --subject-alternative-names "staging.ohmycoins.com" \
    --validation-method DNS \
    --region ap-southeast-2
```

### 8.2 Validate Certificate

Follow the instructions in the ACM console to add DNS validation records.

### 8.3 Update Terraform

Update `terraform.tfvars`:
```hcl
certificate_arn = "arn:aws:acm:ap-southeast-2:ACCOUNT_ID:certificate/CERT_ID"
```

Apply the changes:
```bash
terraform apply
```

## Monitoring and Maintenance

### View Logs

```bash
# Backend logs
aws logs tail /ecs/ohmycoins-staging/backend --follow

# Frontend logs
aws logs tail /ecs/ohmycoins-staging/frontend --follow
```

### Check Service Status

```bash
CLUSTER_NAME=$(terraform output -raw ecs_cluster_name)

aws ecs describe-services \
    --cluster "$CLUSTER_NAME" \
    --services $(terraform output -raw backend_service_name) \
    --region ap-southeast-2
```

### Database Access

```bash
# Get database endpoint
DB_ENDPOINT=$(terraform output -raw db_endpoint)

# Connect via bastion or VPN (database is in private subnet)
psql -h "$DB_ENDPOINT" -U postgres -d app
```

## Troubleshooting

### ECS Tasks Not Starting

```bash
# Check task failures
aws ecs list-tasks --cluster "$CLUSTER_NAME" --desired-status STOPPED

# Get task details
aws ecs describe-tasks --cluster "$CLUSTER_NAME" --tasks <task-id>
```

### Database Connection Issues

1. Verify security groups allow ECS → RDS traffic
2. Check database endpoint and credentials in secrets
3. Verify ECS tasks are in correct subnets

### High Costs

1. Review CloudWatch metrics for unused resources
2. Check NAT Gateway data transfer
3. Consider using Spot instances for non-production

## Cleanup

To destroy all infrastructure:

```bash
cd infrastructure/terraform/environments/staging
terraform destroy
```

**Warning:** This will delete all data. Ensure you have backups.

## Cost Estimation

Current staging configuration:
- **Monthly Cost:** ~$125-155
  - RDS db.t3.micro: ~$15
  - ElastiCache cache.t3.micro: ~$15
  - ECS Fargate (1 backend, 1 frontend): ~$30
  - ALB: ~$20
  - NAT Gateway: ~$35
  - Data Transfer: ~$10

For production, see `environments/production/README.md`.

## Next Steps

1. Set up monitoring and alerting
2. Configure backup policies
3. Implement auto-scaling policies
4. Set up CI/CD pipelines
5. Configure custom domain and SSL

## Support

For issues or questions, see:
- [Main Terraform README](../../README.md)
- [Troubleshooting Guide](../../README.md#troubleshooting)
- GitHub Issues
