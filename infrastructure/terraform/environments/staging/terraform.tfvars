# Staging Environment Configuration
# Copy this file to terraform.tfvars and fill in the values

aws_region = "ap-southeast-2"
vpc_cidr = "10.1.0.0/16"

# Subnet CIDRs
public_subnet_cidrs      = ["10.1.1.0/24", "10.1.2.0/24"]
private_app_subnet_cidrs = ["10.1.11.0/24", "10.1.12.0/24"]
private_db_subnet_cidrs  = ["10.1.21.0/24", "10.1.22.0/24"]

# Database password - CHANGE THIS!
master_password = "wAPXmk9gqyG3"

# Domain configuration - Update with your actual domains
domain              = "staging.ohmycoins.com"
backend_domain      = "api.staging.ohmycoins.com"
frontend_host       = "https://dashboard.staging.ohmycoins.com"
backend_cors_origins = "https://dashboard.staging.ohmycoins.com,http://localhost:5173"

# ACM Certificate ARN for HTTPS (leave empty for HTTP only)
certificate_arn = "arn:aws:acm:ap-southeast-2:220711411889:certificate/08b74575-c6dc-4268-b055-3e0f77c4d55e"

# GitHub configuration
github_repo                = "MarkLimmage/ohmycoins"
create_github_oidc_provider = true

# Container images
backend_image      = "ghcr.io/marklimmage/ohmycoins-backend"
backend_image_tag  = "latest"
frontend_image     = "ghcr.io/marklimmage/ohmycoins-frontend"
frontend_image_tag = "latest"
