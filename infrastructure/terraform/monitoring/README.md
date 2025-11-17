# CloudWatch Monitoring Configuration

This directory contains CloudWatch dashboard and alarm configurations for Oh My Coins infrastructure.

## Dashboard Templates

### Infrastructure Dashboard

To create the main infrastructure dashboard:

```bash
aws cloudwatch put-dashboard \
  --dashboard-name ohmycoins-staging-infrastructure \
  --dashboard-body file://dashboards/infrastructure-dashboard.json
```

### Application Dashboard

To create the application monitoring dashboard:

```bash
aws cloudwatch put-dashboard \
  --dashboard-name ohmycoins-staging-application \
  --dashboard-body file://dashboards/application-dashboard.json
```

## Alarm Configuration

Alarms are automatically created by Terraform modules. To view all alarms:

```bash
aws cloudwatch describe-alarms \
  --alarm-name-prefix ohmycoins-staging
```

## Key Metrics to Monitor

### ECS Service Metrics
- **CPUUtilization**: Target < 70%
- **MemoryUtilization**: Target < 80%
- **RunningTaskCount**: Should match desired count
- **HealthyTargetCount**: Should match running tasks

### RDS Metrics
- **DatabaseConnections**: Monitor for connection leaks
- **CPUUtilization**: Alert if > 80%
- **FreeStorageSpace**: Alert if < 20% remaining
- **ReadLatency / WriteLatency**: Monitor for slow queries

### Redis Metrics
- **CacheHitRate**: Target > 80%
- **EngineCPUUtilization**: Alert if > 70%
- **Evictions**: Should be minimal
- **CurrConnections**: Monitor for connection leaks

### ALB Metrics
- **TargetResponseTime**: Target < 500ms for p95
- **HTTPCode_Target_5XX_Count**: Alert if > 5% of requests
- **UnHealthyHostCount**: Alert if > 0
- **RequestCount**: Monitor for traffic patterns

## Setting Up SNS for Alerts

1. **Create SNS Topic**:
   ```bash
   aws sns create-topic --name ohmycoins-alerts
   ```

2. **Subscribe Email**:
   ```bash
   aws sns subscribe \
     --topic-arn arn:aws:sns:ap-southeast-2:ACCOUNT_ID:ohmycoins-alerts \
     --protocol email \
     --notification-endpoint your-email@example.com
   ```

3. **Confirm Subscription**: Check your email and confirm.

4. **Update Alarms** to use SNS topic (can be added to Terraform modules).

## Log Insights Queries

### Find Application Errors

```
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 100
```

### Track API Response Times

```
fields @timestamp, @message
| filter @message like /response_time/
| parse @message "response_time: * ms" as response_time
| stats avg(response_time), max(response_time), min(response_time) by bin(5m)
```

### Monitor Database Connections

```
fields @timestamp, @message
| filter @message like /database/
| filter @message like /connection/
| stats count() by bin(5m)
```

## Custom Metrics

To publish custom metrics from your application:

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

cloudwatch.put_metric_data(
    Namespace='OhMyCoins/Application',
    MetricData=[
        {
            'MetricName': 'DataCollectionDuration',
            'Value': duration_seconds,
            'Unit': 'Seconds',
            'Timestamp': datetime.utcnow(),
        }
    ]
)
```

## Monitoring Best Practices

1. **Set up dashboards** before deployment
2. **Configure SNS alerts** for critical metrics
3. **Review metrics daily** in the morning
4. **Set up weekly reports** for cost and performance
5. **Use Container Insights** for ECS detailed metrics
6. **Enable RDS Performance Insights** for query analysis

## Cost Monitoring

Monitor CloudWatch costs:

```bash
# Check CloudWatch costs
aws ce get-cost-and-usage \
  --time-period Start=2025-11-01,End=2025-11-30 \
  --granularity MONTHLY \
  --metrics UnblendedCost \
  --filter file://filter.json
```

Where `filter.json`:
```json
{
  "Dimensions": {
    "Key": "SERVICE",
    "Values": ["Amazon CloudWatch"]
  }
}
```

## Troubleshooting

### Alarms Not Triggering

1. Check metric has recent data
2. Verify alarm threshold and evaluation periods
3. Check SNS topic subscription is confirmed
4. Review CloudWatch Logs for metric publication errors

### Dashboard Not Showing Data

1. Verify resource names match dashboard configuration
2. Check time range in dashboard
3. Ensure metrics are being published
4. Verify correct region (ap-southeast-2)

---

**Last Updated:** 2025-11-17  
**Maintained By:** Developer C (Infrastructure & DevOps)
