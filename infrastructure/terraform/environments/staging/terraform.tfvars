# Staging Environment Configuration
# Updated by setup-ssl-dns.sh on Sun Jan 11 22:39:21 AEDT 2026

aws_region = "ap-southeast-2"

# Database password - RDS-compatible (no /, @, ", or space characters)
master_password = "8Zm2bz5rKnoex3Ybd15SfuC8T1R5pP3U"

# Domain configuration - Using custom domain with SSL
domain               = "staging.ohmycoins.com"
backend_domain       = "api.staging.ohmycoins.com"
frontend_host        = "https://dashboard.staging.ohmycoins.com"
backend_cors_origins = "https://dashboard.staging.ohmycoins.com,http://localhost:5173"

# ACM Certificate ARN for HTTPS
certificate_arn = "arn:aws:acm:ap-southeast-2:220711411889:certificate/8ac367f3-94cf-4aac-8fa9-10e037951521"

# GitHub configuration
github_repo                 = "MarkLimmage/ohmycoins"
create_github_oidc_provider = true

# Container images
backend_image      = "220711411889.dkr.ecr.ap-southeast-2.amazonaws.com/omc-backend"
backend_image_tag  = "latest"
frontend_image     = "ghcr.io/marklimmage/ohmycoins-frontend"
frontend_image_tag = "latest"
