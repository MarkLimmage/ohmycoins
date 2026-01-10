# Monitoring Module Integration Example

This document shows how to integrate the monitoring module into your staging and production environments.

## Example: Staging Environment

Add to `environments/staging/main.tf`:

```hcl
# Monitoring Module
module "monitoring" {
  source = "../../modules/monitoring"

  project_name = local.project_name
  environment  = "staging"
  aws_region   = var.aws_region

  # ECS Configuration
  cluster_name         = module.ecs.cluster_name
  backend_service_name = module.ecs.backend_service_name

  # ALB Configuration
  alb_arn_suffix          = module.alb.alb_arn_suffix
  target_group_arn_suffix = module.alb.backend_target_group_arn_suffix

  # Database Configuration
  db_instance_id   = module.rds.db_instance_id
  redis_cluster_id = module.redis.cluster_id

  # Alert Configuration
  alert_emails = var.alert_emails

  # Staging Thresholds (more lenient)
  cpu_threshold            = 90
  memory_threshold         = 90
  error_5xx_threshold      = 20
  rds_cpu_threshold        = 90
  rds_storage_threshold    = 5368709120  # 5GB for staging
  cache_hit_rate_threshold = 60
  redis_cpu_threshold      = 80

  tags = local.tags
}
```

Add to `environments/staging/variables.tf`:

```hcl
variable "alert_emails" {
  description = "List of email addresses for CloudWatch alarm notifications"
  type        = list(string)
  default     = []
}
```

Add to `environments/staging/terraform.tfvars`:

```hcl
alert_emails = [
  "devops@example.com",
  "staging-alerts@example.com"
]
```

Add to `environments/staging/outputs.tf`:

```hcl
# Monitoring Outputs
output "sns_topic_arn" {
  description = "ARN of the SNS topic for alerts"
  value       = module.monitoring.sns_topic_arn
}

output "dashboard_name" {
  description = "Name of the CloudWatch dashboard"
  value       = module.monitoring.dashboard_name
}

output "dashboard_url" {
  description = "URL to view the CloudWatch dashboard"
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${module.monitoring.dashboard_name}"
}

output "alarm_names" {
  description = "List of all CloudWatch alarm names"
  value       = module.monitoring.alarm_names
}
```

## Example: Production Environment

Add to `environments/production/main.tf`:

```hcl
# Monitoring Module with Production Settings
module "monitoring" {
  source = "../../modules/monitoring"

  project_name = local.project_name
  environment  = "production"
  aws_region   = var.aws_region

  # ECS Configuration
  cluster_name         = module.ecs.cluster_name
  backend_service_name = module.ecs.backend_service_name

  # ALB Configuration
  alb_arn_suffix          = module.alb.alb_arn_suffix
  target_group_arn_suffix = module.alb.backend_target_group_arn_suffix

  # Database Configuration
  db_instance_id   = module.rds.db_instance_id
  redis_cluster_id = module.redis.cluster_id

  # Alert Configuration
  alert_emails = var.alert_emails
  kms_key_id   = aws_kms_key.monitoring.id  # Encrypt SNS in production

  # Production Thresholds (strict)
  cpu_threshold            = 70
  memory_threshold         = 70
  error_5xx_threshold      = 5
  rds_cpu_threshold        = 70
  rds_storage_threshold    = 21474836480  # 20GB for production
  cache_hit_rate_threshold = 80
  redis_cpu_threshold      = 60

  tags = local.tags
}

# KMS Key for SNS Topic Encryption (Production Only)
resource "aws_kms_key" "monitoring" {
  description             = "KMS key for encrypting monitoring SNS topic"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = local.tags
}

resource "aws_kms_alias" "monitoring" {
  name          = "alias/${local.project_name}-monitoring"
  target_key_id = aws_kms_key.monitoring.key_id
}
```

Add to `environments/production/terraform.tfvars`:

```hcl
alert_emails = [
  "devops@example.com",
  "oncall@example.com",
  "production-alerts@example.com"
]
```

## Required Module Outputs

The monitoring module requires these outputs from other modules:

### ECS Module (`modules/ecs/outputs.tf`)

```hcl
output "cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "backend_service_name" {
  description = "Name of the backend ECS service"
  value       = aws_ecs_service.backend.name
}
```

### ALB Module (`modules/alb/outputs.tf`)

```hcl
output "alb_arn_suffix" {
  description = "ARN suffix of the ALB (for CloudWatch metrics)"
  value       = aws_lb.main.arn_suffix
}

output "backend_target_group_arn_suffix" {
  description = "ARN suffix of the backend target group"
  value       = aws_lb_target_group.backend.arn_suffix
}
```

### RDS Module (`modules/rds/outputs.tf`)

```hcl
output "db_instance_id" {
  description = "RDS instance identifier"
  value       = aws_db_instance.main.id
}
```

### Redis Module (`modules/redis/outputs.tf`)

```hcl
output "cluster_id" {
  description = "Redis cluster identifier"
  value       = aws_elasticache_replication_group.main.id
}
```

## Deployment Steps

### 1. Update Module Outputs (if needed)

Check if your existing modules already export the required values:

```bash
cd infrastructure/terraform/environments/staging

# Check current outputs
terraform output

# If missing, add outputs to respective modules
```

### 2. Add Monitoring Module

```bash
# Edit main.tf to add monitoring module
# Edit variables.tf to add alert_emails
# Edit terraform.tfvars to set alert emails
```

### 3. Initialize and Plan

```bash
cd infrastructure/terraform/environments/staging

terraform init
terraform plan -out=tfplan
```

### 4. Review Plan

Verify the plan will create:
- 1 SNS topic
- N SNS subscriptions (one per email)
- 1 CloudWatch dashboard
- 8 CloudWatch alarms

### 5. Apply Changes

```bash
terraform apply tfplan
```

### 6. Confirm Email Subscriptions

Each email address will receive a confirmation email:
1. Check your inbox (and spam folder)
2. Click "Confirm subscription" link
3. Verify subscription is confirmed:
   ```bash
   aws sns list-subscriptions-by-topic \
     --topic-arn $(terraform output -raw sns_topic_arn)
   ```

### 7. View Dashboard

```bash
# Get dashboard URL
terraform output dashboard_url

# Or open directly
echo "https://console.aws.amazon.com/cloudwatch/home?region=ap-southeast-2#dashboards:name=$(terraform output -raw dashboard_name)"
```

### 8. Test Alarms

```bash
# List all alarms
aws cloudwatch describe-alarms \
  --alarm-name-prefix $(terraform output -raw project_name)

# Trigger test notification
aws sns publish \
  --topic-arn $(terraform output -raw sns_topic_arn) \
  --message "Test notification from monitoring module" \
  --subject "Test Alert"
```

## Updating Thresholds

To adjust alarm thresholds after deployment:

1. Edit `main.tf`:
   ```hcl
   module "monitoring" {
     # ...
     cpu_threshold = 85  # Changed from 80
   }
   ```

2. Apply changes:
   ```bash
   terraform plan -target=module.monitoring
   terraform apply -target=module.monitoring
   ```

3. Verify alarm updated:
   ```bash
   aws cloudwatch describe-alarms \
     --alarm-names ohmycoins-staging-ecs-high-cpu \
     --query 'MetricAlarms[0].{Name:AlarmName,Threshold:Threshold}'
   ```

## Adding/Removing Email Addresses

### Add Email

1. Update `terraform.tfvars`:
   ```hcl
   alert_emails = [
     "existing@example.com",
     "new@example.com"  # Add new email
   ]
   ```

2. Apply:
   ```bash
   terraform apply
   ```

3. New recipient receives confirmation email

### Remove Email

1. Update `terraform.tfvars` (remove email from list)

2. Apply:
   ```bash
   terraform apply
   ```

Note: Subscription is automatically removed from SNS

## Troubleshooting

### Module Not Found

```
Error: Module not found
│ Module source not found: ../../modules/monitoring
```

**Solution:** Verify module directory exists and path is correct

### Missing Required Outputs

```
Error: Reference to undeclared output value
│ module.ecs.cluster_name
```

**Solution:** Add missing output to the respective module

### Invalid ARN Suffix Format

```
Error: Invalid dimension value for ALB metrics
```

**Solution:** Verify ARN suffix format is `app/name/id` (not full ARN)

Example:
```hcl
# Correct (ARN suffix)
alb_arn_suffix = "app/ohmycoins-staging-alb/abc123"

# Incorrect (Full ARN)
alb_arn_suffix = "arn:aws:elasticloadbalancing:region:account:loadbalancer/app/name/id"
```

To extract ARN suffix:
```bash
aws elbv2 describe-load-balancers \
  --names ohmycoins-staging-alb \
  --query 'LoadBalancers[0].LoadBalancerArn' | \
  sed 's/.*loadbalancer\///'
```

### Dashboard Not Showing Data

**Symptoms:** Dashboard widgets show "No data available"

**Possible Causes:**
1. Resources recently created (wait 5 minutes for metrics)
2. Resource names don't match dimensions
3. Wrong region specified

**Solution:**
```bash
# Verify resource exists and get correct identifier
aws ecs describe-clusters --clusters ohmycoins-staging-cluster

# Check if metrics are being published
aws cloudwatch list-metrics \
  --namespace AWS/ECS \
  --dimensions Name=ClusterName,Value=ohmycoins-staging-cluster
```

## Complete Example

See the full working example in `environments/staging/main.tf` after integration:

```bash
# View complete staging configuration
cat infrastructure/terraform/environments/staging/main.tf | grep -A 30 "module \"monitoring\""
```

## Next Steps

After deploying monitoring:

1. **View Dashboard** - Check all widgets display data
2. **Test Alarms** - Trigger a test alarm to verify notifications
3. **Set Baselines** - Document normal metric values
4. **Tune Thresholds** - Adjust based on actual usage patterns
5. **Add Custom Metrics** - Extend with application-specific metrics
6. **Integrate Tools** - Connect to Slack, PagerDuty, etc.
7. **Document Runbook** - Add monitoring procedures to operations runbook

## Reference

- [Module README](README.md) - Detailed module documentation
- [CloudWatch Metrics](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/working_with_metrics.html)
- [Operations Runbook](../../OPERATIONS_RUNBOOK.md#monitoring-and-alerts) - Monitoring procedures
