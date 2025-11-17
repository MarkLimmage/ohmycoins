output "replication_group_id" {
  description = "ID of the Redis replication group"
  value       = aws_elasticache_replication_group.main.id
}

output "replication_group_arn" {
  description = "ARN of the Redis replication group"
  value       = aws_elasticache_replication_group.main.arn
}

output "primary_endpoint_address" {
  description = "Primary endpoint address"
  value       = aws_elasticache_replication_group.main.primary_endpoint_address
}

output "reader_endpoint_address" {
  description = "Reader endpoint address (for read replicas)"
  value       = aws_elasticache_replication_group.main.reader_endpoint_address
}

output "port" {
  description = "Redis port"
  value       = 6379
}

output "subnet_group_name" {
  description = "Name of the Redis subnet group"
  value       = aws_elasticache_subnet_group.main.name
}
