# ElastiCache Redis Module for Oh My Coins
# Creates a Redis cluster for session management and agent state

resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.project_name}-redis-subnet-group"
  subnet_ids = var.subnet_ids

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-redis-subnet-group"
    }
  )
}

resource "aws_elasticache_parameter_group" "main" {
  name   = "${var.project_name}-redis-params"
  family = var.parameter_group_family

  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }

  tags = var.tags
}

resource "aws_elasticache_replication_group" "main" {
  replication_group_id       = "${var.project_name}-redis"
  replication_group_description = "Redis cluster for ${var.project_name}"
  
  engine               = "redis"
  engine_version       = var.engine_version
  node_type            = var.node_type
  num_cache_clusters   = var.num_cache_clusters
  port                 = 6379
  
  parameter_group_name = aws_elasticache_parameter_group.main.name
  subnet_group_name    = aws_elasticache_subnet_group.main.name
  security_group_ids   = var.security_group_ids
  
  # Automatic failover (requires at least 2 nodes)
  automatic_failover_enabled = var.num_cache_clusters > 1
  multi_az_enabled          = var.multi_az_enabled && var.num_cache_clusters > 1
  
  # Encryption
  at_rest_encryption_enabled = true
  transit_encryption_enabled = var.transit_encryption_enabled
  auth_token_enabled        = var.auth_token_enabled
  auth_token                = var.auth_token_enabled ? var.auth_token : null
  
  # Backup and maintenance
  snapshot_retention_limit   = var.snapshot_retention_limit
  snapshot_window           = var.snapshot_window
  maintenance_window        = var.maintenance_window
  
  # Apply changes immediately for non-production
  apply_immediately = var.apply_immediately
  
  # Auto minor version upgrade
  auto_minor_version_upgrade = true
  
  # Logging
  log_delivery_configuration {
    destination      = aws_cloudwatch_log_group.redis_slow_log.name
    destination_type = "cloudwatch-logs"
    log_format       = "json"
    log_type         = "slow-log"
  }
  
  log_delivery_configuration {
    destination      = aws_cloudwatch_log_group.redis_engine_log.name
    destination_type = "cloudwatch-logs"
    log_format       = "json"
    log_type         = "engine-log"
  }
  
  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-redis"
    }
  )
}

# CloudWatch Log Groups for Redis logs
resource "aws_cloudwatch_log_group" "redis_slow_log" {
  name              = "/aws/elasticache/${var.project_name}/slow-log"
  retention_in_days = 7
  
  tags = var.tags
}

resource "aws_cloudwatch_log_group" "redis_engine_log" {
  name              = "/aws/elasticache/${var.project_name}/engine-log"
  retention_in_days = 7
  
  tags = var.tags
}

# CloudWatch Alarms for Redis
resource "aws_cloudwatch_metric_alarm" "cpu_utilization" {
  alarm_name          = "${var.project_name}-redis-cpu-utilization"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Average"
  threshold           = var.cpu_alarm_threshold
  alarm_description   = "This metric monitors Redis CPU utilization"
  alarm_actions       = var.alarm_actions
  
  dimensions = {
    ReplicationGroupId = aws_elasticache_replication_group.main.id
  }
  
  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "memory_utilization" {
  alarm_name          = "${var.project_name}-redis-memory-utilization"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "DatabaseMemoryUsagePercentage"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Average"
  threshold           = var.memory_alarm_threshold
  alarm_description   = "This metric monitors Redis memory utilization"
  alarm_actions       = var.alarm_actions
  
  dimensions = {
    ReplicationGroupId = aws_elasticache_replication_group.main.id
  }
  
  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "evictions" {
  alarm_name          = "${var.project_name}-redis-evictions"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Evictions"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Sum"
  threshold           = var.evictions_alarm_threshold
  alarm_description   = "This metric monitors Redis evictions"
  alarm_actions       = var.alarm_actions
  
  dimensions = {
    ReplicationGroupId = aws_elasticache_replication_group.main.id
  }
  
  tags = var.tags
}
