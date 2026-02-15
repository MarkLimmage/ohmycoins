# Secrets Management Guide

This guide explains how secrets are managed across different environments in the Oh My Coins platform.

## Overview

The OMC platform uses different secrets management strategies depending on the environment:

- **Local Development:** Secrets stored in `.env` file (not committed to git)
- **Local Server (Production):** Secrets stored in `.env` file manually placed on the server.
- **Legacy (AWS):** Secrets stored in AWS Secrets Manager (Archived).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Environment: LOCAL DEV & LOCAL SERVER                       │
├─────────────────────────────────────────────────────────────┤
│ .env file → Environment Variables → Application Settings    │
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

# CryptoPanic API Key - Get from: https://cryptopanic.com/developers/api/
CRYPTOPANIC_API_KEY=your-cryptopanic-api-key-here
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

# Tier 2 Data Collection APIs (optional)
NEWSCATCHER_API_KEY=your-newscatcher-api-key
NANSEN_API_KEY=your-nansen-api-key
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

## Local Server Management (192.168.0.241)

In the Local Server environment, which uses a self-hosted GitHub Actions runner, secrets are managed via a centralized "safe" file on the host machine.

### Strategy
1.  **Central Source:** All secrets are stored in a single master file: `~/omc/secrets.safe` on the host machine.
2.  **Injection:** The `populate_secrets.sh` script is used to generate `.env` files for specific deployments.
3.  **Deployment:** The GitHub Actions workflow (`deploy-local.yml`) executes this script during the build process to inject secrets into the runner's workspace.

### The `secrets.safe` File
This file is a simple key-value store, compatible with shell sourcing but never committed to git. It resides outside the repository structure.

```bash
# ~/omc/secrets.safe on 192.168.0.241
COINSPOT_API_KEY=...
COINSPOT_SECRET=...
OPENAI_API_KEY=...
# ... other secrets
```

### The `populate_secrets.sh` Script
This script automates the creation of `.env` files for different contexts (production vs. feature tracks).

**Usage:**
```bash
./populate_secrets.sh <target-directory>
```
*   **Production:** `STACK=ohmycoins ./populate_secrets.sh .` (Used by CI/CD)
*   **Feature Tracks:** `./populate_secrets.sh ../omc-track-a` (Used by developers for worktrees)

The script automatically:
1.  Copies `.env.template` to the target.
2.  Injects secrets from `~/omc/secrets.safe`.
3.  Configures unique ports based on the directory name (e.g., `track-a` uses ports 8010/5433).

### Updating Secrets
1.  **SSH into Server:**
    ```bash
    ssh mark@192.168.0.241
    ```
2.  **Edit Master Safe:**
    ```bash
    nano ~/omc/secrets.safe
    ```
3.  **Apply Changes:**
    Commit a change to `main` (even an empty one) to trigger a redeployment, or manually run the script and restart containers:
    ```bash
    cd ~/omc/ohmycoins/
    ./populate_secrets.sh .
    docker compose up -d --force-recreate
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

### 3. Update Master Secrets

- **Server:** SSH into `192.168.0.241` and add the key to `~/omc/secrets.safe`.
- **Local Dev:** Add the key to your local `secrets.safe` (refrence it in `populate_secrets.sh`) or manually update your `.env`.

---

## Legacy Infrastructure (AWS)

*Note: The following section describes the archived AWS infrastructure.*

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
  "SENTRY_DSN": "...",
  "omc-CryptoPanic-testkey": "...",
  "omc-newscatcher-testkey": "...",
  "omc-nasen-testkey": "..."
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

**Important:** Delete `secrets.json` securely after updating!

```bash
# Securely delete the file
shred -u secrets.json 2>/dev/null || rm -P secrets.json 2>/dev/null || rm secrets.json
```

---

**Last Updated:** 2026-02-14
