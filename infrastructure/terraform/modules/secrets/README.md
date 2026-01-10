# Secrets Module

This module manages AWS Secrets Manager secrets for the Oh My Coins application.

## Features

- Creates secrets in AWS Secrets Manager with KMS encryption
- Supports custom recovery windows (0-30 days)
- Optional IAM policy creation for ECS task access
- Lifecycle management to prevent secret value overwrites

## Usage

```hcl
module "app_secrets" {
  source = "../../modules/secrets"

  secret_name             = "ohmycoins-staging-app-secrets"
  description             = "Application secrets for Oh My Coins staging"
  environment             = "staging"
  aws_region              = "ap-southeast-2"
  recovery_window_in_days = 7
  
  secret_value = jsonencode({
    SECRET_KEY                 = var.secret_key
    OPENAI_API_KEY             = var.openai_api_key
    POSTGRES_PASSWORD          = var.postgres_password
    FIRST_SUPERUSER            = var.first_superuser
    FIRST_SUPERUSER_PASSWORD   = var.first_superuser_password
    # Add more secrets as needed
  })

  tags = {
    Project     = "Oh My Coins"
    Environment = "staging"
    ManagedBy   = "Terraform"
  }
}
```

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| secret_name | Name of the secret in AWS Secrets Manager | `string` | n/a | yes |
| description | Description of the secret | `string` | `"Application secrets managed by Terraform"` | no |
| secret_value | JSON string containing the secret values | `string` | n/a | yes |
| environment | Environment name (staging, production, etc.) | `string` | n/a | yes |
| recovery_window_in_days | Number of days AWS Secrets Manager waits before deleting (0-30) | `number` | `30` | no |
| kms_key_id | KMS key ID for encryption (uses AWS managed key if not specified) | `string` | `null` | no |
| aws_region | AWS region where resources will be created | `string` | n/a | yes |
| create_iam_policy | Whether to create an IAM policy for accessing this secret | `bool` | `true` | no |
| tags | Tags to apply to all resources | `map(string)` | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| secret_id | ID of the secret |
| secret_arn | ARN of the secret |
| secret_name | Name of the secret |
| iam_policy_arn | ARN of the IAM policy for accessing the secret (if created) |
| iam_policy_name | Name of the IAM policy for accessing the secret (if created) |

## Security Best Practices

1. **Never commit secret values to version control**
   - Use Terraform variables or external secret management tools
   - Leverage lifecycle `ignore_changes` to prevent overwriting secrets

2. **Update secrets outside of Terraform**
   ```bash
   aws secretsmanager put-secret-value \
     --secret-id ohmycoins-staging-app-secrets \
     --secret-string file://secrets.json
   ```

3. **Use KMS encryption** (recommended for production)
   ```hcl
   kms_key_id = "arn:aws:kms:region:account:key/key-id"
   ```

4. **Set appropriate recovery windows**
   - Staging: 0-7 days (faster iteration)
   - Production: 30 days (safety net)

5. **Restrict IAM access**
   - Only grant `secretsmanager:GetSecretValue` to services that need it
   - Use resource-level permissions

## ECS Integration

This module is designed to work seamlessly with the ECS module. The secret ARN can be passed to ECS tasks:

```hcl
module "ecs" {
  source = "../../modules/ecs"
  
  secrets_arn = module.app_secrets.secret_arn
  # ... other variables
}
```

ECS task definitions will automatically inject secrets as environment variables using the format:
```json
{
  "secrets": [
    {
      "name": "OPENAI_API_KEY",
      "valueFrom": "arn:aws:secretsmanager:region:account:secret:name:OPENAI_API_KEY::"
    }
  ]
}
```

## Rotation

This module does not currently support automatic secret rotation. To implement rotation:

1. Enable automatic rotation in AWS console or using AWS CLI
2. Create a Lambda function for rotation logic
3. Configure rotation schedule

## Examples

### Staging Environment (Quick Deletion)
```hcl
module "staging_secrets" {
  source = "../../modules/secrets"

  secret_name             = "ohmycoins-staging-app-secrets"
  environment             = "staging"
  aws_region              = "ap-southeast-2"
  recovery_window_in_days = 0  # Immediate deletion for staging
  
  secret_value = jsonencode({
    OPENAI_API_KEY = var.staging_openai_key
  })
}
```

### Production Environment (With KMS and Recovery)
```hcl
module "production_secrets" {
  source = "../../modules/secrets"

  secret_name             = "ohmycoins-production-app-secrets"
  environment             = "production"
  aws_region              = "ap-southeast-2"
  recovery_window_in_days = 30  # 30-day recovery for production
  kms_key_id              = aws_kms_key.production.id
  
  secret_value = jsonencode({
    OPENAI_API_KEY = var.production_openai_key
  })
}
```

## Troubleshooting

### Secret Already Exists Error
If you get "already exists" error after deletion:
- Check if secret is in deletion pending state
- Wait for recovery window to expire, or
- Use AWS CLI to force deletion: `aws secretsmanager delete-secret --secret-id <name> --force-delete-without-recovery`

### KMS Access Denied
Ensure the ECS task execution role has `kms:Decrypt` permission for the KMS key used to encrypt secrets.

### Secret Values Not Updating
Remember that `lifecycle.ignore_changes` prevents Terraform from overwriting secrets. Update secrets using AWS CLI or console.
