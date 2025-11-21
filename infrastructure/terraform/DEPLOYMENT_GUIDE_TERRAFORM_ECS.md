# OMC Deployment Guide - Terraform/ECS (Current Infrastructure)

**Purpose:** Deploy OMC applications using the existing Terraform/ECS infrastructure  
**Target Audience:** Developer C, DevOps engineers with Terraform experience  
**Deployment Method:** Terraform (Infrastructure as Code)  
**Container Orchestration:** AWS ECS Fargate  
**Last Updated:** 2025-11-21

---

## Table of Contents

1. [Overview](#overview)
2. [Current Infrastructure Status](#current-infrastructure-status)
3. [Prerequisites](#prerequisites)
4. [Week 9-10: Deploy Applications via Terraform](#week-9-10-deploy-applications-via-terraform)
5. [Week 11: Production Environment](#week-11-production-environment)
6. [Week 12: Monitoring & Security](#week-12-monitoring--security)
7. [Troubleshooting](#troubleshooting)

---

## Overview

The OMC infrastructure is deployed using **Terraform** and runs on **AWS ECS Fargate**. This guide covers how to deploy and manage the complete application stack.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         AWS Account                          │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                    VPC (Multi-AZ)                       │ │
│  │                                                          │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │ │
│  │  │   Public     │  │   Private    │  │   Private    │ │ │
│  │  │   Subnets    │  │  App Subnets │  │  DB Subnets  │ │ │
│  │  │              │  │              │  │              │ │ │
│  │  │     ALB      │  │  ECS Tasks   │  │ RDS/Redis    │ │ │
│  │  │              │  │              │  │              │ │ │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │ │
│  │         │                  │                  │         │ │
│  │         │   Internet       │   Private        │  DB     │ │
│  │         │   Gateway        │   via NAT        │  Only   │ │
│  │         │                  │                  │         │ │
│  └─────────┴──────────────────┴──────────────────┴─────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │             ECS Fargate Cluster                        │ │
│  │                                                          │ │
│  │  Backend API (FastAPI)  │  Frontend (Vue.js)           │ │
│  │  Future: Collectors     │  Future: Agents              │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  Supporting Services:                                        │
│  • RDS PostgreSQL (application data)                        │
│  • ElastiCache Redis (caching, session management)          │
│  • Secrets Manager (credentials)                            │
│  • CloudWatch (logging, monitoring)                         │
│  • ECR (container registry)                                 │
└──────────────────────────────────────────────────────────────┘
```

### Deployment Method

**Terraform manages:**
- VPC and networking
- RDS PostgreSQL database
- ElastiCache Redis cluster
- ECS cluster and task definitions
- Application Load Balancer
- IAM roles and security groups
- Secrets Manager
- CloudWatch logging

**Container images stored in:**
- AWS ECR (Elastic Container Registry)
- Built via GitHub Actions CI/CD

---

## Current Infrastructure Status

### What's Already Deployed (Weeks 1-8 Complete)

✅ **Staging Environment:**
- VPC with public/private subnets
- RDS PostgreSQL (db.t3.micro, single-AZ)
- ElastiCache Redis (cache.t3.micro, single node)
- ECS Fargate cluster
- Application Load Balancer
- Backend API (FastAPI) - 1 task
- Frontend (Vue.js) - 1 task

✅ **Terraform Modules:**
- `modules/vpc/` - Networking infrastructure
- `modules/rds/` - PostgreSQL database
- `modules/redis/` - Redis cluster
- `modules/ecs/` - ECS cluster and tasks
- `modules/alb/` - Load balancer
- `modules/security/` - Security groups
- `modules/iam/` - IAM roles and policies

✅ **Environments:**
- `environments/staging/` - Staging configuration
- `environments/production/` - Production configuration

### What Needs to be Added (Weeks 9-12)

📍 **Phase 2.5 Data Collectors (5 services):**
- DeFiLlama collector (scheduled task - daily)
- SEC API collector (scheduled task - daily)
- CoinSpot announcements (scheduled task - hourly)
- Reddit collector (continuous service)
- CryptoPanic collector (continuous service)

📍 **Phase 3 Agentic System:**
- Agentic system (continuous service)
- PersistentVolume for artifacts (EFS mount)

📍 **Monitoring:**
- CloudWatch dashboards
- CloudWatch alarms
- Log aggregation

📍 **Production:**
- Production environment deployment
- DNS and SSL configuration
- WAF enablement
- Security hardening

---

## Prerequisites

### Required Tools

1. **Terraform** (v1.5+)
   ```bash
   terraform version
   ```

2. **AWS CLI** (configured)
   ```bash
   aws sts get-caller-identity
   aws configure get region  # Should be ap-southeast-2
   ```

3. **Git** (repository cloned)
   ```bash
   cd /path/to/ohmycoins
   ls infrastructure/terraform
   ```

### Required AWS Resources

✅ **Already Created:**
- S3 bucket for Terraform state: `ohmycoins-terraform-state`
- DynamoDB table for state locking: `ohmycoins-terraform-locks`
- Staging infrastructure deployed

📍 **To Verify:**
```bash
# Check S3 bucket exists
aws s3 ls s3://ohmycoins-terraform-state/

# Check DynamoDB table exists
aws dynamodb describe-table --table-name ohmycoins-terraform-locks

# Check current infrastructure
cd infrastructure/terraform/environments/staging
terraform init
terraform show
```

### Required Secrets

Secrets are stored in AWS Secrets Manager. Current secrets:

```bash
# Get secret ARN
cd infrastructure/terraform/environments/staging
SECRET_ARN=$(terraform output -raw secrets_manager_secret_arn)

# View current secrets (without values)
aws secretsmanager describe-secret --secret-id "$SECRET_ARN"
```

**Secrets that need updating:**
- `OPENAI_API_KEY` - For agentic system
- `ANTHROPIC_API_KEY` - For agentic system (optional)
- `SECRET_KEY` - Application secret key
- `FIRST_SUPERUSER_PASSWORD` - Admin password

---

## Week 9-10: Deploy Applications via Terraform

### Current State

The `infrastructure/terraform/modules/ecs/` module currently deploys:
- Backend API (FastAPI)
- Frontend (Vue.js)

### Goal

Add ECS task definitions for:
- Phase 2.5 Collectors (5 tasks)
- Phase 3 Agentic System (1 task)

### Step 1: Review Current ECS Module (15 minutes)

```bash
cd infrastructure/terraform/modules/ecs
ls -la

# Review main task definitions
cat main.tf | grep -A 20 "aws_ecs_task_definition"
```

**Current task definitions:**
- `backend` - FastAPI backend service
- `frontend` - Vue.js frontend service

### Step 2: Plan New ECS Tasks (30 minutes)

For each new service, we need to decide:

#### Collectors

**1. DeFiLlama Collector**
- **Type:** Scheduled Task (ECS Scheduled Task)
- **Schedule:** Daily at 2 AM UTC (`cron(0 2 * * ? *)`)
- **Resources:** 256 CPU, 512 MB memory
- **Command:** `python -m app.services.collectors.glass.defillama`

**2. SEC API Collector**
- **Type:** Scheduled Task
- **Schedule:** Daily at 3 AM UTC (`cron(0 3 * * ? *)`)
- **Resources:** 256 CPU, 512 MB memory
- **Command:** `python -m app.services.collectors.catalyst.sec_api`

**3. CoinSpot Announcements**
- **Type:** Scheduled Task
- **Schedule:** Hourly (`cron(0 * * * ? *)`)
- **Resources:** 256 CPU, 512 MB memory
- **Command:** `python -m app.services.collectors.catalyst.coinspot_announcements`

**4. Reddit Collector**
- **Type:** Continuous Service (ECS Service)
- **Desired Count:** 1
- **Resources:** 256 CPU, 512 MB memory
- **Command:** `python -m app.services.collectors.human.reddit` (with internal loop, 15 min interval)

**5. CryptoPanic Collector**
- **Type:** Continuous Service (ECS Service)
- **Desired Count:** 1
- **Resources:** 256 CPU, 512 MB memory
- **Command:** `python -m app.services.collectors.human.cryptopanic` (with internal loop, 5 min interval)

#### Agentic System

**6. Agentic System**
- **Type:** Continuous Service (ECS Service)
- **Desired Count:** 1 (can scale to 2-5 with auto-scaling)
- **Resources:** 1024 CPU, 2048 MB memory
- **Command:** `python -m app.services.agent.main`
- **Volume:** EFS mount for artifact storage

### Step 3: Add Collector Task Definitions to Terraform (1-2 hours)

**Create new file:** `infrastructure/terraform/modules/ecs/collectors.tf`

```hcl
# DeFiLlama Collector - Scheduled Task
resource "aws_ecs_task_definition" "defillama_collector" {
  family                   = "${var.project_name}-defillama-collector"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = var.task_execution_role_arn
  task_role_arn            = var.task_role_arn

  container_definitions = jsonencode([{
    name  = "defillama-collector"
    image = "${var.backend_image}:${var.backend_image_tag}"
    
    command = ["python", "-m", "app.services.collectors.glass.defillama"]
    
    environment = [
      { name = "ENVIRONMENT", value = var.environment },
      { name = "PROJECT_NAME", value = var.project_name },
      { name = "POSTGRES_SERVER", value = var.db_host },
      { name = "POSTGRES_PORT", value = tostring(var.db_port) },
      { name = "POSTGRES_DB", value = var.db_name },
      { name = "POSTGRES_USER", value = var.db_user },
      { name = "REDIS_HOST", value = var.redis_host },
      { name = "REDIS_PORT", value = tostring(var.redis_port) }
    ]
    
    secrets = [
      { name = "POSTGRES_PASSWORD", valueFrom = "${var.secrets_arn}:POSTGRES_PASSWORD::" }
    ]
    
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.collectors.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "defillama"
      }
    }
  }])

  tags = var.tags
}

# EventBridge Rule for DeFiLlama Collector
resource "aws_cloudwatch_event_rule" "defillama_schedule" {
  name                = "${var.project_name}-defillama-schedule"
  description         = "Trigger DeFiLlama collector daily at 2 AM UTC"
  schedule_expression = "cron(0 2 * * ? *)"
  
  tags = var.tags
}

resource "aws_cloudwatch_event_target" "defillama_target" {
  rule      = aws_cloudwatch_event_rule.defillama_schedule.name
  target_id = "defillama-collector"
  arn       = aws_ecs_cluster.main.arn
  role_arn  = var.eventbridge_role_arn

  ecs_target {
    task_count          = 1
    task_definition_arn = aws_ecs_task_definition.defillama_collector.arn
    launch_type         = "FARGATE"
    platform_version    = "LATEST"

    network_configuration {
      subnets          = var.private_subnet_ids
      security_groups  = var.ecs_security_group_ids
      assign_public_ip = false
    }
  }
}

# Repeat for other scheduled collectors (SEC API, CoinSpot)
# ...

# CloudWatch Log Group for Collectors
resource "aws_cloudwatch_log_group" "collectors" {
  name              = "/ecs/${var.project_name}/collectors"
  retention_in_days = var.log_retention_days

  tags = var.tags
}
```

**Note:** You'll need to add similar definitions for:
- SEC API collector (daily at 3 AM)
- CoinSpot announcements (hourly)

### Step 4: Add Continuous Collector Services (1 hour)

**Add to** `infrastructure/terraform/modules/ecs/collectors.tf`:

```hcl
# Reddit Collector - Continuous Service
resource "aws_ecs_task_definition" "reddit_collector" {
  family                   = "${var.project_name}-reddit-collector"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = var.task_execution_role_arn
  task_role_arn            = var.task_role_arn

  container_definitions = jsonencode([{
    name  = "reddit-collector"
    image = "${var.backend_image}:${var.backend_image_tag}"
    
    command = ["python", "-m", "app.services.collectors.human.reddit"]
    
    environment = [
      { name = "ENVIRONMENT", value = var.environment },
      { name = "POSTGRES_SERVER", value = var.db_host },
      { name = "REDIS_HOST", value = var.redis_host }
      # ... other environment variables
    ]
    
    secrets = [
      { name = "POSTGRES_PASSWORD", valueFrom = "${var.secrets_arn}:POSTGRES_PASSWORD::" }
    ]
    
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.collectors.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "reddit"
      }
    }
  }])

  tags = var.tags
}

resource "aws_ecs_service" "reddit_collector" {
  name            = "${var.project_name}-reddit-collector"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.reddit_collector.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  platform_version = "LATEST"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = var.ecs_security_group_ids
    assign_public_ip = false
  }

  tags = var.tags
}

# Repeat for CryptoPanic collector
# ...
```

### Step 5: Add Agentic System (1 hour)

**Add to** `infrastructure/terraform/modules/ecs/agents.tf`:

```hcl
# Agentic System Task Definition
resource "aws_ecs_task_definition" "agents" {
  family                   = "${var.project_name}-agents"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 1024
  memory                   = 2048
  execution_role_arn       = var.task_execution_role_arn
  task_role_arn            = var.task_role_arn

  # EFS Volume for artifact storage
  volume {
    name = "agent-data"
    
    efs_volume_configuration {
      file_system_id     = var.efs_file_system_id
      transit_encryption = "ENABLED"
      authorization_config {
        access_point_id = var.efs_access_point_id
        iam             = "ENABLED"
      }
    }
  }

  container_definitions = jsonencode([{
    name  = "agents"
    image = "${var.backend_image}:${var.backend_image_tag}"
    
    command = ["python", "-m", "app.services.agent.main"]
    
    mountPoints = [{
      sourceVolume  = "agent-data"
      containerPath = "/app/artifacts"
      readOnly      = false
    }]
    
    environment = [
      { name = "ENVIRONMENT", value = var.environment },
      { name = "POSTGRES_SERVER", value = var.db_host },
      { name = "REDIS_HOST", value = var.redis_host },
      { name = "ARTIFACT_STORAGE_PATH", value = "/app/artifacts" }
    ]
    
    secrets = [
      { name = "POSTGRES_PASSWORD", valueFrom = "${var.secrets_arn}:POSTGRES_PASSWORD::" },
      { name = "OPENAI_API_KEY", valueFrom = "${var.secrets_arn}:OPENAI_API_KEY::" },
      { name = "ANTHROPIC_API_KEY", valueFrom = "${var.secrets_arn}:ANTHROPIC_API_KEY::" }
    ]
    
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.agents.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "agents"
      }
    }
  }])

  tags = var.tags
}

resource "aws_ecs_service" "agents" {
  name            = "${var.project_name}-agents"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.agents.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  platform_version = "LATEST"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = var.ecs_security_group_ids
    assign_public_ip = false
  }

  # Auto-scaling (optional)
  # ...

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "agents" {
  name              = "/ecs/${var.project_name}/agents"
  retention_in_days = var.log_retention_days

  tags = var.tags
}
```

### Step 6: Create EFS for Agent Artifacts (30 minutes)

**Create new file:** `infrastructure/terraform/modules/efs/main.tf`

```hcl
# EFS File System for Agent Artifacts
resource "aws_efs_file_system" "agents" {
  creation_token = "${var.project_name}-agents"
  encrypted      = true
  
  lifecycle_policy {
    transition_to_ia = "AFTER_30_DAYS"
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-agents-efs"
    }
  )
}

# EFS Mount Targets (one per subnet)
resource "aws_efs_mount_target" "agents" {
  count = length(var.subnet_ids)
  
  file_system_id  = aws_efs_file_system.agents.id
  subnet_id       = var.subnet_ids[count.index]
  security_groups = var.security_group_ids
}

# EFS Access Point for Agents
resource "aws_efs_access_point" "agents" {
  file_system_id = aws_efs_file_system.agents.id

  posix_user {
    gid = 1000
    uid = 1000
  }

  root_directory {
    path = "/agents"
    creation_info {
      owner_gid   = 1000
      owner_uid   = 1000
      permissions = "755"
    }
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-agents-access-point"
    }
  )
}
```

### Step 7: Update IAM Role for EventBridge (30 minutes)

EventBridge needs permission to run ECS tasks.

**Add to** `infrastructure/terraform/modules/iam/main.tf`:

```hcl
# IAM Role for EventBridge to run ECS tasks
resource "aws_iam_role" "eventbridge_ecs" {
  name = "${var.project_name}-eventbridge-ecs-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "events.amazonaws.com"
      }
    }]
  })

  tags = var.tags
}

resource "aws_iam_role_policy" "eventbridge_ecs" {
  name = "${var.project_name}-eventbridge-ecs-policy"
  role = aws_iam_role.eventbridge_ecs.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ecs:RunTask"
      ]
      Resource = [
        "*"  # TODO: Restrict to specific task definitions
      ]
      Condition = {
        ArnLike = {
          "ecs:cluster" = "arn:aws:ecs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:cluster/${var.project_name}-cluster"
        }
      }
    },
    {
      Effect = "Allow"
      Action = [
        "iam:PassRole"
      ]
      Resource = [
        "*"  # TODO: Restrict to specific roles
      ]
    }]
  })
}
```

### Step 8: Update Secrets with LLM API Keys (15 minutes)

```bash
cd infrastructure/terraform/environments/staging

# Get secret ARN
SECRET_ARN=$(terraform output -raw secrets_manager_secret_arn)

# Create secrets file
cat > /tmp/secrets.json <<EOF
{
  "SECRET_KEY": "$(openssl rand -base64 32)",
  "FIRST_SUPERUSER": "admin@ohmycoins.com",
  "FIRST_SUPERUSER_PASSWORD": "$(openssl rand -base64 24)",
  "POSTGRES_SERVER": "$(terraform output -raw rds_endpoint)",
  "POSTGRES_PORT": "5432",
  "POSTGRES_DB": "omc",
  "POSTGRES_USER": "omc_admin",
  "POSTGRES_PASSWORD": "$(terraform output -raw rds_password)",
  "SMTP_HOST": "",
  "SMTP_USER": "",
  "SMTP_PASSWORD": "",
  "EMAILS_FROM_EMAIL": "noreply@staging.ohmycoins.com",
  "SMTP_TLS": "True",
  "SMTP_SSL": "False",
  "SMTP_PORT": "587",
  "REDIS_HOST": "$(terraform output -raw redis_endpoint)",
  "REDIS_PORT": "6379",
  "LLM_PROVIDER": "openai",
  "OPENAI_API_KEY": "sk-your-actual-openai-key-here",
  "ANTHROPIC_API_KEY": "sk-ant-your-actual-anthropic-key-here",
  "OPENAI_MODEL": "gpt-4-turbo-preview",
  "SENTRY_DSN": "",
  "ENVIRONMENT": "staging",
  "FRONTEND_HOST": "http://$(terraform output -raw alb_dns_name)"
}
EOF

# Upload to Secrets Manager
aws secretsmanager put-secret-value \
  --secret-id "$SECRET_ARN" \
  --secret-string file:///tmp/secrets.json \
  --region ap-southeast-2

# Clean up
rm /tmp/secrets.json
```

### Step 9: Deploy via Terraform (30 minutes)

```bash
cd infrastructure/terraform/environments/staging

# Initialize (if needed)
terraform init

# Plan the changes
terraform plan -out=tfplan

# Review the plan carefully
# Expected: New resources for collectors, agents, EFS

# Apply the changes
terraform apply tfplan

# Monitor deployment
watch -n 5 'aws ecs list-tasks --cluster ohmycoins-staging-cluster'
```

### Step 10: Verify Deployment (30 minutes)

```bash
# Check ECS cluster
aws ecs list-services --cluster ohmycoins-staging-cluster

# Expected services:
# - ohmycoins-staging-backend
# - ohmycoins-staging-frontend
# - ohmycoins-staging-reddit-collector
# - ohmycoins-staging-cryptopanic-collector
# - ohmycoins-staging-agents

# Check running tasks
aws ecs list-tasks --cluster ohmycoins-staging-cluster

# Check scheduled tasks
aws events list-rules --name-prefix ohmycoins-staging

# Expected rules:
# - ohmycoins-staging-defillama-schedule
# - ohmycoins-staging-sec-api-schedule
# - ohmycoins-staging-coinspot-schedule

# Check CloudWatch logs
aws logs describe-log-groups --log-group-name-prefix /ecs/ohmycoins-staging

# View recent collector logs
aws logs tail /ecs/ohmycoins-staging/collectors --follow
```

### Step 11: Test Collectors (30 minutes)

**Manually trigger a scheduled collector:**

```bash
# Trigger DeFiLlama collector manually
aws ecs run-task \
  --cluster ohmycoins-staging-cluster \
  --task-definition ohmycoins-staging-defillama-collector \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx]}"

# Watch task status
TASK_ARN=$(aws ecs list-tasks --cluster ohmycoins-staging-cluster --family ohmycoins-staging-defillama-collector --query 'taskArns[0]' --output text)

aws ecs describe-tasks --cluster ohmycoins-staging-cluster --tasks $TASK_ARN

# Check logs
aws logs tail /ecs/ohmycoins-staging/collectors --follow --filter-pattern "defillama"
```

**Test continuous collectors:**

```bash
# Check Reddit collector logs
aws logs tail /ecs/ohmycoins-staging/collectors --follow --filter-pattern "reddit"

# Check CryptoPanic collector logs
aws logs tail /ecs/ohmycoins-staging/collectors --follow --filter-pattern "cryptopanic"
```

**Test agentic system:**

```bash
# Check agents logs
aws logs tail /ecs/ohmycoins-staging/agents --follow

# Test agent API (if exposed via ALB)
ALB_URL=$(cd infrastructure/terraform/environments/staging && terraform output -raw alb_dns_name)
curl http://$ALB_URL/api/v1/lab/agent/health
```

### Week 9-10 Deliverables Checklist

- [ ] Terraform modules updated with collector task definitions
- [ ] Terraform modules updated with agentic system task definition
- [ ] EFS module created for agent artifacts
- [ ] IAM role for EventBridge created
- [ ] Secrets updated with LLM API keys
- [ ] Terraform applied successfully
- [ ] All ECS services running
- [ ] Scheduled tasks configured
- [ ] CloudWatch logs showing data collection
- [ ] Manual collector test successful
- [ ] Continuous collectors running
- [ ] Agentic system operational

---

## Week 11: Production Environment

### Step 1: Review Production Configuration (30 minutes)

```bash
cd infrastructure/terraform/environments/production

# Review terraform.tfvars
cat terraform.tfvars.example

# Key differences from staging:
# - Multi-AZ RDS
# - Multi-AZ Redis replication
# - Multiple NAT Gateways
# - Larger instance sizes
# - Enhanced monitoring
# - Deletion protection enabled
```

### Step 2: Configure Production Variables (1 hour)

```bash
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars
```

**Update production values:**

```hcl
# Production-specific settings
aws_region = "ap-southeast-2"

# VPC
vpc_cidr = "10.1.0.0/16"  # Different from staging
availability_zones = ["ap-southeast-2a", "ap-southeast-2b", "ap-southeast-2c"]

# RDS - Production sizing
rds_instance_class = "db.t3.small"
rds_allocated_storage = 100
master_password = "STRONG-PRODUCTION-PASSWORD"

# Redis - Production sizing
redis_node_type = "cache.t3.small"

# Domains
domain = "ohmycoins.com"
backend_domain = "api.ohmycoins.com"
frontend_host = "https://app.ohmycoins.com"

# SSL Certificate (must be created in ACM first)
certificate_arn = "arn:aws:acm:ap-southeast-2:ACCOUNT:certificate/CERT-ID"

# ECS - Production sizing
backend_cpu = 1024
backend_memory = 2048
backend_desired_count = 2

# Auto-scaling
enable_autoscaling = true
backend_min_capacity = 2
backend_max_capacity = 10
```

### Step 3: Create SSL Certificate (30 minutes)

```bash
# Request ACM certificate
aws acm request-certificate \
  --domain-name ohmycoins.com \
  --subject-alternative-names "*.ohmycoins.com" \
  --validation-method DNS \
  --region ap-southeast-2

# Get certificate ARN
CERT_ARN=$(aws acm list-certificates --query 'CertificateSummaryList[?DomainName==`ohmycoins.com`].CertificateArn' --output text)

# Get validation records
aws acm describe-certificate --certificate-arn $CERT_ARN

# Add CNAME records to Route53 for validation
# (Use AWS Console or CLI)

# Wait for validation
aws acm wait certificate-validated --certificate-arn $CERT_ARN

# Update terraform.tfvars with certificate ARN
```

### Step 4: Deploy Production Infrastructure (2-3 hours)

```bash
cd infrastructure/terraform/environments/production

# Initialize
terraform init

# Plan
terraform plan -out=prod.tfplan

# Review plan carefully!
# Verify:
# - RDS is Multi-AZ
# - Redis has replication
# - NAT in multiple AZs
# - Larger instance sizes

# Apply (takes 20-30 minutes)
terraform apply prod.tfplan

# Monitor deployment
watch -n 10 'terraform show | grep -E "status|state"'
```

### Step 5: Configure Production Secrets (30 minutes)

```bash
# Get production secret ARN
cd infrastructure/terraform/environments/production
SECRET_ARN=$(terraform output -raw secrets_manager_secret_arn)

# Create production secrets (use strong passwords!)
cat > /tmp/prod-secrets.json <<EOF
{
  "SECRET_KEY": "$(openssl rand -base64 48)",
  "FIRST_SUPERUSER": "admin@ohmycoins.com",
  "FIRST_SUPERUSER_PASSWORD": "STRONG-ADMIN-PASSWORD",
  "POSTGRES_SERVER": "$(terraform output -raw rds_endpoint)",
  "POSTGRES_PASSWORD": "$(terraform output -raw rds_password)",
  "REDIS_HOST": "$(terraform output -raw redis_endpoint)",
  "OPENAI_API_KEY": "sk-prod-openai-key",
  "ANTHROPIC_API_KEY": "sk-ant-prod-key",
  "ENVIRONMENT": "production"
}
EOF

# Upload
aws secretsmanager put-secret-value \
  --secret-id "$SECRET_ARN" \
  --secret-string file:///tmp/prod-secrets.json \
  --region ap-southeast-2

# Secure cleanup
shred -u /tmp/prod-secrets.json
```

### Step 6: Configure DNS (30 minutes)

```bash
# Get production ALB DNS
ALB_DNS=$(terraform output -raw alb_dns_name)

# Create Route53 records (use AWS Console or CLI)
# A Record: api.ohmycoins.com -> ALB (Alias)
# A Record: app.ohmycoins.com -> ALB (Alias)
```

### Step 7: Enable WAF (1 hour)

```bash
# Create WAF Web ACL
aws wafv2 create-web-acl \
  --name ohmycoins-production-waf \
  --scope REGIONAL \
  --region ap-southeast-2 \
  --default-action Block={} \
  --rules file://waf-rules.json \
  --visibility-config SampledRequestsEnabled=true,CloudWatchMetricsEnabled=true,MetricName=ohmycoins-waf

# Associate with ALB
ALB_ARN=$(terraform output -raw alb_arn)
WAF_ARN=$(aws wafv2 list-web-acls --scope REGIONAL --region ap-southeast-2 --query 'WebACLs[?Name==`ohmycoins-production-waf`].ARN' --output text)

aws wafv2 associate-web-acl \
  --web-acl-arn $WAF_ARN \
  --resource-arn $ALB_ARN \
  --region ap-southeast-2
```

**WAF Rules (waf-rules.json):**

```json
[
  {
    "Name": "AWS-AWSManagedRulesCommonRuleSet",
    "Priority": 0,
    "Statement": {
      "ManagedRuleGroupStatement": {
        "VendorName": "AWS",
        "Name": "AWSManagedRulesCommonRuleSet"
      }
    },
    "OverrideAction": {
      "None": {}
    },
    "VisibilityConfig": {
      "SampledRequestsEnabled": true,
      "CloudWatchMetricsEnabled": true,
      "MetricName": "AWS-AWSManagedRulesCommonRuleSet"
    }
  },
  {
    "Name": "RateLimitRule",
    "Priority": 1,
    "Statement": {
      "RateBasedStatement": {
        "Limit": 1000,
        "AggregateKeyType": "IP"
      }
    },
    "Action": {
      "Block": {}
    },
    "VisibilityConfig": {
      "SampledRequestsEnabled": true,
      "CloudWatchMetricsEnabled": true,
      "MetricName": "RateLimitRule"
    }
  }
]
```

### Step 8: Verify Production Deployment (30 minutes)

```bash
# Check ECS services
aws ecs list-services --cluster ohmycoins-production-cluster

# Check RDS
aws rds describe-db-instances --db-instance-identifier ohmycoins-production-db

# Check Redis
aws elasticache describe-cache-clusters --cache-cluster-id ohmycoins-production-redis

# Test HTTPS endpoint
curl https://api.ohmycoins.com/api/v1/health
```

### Week 11 Deliverables Checklist

- [ ] Production terraform.tfvars configured
- [ ] SSL certificate created and validated
- [ ] Production infrastructure deployed
- [ ] Multi-AZ RDS operational
- [ ] Multi-AZ Redis operational
- [ ] Production secrets configured
- [ ] DNS records created
- [ ] HTTPS working on ALB
- [ ] WAF enabled and configured
- [ ] All services running in production
- [ ] Production endpoints accessible

---

## Week 12: Monitoring & Security

### Step 1: CloudWatch Dashboards (2 hours)

**Create CloudWatch dashboard for monitoring:**

```bash
# Create dashboard JSON
cat > /tmp/dashboard.json <<'EOF'
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          [ "AWS/ECS", "CPUUtilization", { "stat": "Average" } ],
          [ ".", "MemoryUtilization", { "stat": "Average" } ]
        ],
        "period": 300,
        "stat": "Average",
        "region": "ap-southeast-2",
        "title": "ECS Cluster Metrics"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          [ "AWS/RDS", "CPUUtilization", { "stat": "Average" } ],
          [ ".", "DatabaseConnections", { "stat": "Average" } ]
        ],
        "period": 300,
        "stat": "Average",
        "region": "ap-southeast-2",
        "title": "RDS Metrics"
      }
    },
    {
      "type": "log",
      "properties": {
        "query": "SOURCE '/ecs/ohmycoins-staging/collectors'\n| fields @timestamp, @message\n| filter @message like /ERROR/\n| sort @timestamp desc\n| limit 20",
        "region": "ap-southeast-2",
        "title": "Recent Errors"
      }
    }
  ]
}
EOF

# Create dashboard
aws cloudwatch put-dashboard \
  --dashboard-name OMC-Staging \
  --dashboard-body file:///tmp/dashboard.json

rm /tmp/dashboard.json
```

### Step 2: CloudWatch Alarms (1 hour)

```bash
# ECS High CPU Alarm
aws cloudwatch put-metric-alarm \
  --alarm-name omc-staging-ecs-high-cpu \
  --alarm-description "Alert when ECS CPU is high" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2

# RDS High CPU Alarm
aws cloudwatch put-metric-alarm \
  --alarm-name omc-staging-rds-high-cpu \
  --alarm-description "Alert when RDS CPU is high" \
  --metric-name CPUUtilization \
  --namespace AWS/RDS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2

# Application Error Rate Alarm
aws cloudwatch put-metric-alarm \
  --alarm-name omc-staging-high-error-rate \
  --alarm-description "Alert on high error rate" \
  --metric-name Errors \
  --namespace AWS/ApplicationELB \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1
```

### Step 3: Enable AWS Config (30 minutes)

```bash
# Create S3 bucket for Config
aws s3 mb s3://ohmycoins-aws-config-$(aws sts get-caller-identity --query Account --output text) --region ap-southeast-2

# Enable AWS Config (use AWS Console for easier setup)
# Or use Terraform module

# Enable Config rules:
# - rds-encryption-enabled
# - s3-bucket-public-read-prohibited
# - iam-password-policy
# - vpc-default-security-group-closed
```

### Step 4: Enable GuardDuty (15 minutes)

```bash
# Enable GuardDuty
aws guardduty create-detector \
  --enable \
  --finding-publishing-frequency FIFTEEN_MINUTES \
  --region ap-southeast-2
```

### Step 5: Enable CloudTrail (30 minutes)

```bash
# Create S3 bucket for CloudTrail
aws s3 mb s3://ohmycoins-cloudtrail-$(aws sts get-caller-identity --query Account --output text) --region ap-southeast-2

# Create CloudTrail
aws cloudtrail create-trail \
  --name omc-audit-trail \
  --s3-bucket-name ohmycoins-cloudtrail-$(aws sts get-caller-identity --query Account --output text) \
  --is-multi-region-trail

# Start logging
aws cloudtrail start-logging --name omc-audit-trail
```

### Step 6: Security Audit (2 hours)

**Review checklist:**

- [ ] All RDS instances have encryption at rest
- [ ] All data in transit uses TLS
- [ ] Security groups follow least privilege
- [ ] IAM roles follow least privilege
- [ ] No public S3 buckets
- [ ] Secrets stored in Secrets Manager
- [ ] CloudTrail enabled
- [ ] GuardDuty enabled
- [ ] AWS Config enabled
- [ ] WAF enabled on production ALB

### Step 7: Update Documentation (2 hours)

Update the following files:

1. **DEVELOPER_C_SUMMARY.md** - Add Weeks 9-12 summary
2. **infrastructure/terraform/README.md** - Update with new resources
3. **infrastructure/terraform/OPERATIONS_RUNBOOK.md** - Add collector/agent operations
4. Create **PRODUCTION_DEPLOYMENT_RUNBOOK.md**

### Week 12 Deliverables Checklist

- [ ] CloudWatch dashboards created
- [ ] CloudWatch alarms configured
- [ ] AWS Config enabled
- [ ] GuardDuty enabled
- [ ] CloudTrail enabled
- [ ] Security audit completed
- [ ] All documentation updated
- [ ] DEVELOPER_C_SUMMARY.md updated with Weeks 9-12

---

## Troubleshooting

### ECS Task Not Starting

**Problem:** ECS task fails to start or is in STOPPED state

**Diagnosis:**
```bash
# Get task details
aws ecs describe-tasks \
  --cluster ohmycoins-staging-cluster \
  --tasks TASK_ARN

# Check stopped reason
aws ecs describe-tasks \
  --cluster ohmycoins-staging-cluster \
  --tasks TASK_ARN \
  --query 'tasks[0].stoppedReason'
```

**Common causes:**
1. Image pull error - Check ECR permissions
2. Resource limit - Check CPU/memory limits
3. Environment variable error - Check secrets
4. Health check failure - Check application logs

### Scheduled Task Not Running

**Problem:** EventBridge scheduled task not triggering

**Diagnosis:**
```bash
# Check EventBridge rule
aws events describe-rule --name ohmycoins-staging-defillama-schedule

# Check rule targets
aws events list-targets-by-rule --rule ohmycoins-staging-defillama-schedule

# Check CloudWatch Events logs
aws logs tail /aws/events/ohmycoins-staging-defillama-schedule --follow
```

**Common causes:**
1. IAM permission issue - Check EventBridge role
2. Schedule expression error - Verify cron syntax
3. Subnet/security group issue - Check network config

### Application Can't Connect to RDS

**Problem:** Application logs show database connection errors

**Diagnosis:**
```bash
# Check security group rules
aws ec2 describe-security-groups \
  --group-ids sg-xxx \
  --query 'SecurityGroups[0].IpPermissions'

# Check RDS status
aws rds describe-db-instances \
  --db-instance-identifier ohmycoins-staging-db \
  --query 'DBInstances[0].DBInstanceStatus'
```

**Common causes:**
1. Security group not allowing ECS → RDS - Add ingress rule
2. Wrong RDS endpoint in secrets - Update secrets
3. Wrong password - Update secrets

### High AWS Costs

**Problem:** AWS bill higher than expected

**Diagnosis:**
```bash
# Check ECS service count
aws ecs list-services --cluster ohmycoins-staging-cluster

# Check running tasks
aws ecs list-tasks --cluster ohmycoins-staging-cluster

# Check NAT Gateway usage
aws ec2 describe-nat-gateways --filter "Name=state,Values=available"
```

**Cost optimization:**
- Ensure services scale down when not needed
- Use single NAT Gateway for staging
- Set appropriate log retention
- Delete unused resources

---

## Summary

This guide covers deploying OMC applications using Terraform and ECS Fargate:

**Week 9-10:**
- ✅ Add collector task definitions to Terraform
- ✅ Add agentic system task definition
- ✅ Create EFS for agent artifacts
- ✅ Update IAM roles
- ✅ Deploy via `terraform apply`

**Week 11:**
- ✅ Deploy production infrastructure
- ✅ Configure DNS and SSL
- ✅ Enable WAF
- ✅ Configure backups

**Week 12:**
- ✅ Set up CloudWatch monitoring
- ✅ Enable security services
- ✅ Security audit
- ✅ Update documentation

**Key Files:**
- `infrastructure/terraform/modules/ecs/collectors.tf` (new)
- `infrastructure/terraform/modules/ecs/agents.tf` (new)
- `infrastructure/terraform/modules/efs/main.tf` (new)
- `infrastructure/terraform/environments/staging/terraform.tfvars` (updated)
- `infrastructure/terraform/environments/production/terraform.tfvars` (updated)

**Deployment Command:**
```bash
cd infrastructure/terraform/environments/staging
terraform init
terraform plan
terraform apply
```

For questions or issues, refer to:
- `infrastructure/terraform/README.md`
- `infrastructure/terraform/TROUBLESHOOTING.md`
- `infrastructure/terraform/OPERATIONS_RUNBOOK.md`
