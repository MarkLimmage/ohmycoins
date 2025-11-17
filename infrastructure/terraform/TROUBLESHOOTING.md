# Terraform Deployment Troubleshooting Guide

## Table of Contents
- [Pre-Deployment Checks](#pre-deployment-checks)
- [Common Terraform Errors](#common-terraform-errors)
- [AWS-Specific Issues](#aws-specific-issues)
- [Validation and Testing](#validation-and-testing)
- [Recovery Procedures](#recovery-procedures)

---

## Pre-Deployment Checks

### Before Running Terraform

1. **Check AWS Credentials**
   ```bash
   aws sts get-caller-identity
   ```
   Should return your AWS account ID and user/role ARN.

2. **Verify Region**
   ```bash
   aws configure get region
   ```
   Should be `ap-southeast-2` (Sydney).

3. **Check Terraform Version**
   ```bash
   terraform version
   ```
   Should be v1.5.0 or higher.

4. **Validate S3 Backend Exists**
   ```bash
   aws s3 ls s3://ohmycoins-terraform-state
   ```
   If it doesn't exist, create it first (see QUICKSTART.md).

5. **Check DynamoDB Lock Table**
   ```bash
   aws dynamodb describe-table --table-name ohmycoins-terraform-locks
   ```

---

## Common Terraform Errors

### Error: Backend Configuration Required

```
Error: Backend configuration changed
```

**Cause:** Terraform state backend not initialized or changed.

**Solution:**
```bash
cd infrastructure/terraform/environments/staging
terraform init -reconfigure
```

### Error: No Valid Credential Sources

```
Error: error configuring Terraform AWS Provider: no valid credential sources
```

**Cause:** AWS credentials not configured.

**Solution:**
```bash
# Configure AWS CLI
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_DEFAULT_REGION="ap-southeast-2"
```

### Error: S3 Bucket Does Not Exist

```
Error: Failed to get existing workspaces: S3 bucket does not exist
```

**Cause:** Terraform state S3 bucket not created.

**Solution:**
```bash
# Create the S3 bucket
aws s3api create-bucket \
    --bucket ohmycoins-terraform-state \
    --region ap-southeast-2 \
    --create-bucket-configuration LocationConstraint=ap-southeast-2

# Enable versioning
aws s3api put-bucket-versioning \
    --bucket ohmycoins-terraform-state \
    --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
    --bucket ohmycoins-terraform-state \
    --server-side-encryption-configuration \
    '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
```

### Error: State Lock Acquisition Failed

```
Error: Error acquiring the state lock
```

**Cause:** Another process is holding the lock, or previous operation didn't release lock.

**Solution:**
```bash
# Check for lock in DynamoDB
aws dynamodb scan \
    --table-name ohmycoins-terraform-locks \
    --filter-expression "attribute_exists(LockID)"

# If lock is stale, force unlock (use with caution!)
terraform force-unlock <LOCK_ID>
```

### Error: Invalid Variable Value

```
Error: Invalid value for input variable
```

**Cause:** Required variable not provided or has invalid value.

**Solution:**
```bash
# Check terraform.tfvars exists
ls -la terraform.tfvars

# Copy from example if missing
cp terraform.tfvars.example terraform.tfvars

# Edit with correct values
nano terraform.tfvars
```

### Error: Resource Already Exists

```
Error: resource already exists
```

**Cause:** Trying to create a resource that already exists in AWS.

**Solution:**
```bash
# Option 1: Import existing resource
terraform import <resource_type>.<resource_name> <resource_id>

# Option 2: Remove from state (if managed elsewhere)
terraform state rm <resource_type>.<resource_name>

# Option 3: Manually delete resource in AWS Console
```

### Error: Insufficient Permissions

```
Error: error creating/updating resource: UnauthorizedOperation
```

**Cause:** IAM user/role lacks necessary permissions.

**Solution:**
```bash
# Check current permissions
aws iam get-user-policy --user-name <username> --policy-name <policy>

# Required permissions:
# - EC2 (VPC, subnets, security groups, etc.)
# - RDS (create/modify databases)
# - ElastiCache (create/modify clusters)
# - ECS (create/modify services)
# - IAM (create/modify roles, policies)
# - S3 (state bucket access)
# - DynamoDB (state lock access)
```

---

## AWS-Specific Issues

### VPC and Networking

#### Issue: CIDR Block Conflicts

```
Error: The CIDR 'x.x.x.x/x' conflicts with another subnet
```

**Solution:**
- Check existing VPCs and their CIDR blocks
- Modify `vpc_cidr` in terraform.tfvars
- Ensure no overlap with existing VPCs

#### Issue: NAT Gateway Creation Timeout

```
Error: timeout while waiting for resource to be created
```

**Solution:**
- NAT Gateway can take 5-10 minutes to create
- Increase timeout in module if needed
- Check AWS Service Health Dashboard for outages
- Retry after a few minutes

### RDS Issues

#### Issue: Database Master Password Invalid

```
Error: MasterUserPassword: The parameter MasterUserPassword is not a valid password
```

**Solution:**
- Password must be 8-41 characters
- Must contain uppercase, lowercase, and numbers
- Cannot contain /, ", or @

#### Issue: Insufficient Storage

```
Error: InvalidParameterValue: AllocatedStorage must be at least 20
```

**Solution:**
- Minimum RDS storage is 20 GB
- Check `allocated_storage` in terraform.tfvars
- Production should have 100+ GB

#### Issue: Database in Use, Cannot Delete

```
Error: InvalidDBInstanceState: Database instance is not in available state
```

**Solution:**
```bash
# If deletion_protection is enabled, disable it first
aws rds modify-db-instance \
    --db-instance-identifier <instance-id> \
    --no-deletion-protection

# Create final snapshot before deletion
aws rds delete-db-instance \
    --db-instance-identifier <instance-id> \
    --final-db-snapshot-identifier <snapshot-name>
```

### ECS Issues

#### Issue: Task Definition Invalid

```
Error: ClientException: No Fargate configuration exists for given values
```

**Solution:**
- Check CPU and memory combinations
- Valid Fargate combinations:
  - 0.25 vCPU: 0.5-2 GB
  - 0.5 vCPU: 1-4 GB
  - 1 vCPU: 2-8 GB
  - 2 vCPU: 4-16 GB

#### Issue: Container Cannot Pull Image

```
Error: CannotPullContainerError: Error response from daemon
```

**Solution:**
```bash
# Verify ECR repository exists
aws ecr describe-repositories --repository-names ohmycoins-backend

# Create if missing
aws ecr create-repository --repository-name ohmycoins-backend

# Check task execution role has ECR permissions
aws iam get-role-policy \
    --role-name ohmycoins-ecs-task-execution-role \
    --policy-name ECRAccess
```

### Load Balancer Issues

#### Issue: Certificate Not Found

```
Error: CertificateNotFound: Certificate 'arn:aws:acm:...' not found
```

**Solution:**
```bash
# For staging with HTTP-only, set enable_https = false in terraform.tfvars

# For production, create certificate first:
aws acm request-certificate \
    --domain-name ohmycoins.example.com \
    --validation-method DNS \
    --region ap-southeast-2
```

#### Issue: Target Group Has No Targets

```
Error: Target group has no registered targets
```

**Solution:**
- This is expected initially
- ECS service will register targets after deployment
- Check ECS service is running and healthy

---

## Validation and Testing

### Validate Terraform Configuration

```bash
# Run validation script
cd infrastructure/terraform
./scripts/validate-terraform.sh

# Or manually for specific environment
cd environments/staging
terraform init -backend=false
terraform validate
terraform fmt -check -recursive
```

### Test Plan Without Applying

```bash
cd infrastructure/terraform/environments/staging

# Generate plan
terraform plan -out=tfplan

# Review plan carefully
terraform show tfplan

# If looks good, apply
terraform apply tfplan
```

### Verify Deployment

```bash
# Check VPC created
aws ec2 describe-vpcs \
    --filters "Name=tag:Project,Values=Oh My Coins"

# Check RDS instance
aws rds describe-db-instances \
    --db-instance-identifier ohmycoins-staging

# Check ECS cluster
aws ecs describe-clusters --clusters ohmycoins-staging

# Check ALB
aws elbv2 describe-load-balancers \
    --names ohmycoins-staging-alb
```

---

## Recovery Procedures

### Recover from Failed Apply

1. **Don't Panic!** Terraform state is in S3 with versioning enabled.

2. **Check State**
   ```bash
   terraform show
   ```

3. **If State is Corrupted**
   ```bash
   # List state versions
   aws s3api list-object-versions \
       --bucket ohmycoins-terraform-state \
       --prefix staging/terraform.tfstate
   
   # Download previous version
   aws s3api get-object \
       --bucket ohmycoins-terraform-state \
       --key staging/terraform.tfstate \
       --version-id <previous-version-id> \
       terraform.tfstate.backup
   ```

4. **Restore State**
   ```bash
   # Copy backup to current state
   cp terraform.tfstate.backup terraform.tfstate
   
   # Push to S3
   aws s3 cp terraform.tfstate \
       s3://ohmycoins-terraform-state/staging/terraform.tfstate
   ```

### Complete Infrastructure Teardown

**Warning:** This will destroy ALL resources!

```bash
cd infrastructure/terraform/environments/staging

# For staging (safe)
terraform destroy -auto-approve

# For production (requires manual confirmation)
terraform destroy
```

### Selective Resource Destruction

```bash
# Target specific resource
terraform destroy -target=module.ecs.aws_ecs_service.backend

# Remove from state without destroying
terraform state rm module.ecs.aws_ecs_service.backend
```

---

## Best Practices

### Before Every Apply

1. [ ] Run `terraform plan` and review carefully
2. [ ] Check cost estimates
3. [ ] Verify in correct environment (staging vs production)
4. [ ] Ensure backups are recent
5. [ ] Have rollback plan ready

### Regular Maintenance

1. **Weekly:**
   - Review Terraform state for drift
   - Check for security updates
   - Monitor costs

2. **Monthly:**
   - Update Terraform and provider versions
   - Review and update documentation
   - Test disaster recovery procedures

3. **Quarterly:**
   - Security audit
   - Cost optimization review
   - Performance tuning

---

## Getting Help

### Debugging Commands

```bash
# Enable Terraform debug logging
export TF_LOG=DEBUG
terraform plan

# Check AWS service status
curl -s https://status.aws.amazon.com/ | grep ap-southeast-2

# Test AWS API connectivity
aws ec2 describe-regions --region ap-southeast-2
```

### Resources

- [Terraform AWS Provider Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS Service Quotas](https://console.aws.amazon.com/servicequotas/)
- [Terraform State Management](https://www.terraform.io/docs/language/state/index.html)
- [AWS Support Center](https://console.aws.amazon.com/support/)

### Contact

- **Primary**: Developer C (Infrastructure/DevOps)
- **Secondary**: DevOps Team Lead
- **Emergency**: On-call rotation (see OPERATIONS_RUNBOOK.md)

---

**Last Updated:** 2025-11-17  
**Maintained By:** Developer C (Infrastructure & DevOps)
