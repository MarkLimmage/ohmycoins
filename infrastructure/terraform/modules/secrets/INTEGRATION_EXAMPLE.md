# Example: Using the Secrets Module in Staging Environment
# 
# This file shows how to refactor staging/main.tf to use the secrets module.
# Currently, staging/main.tf has inline secrets configuration (lines 217-256).
# 
# To migrate to using the module, replace the inline configuration with:

# Instead of:
# resource "aws_secretsmanager_secret" "app_secrets" { ... }
# resource "aws_secretsmanager_secret_version" "app_secrets_initial_version" { ... }

# Use the module:
module "app_secrets" {
  source = "../../modules/secrets"

  secret_name             = "${local.project_name}-app-secrets"
  description             = "Application secrets for Oh My Coins staging"
  environment             = "staging"
  aws_region              = var.aws_region
  recovery_window_in_days = 0 # No recovery window for staging

  secret_value = jsonencode({
    SECRET_KEY                 = "temporary-secret-key-please-update"
    FIRST_SUPERUSER            = "admin@example.com"
    FIRST_SUPERUSER_PASSWORD   = "temporary-password-please-update"
    POSTGRES_SERVER            = module.rds.db_instance_address
    POSTGRES_PORT              = module.rds.db_instance_port
    POSTGRES_DB                = module.rds.db_instance_name
    POSTGRES_USER              = module.rds.db_instance_username
    POSTGRES_PASSWORD          = module.rds.db_instance_password
    SMTP_HOST                  = ""
    SMTP_USER                  = ""
    SMTP_PASSWORD              = ""
    EMAILS_FROM_EMAIL          = "noreply@${var.domain}"
    SMTP_TLS                   = "True"
    SMTP_SSL                   = "False"
    SMTP_PORT                  = "587"
    REDIS_HOST                 = module.redis.primary_endpoint_address
    REDIS_PORT                 = module.redis.port
    LLM_PROVIDER               = "openai"
    OPENAI_API_KEY             = ""
    OPENAI_MODEL               = "gpt-4-turbo-preview"
    SENTRY_DSN                 = ""
    ENVIRONMENT                = "staging"
    FRONTEND_HOST              = "http://${module.alb.alb_dns_name}"
  })

  tags = local.tags
}

# Then update references from:
# aws_secretsmanager_secret.app_secrets.arn
# 
# To:
# module.app_secrets.secret_arn

# Example IAM module usage:
module "iam" {
  source = "../../modules/iam"

  project_name                = local.project_name
  secrets_arns                = [module.app_secrets.secret_arn]  # Updated reference
  create_github_actions_role  = true
  create_github_oidc_provider = var.create_github_oidc_provider
  github_repo                 = var.github_repo
  github_oidc_provider_arn    = var.github_oidc_provider_arn

  tags = local.tags
}

# Example ECS module usage:
module "ecs" {
  source = "../../modules/ecs"

  # ... other configuration ...
  
  secrets_arn = module.app_secrets.secret_arn  # Updated reference

  # ... rest of configuration ...
}

# Example outputs:
output "secrets_manager_arn" {
  description = "ARN of the application secrets in AWS Secrets Manager"
  value       = module.app_secrets.secret_arn  # Updated reference
  sensitive   = true
}

# Migration Steps:
# 1. Backup current state: terraform state pull > backup.tfstate
# 2. Comment out inline secret resources in main.tf (lines 217-256)
# 3. Add module configuration above
# 4. Update all references (4 locations in main.tf and outputs.tf)
# 5. Run: terraform plan -out=tfplan
# 6. Review plan to ensure no resource destruction
# 7. If satisfied: terraform apply tfplan
#
# Note: This may require terraform state manipulation to import existing secrets
# into the module. Use with caution in production environments.
