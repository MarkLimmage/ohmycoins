# Monitoring Module

This module creates comprehensive CloudWatch monitoring infrastructure for Oh My Coins, including dashboards, alarms, and SNS notifications.

## Features

- **CloudWatch Dashboard** with 6 widgets covering ECS, ALB, RDS, and Redis metrics
- **8 CloudWatch Alarms** for critical system metrics
- **SNS Topic** for alarm notifications with email subscriptions
- **Configurable Thresholds** for all alarms
- **KMS Encryption** support for SNS topics

## What Gets Monitored

### ECS Service Metrics
- CPU Utilization (threshold: 80%)
- Memory Utilization (threshold: 80%)
- Task counts (desired vs running)

### Application Load Balancer
- Response times (average, p95, p99)
- HTTP status codes (2xx, 4xx, 5xx)
- Unhealthy target count
- 5xx error rate (threshold: 10 errors in 5 minutes)

### RDS Database
- CPU Utilization (threshold: 80%)
- Database connections
- Free memory
- Free storage space (threshold: 10GB)

### Redis Cache
- Cache hit rate (threshold: 70%)
- CPU utilization (threshold: 70%)
- Current connections

## Usage

```hcl
module "monitoring" {
  source = "../../modules/monitoring"

  project_name         = "ohmycoins-staging"
  environment          = "staging"
  aws_region           = "ap-southeast-2"
  
  # ECS Configuration
  cluster_name          = module.ecs.cluster_name
  backend_service_name  = module.ecs.backend_service_name
  
  # ALB Configuration
  alb_arn_suffix           = module.alb.alb_arn_suffix
  target_group_arn_suffix  = module.alb.backend_target_group_arn_suffix
  
  # Database Configuration
  db_instance_id    = module.rds.db_instance_id
  redis_cluster_id  = module.redis.cluster_id
  
  # Alert Configuration
  alert_emails = [
    "devops@example.com",
    "oncall@example.com"
  ]
  
  # Custom Thresholds (optional)
  cpu_threshold              = 80
  memory_threshold           = 80
  error_5xx_threshold        = 10
  rds_cpu_threshold          = 80
  rds_storage_threshold      = 10737418240  # 10GB
  cache_hit_rate_threshold   = 70
  redis_cpu_threshold        = 70
  
  tags = {
    Project     = "Oh My Coins"
    Environment = "staging"
    ManagedBy   = "Terraform"
  }
}
```

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| project_name | Name of the project (used for resource naming) | `string` | n/a | yes |
| environment | Environment name (staging, production) | `string` | n/a | yes |
| aws_region | AWS region | `string` | n/a | yes |
| cluster_name | Name of the ECS cluster | `string` | n/a | yes |
| backend_service_name | Name of the backend ECS service | `string` | n/a | yes |
| alb_arn_suffix | ARN suffix of the ALB (app/name/id) | `string` | n/a | yes |
| target_group_arn_suffix | ARN suffix of the target group | `string` | n/a | yes |
| db_instance_id | RDS database instance identifier | `string` | n/a | yes |
| redis_cluster_id | ElastiCache Redis cluster identifier | `string` | n/a | yes |
| alert_emails | List of email addresses for alarm notifications | `list(string)` | `[]` | no |
| kms_key_id | KMS key ID for SNS topic encryption | `string` | `null` | no |
| cpu_threshold | ECS CPU utilization threshold (%) | `number` | `80` | no |
| memory_threshold | ECS memory utilization threshold (%) | `number` | `80` | no |
| error_5xx_threshold | Number of 5xx errors to trigger alarm | `number` | `10` | no |
| rds_cpu_threshold | RDS CPU utilization threshold (%) | `number` | `80` | no |
| rds_storage_threshold | Min free storage for RDS (bytes) | `number` | `10737418240` | no |
| cache_hit_rate_threshold | Min cache hit rate for Redis (%) | `number` | `70` | no |
| redis_cpu_threshold | Redis CPU utilization threshold (%) | `number` | `70` | no |
| tags | Tags to apply to all resources | `map(string)` | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| sns_topic_arn | ARN of the SNS topic for alerts |
| sns_topic_name | Name of the SNS topic |
| dashboard_name | Name of the CloudWatch dashboard |
| dashboard_arn | ARN of the CloudWatch dashboard |
| alarm_names | List of all CloudWatch alarm names |
| alarm_arns | Map of alarm names to ARNs |

## CloudWatch Dashboard

The module creates a comprehensive dashboard with:

### Layout
```
┌─────────────────────┬─────────────────────┐
│ ECS CPU & Memory    │ ALB Response Times  │
│ (12x6)              │ (12x6)              │
├─────────────────────┼─────────────────────┤
│ HTTP Status Codes   │ RDS Metrics         │
│ (12x6)              │ (12x6)              │
├─────────────────────┼─────────────────────┤
│ Redis Metrics       │ ECS Task Counts     │
│ (12x6)              │ (12x6)              │
└─────────────────────┴─────────────────────┘
```

### Accessing the Dashboard

**Via AWS Console:**
1. Go to CloudWatch → Dashboards
2. Select `ohmycoins-staging-infrastructure`

**Via AWS CLI:**
```bash
# View dashboard
aws cloudwatch get-dashboard \
  --dashboard-name ohmycoins-staging-infrastructure \
  --region ap-southeast-2

# Get dashboard URL
echo "https://console.aws.amazon.com/cloudwatch/home?region=ap-southeast-2#dashboards:name=ohmycoins-staging-infrastructure"
```

## CloudWatch Alarms

### Alarm List

1. **ecs-high-cpu**: ECS CPU > 80% for 10 minutes
2. **ecs-high-memory**: ECS Memory > 80% for 10 minutes
3. **alb-high-5xx-errors**: More than 10 5xx errors in 5 minutes
4. **alb-unhealthy-targets**: Any unhealthy targets detected
5. **rds-high-cpu**: RDS CPU > 80% for 10 minutes
6. **rds-low-storage**: RDS free storage < 10GB
7. **redis-low-cache-hit-rate**: Cache hit rate < 70% for 10 minutes
8. **redis-high-cpu**: Redis CPU > 70% for 10 minutes

### Alarm Actions

All alarms send notifications to the SNS topic when:
- Alarm state changes to ALARM
- Alarm state returns to OK (optional)

### Viewing Alarms

**Via AWS Console:**
```
CloudWatch → Alarms → All alarms → Filter by "ohmycoins-staging"
```

**Via AWS CLI:**
```bash
# List all alarms
aws cloudwatch describe-alarms \
  --alarm-name-prefix ohmycoins-staging \
  --region ap-southeast-2

# List alarms in ALARM state
aws cloudwatch describe-alarms \
  --alarm-name-prefix ohmycoins-staging \
  --state-value ALARM \
  --region ap-southeast-2
```

## SNS Topic and Email Subscriptions

### Email Setup

When you first deploy this module with email addresses:

1. **Subscription emails are sent** to all addresses in `alert_emails`
2. **Recipients must confirm** by clicking the link in the email
3. **After confirmation**, they'll receive alarm notifications

### Managing Subscriptions

**Add email via Terraform:**
```hcl
alert_emails = [
  "existing@example.com",
  "new@example.com"  # Add new email
]
```

**Add email via AWS CLI:**
```bash
aws sns subscribe \
  --topic-arn arn:aws:sns:ap-southeast-2:ACCOUNT_ID:ohmycoins-staging-alerts \
  --protocol email \
  --notification-endpoint new-email@example.com
```

**Remove email:**
```bash
# List subscriptions
aws sns list-subscriptions-by-topic \
  --topic-arn arn:aws:sns:ap-southeast-2:ACCOUNT_ID:ohmycoins-staging-alerts

# Unsubscribe
aws sns unsubscribe \
  --subscription-arn SUBSCRIPTION_ARN
```

## Customizing Thresholds

### Staging vs Production

**Staging (Development):**
```hcl
cpu_threshold            = 90  # More lenient
memory_threshold         = 90  # More lenient
error_5xx_threshold      = 20  # Higher tolerance
cache_hit_rate_threshold = 60  # Lower expectation
```

**Production (Strict):**
```hcl
cpu_threshold            = 70  # More aggressive
memory_threshold         = 70  # More aggressive
error_5xx_threshold      = 5   # Low tolerance
cache_hit_rate_threshold = 80  # High expectation
```

## Testing Alarms

### Test SNS Notifications

```bash
aws sns publish \
  --topic-arn arn:aws:sns:ap-southeast-2:ACCOUNT_ID:ohmycoins-staging-alerts \
  --message "Test alarm notification" \
  --subject "Test Alert"
```

### Trigger Test Alarm

**CPU Stress Test:**
```bash
# Run CPU-intensive task to trigger alarm
aws ecs execute-command \
  --cluster ohmycoins-staging-cluster \
  --task TASK_ARN \
  --container backend \
  --command "stress --cpu 4 --timeout 600s" \
  --interactive
```

**Trigger 5xx Errors:**
```bash
# Send requests that cause errors
for i in {1..20}; do
  curl https://api.staging.ohmycoins.com/nonexistent
done
```

## Troubleshooting

### Alarms Not Triggering

1. **Check metric data exists:**
   ```bash
   aws cloudwatch get-metric-statistics \
     --namespace AWS/ECS \
     --metric-name CPUUtilization \
     --dimensions Name=ServiceName,Value=ohmycoins-staging-backend-service Name=ClusterName,Value=ohmycoins-staging-cluster \
     --start-time $(date -u -d '1 hour ago' --iso-8601) \
     --end-time $(date -u --iso-8601) \
     --period 300 \
     --statistics Average
   ```

2. **Verify alarm configuration:**
   ```bash
   aws cloudwatch describe-alarms \
     --alarm-names ohmycoins-staging-ecs-high-cpu
   ```

3. **Check SNS topic subscriptions:**
   ```bash
   aws sns list-subscriptions-by-topic \
     --topic-arn TOPIC_ARN
   ```

### Email Notifications Not Received

1. **Confirm subscription** - Check spam folder for confirmation email
2. **Verify subscription status** - Should be "Confirmed"
3. **Test SNS topic** - Send test message
4. **Check email filters** - Ensure AWS emails not blocked

### Dashboard Not Showing Data

1. **Verify resource names match** - Check ARN suffixes
2. **Wait for metrics** - ECS metrics can take 1-2 minutes
3. **Check time range** - Ensure viewing recent data
4. **Verify permissions** - IAM role has CloudWatch read access

## Cost Considerations

### CloudWatch Costs

- **Dashboards**: $3/month per dashboard
- **Alarms**: $0.10/month per alarm (first 10 free)
- **Metrics**: Free for AWS services (ECS, ALB, RDS, Redis)
- **SNS**: $0.50 per million notifications

**Estimated Monthly Cost:**
- 1 Dashboard: $3
- 8 Alarms: $0 (under free tier)
- SNS (100 notifications): <$0.01
- **Total: ~$3/month**

### Cost Optimization

- Use fewer alarms in staging
- Aggregate related metrics
- Use metric math to combine alarms
- Set appropriate evaluation periods

## Best Practices

1. **Start with conservative thresholds**, adjust based on actual usage
2. **Test alarms in staging** before deploying to production
3. **Document baseline metrics** for comparison
4. **Review alarm history monthly** to tune thresholds
5. **Set up alarm actions** beyond just email (PagerDuty, Slack)
6. **Use composite alarms** for complex conditions
7. **Add custom application metrics** for business logic monitoring

## Integration with Other Tools

### Slack Integration

```bash
# Create Lambda function to forward SNS to Slack
# Subscribe Lambda to SNS topic
aws sns subscribe \
  --topic-arn TOPIC_ARN \
  --protocol lambda \
  --notification-endpoint arn:aws:lambda:REGION:ACCOUNT:function:sns-to-slack
```

### PagerDuty Integration

```bash
# Use PagerDuty email endpoint
aws sns subscribe \
  --topic-arn TOPIC_ARN \
  --protocol email \
  --notification-endpoint your-service@company.pagerduty.com
```

## Examples

See `INTEGRATION_EXAMPLE.md` for complete examples of using this module in staging and production environments.

## References

- [CloudWatch Alarms Documentation](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html)
- [CloudWatch Dashboards](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Dashboards.html)
- [SNS Topics](https://docs.aws.amazon.com/sns/latest/dg/sns-create-topic.html)
- [Monitoring Best Practices](../monitoring/README.md)
