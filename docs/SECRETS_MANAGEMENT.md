# Secrets Management Guide

This guide explains how secrets are managed across different environments in the Oh My Coins platform.

## Overview

The OMC platform uses different secrets management strategies depending on the environment:

- **Local Development:** Secrets stored in `.env` file (not committed to git)
- **Staging/Production:** Secrets stored in AWS Secrets Manager and injected by ECS

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Environment: LOCAL                                           │
├─────────────────────────────────────────────────────────────┤
│ .env file → Environment Variables → Application Settings    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Environment: STAGING / PRODUCTION                            │
├─────────────────────────────────────────────────────────────┤
│ AWS Secrets Manager → ECS Task Definition →                 │
│ Environment Variables → Application Settings                │
└─────────────────────────────────────────────────────────────┘
```

## Local Development Setup

### 1. Create Your Environment File

Copy the template to create your local `.env` file:

```bash
cp .env.template .env
```

### 2. Configure Required Secrets

Edit the `.env` file and set the following **required** variables:

```bash
# JWT secret key - Generate with: openssl rand -hex 32
SECRET_KEY=your-secret-key-here

# Database password - Generate with: openssl rand -base64 32
POSTGRES_PASSWORD=your-postgres-password

# Superuser credentials
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=your-admin-password

# AI Agent API Key - Get from: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### 3. Configure Optional Secrets

For full functionality, also configure:

```bash
# Email (optional - leave empty to disable emails)
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Error tracking (optional)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

### 4. Security Best Practices

- ✅ **DO** use strong, randomly generated passwords
- ✅ **DO** use different passwords for each environment
- ✅ **DO** keep your `.env` file secure (chmod 600)
- ✅ **DO** use app-specific passwords for SMTP
- ❌ **DON'T** commit `.env` to git (it's in `.gitignore`)
- ❌ **DON'T** share your `.env` file
- ❌ **DON'T** use production secrets in development

### 5. Verify Configuration

Start the application to verify your configuration:

```bash
docker compose up -d
```

Check the backend logs for any configuration errors:

```bash
docker compose logs backend
```

---

## AWS Secrets Manager (Staging/Production)

### Architecture

In AWS environments, secrets are managed through AWS Secrets Manager:

1. **Terraform** creates and manages secrets in AWS Secrets Manager
2. **ECS Task Definitions** reference secrets using ARNs
3. **ECS** injects secrets as environment variables at container startup
4. **Application** reads secrets from environment variables (same as local)

### Secrets Storage

Secrets are stored in JSON format in AWS Secrets Manager:

```json
{
  "SECRET_KEY": "...",
  "POSTGRES_PASSWORD": "...",
  "OPENAI_API_KEY": "sk-...",
  "FIRST_SUPERUSER": "admin@example.com",
  "FIRST_SUPERUSER_PASSWORD": "...",
  "SMTP_HOST": "smtp.gmail.com",
  "SMTP_USER": "...",
  "SMTP_PASSWORD": "...",
  "SENTRY_DSN": "..."
}
```

### Initial Configuration

When deploying to a new environment, the secrets are created with temporary placeholder values:

```bash
cd infrastructure/terraform/environments/staging
terraform apply
```

This creates the secret: `ohmycoins-staging-app-secrets`

### Updating Secrets

**Method 1: AWS Console**

1. Go to AWS Secrets Manager in the AWS Console
2. Find `ohmycoins-staging-app-secrets` (or production variant)
3. Click "Retrieve secret value"
4. Click "Edit"
5. Update the JSON with actual secret values
6. Click "Save"

**Method 2: AWS CLI**

Create a file `secrets.json` with your secret values:

```json
{
  "SECRET_KEY": "actual-secret-key",
  "POSTGRES_PASSWORD": "actual-password",
  "OPENAI_API_KEY": "sk-actual-key",
  "FIRST_SUPERUSER": "admin@ohmycoins.com",
  "FIRST_SUPERUSER_PASSWORD": "actual-admin-password",
  "SMTP_HOST": "smtp.gmail.com",
  "SMTP_USER": "noreply@ohmycoins.com",
  "SMTP_PASSWORD": "actual-smtp-password",
  "SENTRY_DSN": "https://actual-sentry-dsn@sentry.io/project"
}
```

Update the secret:

```bash
aws secretsmanager put-secret-value \
  --secret-id ohmycoins-staging-app-secrets \
  --secret-string file://secrets.json \
  --region ap-southeast-2
```

**Important:** Delete `secrets.json` after updating!

```bash
rm secrets.json
```

### Rotating Secrets

To rotate a secret:

1. Update the secret value in AWS Secrets Manager
2. Force a new ECS deployment to pick up the new value:

```bash
aws ecs update-service \
  --cluster ohmycoins-staging \
  --service backend \
  --force-new-deployment \
  --region ap-southeast-2
```

ECS will gracefully roll out new tasks with the updated secrets.

### Verifying Secrets in ECS

To verify secrets are being injected correctly:

1. **Check task definition:**

```bash
aws ecs describe-task-definition \
  --task-definition ohmycoins-staging-backend \
  --region ap-southeast-2 \
  | jq '.taskDefinition.containerDefinitions[0].secrets'
```

2. **Check running task (if enabled):**

```bash
# Get task ID
TASK_ID=$(aws ecs list-tasks \
  --cluster ohmycoins-staging \
  --service backend \
  --region ap-southeast-2 \
  | jq -r '.taskArns[0]' | cut -d'/' -f3)

# Execute command in task (requires enable_execute_command=true)
aws ecs execute-command \
  --cluster ohmycoins-staging \
  --task $TASK_ID \
  --container backend \
  --command "env | grep -E 'SECRET_KEY|OPENAI_API_KEY'" \
  --interactive \
  --region ap-southeast-2
```

---

## IAM Permissions

### ECS Task Execution Role

The ECS Task Execution Role needs permissions to read from Secrets Manager:

```json
{
  "Effect": "Allow",
  "Action": [
    "secretsmanager:GetSecretValue",
    "kms:Decrypt"
  ],
  "Resource": "arn:aws:secretsmanager:region:account:secret:*"
}
```

This is configured in `infrastructure/terraform/modules/iam/main.tf`.

### Application (ECS Task Role)

The application can also read secrets at runtime if needed:

```json
{
  "Effect": "Allow",
  "Action": [
    "secretsmanager:GetSecretValue"
  ],
  "Resource": "arn:aws:secretsmanager:region:account:secret:*"
}
```

---

## Adding New Secrets

To add a new secret to the application:

### 1. Update Application Code

Add the secret to `backend/app/core/config.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # New secret
    NEW_API_KEY: str | None = None
```

### 2. Update .env.template

Document the new secret in `.env.template`:

```bash
# New Service API Key
# Get your API key from: https://example.com/api-keys
NEW_API_KEY=<your-api-key-here>
```

### 3. Update ECS Task Definition

Add the secret to `infrastructure/terraform/modules/ecs/main.tf`:

```hcl
secrets = [
  # ... existing secrets ...
  {
    name      = "NEW_API_KEY"
    valueFrom = "${var.secrets_arn}:NEW_API_KEY::"
  }
]
```

### 4. Update Secrets Manager

Add the new secret to AWS Secrets Manager:

```bash
# Get current secrets
aws secretsmanager get-secret-value \
  --secret-id ohmycoins-staging-app-secrets \
  --region ap-southeast-2 \
  | jq -r '.SecretString' > secrets.json

# Edit secrets.json to add NEW_API_KEY

# Update secrets
aws secretsmanager put-secret-value \
  --secret-id ohmycoins-staging-app-secrets \
  --secret-string file://secrets.json \
  --region ap-southeast-2

# Clean up
rm secrets.json
```

### 5. Deploy Changes

Deploy the infrastructure and application updates:

```bash
# Deploy terraform changes
cd infrastructure/terraform/environments/staging
terraform apply

# Force ECS to deploy new task definition
aws ecs update-service \
  --cluster ohmycoins-staging \
  --service backend \
  --force-new-deployment \
  --region ap-southeast-2
```

---

## Troubleshooting

### Issue: Application can't read secrets

**Symptoms:**
- Application fails to start
- Logs show missing environment variables
- Secret values are empty

**Solutions:**

1. **Verify secret exists in Secrets Manager:**
   ```bash
   aws secretsmanager describe-secret \
     --secret-id ohmycoins-staging-app-secrets \
     --region ap-southeast-2
   ```

2. **Verify IAM permissions:**
   ```bash
   # Check task execution role has secretsmanager:GetSecretValue
   aws iam get-role-policy \
     --role-name ohmycoins-staging-ecs-task-execution-role \
     --policy-name ohmycoins-staging-ecs-task-execution-secrets-policy \
     --region ap-southeast-2
   ```

3. **Verify secrets in task definition:**
   ```bash
   aws ecs describe-task-definition \
     --task-definition ohmycoins-staging-backend \
     --region ap-southeast-2
   ```

### Issue: Secrets not updating after rotation

**Symptoms:**
- Updated secrets in Secrets Manager
- Application still using old values

**Solution:**

Force a new deployment to pick up updated secrets:

```bash
aws ecs update-service \
  --cluster ohmycoins-staging \
  --service backend \
  --force-new-deployment \
  --region ap-southeast-2
```

### Issue: Local development secrets not working

**Symptoms:**
- Application fails to start locally
- Missing environment variable errors

**Solutions:**

1. **Verify .env file exists:**
   ```bash
   ls -la .env
   ```

2. **Verify .env has required variables:**
   ```bash
   grep -E "SECRET_KEY|POSTGRES_PASSWORD|OPENAI_API_KEY" .env
   ```

3. **Verify environment is set to local:**
   ```bash
   grep "ENVIRONMENT=local" .env
   ```

---

## Security Best Practices

### 1. Secret Rotation

Rotate secrets regularly:

- **Production:** Every 90 days minimum
- **Staging:** Every 180 days or when compromised
- **Development:** Use different secrets than production

### 2. Access Control

Limit who can access secrets:

- Use AWS IAM policies to restrict access
- Enable CloudTrail logging for secret access
- Use separate secrets for staging and production
- Never share production secrets

### 3. Monitoring

Monitor secret access:

- Enable CloudTrail logging for Secrets Manager
- Set up CloudWatch alarms for unusual access patterns
- Review secret access logs regularly

### 4. Development Security

For local development:

- Use different API keys than production
- Use rate-limited or test-mode API keys when available
- Never commit `.env` files to git
- Use `.env.template` for documentation only

---

## References

- [AWS Secrets Manager Documentation](https://docs.aws.amazon.com/secretsmanager/)
- [ECS Task Definition Secrets](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/specifying-sensitive-data-secrets.html)
- [Terraform AWS Secrets Manager](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret)
- [Pydantic Settings Documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)

---

**Last Updated:** 2026-01-09
