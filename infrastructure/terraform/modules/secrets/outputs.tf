# Outputs for Secrets Module

output "secret_id" {
  description = "ID of the secret"
  value       = aws_secretsmanager_secret.app_secrets.id
}

output "secret_arn" {
  description = "ARN of the secret"
  value       = aws_secretsmanager_secret.app_secrets.arn
}

output "secret_name" {
  description = "Name of the secret"
  value       = aws_secretsmanager_secret.app_secrets.name
}

output "iam_policy_arn" {
  description = "ARN of the IAM policy for accessing the secret (if created)"
  value       = var.create_iam_policy ? aws_iam_policy.secrets_access[0].arn : null
}

output "iam_policy_name" {
  description = "Name of the IAM policy for accessing the secret (if created)"
  value       = var.create_iam_policy ? aws_iam_policy.secrets_access[0].name : null
}
