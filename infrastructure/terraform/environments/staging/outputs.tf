output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "alb_dns_name" {
  description = "DNS name of the ALB"
  value       = module.alb.alb_dns_name
}

output "db_endpoint" {
  description = "RDS endpoint"
  value       = module.rds.db_instance_endpoint
}

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = module.redis.primary_endpoint_address
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = module.ecs.cluster_name
}

output "backend_service_name" {
  description = "Name of the backend ECS service"
  value       = module.ecs.backend_service_name
}

output "frontend_service_name" {
  description = "Name of the frontend ECS service"
  value       = module.ecs.frontend_service_name
}

output "github_actions_role_arn" {
  description = "ARN of the GitHub Actions deployment role"
  value       = module.iam.github_actions_role_arn
}

output "secrets_manager_secret_arn" {
  description = "ARN of the Secrets Manager secret"
  value       = aws_secretsmanager_secret.app_secrets.arn
}

output "rds_endpoint" {
  description = "Connection endpoint for the RDS instance"
  value       = module.rds.db_instance_endpoint
}

output "rds_username" {
  description = "Username for the RDS database"
  value       = module.rds.db_instance_username
  sensitive   = true
}

output "rds_password" {
  description = "Password for the RDS database"
  value       = module.rds.db_instance_password
  sensitive   = true
}

output "rds_db_name" {
  description = "Name of the RDS database"
  value       = module.rds.db_instance_name
}
