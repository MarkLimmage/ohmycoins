variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "secrets_arns" {
  description = "List of ARNs for secrets that ECS tasks need access to"
  type        = list(string)
  default     = ["*"]
}

variable "create_github_actions_role" {
  description = "Create IAM role for GitHub Actions deployment"
  type        = bool
  default     = true
}

variable "create_github_oidc_provider" {
  description = "Create OIDC provider for GitHub Actions"
  type        = bool
  default     = true
}

variable "github_repo" {
  description = "GitHub repository in format 'owner/repo'"
  type        = string
  default     = ""
}

variable "github_oidc_provider_arn" {
  description = "ARN of existing GitHub OIDC provider (if create_github_oidc_provider is false)"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
