# Outputs for Monitoring Module

output "sns_topic_arn" {
  description = "ARN of the SNS topic for alerts"
  value       = aws_sns_topic.alerts.arn
}

output "sns_topic_name" {
  description = "Name of the SNS topic for alerts"
  value       = aws_sns_topic.alerts.name
}

output "dashboard_name" {
  description = "Name of the CloudWatch dashboard"
  value       = aws_cloudwatch_dashboard.main.dashboard_name
}

output "dashboard_arn" {
  description = "ARN of the CloudWatch dashboard"
  value       = aws_cloudwatch_dashboard.main.dashboard_arn
}

output "alarm_names" {
  description = "List of all CloudWatch alarm names"
  value = [
    aws_cloudwatch_metric_alarm.ecs_high_cpu.alarm_name,
    aws_cloudwatch_metric_alarm.ecs_high_memory.alarm_name,
    aws_cloudwatch_metric_alarm.alb_high_5xx.alarm_name,
    aws_cloudwatch_metric_alarm.alb_unhealthy_targets.alarm_name,
    aws_cloudwatch_metric_alarm.rds_high_cpu.alarm_name,
    aws_cloudwatch_metric_alarm.rds_low_storage.alarm_name,
    aws_cloudwatch_metric_alarm.redis_low_cache_hit_rate.alarm_name,
    aws_cloudwatch_metric_alarm.redis_high_cpu.alarm_name,
  ]
}

output "alarm_arns" {
  description = "Map of alarm names to ARNs"
  value = {
    ecs_high_cpu            = aws_cloudwatch_metric_alarm.ecs_high_cpu.arn
    ecs_high_memory         = aws_cloudwatch_metric_alarm.ecs_high_memory.arn
    alb_high_5xx            = aws_cloudwatch_metric_alarm.alb_high_5xx.arn
    alb_unhealthy_targets   = aws_cloudwatch_metric_alarm.alb_unhealthy_targets.arn
    rds_high_cpu            = aws_cloudwatch_metric_alarm.rds_high_cpu.arn
    rds_low_storage         = aws_cloudwatch_metric_alarm.rds_low_storage.arn
    redis_low_cache_hit_rate = aws_cloudwatch_metric_alarm.redis_low_cache_hit_rate.arn
    redis_high_cpu          = aws_cloudwatch_metric_alarm.redis_high_cpu.arn
  }
}
