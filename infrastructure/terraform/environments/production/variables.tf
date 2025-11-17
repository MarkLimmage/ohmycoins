# Production environment variables
# Values configured for production workloads with high availability and security

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-southeast-2"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.1.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["ap-southeast-2a", "ap-southeast-2b", "ap-southeast-2c"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.1.1.0/24", "10.1.2.0/24", "10.1.3.0/24"]
}

variable "private_app_subnet_cidrs" {
  description = "CIDR blocks for private application subnets"
  type        = list(string)
  default     = ["10.1.11.0/24", "10.1.12.0/24", "10.1.13.0/24"]
}

variable "private_db_subnet_cidrs" {
  description = "CIDR blocks for private database subnets"
  type        = list(string)
  default     = ["10.1.21.0/24", "10.1.22.0/24", "10.1.23.0/24"]
}

variable "management_cidr_blocks" {
  description = "CIDR blocks allowed to access RDS for management"
  type        = list(string)
  default     = []
}

# RDS Configuration
variable "rds_engine_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "17.2"
}

variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.small"
}

variable "rds_allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 50
}

variable "database_name" {
  description = "Name of the database"
  type        = string
  default     = "app"
}

variable "master_username" {
  description = "Master username for the database"
  type        = string
  default     = "postgres"
}

variable "master_password" {
  description = "Master password for the database"
  type        = string
  sensitive   = true
}

variable "create_read_replica" {
  description = "Create read replica for RDS"
  type        = bool
  default     = false
}

variable "replica_instance_class" {
  description = "Instance class for read replica"
  type        = string
  default     = "db.t3.small"
}

# Redis Configuration
variable "redis_engine_version" {
  description = "Redis engine version"
  type        = string
  default     = "7.0"
}

variable "redis_node_type" {
  description = "Redis node type"
  type        = string
  default     = "cache.t3.small"
}

variable "redis_auth_token_enabled" {
  description = "Enable auth token for Redis"
  type        = bool
  default     = true
}

variable "redis_auth_token" {
  description = "Auth token for Redis"
  type        = string
  sensitive   = true
  default     = ""
}

# Domain Configuration
variable "domain" {
  description = "Domain name for the application"
  type        = string
  default     = "ohmycoins.com"
}

variable "backend_domain" {
  description = "Backend API domain"
  type        = string
  default     = "api.ohmycoins.com"
}

variable "frontend_host" {
  description = "Frontend host URL"
  type        = string
  default     = "https://dashboard.ohmycoins.com"
}

variable "backend_cors_origins" {
  description = "CORS origins for backend"
  type        = string
  default     = ""
}

variable "certificate_arn" {
  description = "ARN of ACM certificate for HTTPS (REQUIRED for production)"
  type        = string
}

# Container Images
variable "backend_image" {
  description = "Backend Docker image"
  type        = string
  default     = "ghcr.io/marklimmage/ohmycoins-backend"
}

variable "backend_image_tag" {
  description = "Backend Docker image tag"
  type        = string
  default     = "latest"
}

variable "frontend_image" {
  description = "Frontend Docker image"
  type        = string
  default     = "ghcr.io/marklimmage/ohmycoins-frontend"
}

variable "frontend_image_tag" {
  description = "Frontend Docker image tag"
  type        = string
  default     = "latest"
}

# GitHub Actions
variable "create_github_oidc_provider" {
  description = "Create GitHub OIDC provider (set to false if already exists)"
  type        = bool
  default     = false
}

variable "github_repo" {
  description = "GitHub repository in format 'owner/repo'"
  type        = string
  default     = "MarkLimmage/ohmycoins"
}

variable "github_oidc_provider_arn" {
  description = "ARN of existing GitHub OIDC provider"
  type        = string
  default     = ""
}
