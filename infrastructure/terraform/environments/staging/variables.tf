variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-southeast-2"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["ap-southeast-2a", "ap-southeast-2b"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_app_subnet_cidrs" {
  description = "CIDR blocks for private application subnets"
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24"]
}

variable "private_db_subnet_cidrs" {
  description = "CIDR blocks for private database subnets"
  type        = list(string)
  default     = ["10.0.21.0/24", "10.0.22.0/24"]
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
  default     = "db.t3.micro"
}

variable "rds_allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 20
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

# Redis Configuration
variable "redis_engine_version" {
  description = "Redis engine version"
  type        = string
  default     = "7.0"
}

variable "redis_node_type" {
  description = "Redis node type"
  type        = string
  default     = "cache.t3.micro"
}

# Domain Configuration
variable "domain" {
  description = "Domain name for the application"
  type        = string
  default     = "staging.ohmycoins.com"
}

variable "backend_domain" {
  description = "Backend API domain"
  type        = string
  default     = "api.staging.ohmycoins.com"
}

variable "frontend_host" {
  description = "Frontend host URL"
  type        = string
  default     = "https://dashboard.staging.ohmycoins.com"
}

variable "backend_cors_origins" {
  description = "CORS origins for backend"
  type        = string
  default     = ""
}

variable "certificate_arn" {
  description = "ARN of ACM certificate for HTTPS"
  type        = string
  default     = ""
}

# Container Images
variable "backend_image" {
  description = "Backend Docker image"
  type        = string
  default     = "220711411889.dkr.ecr.ap-southeast-2.amazonaws.com/omc-backend"
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
  default     = true
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
