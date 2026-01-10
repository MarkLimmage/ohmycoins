# Secrets Module for Oh My Coins
# Manages AWS Secrets Manager secrets for application configuration

# Create the secret in AWS Secrets Manager
resource "aws_secretsmanager_secret" "app_secrets" {
  name                    = var.secret_name
  description             = var.description
  recovery_window_in_days = var.recovery_window_in_days
  kms_key_id              = var.kms_key_id

  tags = merge(
    var.tags,
    {
      Name        = var.secret_name
      Environment = var.environment
    }
  )
}

# Store the initial secret values
# Note: In production, secret values should be updated separately
# using AWS CLI or console, not managed by Terraform
resource "aws_secretsmanager_secret_version" "app_secrets_version" {
  secret_id     = aws_secretsmanager_secret.app_secrets.id
  secret_string = var.secret_value

  lifecycle {
    ignore_changes = [secret_string]
  }
}

# IAM Policy for ECS Task Execution Role to access secrets
# This policy allows ECS tasks to retrieve secret values
resource "aws_iam_policy" "secrets_access" {
  count = var.create_iam_policy ? 1 : 0

  name        = "${var.secret_name}-access-policy"
  description = "Policy to allow ECS tasks to access ${var.secret_name}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = aws_secretsmanager_secret.app_secrets.arn
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt"
        ]
        Resource = var.kms_key_id != null ? var.kms_key_id : "*"
        Condition = {
          StringEquals = {
            "kms:ViaService" = "secretsmanager.${var.aws_region}.amazonaws.com"
          }
        }
      }
    ]
  })

  tags = var.tags
}
