# Production Environment Configuration
# Oh My Coins - Production Infrastructure
# Last Updated: 2025-11-20
# Environment: Production
# Region: ap-southeast-2 (Sydney)

# =============================================================================
# AWS Configuration
# =============================================================================
aws_region = "ap-southeast-2"

# VPC Configuration - Production uses separate CIDR from staging
vpc_cidr = "10.0.0.0/16"

# Subnet CIDRs - Multi-AZ for high availability
public_subnet_cidrs      = ["10.0.1.0/24", "10.0.2.0/24"]
private_app_subnet_cidrs = ["10.0.11.0/24", "10.0.12.0/24"]
private_db_subnet_cidrs  = ["10.0.21.0/24", "10.0.22.0/24"]

# =============================================================================
# Security Configuration
# =============================================================================

# Database password - MUST BE CHANGED BEFORE DEPLOYMENT!
# SECURITY WARNING: Never commit actual passwords to version control!
# 
# Option 1 (Recommended): Use Terraform's manage_master_user_password feature
#   Remove this variable and use AWS Secrets Manager automatic management
#
# Option 2: Reference AWS Secrets Manager ARN
#   master_password = "{{resolve:secretsmanager:prod/db/password:SecretString:password}}"
#
# Option 3: Use environment variable
#   export TF_VAR_master_password=$(aws secretsmanager get-secret-value --secret-id prod/db/password --query SecretString --output text)
#
# For initial setup, generate with: openssl rand -base64 32
master_password = "CHANGE_ME_BEFORE_DEPLOYMENT"

# Redis authentication - Same security considerations as above
redis_auth_token_enabled = true
redis_auth_token         = "CHANGE_ME_BEFORE_DEPLOYMENT"

# =============================================================================
# Domain Configuration
# =============================================================================
domain              = "ohmycoins.com"
backend_domain      = "api.ohmycoins.com"
frontend_host       = "https://dashboard.ohmycoins.com"
backend_cors_origins = "https://dashboard.ohmycoins.com"

# ACM Certificate ARN for HTTPS
# IMPORTANT: This must be updated with the actual certificate ARN before deployment
# The certificate should be requested through AWS Certificate Manager before deployment
# The certificate must cover: ohmycoins.com, *.ohmycoins.com
# 
# To request certificate:
#   aws acm request-certificate \
#     --domain-name ohmycoins.com \
#     --subject-alternative-names *.ohmycoins.com \
#     --validation-method DNS \
#     --region ap-southeast-2
#
# Replace PRODUCTION_CERT_ID below with the actual certificate ID from the ARN
certificate_arn = "arn:aws:acm:ap-southeast-2:220711411889:certificate/PRODUCTION_CERT_ID"

# =============================================================================
# GitHub Actions Configuration
# =============================================================================
github_repo                = "MarkLimmage/ohmycoins"
# OIDC provider should already exist from staging deployment
create_github_oidc_provider = false
github_oidc_provider_arn    = "arn:aws:iam::220711411889:oidc-provider/token.actions.githubusercontent.com"

# =============================================================================
# Container Images
# =============================================================================
# Production MUST use specific version tags, never "latest"
backend_image      = "ghcr.io/marklimmage/ohmycoins-backend"
backend_image_tag  = "v1.0.0"  # IMPORTANT: Update to actual release version
frontend_image     = "ghcr.io/marklimmage/ohmycoins-frontend"
frontend_image_tag = "v1.0.0"  # IMPORTANT: Update to actual release version

# =============================================================================
# Database Configuration (Production-Grade)
# =============================================================================

# RDS Instance Configuration
rds_instance_class    = "db.t3.small"   # Upgrade to db.t3.medium for higher load
rds_allocated_storage = 100             # 100GB for production data
rds_max_allocated_storage = 500         # Auto-scaling up to 500GB

# Multi-AZ for high availability
multi_az = true

# Backup Configuration
backup_retention_period = 30            # 30 days for compliance
backup_window          = "03:00-04:00"  # 3-4 AM AEST (low traffic period)
maintenance_window     = "sun:05:00-sun:06:00"  # Sunday 5-6 AM AEST

# Read Replica (optional, for read-heavy workloads)
create_read_replica   = false           # Set to true if needed
replica_instance_class = "db.t3.small"

# Enhanced Monitoring
performance_insights_enabled = true
monitoring_interval         = 60        # 60 seconds

# =============================================================================
# Redis Configuration (Production-Grade)
# =============================================================================

# ElastiCache Node Type
redis_node_type = "cache.t3.small"      # Upgrade to cache.t3.medium for higher load

# Number of cache nodes (replicas)
redis_num_cache_nodes = 2               # 1 primary + 1 replica

# Automatic failover for Multi-AZ
automatic_failover_enabled = true
multi_az_enabled          = true

# Backup Configuration
redis_snapshot_retention_limit = 7      # 7 days of snapshots
redis_snapshot_window         = "04:00-05:00"  # 4-5 AM AEST

# =============================================================================
# ECS Configuration
# =============================================================================

# Task Configuration
backend_cpu    = 1024   # 1 vCPU
backend_memory = 2048   # 2GB RAM

frontend_cpu    = 512   # 0.5 vCPU
frontend_memory = 1024  # 1GB RAM

# Auto-scaling Configuration
backend_desired_count  = 2    # Start with 2 tasks
backend_min_capacity   = 2    # Minimum 2 for high availability
backend_max_capacity   = 10   # Scale up to 10 under load

frontend_desired_count = 2
frontend_min_capacity  = 2
frontend_max_capacity  = 5

# =============================================================================
# ALB Configuration
# =============================================================================

# Deletion protection for production
deletion_protection = true

# Access logs (recommended for production)
enable_alb_access_logs = true
alb_access_logs_bucket = "ohmycoins-prod-alb-logs"  # IMPORTANT: Create this bucket before deployment
                                                     # See pre-deployment checklist for bucket creation steps
                                                     # The bucket must exist in the same region (ap-southeast-2)

# =============================================================================
# CloudWatch Configuration
# =============================================================================

# Log retention
log_retention_days = 90  # 90 days for production

# Container Insights
enable_container_insights = true

# =============================================================================
# Tags
# =============================================================================

# Resource tagging for cost allocation and management
tags = {
  Environment = "production"
  Project     = "ohmycoins"
  ManagedBy   = "terraform"
  CostCenter  = "trading-platform"
  Compliance  = "required"
}

# =============================================================================
# Disaster Recovery Configuration
# =============================================================================

# Enable deletion protection for critical resources
enable_deletion_protection = true

# Enable cross-region backup replication (optional)
enable_cross_region_backup = false
backup_replication_region  = "us-west-2"  # Set if enabling cross-region backup

# =============================================================================
# Security Hardening
# =============================================================================

# Enable encryption for all resources
enable_encryption = true

# Enable VPC Flow Logs for security monitoring
enable_vpc_flow_logs = true
flow_logs_retention  = 30  # 30 days

# =============================================================================
# NOTES FOR DEPLOYMENT
# =============================================================================
# 
# BEFORE DEPLOYING TO PRODUCTION:
# 
# 1. Update ALL passwords and tokens with strong, randomly generated values
#    - Use: openssl rand -base64 32
#    - Store in AWS Secrets Manager
#    - Reference them in this file
# 
# 2. Request ACM certificate for ohmycoins.com and *.ohmycoins.com
#    - Update certificate_arn with actual ARN
# 
# 3. Create S3 bucket for ALB access logs
#    - Bucket name: ohmycoins-prod-alb-logs
#    - Enable server-side encryption
#    - Configure lifecycle policies
# 
# 4. Configure Route53 DNS
#    - Create hosted zone for ohmycoins.com
#    - Update NS records with your domain registrar
# 
# 5. Review and adjust resource sizes based on expected load
#    - Consider db.t3.medium or larger for database
#    - Consider cache.t3.medium or larger for Redis
#    - Adjust ECS task sizes based on performance testing
# 
# 6. Enable AWS Config, GuardDuty, and CloudTrail
#    - See SECURITY_HARDENING.md for details
# 
# 7. Review OPERATIONS_RUNBOOK.md for operational procedures
# 
# 8. Test disaster recovery procedures before go-live
#    - Database restore from backup
#    - Infrastructure recreation from Terraform
# 
# =============================================================================
