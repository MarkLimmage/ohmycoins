# Monitoring Setup and Configuration Guide

**Purpose:** Complete guide for setting up and configuring CloudWatch monitoring for Oh My Coins  
**Target Audience:** DevOps engineers, SREs  
**Environment:** AWS ECS Fargate  
**Last Updated:** January 10, 2026

---

## Table of Contents

1. [Overview](#overview)
2. [Monitoring Architecture](#monitoring-architecture)
3. [Initial Setup](#initial-setup)
4. [CloudWatch Dashboard Configuration](#cloudwatch-dashboard-configuration)
5. [Alarm Configuration](#alarm-configuration)
6. [SNS Notification Setup](#sns-notification-setup)
7. [Custom Metrics](#custom-metrics)
8. [Log Aggregation](#log-aggregation)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The Oh My Coins monitoring infrastructure provides comprehensive observability across all application components:

- **CloudWatch Dashboard**: Real-time visualization of key metrics
- **CloudWatch Alarms**: Automated alerting for critical thresholds
- **CloudWatch Logs**: Centralized log aggregation and search
- **SNS Topics**: Multi-channel notification delivery
- **CloudWatch Insights**: Advanced log analytics

### What Gets Monitored

✅ **ECS Services**: CPU, memory, task counts  
✅ **Load Balancer**: Response times, HTTP status codes, target health  
✅ **RDS Database**: CPU, connections, storage, I/O  
✅ **ElastiCache Redis**: Cache hit rate, memory, connections  
✅ **Application**: Custom business metrics (optional)

---

## Monitoring Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Backend  │  │ Frontend │  │   RDS    │  │  Redis   │   │
│  │   ECS    │  │   ECS    │  │PostgreSQL│  │  Cache   │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │             │              │             │          │
│       └─────────────┴──────────────┴─────────────┘          │
│                         ↓                                    │
└─────────────────────────┼────────────────────────────────────┘
                          ↓
┌─────────────────────────┼────────────────────────────────────┐
│                  CloudWatch Metrics                          │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  • ECS: CPUUtilization, MemoryUtilization             │  │
│  │  • ALB: TargetResponseTime, HTTPCode_Target_2XX_Count │  │
│  │  • RDS: DatabaseConnections, FreeStorageSpace         │  │
│  │  • Redis: CacheHits, EngineCPUUtilization            │  │
│  └────────────────────┬──────────────────────────────────┘  │
│                       ↓                                      │
│  ┌────────────────────────────────────────────────────┐     │
│  │          CloudWatch Dashboard                      │     │
│  │  • 6 widgets with real-time visualizations         │     │
│  └────────────────────────────────────────────────────┘     │
│                       ↓                                      │
│  ┌────────────────────────────────────────────────────┐     │
│  │          CloudWatch Alarms (8 alarms)              │     │
│  │  • High CPU, High Memory, 5xx Errors, etc.         │     │
│  └────────────────────┬───────────────────────────────┘     │
└─────────────────────────┼────────────────────────────────────┘
                          ↓
┌─────────────────────────┼────────────────────────────────────┐
│                   SNS Topic                                  │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Email, SMS, Lambda, HTTP/S endpoints              │     │
│  └───┬──────────────┬──────────────┬─────────────────┘     │
│      ↓              ↓              ↓                         │
│   Email         Slack          PagerDuty                     │
└──────────────────────────────────────────────────────────────┘
```

---

## Initial Setup

### Prerequisites

- Terraform infrastructure deployed
- AWS CLI configured
- Access to AWS Console
- Email address for notifications

### Verify Monitoring Module Deployment

```bash
# Navigate to staging environment
cd infrastructure/terraform/environments/staging

# Check if monitoring module is deployed
terraform output monitoring_sns_topic_arn

# If output is empty, monitoring module needs to be enabled
# Check main.tf for monitoring module configuration
```

### Deploy Monitoring Module (If Not Already Deployed)

The monitoring module is included in the main Terraform configuration. If it's not showing outputs:

```bash
# Ensure monitoring module is uncommented in main.tf
# Then re-apply
terraform plan
terraform apply
```

---

## CloudWatch Dashboard Configuration

### Access Dashboard

**Via AWS Console:**
1. Open CloudWatch Console: https://console.aws.amazon.com/cloudwatch/
2. Navigate to: Dashboards → `ohmycoins-staging-infrastructure`
3. Bookmark this URL for quick access

**Via Terraform Output:**
```bash
# Get dashboard name
terraform output dashboard_name

# Construct dashboard URL
DASHBOARD_NAME=$(terraform output -raw dashboard_name)
echo "https://console.aws.amazon.com/cloudwatch/home?region=ap-southeast-2#dashboards:name=$DASHBOARD_NAME"
```

### Dashboard Widgets

The default dashboard includes 6 widgets:

#### 1. ECS CPU & Memory (Top Left)
- **Metrics**: CPUUtilization, MemoryUtilization
- **Namespace**: AWS/ECS
- **Dimensions**: ClusterName, ServiceName
- **Period**: 5 minutes
- **Statistic**: Average

**What to Look For:**
- Normal: CPU 20-50%, Memory 30-60%
- Warning: CPU >60%, Memory >70%
- Critical: CPU >80%, Memory >80%

#### 2. ALB Response Times (Top Right)
- **Metrics**: TargetResponseTime (avg, p95, p99)
- **Namespace**: AWS/ApplicationELB
- **Dimensions**: LoadBalancer, TargetGroup
- **Period**: 1 minute

**What to Look For:**
- Good: p99 <500ms
- Acceptable: p99 <1000ms
- Poor: p99 >1000ms

#### 3. HTTP Status Codes (Middle Left)
- **Metrics**: HTTPCode_Target_2XX_Count, 4XX_Count, 5XX_Count
- **Namespace**: AWS/ApplicationELB
- **Period**: 1 minute
- **Statistic**: Sum

**What to Look For:**
- Healthy: 2XX >95%, 4XX <5%, 5XX <0.1%
- Warning: 5XX >1%
- Critical: 5XX >5%

#### 4. RDS Metrics (Middle Right)
- **Metrics**: CPUUtilization, DatabaseConnections, FreeStorageSpace
- **Namespace**: AWS/RDS
- **Dimensions**: DBInstanceIdentifier
- **Period**: 5 minutes

**What to Look For:**
- CPU: <70% normal operation
- Connections: Track baseline (usually <50 for staging)
- Storage: Alert if <10GB free

#### 5. Redis Metrics (Bottom Left)
- **Metrics**: CacheHits, CacheMisses, EngineCPUUtilization
- **Namespace**: AWS/ElastiCache
- **Dimensions**: CacheClusterId
- **Period**: 1 minute

**What to Look For:**
- Cache Hit Rate: >70% is good
- CPU: <70% normal
- Evictions: Should be minimal

#### 6. ECS Task Counts (Bottom Right)
- **Metrics**: DesiredTaskCount, RunningTaskCount
- **Namespace**: AWS/ECS
- **Dimensions**: ClusterName, ServiceName
- **Period**: 1 minute

**What to Look For:**
- Running should equal Desired
- Any mismatch indicates deployment or health issues

### Customizing Dashboard

**Add Custom Widget:**
```bash
# Get current dashboard
aws cloudwatch get-dashboard \
    --dashboard-name ohmycoins-staging-infrastructure \
    --output json > dashboard.json

# Edit dashboard.json to add widgets
# Upload updated dashboard
aws cloudwatch put-dashboard \
    --dashboard-name ohmycoins-staging-infrastructure \
    --dashboard-body file://dashboard.json
```

**Example: Add Custom Application Metric Widget**
```json
{
  "type": "metric",
  "properties": {
    "metrics": [
      ["OhMyCoins", "TransactionsProcessed", {"stat": "Sum"}]
    ],
    "region": "ap-southeast-2",
    "title": "Transactions Processed",
    "period": 300
  }
}
```

---

## Alarm Configuration

### View All Alarms

```bash
# List all alarms
aws cloudwatch describe-alarms \
    --alarm-name-prefix ohmycoins-staging \
    --query 'MetricAlarms[*].[AlarmName,StateValue,MetricName]' \
    --output table
```

### Alarm Definitions

#### 1. High ECS CPU
- **Threshold**: >80% for 10 minutes (2 consecutive periods)
- **Actions**: SNS notification
- **Auto-Recovery**: None (investigate cause)

```bash
# View alarm details
aws cloudwatch describe-alarms \
    --alarm-names ohmycoins-staging-ecs-high-cpu
```

#### 2. High ECS Memory
- **Threshold**: >80% for 10 minutes
- **Actions**: SNS notification
- **Auto-Recovery**: None (may need task scaling)

#### 3. ALB 5xx Errors
- **Threshold**: >10 errors in 5 minutes
- **Actions**: SNS notification
- **Auto-Recovery**: None (indicates application errors)

#### 4. ALB Unhealthy Targets
- **Threshold**: >0 unhealthy targets for 3 minutes
- **Actions**: SNS notification
- **Auto-Recovery**: ECS will restart unhealthy tasks

#### 5. RDS High CPU
- **Threshold**: >80% for 10 minutes
- **Actions**: SNS notification
- **Auto-Recovery**: None (may need DB optimization)

#### 6. RDS Low Storage
- **Threshold**: <10GB free storage
- **Actions**: SNS notification
- **Auto-Recovery**: None (manual intervention required)

#### 7. Redis Low Cache Hit Rate
- **Threshold**: <70% for 10 minutes
- **Actions**: SNS notification
- **Auto-Recovery**: None (investigate cache configuration)

#### 8. Redis High CPU
- **Threshold**: >70% for 10 minutes
- **Actions**: SNS notification
- **Auto-Recovery**: None (may need node scaling)

### Modify Alarm Thresholds

**Example: Make CPU alarm more aggressive for production**

```bash
# Update alarm threshold to 70% instead of 80%
aws cloudwatch put-metric-alarm \
    --alarm-name ohmycoins-production-ecs-high-cpu \
    --alarm-description "ECS CPU utilization exceeds 70%" \
    --metric-name CPUUtilization \
    --namespace AWS/ECS \
    --statistic Average \
    --period 300 \
    --evaluation-periods 2 \
    --threshold 70.0 \
    --comparison-operator GreaterThanThreshold \
    --dimensions Name=ServiceName,Value=ohmycoins-production-backend-service Name=ClusterName,Value=ohmycoins-production-cluster \
    --alarm-actions arn:aws:sns:ap-southeast-2:ACCOUNT_ID:ohmycoins-production-alerts
```

### Test Alarms

**Method 1: Manual SNS Test**
```bash
SNS_TOPIC_ARN=$(terraform output -raw monitoring_sns_topic_arn)

aws sns publish \
    --topic-arn $SNS_TOPIC_ARN \
    --message "Test alarm notification" \
    --subject "TEST: CloudWatch Alarm"
```

**Method 2: Trigger Real Alarm (Careful!)**
```bash
# Stop ECS task to trigger unhealthy target alarm
CLUSTER_NAME=$(terraform output -raw ecs_cluster_name)
TASK_ARN=$(aws ecs list-tasks --cluster $CLUSTER_NAME --service-name ohmycoins-staging-backend-service --query 'taskArns[0]' --output text)

aws ecs stop-task \
    --cluster $CLUSTER_NAME \
    --task $TASK_ARN \
    --reason "Testing alarm notification"

# Wait 3-5 minutes for alarm to fire
# ECS will automatically start replacement task
```

---

## SNS Notification Setup

### Subscribe Email to Alerts

```bash
# Get SNS topic ARN
SNS_TOPIC_ARN=$(terraform output -raw monitoring_sns_topic_arn)

# Subscribe your email
aws sns subscribe \
    --topic-arn $SNS_TOPIC_ARN \
    --protocol email \
    --notification-endpoint devops@ohmycoins.com
```

**Important:** Check your email and click the confirmation link!

### Verify Subscription

```bash
# List all subscriptions
aws sns list-subscriptions-by-topic \
    --topic-arn $SNS_TOPIC_ARN \
    --query 'Subscriptions[*].[Protocol,Endpoint,SubscriptionArn]' \
    --output table

# Status should be confirmed, not pending
```

### Add Multiple Recipients

```bash
# Add additional emails
aws sns subscribe --topic-arn $SNS_TOPIC_ARN --protocol email --notification-endpoint oncall@ohmycoins.com
aws sns subscribe --topic-arn $SNS_TOPIC_ARN --protocol email --notification-endpoint team@ohmycoins.com
```

### Configure Slack Integration

**Option 1: Email to Slack**
Use Slack's email integration (simple but limited):
1. Create email integration in Slack: `Settings & administration` → `Manage apps` → `Email`
2. Get Slack email address (e.g., `alerts@myworkspace.slack.com`)
3. Subscribe this email to SNS topic

**Option 2: Lambda + Slack Webhook (Recommended)**

```bash
# 1. Create Lambda function
cat > lambda_function.py << 'EOF'
import json
import urllib3

http = urllib3.PoolManager()

def lambda_handler(event, context):
    message = json.loads(event['Records'][0]['Sns']['Message'])
    
    slack_message = {
        'text': f"🚨 CloudWatch Alarm: {message.get('AlarmName', 'Unknown')}",
        'attachments': [{
            'color': 'danger',
            'fields': [
                {'title': 'Description', 'value': message.get('AlarmDescription', 'N/A'), 'short': False},
                {'title': 'State', 'value': message.get('NewStateValue', 'ALARM'), 'short': True},
                {'title': 'Reason', 'value': message.get('NewStateReason', 'N/A'), 'short': False}
            ]
        }]
    }
    
    encoded_msg = json.dumps(slack_message).encode('utf-8')
    resp = http.request('POST', 'YOUR_SLACK_WEBHOOK_URL', body=encoded_msg)
    
    return {'statusCode': 200}
EOF

# 2. Create deployment package
zip function.zip lambda_function.py

# 3. Create Lambda function
aws lambda create-function \
    --function-name sns-to-slack \
    --runtime python3.11 \
    --role arn:aws:iam::ACCOUNT_ID:role/lambda-execution-role \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://function.zip

# 4. Subscribe Lambda to SNS
LAMBDA_ARN=$(aws lambda get-function --function-name sns-to-slack --query 'Configuration.FunctionArn' --output text)

aws sns subscribe \
    --topic-arn $SNS_TOPIC_ARN \
    --protocol lambda \
    --notification-endpoint $LAMBDA_ARN

# 5. Grant SNS permission to invoke Lambda
aws lambda add-permission \
    --function-name sns-to-slack \
    --statement-id sns-invoke \
    --action lambda:InvokeFunction \
    --principal sns.amazonaws.com \
    --source-arn $SNS_TOPIC_ARN
```

### Configure PagerDuty Integration

```bash
# Get your PagerDuty email endpoint from PagerDuty console
# Format: service-key@company.pagerduty.com

aws sns subscribe \
    --topic-arn $SNS_TOPIC_ARN \
    --protocol email \
    --notification-endpoint your-service@company.pagerduty.com
```

---

## Custom Metrics

### Publishing Custom Application Metrics

**From Application Code (Python example):**

```python
import boto3

cloudwatch = boto3.client('cloudwatch', region_name='ap-southeast-2')

def record_transaction(amount, status):
    """Record a custom metric for transaction processing"""
    cloudwatch.put_metric_data(
        Namespace='OhMyCoins',
        MetricData=[
            {
                'MetricName': 'TransactionAmount',
                'Value': amount,
                'Unit': 'None',
                'Dimensions': [
                    {'Name': 'Status', 'Value': status},
                    {'Name': 'Environment', 'Value': 'staging'}
                ]
            }
        ]
    )
```

**From Command Line:**

```bash
# Publish custom metric
aws cloudwatch put-metric-data \
    --namespace OhMyCoins \
    --metric-name TransactionsProcessed \
    --value 1 \
    --dimensions Environment=staging
```

### Create Alarm for Custom Metric

```bash
aws cloudwatch put-metric-alarm \
    --alarm-name ohmycoins-staging-low-transaction-volume \
    --alarm-description "Transactions per minute below expected" \
    --metric-name TransactionsProcessed \
    --namespace OhMyCoins \
    --statistic Sum \
    --period 300 \
    --evaluation-periods 2 \
    --threshold 10 \
    --comparison-operator LessThanThreshold \
    --dimensions Name=Environment,Value=staging \
    --alarm-actions $SNS_TOPIC_ARN
```

---

## Log Aggregation

### CloudWatch Logs Setup

Logs are automatically configured for ECS tasks. View logs:

```bash
# View backend logs
aws logs tail /ecs/ohmycoins-staging-backend --follow

# View frontend logs
aws logs tail /ecs/ohmycoins-staging-frontend --follow

# Filter logs by pattern
aws logs filter-log-events \
    --log-group-name /ecs/ohmycoins-staging-backend \
    --filter-pattern "ERROR" \
    --start-time $(date -u -d '1 hour ago' +%s)000
```

### CloudWatch Logs Insights

**Example Query: Error Analysis**

```sql
fields @timestamp, @message
| filter @message like /ERROR/
| stats count() by bin(5m)
| sort @timestamp desc
```

**Example Query: Slow Requests**

```sql
fields @timestamp, @message, request_duration
| filter request_duration > 1000
| sort request_duration desc
| limit 20
```

**Run Query via Console:**
1. Open CloudWatch → Logs Insights
2. Select log group: `/ecs/ohmycoins-staging-backend`
3. Paste query
4. Select time range
5. Click "Run query"

**Run Query via CLI:**

```bash
aws logs start-query \
    --log-group-name /ecs/ohmycoins-staging-backend \
    --start-time $(date -u -d '1 hour ago' +%s) \
    --end-time $(date -u +%s) \
    --query-string 'fields @timestamp, @message | filter @message like /ERROR/ | limit 20'
```

---

## Best Practices

### Monitoring Strategy

1. **Start with Defaults**: Use the provided monitoring configuration
2. **Baseline Metrics**: Record normal operation metrics (first 2 weeks)
3. **Tune Thresholds**: Adjust alarm thresholds based on baseline
4. **Review Regularly**: Weekly review of alarms and false positives
5. **Document Changes**: Keep runbook updated with threshold changes

### Alarm Management

✅ **Do:**
- Set realistic thresholds based on actual behavior
- Use multiple evaluation periods to avoid flapping
- Test alarms before production
- Document expected alarm patterns
- Create runbooks for alarm responses

❌ **Don't:**
- Set overly aggressive thresholds (causes alert fatigue)
- Ignore alarms (defeats the purpose)
- Delete alarms without understanding them
- Rely only on email notifications

### Cost Optimization

**CloudWatch Costs:**
- Dashboards: $3/month per dashboard
- Alarms: $0.10/month per alarm (first 10 free)
- Custom Metrics: $0.30 per metric/month
- Log Ingestion: $0.50 per GB
- Log Storage: $0.03 per GB/month

**Tips to Reduce Costs:**
- Use log retention policies (7 days for staging)
- Aggregate similar metrics
- Use metric filters instead of separate metrics
- Archive old logs to S3
- Use log sampling for high-volume logs

---

## Troubleshooting

### Dashboard Not Showing Data

**Symptom:** Dashboard widgets are empty

**Solutions:**
1. Verify resources exist and are running
2. Check metric dimensions match actual resources
3. Wait 1-2 minutes for metrics to populate
4. Verify time range selector

```bash
# Check if metrics exist
aws cloudwatch list-metrics \
    --namespace AWS/ECS \
    --dimensions Name=ClusterName,Value=ohmycoins-staging-cluster
```

### Alarms Not Triggering

**Symptom:** Thresholds exceeded but no alarm

**Solutions:**
1. Check alarm state and reason
2. Verify metric data is being published
3. Check evaluation periods and datapoints to alarm
4. Verify SNS topic ARN is correct

```bash
# Check alarm configuration
aws cloudwatch describe-alarms \
    --alarm-names ohmycoins-staging-ecs-high-cpu

# Test SNS topic
aws sns publish \
    --topic-arn $SNS_TOPIC_ARN \
    --message "Test" \
    --subject "Test"
```

### Email Notifications Not Received

**Symptom:** Alarms trigger but no emails

**Solutions:**
1. Check spam folder
2. Confirm subscription (pending status)
3. Verify email address is correct
4. Test with manual SNS publish

```bash
# Check subscription status
aws sns list-subscriptions-by-topic \
    --topic-arn $SNS_TOPIC_ARN \
    --query 'Subscriptions[*].[Protocol,Endpoint,SubscriptionArn]'
```

### High CloudWatch Costs

**Symptom:** Unexpected CloudWatch charges

**Solutions:**
1. Review log ingestion rates
2. Check custom metric count
3. Enable log retention policies
4. Use log sampling

```bash
# Check log ingestion
aws cloudwatch get-metric-statistics \
    --namespace AWS/Logs \
    --metric-name IncomingBytes \
    --dimensions Name=LogGroupName,Value=/ecs/ohmycoins-staging-backend \
    --start-time $(date -u -d '24 hours ago' --iso-8601) \
    --end-time $(date -u --iso-8601) \
    --period 86400 \
    --statistics Sum
```

---

## References

- [CloudWatch User Guide](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/)
- [CloudWatch Logs Insights Query Syntax](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax.html)
- [SNS Topics](https://docs.aws.amazon.com/sns/latest/dg/welcome.html)
- [ECS CloudWatch Metrics](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/cloudwatch-metrics.html)

---

**Document Version:** 1.0  
**Last Updated:** January 10, 2026  
**Maintained By:** DevOps Team
