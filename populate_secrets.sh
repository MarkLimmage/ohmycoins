#!/bin/bash

# Exit on any error
set -e

# Define static values from the .env file
SECRET_KEY='yHimxsRpn9K8GGPQ'
FIRST_SUPERUSER='admin@example.com'
FIRST_SUPERUSER_PASSWORD='yJp0m7zdwWbVNVUD'
SMTP_HOST=''
SMTP_USER=''
SMTP_PASSWORD=''
EMAILS_FROM_EMAIL='info@example.com'
SMTP_TLS='True'
SMTP_SSL='False'
SMTP_PORT='587'
LLM_PROVIDER='openai'
OPENAI_API_KEY=''
OPENAI_MODEL='gpt-4-turbo-preview'
SENTRY_DSN=''

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
TERRAFORM_DIR="$SCRIPT_DIR/infrastructure/terraform/environments/staging"

# Retrieve dynamic values from Terraform
DB_HOST=$(cd "$TERRAFORM_DIR" && terraform output -raw rds_endpoint | cut -d: -f1)
DB_PORT=$(cd "$TERRAFORM_DIR" && terraform output -raw rds_endpoint | cut -d: -f2)
DB_USER=$(cd "$TERRAFORM_DIR" && terraform output -raw rds_username)
DB_PASSWORD=$(cd "$TERRAFORM_DIR" && terraform output -raw rds_password)
DB_NAME=$(cd "$TERRAFORM_DIR" && terraform output -raw rds_db_name)
REDIS_HOST=$(cd "$TERRAFORM_DIR" && terraform output -raw redis_endpoint | cut -d: -f1)
REDIS_PORT=$(cd "$TERRAFORM_DIR" && terraform output -raw redis_endpoint | cut -d: -f2)
ALB_DNS_NAME=$(cd "$TERRAFORM_DIR" && terraform output -raw alb_dns_name)


# Construct the JSON string safely
SECRET_STRING=$(printf '{
  "SECRET_KEY": "%s",
  "FIRST_SUPERUSER": "%s",
  "FIRST_SUPERUSER_PASSWORD": "%s",
  "SMTP_HOST": "%s",
  "SMTP_USER": "%s",
  "SMTP_PASSWORD": "%s",
  "EMAILS_FROM_EMAIL": "%s",
  "SMTP_TLS": "%s",
  "SMTP_SSL": "%s",
  "SMTP_PORT": "%s",
  "POSTGRES_SERVER": "%s",
  "POSTGRES_PORT": "%s",
  "POSTGRES_USER": "%s",
  "POSTGRES_PASSWORD": "%s",
  "POSTGRES_DB": "%s",
  "REDIS_HOST": "%s",
  "REDIS_PORT": "%s",
  "LLM_PROVIDER": "%s",
  "OPENAI_API_KEY": "%s",
  "OPENAI_MODEL": "%s",
  "SENTRY_DSN": "%s",
  "ENVIRONMENT": "staging",
  "FRONTEND_HOST": "http://%s"
}' \
"$SECRET_KEY" \
"$FIRST_SUPERUSER" \
"$FIRST_SUPERUSER_PASSWORD" \
"$SMTP_HOST" \
"$SMTP_USER" \
"$SMTP_PASSWORD" \
"$EMAILS_FROM_EMAIL" \
"$SMTP_TLS" \
"$SMTP_SSL" \
"$SMTP_PORT" \
"$DB_HOST" \
"$DB_PORT" \
"$DB_USER" \
"$DB_PASSWORD" \
"$DB_NAME" \
"$REDIS_HOST" \
"$REDIS_PORT" \
"$LLM_PROVIDER" \
"$OPENAI_API_KEY" \
"$OPENAI_MODEL" \
"$SENTRY_DSN" \
"$ALB_DNS_NAME" \
)

echo "Updating secret..."
# Update the secret in AWS
aws secretsmanager put-secret-value --secret-id ohmycoins-staging-app-secrets --secret-string "$SECRET_STRING"

echo "Forcing new service deployment..."
# Force a new deployment of the backend service
aws ecs update-service --cluster ohmycoins-staging-cluster --service ohmycoins-staging-backend --force-new-deployment

echo "Secret populated and service restarted successfully."
