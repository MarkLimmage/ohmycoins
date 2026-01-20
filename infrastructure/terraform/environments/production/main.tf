# Oh My Coins - Production Environment
# This configuration creates a production-ready environment on AWS

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
    key            = "production/terraform.tfstate"
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
      Environment = "production"
      ManagedBy   = "Terraform"
    }
  }
}

locals {
  project_name = "ohmycoins-prod"
  tags = {
    Project     = "Oh My Coins"
    Environment = "production"
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

  enable_nat_gateway   = true  # Re-enabled for production deployment
  single_nat_gateway   = false # Multi-AZ for production (3 NAT gateways for high availability)
  enable_flow_logs     = true  # Enable for security
  enable_vpc_endpoints = false # Disabled with NAT gateways

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

  multi_az                    = true  # Multi-AZ for production
  backup_retention_period     = 7     # 7 days retention
  skip_final_snapshot         = false # Always take final snapshot
  deletion_protection         = true  # Prevent accidental deletion
  apply_immediately           = false # Apply during maintenance window
  performance_insights_enabled = true # Enable for monitoring

  create_read_replica         = var.create_read_replica
  replica_instance_class      = var.replica_instance_class

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
  num_cache_clusters         = 2 # Multi-node for production
  multi_az_enabled           = true
  transit_encryption_enabled = true
  auth_token_enabled         = var.redis_auth_token_enabled
  auth_token                 = var.redis_auth_token
  apply_immediately          = false

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
  enable_deletion_protection  = true # Enable for production

  tags = local.tags
}

# ECS Module
module "ecs" {
  source = "../../modules/ecs"

  project_name            = local.project_name
  aws_region              = var.aws_region
  environment             = "production"
  private_subnet_ids      = module.vpc.private_app_subnet_ids
  ecs_security_group_ids  = [module.security.ecs_security_group_id]

  task_execution_role_arn   = module.iam.ecs_task_execution_role_arn
  task_role_arn             = module.iam.ecs_task_role_arn
  backend_target_group_arn  = module.alb.backend_target_group_arn
  frontend_target_group_arn = module.alb.frontend_target_group_arn
  alb_listener_arn          = module.alb.https_listener_arn

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

  # Task resources (production-sized)
  backend_cpu      = 1024
  backend_memory   = 2048
  frontend_cpu     = 512
  frontend_memory  = 1024

  # Service configuration
  backend_desired_count  = 2 # Multiple tasks for redundancy
  frontend_desired_count = 2
  enable_execute_command = false # Disable for security

  # Auto scaling
  enable_autoscaling     = true
  backend_min_capacity   = 2
  backend_max_capacity   = 10

  # Logging
  log_retention_days       = 30 # Longer retention
  enable_container_insights = true

  tags = local.tags
}

# AWS Secrets Manager for application secrets
resource "aws_secretsmanager_secret" "app_secrets" {
  name                    = "${local.project_name}-app-secrets"
  description             = "Application secrets for Oh My Coins production"
  recovery_window_in_days = 30 # 30 days recovery for production

  tags = local.tags
}

# Note: Secret values should be set manually or via a separate secure process
# Example AWS CLI command:
# aws secretsmanager put-secret-value \
#   --secret-id ohmycoins-prod-app-secrets \
#   --secret-string file://secrets.json
