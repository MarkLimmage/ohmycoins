# CloudWatch Monitoring Module
# Creates CloudWatch dashboards, alarms, and SNS topics for Oh My Coins

# SNS Topic for Alerts
resource "aws_sns_topic" "alerts" {
  name              = "${var.project_name}-alerts"
  display_name      = "Oh My Coins ${var.environment} Alerts"
  kms_master_key_id = var.kms_key_id

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-alerts"
    }
  )
}

# SNS Topic Subscription (Email)
resource "aws_sns_topic_subscription" "alerts_email" {
  count     = length(var.alert_emails) > 0 ? length(var.alert_emails) : 0
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_emails[count.index]
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_name}-infrastructure"

  dashboard_body = jsonencode({
    widgets = [
      # ECS Service Metrics
      {
        type = "metric"
        x    = 0
        y    = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/ECS", "CPUUtilization", {
              stat       = "Average"
              label      = "Backend CPU"
              dimensions = {
                ServiceName = var.backend_service_name
                ClusterName = var.cluster_name
              }
            }],
            [".", "MemoryUtilization", {
              stat       = "Average"
              label      = "Backend Memory"
              dimensions = {
                ServiceName = var.backend_service_name
                ClusterName = var.cluster_name
              }
            }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "ECS Backend Service - CPU & Memory"
          period  = 300
          yAxis = {
            left = {
              min = 0
              max = 100
            }
          }
        }
      },
      # ALB Response Times
      {
        type = "metric"
        x    = 12
        y    = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/ApplicationELB", "TargetResponseTime", {
              stat       = "Average"
              label      = "Avg Response Time"
              dimensions = {
                LoadBalancer = var.alb_arn_suffix
              }
            }],
            ["...", {
              stat       = "p95"
              label      = "P95 Response Time"
              dimensions = {
                LoadBalancer = var.alb_arn_suffix
              }
            }],
            ["...", {
              stat       = "p99"
              label      = "P99 Response Time"
              dimensions = {
                LoadBalancer = var.alb_arn_suffix
              }
            }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "ALB Response Times"
          period  = 300
          yAxis = {
            left = {
              min = 0
            }
          }
        }
      },
      # HTTP Status Codes
      {
        type = "metric"
        x    = 0
        y    = 6
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/ApplicationELB", "HTTPCode_Target_2XX_Count", {
              stat       = "Sum"
              label      = "2xx Success"
              dimensions = {
                LoadBalancer = var.alb_arn_suffix
              }
            }],
            [".", "HTTPCode_Target_4XX_Count", {
              stat       = "Sum"
              label      = "4xx Client Error"
              dimensions = {
                LoadBalancer = var.alb_arn_suffix
              }
            }],
            [".", "HTTPCode_Target_5XX_Count", {
              stat       = "Sum"
              label      = "5xx Server Error"
              dimensions = {
                LoadBalancer = var.alb_arn_suffix
              }
            }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "ALB HTTP Status Codes"
          period  = 300
        }
      },
      # RDS Metrics
      {
        type = "metric"
        x    = 12
        y    = 6
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/RDS", "DatabaseConnections", {
              stat       = "Average"
              label      = "Active Connections"
              dimensions = {
                DBInstanceIdentifier = var.db_instance_id
              }
            }],
            [".", "CPUUtilization", {
              stat       = "Average"
              label      = "CPU %"
              dimensions = {
                DBInstanceIdentifier = var.db_instance_id
              }
            }],
            [".", "FreeableMemory", {
              stat       = "Average"
              label      = "Free Memory"
              dimensions = {
                DBInstanceIdentifier = var.db_instance_id
              }
            }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "RDS Metrics"
          period  = 300
        }
      },
      # Redis Metrics
      {
        type = "metric"
        x    = 0
        y    = 12
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/ElastiCache", "CacheHitRate", {
              stat       = "Average"
              label      = "Cache Hit Rate"
              dimensions = {
                CacheClusterId = var.redis_cluster_id
              }
            }],
            [".", "EngineCPUUtilization", {
              stat       = "Average"
              label      = "CPU %"
              dimensions = {
                CacheClusterId = var.redis_cluster_id
              }
            }],
            [".", "CurrConnections", {
              stat       = "Average"
              label      = "Connections"
              dimensions = {
                CacheClusterId = var.redis_cluster_id
              }
            }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Redis Cache Metrics"
          period  = 300
        }
      },
      # ECS Task Counts
      {
        type = "metric"
        x    = 12
        y    = 12
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/ECS", "DesiredTaskCount", {
              stat       = "Average"
              label      = "Desired Tasks"
              dimensions = {
                ServiceName = var.backend_service_name
                ClusterName = var.cluster_name
              }
            }],
            [".", "RunningTaskCount", {
              stat       = "Average"
              label      = "Running Tasks"
              dimensions = {
                ServiceName = var.backend_service_name
                ClusterName = var.cluster_name
              }
            }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "ECS Task Counts"
          period  = 300
        }
      }
    ]
  })
}

# CloudWatch Alarms

# High CPU Alarm - ECS
resource "aws_cloudwatch_metric_alarm" "ecs_high_cpu" {
  alarm_name          = "${var.project_name}-ecs-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "300"
  statistic           = "Average"
  threshold           = var.cpu_threshold
  alarm_description   = "This metric monitors ECS CPU utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    ServiceName = var.backend_service_name
    ClusterName = var.cluster_name
  }

  tags = var.tags
}

# High Memory Alarm - ECS
resource "aws_cloudwatch_metric_alarm" "ecs_high_memory" {
  alarm_name          = "${var.project_name}-ecs-high-memory"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = "300"
  statistic           = "Average"
  threshold           = var.memory_threshold
  alarm_description   = "This metric monitors ECS memory utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    ServiceName = var.backend_service_name
    ClusterName = var.cluster_name
  }

  tags = var.tags
}

# High 5xx Error Rate - ALB
resource "aws_cloudwatch_metric_alarm" "alb_high_5xx" {
  alarm_name          = "${var.project_name}-alb-high-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Sum"
  threshold           = var.error_5xx_threshold
  alarm_description   = "This metric monitors ALB 5xx errors"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
  }

  tags = var.tags
}

# Unhealthy Target Alarm - ALB
resource "aws_cloudwatch_metric_alarm" "alb_unhealthy_targets" {
  alarm_name          = "${var.project_name}-alb-unhealthy-targets"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "UnHealthyHostCount"
  namespace           = "AWS/ApplicationELB"
  period              = "60"
  statistic           = "Average"
  threshold           = "0"
  alarm_description   = "This metric monitors unhealthy ALB targets"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    TargetGroup  = var.target_group_arn_suffix
    LoadBalancer = var.alb_arn_suffix
  }

  tags = var.tags
}

# High Database CPU - RDS
resource "aws_cloudwatch_metric_alarm" "rds_high_cpu" {
  alarm_name          = "${var.project_name}-rds-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = var.rds_cpu_threshold
  alarm_description   = "This metric monitors RDS CPU utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBInstanceIdentifier = var.db_instance_id
  }

  tags = var.tags
}

# Low Storage Space - RDS
resource "aws_cloudwatch_metric_alarm" "rds_low_storage" {
  alarm_name          = "${var.project_name}-rds-low-storage"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = var.rds_storage_threshold # in bytes (10GB = 10737418240)
  alarm_description   = "This metric monitors RDS available storage"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBInstanceIdentifier = var.db_instance_id
  }

  tags = var.tags
}

# Low Cache Hit Rate - Redis
resource "aws_cloudwatch_metric_alarm" "redis_low_cache_hit_rate" {
  alarm_name          = "${var.project_name}-redis-low-cache-hit-rate"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CacheHitRate"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Average"
  threshold           = var.cache_hit_rate_threshold
  alarm_description   = "This metric monitors Redis cache hit rate"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    CacheClusterId = var.redis_cluster_id
  }

  tags = var.tags
}

# High Redis CPU
resource "aws_cloudwatch_metric_alarm" "redis_high_cpu" {
  alarm_name          = "${var.project_name}-redis-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "EngineCPUUtilization"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Average"
  threshold           = var.redis_cpu_threshold
  alarm_description   = "This metric monitors Redis CPU utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    CacheClusterId = var.redis_cluster_id
  }

  tags = var.tags
}
