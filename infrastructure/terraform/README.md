# Oh My Coins - AWS Infrastructure with Terraform

This directory contains Infrastructure as Code (IaC) for deploying Oh My Coins to AWS.

## Architecture Overview

The infrastructure is designed for a microservices-based cryptocurrency trading platform with:

- **VPC**: Isolated network with public/private subnets across multiple AZs
- **RDS PostgreSQL**: Managed database for application data and time-series price data
- **ElastiCache Redis**: In-memory cache for session management and agent state
- **ECS Fargate**: Serverless container orchestration for backend and frontend
- **Application Load Balancer**: Traffic distribution and SSL termination
- **ECR**: Container registry for Docker images
- **Secrets Manager**: Secure storage for sensitive configuration
- **CloudWatch**: Logging and monitoring

## Directory Structure

```
terraform/
├── README.md                    # This file
├── QUICKSTART.md               # Step-by-step deployment guide
├── OPERATIONS_RUNBOOK.md       # Day-to-day operations guide
├── TROUBLESHOOTING.md          # Common issues and solutions
├── DEVELOPER_C_SUMMARY.md      # Developer C work summary
├── modules/                     # Reusable Terraform modules
│   ├── vpc/                    # VPC, subnets, NAT gateway
│   ├── rds/                    # PostgreSQL database
│   ├── redis/                  # ElastiCache Redis cluster
│   ├── ecs/                    # ECS cluster and task definitions
│   ├── alb/                    # Application Load Balancer
│   ├── security/               # Security groups
│   └── iam/                    # IAM roles and policies
├── environments/
│   ├── staging/                # Staging environment configuration
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── terraform.tfvars.example
│   │   └── outputs.tf
│   └── production/             # Production environment configuration
│       ├── main.tf
│       ├── variables.tf
│       ├── terraform.tfvars.example
│       └── outputs.tf
├── scripts/                    # Helper scripts for deployment
│   ├── validate-terraform.sh   # Validate all Terraform configs
│   ├── estimate-costs.sh       # Estimate AWS costs
│   └── pre-deployment-check.sh # Pre-deployment checklist
└── monitoring/                 # CloudWatch monitoring configs
    ├── README.md               # Monitoring guide
    └── dashboards/             # Dashboard templates
```

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** configured (`aws configure`)
3. **Terraform** v1.0+ ([install guide](https://learn.hashicorp.com/tutorials/terraform/install-cli))
4. **S3 Bucket** for Terraform state (create manually first)
5. **DynamoDB Table** for state locking (create manually first)

### Setting Up State Backend

```bash
# Create S3 bucket for Terraform state
aws s3api create-bucket \
    --bucket ohmycoins-terraform-state \
    --region ap-southeast-2 \
    --create-bucket-configuration LocationConstraint=ap-southeast-2

# Enable versioning
aws s3api put-bucket-versioning \
    --bucket ohmycoins-terraform-state \
    --versioning-configuration Status=Enabled

# Create DynamoDB table for state locking
aws dynamodb create-table \
    --table-name ohmycoins-terraform-locks \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region ap-southeast-2
```

## Helper Scripts

To make deployment easier, several helper scripts are available:

### Pre-Deployment Check
Validates all prerequisites before deployment:
```bash
./scripts/pre-deployment-check.sh staging
```

### Cost Estimation
Estimates monthly AWS costs:
```bash
./scripts/estimate-costs.sh
# Or for specific environment
./scripts/estimate-costs.sh production
```

### Terraform Validation
Validates all Terraform configurations:
```bash
./scripts/validate-terraform.sh
```

## Quick Start - Staging Environment

**Recommended approach: Run pre-deployment check first!**

```bash
# 1. Run pre-deployment checklist
./scripts/pre-deployment-check.sh staging

# 2. Navigate to staging environment
cd infrastructure/terraform/environments/staging

# 3. Copy and configure variables
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars  # Edit with your values

# 4. Initialize Terraform
terraform init

# 5. Review the plan
terraform plan

# 6. Apply the infrastructure
terraform apply
   ```

5. **Get outputs:**
   ```bash
   terraform output
   ```

## Quick Start - Production Environment

1. **Navigate to production environment:**
   ```bash
   cd infrastructure/terraform/environments/production
   ```

2. **Initialize Terraform:**
   ```bash
   terraform init
   ```

3. **Review the plan:**
   ```bash
   terraform plan
   ```

4. **Apply the infrastructure:**
   ```bash
   terraform apply
   ```

## Cost Estimation

### Staging Environment (minimal resources)
| Resource | Configuration | Monthly Cost |
|----------|--------------|--------------|
| RDS PostgreSQL | db.t3.micro | ~$15 |
| ElastiCache Redis | cache.t3.micro | ~$15 |
| ECS Fargate | 2 tasks @ 0.5 vCPU, 1GB | ~$30 |
| ALB | Standard | ~$20 |
| NAT Gateway | Single AZ | ~$35 |
| Data Transfer | Minimal | ~$10 |
| **Total** | | **~$125/month** |

### Production Environment (production-ready)
| Resource | Configuration | Monthly Cost |
|----------|--------------|--------------|
| RDS PostgreSQL | db.t3.small, Multi-AZ | ~$60 |
| ElastiCache Redis | cache.t3.small, Multi-AZ | ~$60 |
| ECS Fargate | 4 tasks @ 1 vCPU, 2GB | ~$120 |
| ALB | Standard with WAF | ~$30 |
| NAT Gateway | Multi-AZ | ~$70 |
| Data Transfer | Moderate | ~$30 |
| CloudWatch Logs | Moderate retention | ~$20 |
| **Total** | | **~$390/month** |

## Environment Variables

Each environment requires the following secrets to be set in AWS Secrets Manager:

```json
{
  "SECRET_KEY": "your-secret-key",
  "FIRST_SUPERUSER": "admin@example.com",
  "FIRST_SUPERUSER_PASSWORD": "secure-password",
  "POSTGRES_PASSWORD": "database-password",
  "SMTP_HOST": "smtp.example.com",
  "SMTP_USER": "smtp-user",
  "SMTP_PASSWORD": "smtp-password",
  "OPENAI_API_KEY": "your-openai-key",
  "SENTRY_DSN": "your-sentry-dsn"
}
```

Create secrets with:
```bash
aws secretsmanager create-secret \
    --name ohmycoins/staging/app-secrets \
    --secret-string file://secrets.json \
    --region ap-southeast-2
```

## Deployment Process

### Initial Deployment

1. **Set up AWS credentials**
2. **Create Terraform state backend** (S3 + DynamoDB)
3. **Configure environment variables** in `terraform.tfvars`
4. **Deploy infrastructure** with `terraform apply`
5. **Create secrets** in AWS Secrets Manager
6. **Deploy application** via GitHub Actions or manually

### Updating Infrastructure

1. **Make changes** to Terraform files
2. **Review changes** with `terraform plan`
3. **Apply changes** with `terraform apply`

### Application Deployment

Application deployment is handled by GitHub Actions workflows that:
1. Build Docker images
2. Push to ECR
3. Update ECS task definitions
4. Deploy new versions

See `.github/workflows/deploy-aws.yml` for details.

## Modules Documentation

### VPC Module
Creates a VPC with:
- Public subnets for load balancers
- Private subnets for application and database
- NAT Gateway for outbound internet access
- VPC endpoints for AWS services

### RDS Module
Creates a PostgreSQL database with:
- Automated backups
- Multi-AZ deployment (production)
- Encryption at rest
- Performance Insights

### Redis Module
Creates an ElastiCache Redis cluster with:
- Multi-AZ deployment (production)
- Automatic failover
- Encryption in transit and at rest
- Backup enabled

### ECS Module
Creates ECS resources:
- ECS cluster
- Task definitions for backend and frontend
- Services with auto-scaling
- IAM roles for task execution

### ALB Module
Creates Application Load Balancer with:
- HTTPS listener with ACM certificate
- HTTP to HTTPS redirect
- Target groups for backend and frontend
- Health checks

### Security Module
Creates security groups for:
- ALB (allow 80/443)
- ECS tasks (allow ALB traffic)
- RDS (allow ECS traffic)
- Redis (allow ECS traffic)

### IAM Module
Creates IAM roles and policies for:
- ECS task execution
- ECS task role (application permissions)
- GitHub Actions deployment

## Security Best Practices

1. **Secrets Management**: All secrets stored in AWS Secrets Manager
2. **Encryption**: RDS and Redis encrypted at rest, TLS in transit
3. **Network Isolation**: Private subnets for application and data tiers
4. **Least Privilege**: IAM roles with minimal required permissions
5. **Security Groups**: Restrictive inbound rules
6. **Monitoring**: CloudWatch alarms for critical metrics
7. **Backups**: Automated daily backups for RDS
8. **Updates**: Regular security patches via container updates

## Monitoring and Alerts

CloudWatch alarms are configured for:
- RDS CPU > 80%
- RDS storage < 10GB free
- RDS connection count > 80% max
- Redis CPU > 75%
- Redis memory > 80%
- ECS task health check failures
- ALB 5xx errors > threshold

## Disaster Recovery

### Backup Strategy
- **RDS**: Automated daily backups, 7-day retention
- **Redis**: Daily snapshots, 5-day retention
- **Application**: Stateless, can be redeployed from Git

### Recovery Procedure
1. **Database Recovery**: Restore from RDS snapshot
2. **Application Recovery**: Redeploy from GitHub
3. **Configuration Recovery**: Restore from Terraform state

### RTO/RPO Targets
- **Staging**: RTO 2 hours, RPO 24 hours
- **Production**: RTO 30 minutes, RPO 1 hour

## Troubleshooting

### Common Issues

**Issue: Terraform state lock error**
```bash
# Solution: Release the lock (if safe)
terraform force-unlock <LOCK_ID>
```

**Issue: ECS tasks failing to start**
```bash
# Check CloudWatch logs
aws logs tail /ecs/ohmycoins-backend --follow

# Check task definition
aws ecs describe-task-definition --task-definition ohmycoins-backend
```

**Issue: Database connection issues**
```bash
# Verify security groups
aws ec2 describe-security-groups --group-ids <SG_ID>

# Test connectivity from ECS task
aws ecs execute-command --cluster ohmycoins --task <TASK_ID> --interactive --command "/bin/bash"
```

**Issue: High costs**
- Review CloudWatch metrics for unused resources
- Check NAT Gateway data transfer
- Consider reserved instances for RDS
- Implement auto-scaling policies

## Cleanup

To destroy all infrastructure:

```bash
cd infrastructure/terraform/environments/staging
terraform destroy

cd ../production
terraform destroy
```

**Warning**: This is irreversible. Ensure you have backups of all data.

## CI/CD Integration

The infrastructure supports GitOps-style deployments:

1. **Infrastructure changes**: Terraform updates via GitHub Actions
2. **Application updates**: Container deployments via GitHub Actions
3. **Configuration changes**: Secrets updated in AWS Secrets Manager

See `.github/workflows/` for workflow definitions.

## Support

For issues or questions:
- Check this README
- Review module documentation
- Check AWS CloudWatch logs
- Review GitHub Actions workflow runs
- Open an issue in the repository

## Additional Documentation

For more detailed information, see:

- **[QUICKSTART.md](QUICKSTART.md)** - Step-by-step deployment guide with detailed setup instructions
- **[OPERATIONS_RUNBOOK.md](OPERATIONS_RUNBOOK.md)** - Day-to-day operations, monitoring, and incident response procedures
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and their solutions for deployment and runtime problems
- **[monitoring/README.md](monitoring/README.md)** - CloudWatch monitoring configuration and dashboard setup
- **[DEVELOPER_C_SUMMARY.md](DEVELOPER_C_SUMMARY.md)** - Complete summary of Developer C's infrastructure work

## References

- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS ECS Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [Terraform Best Practices](https://www.terraform-best-practices.com/)

## License

This infrastructure configuration is part of the Oh My Coins project.
Copyright © 2025 Mark Limmage. All rights reserved.
