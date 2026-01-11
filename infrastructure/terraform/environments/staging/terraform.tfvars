# Staging Environment Configuration
# Copy this file to terraform.tfvars and fill in the values

aws_region = "ap-southeast-2"

# Database password - RDS-compatible (no /, @, ", or space characters)
# Generated with: openssl rand -base64 32 | tr -d '/+=' | head -c 32
master_password = "8Zm2bz5rKnoex3Ybd15SfuC8T1R5pP3U"

# Domain configuration - Update with your actual domains
domain               = "staging.ohmycoins.com"
backend_domain       = "api.staging.ohmycoins.com"
frontend_host        = "https://dashboard.staging.ohmycoins.com"
backend_cors_origins = "https://dashboard.staging.ohmycoins.com,http://localhost:5173"

# ACM Certificate ARN for HTTPS (leave empty for HTTP only)
# certificate_arn = "arn:aws:acm:ap-southeast-2:ACCOUNT_ID:certificate/CERT_ID"

# GitHub configuration
github_repo                 = "MarkLimmage/ohmycoins"
create_github_oidc_provider = true

# Container images
backend_image      = "220711411889.dkr.ecr.ap-southeast-2.amazonaws.com/omc-backend"
backend_image_tag  = "latest"
frontend_image     = "ghcr.io/marklimmage/ohmycoins-frontend"
frontend_image_tag = "latest"
