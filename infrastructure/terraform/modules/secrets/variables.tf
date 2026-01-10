# Variables for Secrets Module

variable "secret_name" {
  description = "Name of the secret in AWS Secrets Manager"
  type        = string
}

variable "description" {
  description = "Description of the secret"
  type        = string
  default     = "Application secrets managed by Terraform"
}

variable "secret_value" {
  description = "JSON string containing the secret values"
  type        = string
  sensitive   = true
}

variable "environment" {
  description = "Environment name (staging, production, etc.)"
  type        = string
}

variable "recovery_window_in_days" {
  description = "Number of days AWS Secrets Manager waits before deleting a secret (0-30)"
  type        = number
  default     = 30

  validation {
    condition     = var.recovery_window_in_days >= 0 && var.recovery_window_in_days <= 30
    error_message = "Recovery window must be between 0 and 30 days."
  }
}

variable "kms_key_id" {
  description = "KMS key ID for encrypting the secret (uses AWS managed key if not specified)"
  type        = string
  default     = null
}

variable "aws_region" {
  description = "AWS region where resources will be created"
  type        = string
}

variable "create_iam_policy" {
  description = "Whether to create an IAM policy for accessing this secret"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
