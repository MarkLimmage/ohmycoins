# Variables for Monitoring Module

variable "project_name" {
  description = "Name of the project (used for resource naming)"
  type        = string
}

variable "environment" {
  description = "Environment name (staging, production)"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "cluster_name" {
  description = "Name of the ECS cluster"
  type        = string
}

variable "backend_service_name" {
  description = "Name of the backend ECS service"
  type        = string
}

variable "alb_arn_suffix" {
  description = "ARN suffix of the Application Load Balancer (app/name/id)"
  type        = string
}

variable "target_group_arn_suffix" {
  description = "ARN suffix of the target group (targetgroup/name/id)"
  type        = string
}

variable "db_instance_id" {
  description = "RDS database instance identifier"
  type        = string
}

variable "redis_cluster_id" {
  description = "ElastiCache Redis cluster identifier"
  type        = string
}

variable "alert_emails" {
  description = "List of email addresses to receive CloudWatch alarm notifications"
  type        = list(string)
  default     = []
}

variable "kms_key_id" {
  description = "KMS key ID for SNS topic encryption (optional)"
  type        = string
  default     = null
}

# Alarm Thresholds

variable "cpu_threshold" {
  description = "CPU utilization threshold for ECS alarms (%)"
  type        = number
  default     = 80
}

variable "memory_threshold" {
  description = "Memory utilization threshold for ECS alarms (%)"
  type        = number
  default     = 80
}

variable "error_5xx_threshold" {
  description = "Number of 5xx errors to trigger alarm"
  type        = number
  default     = 10
}

variable "rds_cpu_threshold" {
  description = "CPU utilization threshold for RDS alarms (%)"
  type        = number
  default     = 80
}

variable "rds_storage_threshold" {
  description = "Minimum free storage space for RDS (bytes). Default: 10GB"
  type        = number
  default     = 10737418240 # 10 GB in bytes
}

variable "cache_hit_rate_threshold" {
  description = "Minimum cache hit rate threshold for Redis (%)"
  type        = number
  default     = 70
}

variable "redis_cpu_threshold" {
  description = "CPU utilization threshold for Redis alarms (%)"
  type        = number
  default     = 70
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
