# Oh My Coins - Staging Environment
# This configuration creates a complete staging environment on AWS

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "ohmycoins-terraform-state"
    key            = "staging/terraform.tfstate"
    region         = "ap-southeast-2"
    dynamodb_table = "ohmycoins-terraform-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "Oh My Coins"
      Environment = "staging"
      ManagedBy   = "Terraform"
    }
  }
}

locals {
  project_name = "ohmycoins-staging"
  tags = {
    Project     = "Oh My Coins"
    Environment = "staging"
    ManagedBy   = "Terraform"
  }
}

# VPC Module
module "vpc" {
  source = "../../modules/vpc"

  project_name       = local.project_name
  aws_region         = var.aws_region
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones

  public_subnet_cidrs      = var.public_subnet_cidrs
  private_app_subnet_cidrs = var.private_app_subnet_cidrs
  private_db_subnet_cidrs  = var.private_db_subnet_cidrs

  enable_nat_gateway   = true
  single_nat_gateway   = true # Cost optimization for staging
  enable_flow_logs     = false
  enable_vpc_endpoints = false

  tags = local.tags
}

# Security Groups Module
module "security" {
  source = "../../modules/security"

  project_name            = local.project_name
  vpc_id                  = module.vpc.vpc_id
  management_cidr_blocks  = var.management_cidr_blocks

  tags = local.tags
}

# IAM Module
module "iam" {
  source = "../../modules/iam"

  project_name                = local.project_name
  secrets_arns                = [aws_secretsmanager_secret.app_secrets.arn]
  create_github_actions_role  = true
  create_github_oidc_provider = var.create_github_oidc_provider
  github_repo                 = var.github_repo
  github_oidc_provider_arn    = var.github_oidc_provider_arn

  tags = local.tags
}

# RDS Module
module "rds" {
  source = "../../modules/rds"

  project_name        = local.project_name
  subnet_ids          = module.vpc.private_db_subnet_ids
  security_group_ids  = [module.security.rds_security_group_id]

  engine_version      = var.rds_engine_version
  instance_class      = var.rds_instance_class
  allocated_storage   = var.rds_allocated_storage
  storage_type        = "gp3"

  database_name       = var.database_name
  master_username     = var.master_username
  master_password     = var.master_password

  multi_az                    = false # Single AZ for staging
  backup_retention_period     = 3     # Shorter retention for staging
  skip_final_snapshot         = true  # Can skip final snapshot for staging
  deletion_protection         = false # Allow deletion for staging
  apply_immediately           = true  # Apply changes immediately for staging
  performance_insights_enabled = false # Disable for cost savings

  tags = local.tags
}

# Redis Module
module "redis" {
  source = "../../modules/redis"

  project_name       = local.project_name
  subnet_ids         = module.vpc.private_db_subnet_ids
  security_group_ids = [module.security.redis_security_group_id]

  engine_version             = var.redis_engine_version
  node_type                  = var.redis_node_type
  num_cache_clusters         = 1 # Single node for staging
  multi_az_enabled           = false
  transit_encryption_enabled = false # Disable for simplicity in staging
  auth_token_enabled         = false
  apply_immediately          = true

  tags = local.tags
}

# ALB Module
module "alb" {
  source = "../../modules/alb"

  project_name        = local.project_name
  vpc_id              = module.vpc.vpc_id
  subnet_ids          = module.vpc.public_subnet_ids
  security_group_ids  = [module.security.alb_security_group_id]

  certificate_arn             = var.certificate_arn
  backend_domain              = var.backend_domain
  enable_deletion_protection  = false # Allow deletion for staging

  tags = local.tags
}

# ECS Module
module "ecs" {
  source = "../../modules/ecs"

  project_name            = local.project_name
  aws_region              = var.aws_region
  environment             = "staging"
  private_subnet_ids      = module.vpc.private_app_subnet_ids
  ecs_security_group_ids  = [module.security.ecs_security_group_id]

  task_execution_role_arn   = module.iam.ecs_task_execution_role_arn
  task_role_arn             = module.iam.ecs_task_role_arn
  backend_target_group_arn  = module.alb.backend_target_group_arn
  frontend_target_group_arn = module.alb.frontend_target_group_arn
  alb_listener_arn          = module.alb.http_listener_arn

  # Database configuration
  db_host = module.rds.db_instance_address
  db_port = module.rds.db_instance_port
  db_name = var.database_name
  db_user = var.master_username

  # Redis configuration
  redis_host = module.redis.primary_endpoint_address
  redis_port = 6379

  # Secrets
  secrets_arn = aws_secretsmanager_secret.app_secrets.arn

  # Domain configuration
  domain              = var.domain
  backend_domain      = var.backend_domain
  frontend_host       = var.frontend_host
  backend_cors_origins = var.backend_cors_origins

  # Container images
  backend_image      = var.backend_image
  backend_image_tag  = var.backend_image_tag
  frontend_image     = var.frontend_image
  frontend_image_tag = var.frontend_image_tag

  # Task resources (smaller for staging)
  backend_cpu      = 1024
  backend_memory   = 2048
  frontend_cpu     = 256
  frontend_memory  = 512

  # Service configuration
  backend_desired_count  = 1 # Single task for staging
  frontend_desired_count = 1
  enable_execute_command = true # Enable for debugging

  # Auto scaling
  enable_autoscaling     = false # Disable for staging
  backend_min_capacity   = 1
  backend_max_capacity   = 2

  # Logging
  log_retention_days       = 7
  enable_container_insights = false # Disable for cost savings

  tags = local.tags
}

# AWS Secrets Manager for application secrets
resource "aws_secretsmanager_secret" "app_secrets" {
  name                    = "${local.project_name}-app-secrets"
  description             = "Application secrets for Oh My Coins staging"
  recovery_window_in_days = 0 # No recovery window for staging to allow for quick re-creation.

  tags = local.tags
}

resource "aws_secretsmanager_secret_version" "app_secrets_initial_version" {
  secret_id     = aws_secretsmanager_secret.app_secrets.id
  secret_string = jsonencode({
    SECRET_KEY                 = "temporary-secret-key-please-update",
    FIRST_SUPERUSER            = "admin@example.com",
    FIRST_SUPERUSER_PASSWORD   = "temporary-password-please-update",
    POSTGRES_SERVER            = module.rds.db_instance_address,
    POSTGRES_PORT              = module.rds.db_instance_port,
    POSTGRES_DB                = module.rds.db_instance_name,
    POSTGRES_USER              = module.rds.db_instance_username,
    POSTGRES_PASSWORD          = module.rds.db_instance_password,
    SMTP_HOST                  = "",
    SMTP_USER                  = "",
    SMTP_PASSWORD              = "",
    EMAILS_FROM_EMAIL          = "noreply@${var.domain}",
    SMTP_TLS                   = "True",
    SMTP_SSL                   = "False",
    SMTP_PORT                  = "587",
    REDIS_HOST                 = module.redis.primary_endpoint_address,
    REDIS_PORT                 = module.redis.port,
    LLM_PROVIDER               = "openai",
    OPENAI_API_KEY             = "",
    OPENAI_MODEL               = "gpt-4-turbo-preview",
    SENTRY_DSN                 = "",
    ENVIRONMENT                = "staging",
    FRONTEND_HOST              = "http://${module.alb.alb_dns_name}"
  })

  lifecycle {
    ignore_changes = [secret_string]
  }
}

# Note: Secret values should be set manually or via a separate secure process
# Example AWS CLI command:
# aws secretsmanager put-secret-value \
#   --secret-id ohmycoins-staging-app-secrets \
#   --secret-string file://secrets.json
