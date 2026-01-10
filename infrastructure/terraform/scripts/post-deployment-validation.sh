#!/bin/bash
# Post-Deployment Validation Script
# Validates that the Oh My Coins staging environment is healthy after deployment
#
# Usage: ./post-deployment-validation.sh [staging|production]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

VALIDATION_PASSED=true
WARNINGS=0
CHECKS_PASSED=0
CHECKS_FAILED=0

# Parse environment
ENVIRONMENT=${1:-staging}

echo -e "${BOLD}=========================================${NC}"
echo -e "${BOLD}  Oh My Coins - Post-Deployment Validation${NC}"
echo -e "${BOLD}  Environment: $ENVIRONMENT${NC}"
echo -e "${BOLD}=========================================${NC}"
echo ""

# Function to check and report
check_item() {
    local description=$1
    local command=$2
    local required=${3:-true}
    
    echo -n "  Checking $description... "
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
        return 0
    else
        if [ "$required" = true ]; then
            echo -e "${RED}✗ FAIL${NC}"
            VALIDATION_PASSED=false
            CHECKS_FAILED=$((CHECKS_FAILED + 1))
            return 1
        else
            echo -e "${YELLOW}⚠ WARNING${NC}"
            WARNINGS=$((WARNINGS + 1))
            return 0
        fi
    fi
}

# Get Terraform outputs
echo -e "${BLUE}[1/10] Loading Terraform Outputs...${NC}"
echo ""

cd "$(dirname "$0")/../environments/$ENVIRONMENT" 2>/dev/null || {
    echo -e "${RED}Error: Cannot find environment directory${NC}"
    echo "Expected: $(dirname "$0")/../environments/$ENVIRONMENT"
    exit 1
}

# Load outputs
if [ ! -f "terraform.tfstate" ] && [ ! -f ".terraform/terraform.tfstate" ]; then
    echo -e "${RED}Error: Terraform state not found${NC}"
    echo "Run terraform apply first"
    exit 1
fi

CLUSTER_NAME=$(terraform output -raw ecs_cluster_name 2>/dev/null)
ALB_DNS=$(terraform output -raw alb_dns_name 2>/dev/null)
DB_HOST=$(terraform output -raw db_instance_address 2>/dev/null)
REDIS_HOST=$(terraform output -raw redis_primary_endpoint_address 2>/dev/null)
SECRET_ARN=$(terraform output -raw app_secrets_arn 2>/dev/null)
VPC_ID=$(terraform output -raw vpc_id 2>/dev/null)

if [ -z "$CLUSTER_NAME" ] || [ -z "$ALB_DNS" ]; then
    echo -e "${RED}Error: Cannot load Terraform outputs${NC}"
    echo "Ensure terraform apply completed successfully"
    exit 1
fi

echo -e "${GREEN}✓ Terraform outputs loaded${NC}"
echo "  Cluster: $CLUSTER_NAME"
echo "  ALB DNS: $ALB_DNS"
echo ""

# Section 1: VPC and Networking
echo -e "${BLUE}[2/10] VPC and Networking${NC}"
echo "------------------------"

check_item "VPC exists and is available" \
    "aws ec2 describe-vpcs --vpc-ids $VPC_ID --query 'Vpcs[0].State' --output text | grep -q available"

check_item "NAT Gateway is available" \
    "aws ec2 describe-nat-gateways --filter 'Name=vpc-id,Values=$VPC_ID' --query 'NatGateways[0].State' --output text | grep -q available"

check_item "Internet Gateway attached" \
    "aws ec2 describe-internet-gateways --filters 'Name=attachment.vpc-id,Values=$VPC_ID' --query 'InternetGateways[0].Attachments[0].State' --output text | grep -q available"

echo ""

# Section 2: Database (RDS)
echo -e "${BLUE}[3/10] Database (RDS PostgreSQL)${NC}"
echo "--------------------------------"

check_item "RDS instance is available" \
    "aws rds describe-db-instances --db-instance-identifier ohmycoins-$ENVIRONMENT --query 'DBInstances[0].DBInstanceStatus' --output text | grep -q available"

if aws rds describe-db-instances --db-instance-identifier ohmycoins-$ENVIRONMENT &>/dev/null; then
    DB_STATUS=$(aws rds describe-db-instances --db-instance-identifier ohmycoins-$ENVIRONMENT --query 'DBInstances[0].DBInstanceStatus' --output text)
    echo "  Database Status: $DB_STATUS"
    
    BACKUP_ENABLED=$(aws rds describe-db-instances --db-instance-identifier ohmycoins-$ENVIRONMENT --query 'DBInstances[0].BackupRetentionPeriod' --output text)
    echo "  Backup Retention: $BACKUP_ENABLED days"
fi

check_item "Database endpoint is reachable (DNS)" \
    "nslookup $DB_HOST > /dev/null 2>&1" false

echo ""

# Section 3: Cache (ElastiCache Redis)
echo -e "${BLUE}[4/10] Cache (ElastiCache Redis)${NC}"
echo "--------------------------------"

check_item "Redis cluster is available" \
    "aws elasticache describe-cache-clusters --cache-cluster-id ohmycoins-$ENVIRONMENT --query 'CacheClusters[0].CacheClusterStatus' --output text | grep -q available"

if aws elasticache describe-cache-clusters --cache-cluster-id ohmycoins-$ENVIRONMENT &>/dev/null; then
    REDIS_STATUS=$(aws elasticache describe-cache-clusters --cache-cluster-id ohmycoins-$ENVIRONMENT --query 'CacheClusters[0].CacheClusterStatus' --output text)
    echo "  Redis Status: $REDIS_STATUS"
    
    REDIS_NODE_TYPE=$(aws elasticache describe-cache-clusters --cache-cluster-id ohmycoins-$ENVIRONMENT --query 'CacheClusters[0].CacheNodeType' --output text)
    echo "  Node Type: $REDIS_NODE_TYPE"
fi

check_item "Redis endpoint is reachable (DNS)" \
    "nslookup $REDIS_HOST > /dev/null 2>&1" false

echo ""

# Section 4: ECS Cluster and Services
echo -e "${BLUE}[5/10] ECS Cluster and Services${NC}"
echo "--------------------------------"

check_item "ECS cluster is active" \
    "aws ecs describe-clusters --clusters $CLUSTER_NAME --query 'clusters[0].status' --output text | grep -q ACTIVE"

if aws ecs describe-clusters --clusters $CLUSTER_NAME &>/dev/null; then
    RUNNING_TASKS=$(aws ecs describe-clusters --clusters $CLUSTER_NAME --query 'clusters[0].runningTasksCount' --output text)
    REGISTERED_INSTANCES=$(aws ecs describe-clusters --clusters $CLUSTER_NAME --query 'clusters[0].registeredContainerInstancesCount' --output text)
    echo "  Running Tasks: $RUNNING_TASKS"
    echo "  Registered Instances: $REGISTERED_INSTANCES (Fargate=0 is normal)"
fi

check_item "Backend service is active" \
    "aws ecs describe-services --cluster $CLUSTER_NAME --services ohmycoins-$ENVIRONMENT-backend-service --query 'services[0].status' --output text | grep -q ACTIVE"

check_item "Frontend service is active" \
    "aws ecs describe-services --cluster $CLUSTER_NAME --services ohmycoins-$ENVIRONMENT-frontend-service --query 'services[0].status' --output text | grep -q ACTIVE"

# Check service health
BACKEND_DESIRED=$(aws ecs describe-services --cluster $CLUSTER_NAME --services ohmycoins-$ENVIRONMENT-backend-service --query 'services[0].desiredCount' --output text 2>/dev/null)
BACKEND_RUNNING=$(aws ecs describe-services --cluster $CLUSTER_NAME --services ohmycoins-$ENVIRONMENT-backend-service --query 'services[0].runningCount' --output text 2>/dev/null)

if [ "$BACKEND_DESIRED" = "$BACKEND_RUNNING" ]; then
    echo -e "  ${GREEN}✓${NC} Backend: $BACKEND_RUNNING/$BACKEND_DESIRED tasks running"
else
    echo -e "  ${YELLOW}⚠${NC} Backend: $BACKEND_RUNNING/$BACKEND_DESIRED tasks running (not stable yet)"
    WARNINGS=$((WARNINGS + 1))
fi

FRONTEND_DESIRED=$(aws ecs describe-services --cluster $CLUSTER_NAME --services ohmycoins-$ENVIRONMENT-frontend-service --query 'services[0].desiredCount' --output text 2>/dev/null)
FRONTEND_RUNNING=$(aws ecs describe-services --cluster $CLUSTER_NAME --services ohmycoins-$ENVIRONMENT-frontend-service --query 'services[0].runningCount' --output text 2>/dev/null)

if [ "$FRONTEND_DESIRED" = "$FRONTEND_RUNNING" ]; then
    echo -e "  ${GREEN}✓${NC} Frontend: $FRONTEND_RUNNING/$FRONTEND_DESIRED tasks running"
else
    echo -e "  ${YELLOW}⚠${NC} Frontend: $FRONTEND_RUNNING/$FRONTEND_DESIRED tasks running (not stable yet)"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""

# Section 5: Load Balancer
echo -e "${BLUE}[6/10] Application Load Balancer${NC}"
echo "--------------------------------"

ALB_NAME="ohmycoins-$ENVIRONMENT-alb"

check_item "Load balancer is active" \
    "aws elbv2 describe-load-balancers --names $ALB_NAME --query 'LoadBalancers[0].State.Code' --output text | grep -q active"

# Check target groups
BACKEND_TG_ARN=$(terraform output -raw backend_target_group_arn 2>/dev/null)

if [ -n "$BACKEND_TG_ARN" ]; then
    HEALTHY_TARGETS=$(aws elbv2 describe-target-health --target-group-arn $BACKEND_TG_ARN --query "TargetHealthDescriptions[?TargetHealth.State=='healthy'] | length(@)" --output text 2>/dev/null || echo "0")
    TOTAL_TARGETS=$(aws elbv2 describe-target-health --target-group-arn $BACKEND_TG_ARN --query "length(TargetHealthDescriptions)" --output text 2>/dev/null || echo "0")
    
    if [ "$HEALTHY_TARGETS" = "$TOTAL_TARGETS" ] && [ "$TOTAL_TARGETS" -gt 0 ]; then
        echo -e "  ${GREEN}✓${NC} Backend targets: $HEALTHY_TARGETS/$TOTAL_TARGETS healthy"
    else
        echo -e "  ${YELLOW}⚠${NC} Backend targets: $HEALTHY_TARGETS/$TOTAL_TARGETS healthy"
        WARNINGS=$((WARNINGS + 1))
    fi
fi

echo ""

# Section 6: Secrets Manager
echo -e "${BLUE}[7/10] Secrets Manager${NC}"
echo "--------------------"

check_item "Application secret exists" \
    "aws secretsmanager describe-secret --secret-id $SECRET_ARN > /dev/null 2>&1"

if aws secretsmanager describe-secret --secret-id $SECRET_ARN &>/dev/null; then
    LAST_CHANGED=$(aws secretsmanager describe-secret --secret-id $SECRET_ARN --query 'LastChangedDate' --output text)
    echo "  Last Updated: $LAST_CHANGED"
    
    # Check if KMS encryption is enabled
    KMS_KEY=$(aws secretsmanager describe-secret --secret-id $SECRET_ARN --query 'KmsKeyId' --output text)
    if [ "$KMS_KEY" != "None" ] && [ -n "$KMS_KEY" ]; then
        echo -e "  ${GREEN}✓${NC} KMS Encryption: Enabled"
    else
        echo -e "  ${YELLOW}⚠${NC} KMS Encryption: Using AWS managed key"
        WARNINGS=$((WARNINGS + 1))
    fi
fi

echo ""

# Section 7: Application Health Checks
echo -e "${BLUE}[8/10] Application Health Checks${NC}"
echo "---------------------------------"

echo "  Testing endpoints (waiting 5s for ALB to warm up)..."
sleep 5

# Backend health check
if curl -f -s -o /dev/null -w "%{http_code}" "http://$ALB_DNS/health" 2>/dev/null | grep -q "200"; then
    echo -e "  ${GREEN}✓${NC} Backend health check: PASS (http://$ALB_DNS/health)"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://$ALB_DNS/health" 2>/dev/null || echo "000")
    echo -e "  ${RED}✗${NC} Backend health check: FAIL (HTTP $HTTP_CODE)"
    echo "     URL: http://$ALB_DNS/health"
    VALIDATION_PASSED=false
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
fi

# API docs check
if curl -f -s -o /dev/null -w "%{http_code}" "http://$ALB_DNS/docs" 2>/dev/null | grep -q "200"; then
    echo -e "  ${GREEN}✓${NC} API documentation: PASS (http://$ALB_DNS/docs)"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://$ALB_DNS/docs" 2>/dev/null || echo "000")
    echo -e "  ${YELLOW}⚠${NC} API documentation: WARN (HTTP $HTTP_CODE)"
    WARNINGS=$((WARNINGS + 1))
fi

# Frontend check
if curl -f -s -o /dev/null -w "%{http_code}" "http://$ALB_DNS/" 2>/dev/null | grep -q "200"; then
    echo -e "  ${GREEN}✓${NC} Frontend: PASS (http://$ALB_DNS/)"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://$ALB_DNS/" 2>/dev/null || echo "000")
    echo -e "  ${YELLOW}⚠${NC} Frontend: WARN (HTTP $HTTP_CODE)"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""

# Section 8: CloudWatch Logs
echo -e "${BLUE}[9/10] CloudWatch Logs${NC}"
echo "--------------------"

check_item "Backend log group exists" \
    "aws logs describe-log-groups --log-group-name-prefix /ecs/ohmycoins-$ENVIRONMENT-backend --query 'logGroups[0].logGroupName' --output text | grep -q backend"

check_item "Frontend log group exists" \
    "aws logs describe-log-groups --log-group-name-prefix /ecs/ohmycoins-$ENVIRONMENT-frontend --query 'logGroups[0].logGroupName' --output text | grep -q frontend"

# Check for recent errors
ERROR_COUNT=$(aws logs filter-log-events \
    --log-group-name /ecs/ohmycoins-$ENVIRONMENT-backend \
    --filter-pattern "ERROR" \
    --start-time $(date -u -d '10 minutes ago' +%s)000 \
    --query 'events' \
    --output json 2>/dev/null | jq 'length' 2>/dev/null || echo "0")

if [ "$ERROR_COUNT" -eq 0 ]; then
    echo -e "  ${GREEN}✓${NC} No errors in last 10 minutes"
elif [ "$ERROR_COUNT" -lt 5 ]; then
    echo -e "  ${YELLOW}⚠${NC} $ERROR_COUNT errors in last 10 minutes (review logs)"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "  ${RED}✗${NC} $ERROR_COUNT errors in last 10 minutes (investigate!)"
    VALIDATION_PASSED=false
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
fi

echo ""

# Section 9: CloudWatch Monitoring
echo -e "${BLUE}[10/10] CloudWatch Monitoring${NC}"
echo "----------------------------"

# Check if monitoring module was deployed
SNS_TOPIC_ARN=$(terraform output -raw monitoring_sns_topic_arn 2>/dev/null)

if [ -n "$SNS_TOPIC_ARN" ] && [ "$SNS_TOPIC_ARN" != "" ]; then
    check_item "SNS topic exists" \
        "aws sns get-topic-attributes --topic-arn $SNS_TOPIC_ARN > /dev/null 2>&1"
    
    # Count subscriptions
    SUBSCRIPTIONS=$(aws sns list-subscriptions-by-topic --topic-arn $SNS_TOPIC_ARN --query 'Subscriptions | length(@)' --output text 2>/dev/null || echo "0")
    echo "  SNS Subscriptions: $SUBSCRIPTIONS"
    
    if [ "$SUBSCRIPTIONS" -eq 0 ]; then
        echo -e "  ${YELLOW}⚠${NC} No email subscriptions configured"
        WARNINGS=$((WARNINGS + 1))
    fi
    
    # Check alarms
    ALARMS_OK=$(aws cloudwatch describe-alarms \
        --alarm-name-prefix ohmycoins-$ENVIRONMENT \
        --state-value OK \
        --query 'MetricAlarms | length(@)' \
        --output text 2>/dev/null || echo "0")
    
    ALARMS_ALARM=$(aws cloudwatch describe-alarms \
        --alarm-name-prefix ohmycoins-$ENVIRONMENT \
        --state-value ALARM \
        --query 'MetricAlarms | length(@)' \
        --output text 2>/dev/null || echo "0")
    
    echo "  CloudWatch Alarms: $ALARMS_OK OK, $ALARMS_ALARM in ALARM state"
    
    if [ "$ALARMS_ALARM" -gt 0 ]; then
        echo -e "  ${RED}✗${NC} Some alarms are firing!"
        VALIDATION_PASSED=false
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    fi
    
    # Check dashboard
    DASHBOARD_NAME="ohmycoins-$ENVIRONMENT-infrastructure"
    if aws cloudwatch get-dashboard --dashboard-name $DASHBOARD_NAME &>/dev/null; then
        echo -e "  ${GREEN}✓${NC} CloudWatch dashboard exists: $DASHBOARD_NAME"
        echo "     https://console.aws.amazon.com/cloudwatch/home?region=ap-southeast-2#dashboards:name=$DASHBOARD_NAME"
    else
        echo -e "  ${YELLOW}⚠${NC} CloudWatch dashboard not found"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo -e "  ${YELLOW}⚠${NC} Monitoring module not deployed"
    echo "     Run terraform apply with monitoring module enabled"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""

# Final Summary
echo -e "${BOLD}=========================================${NC}"
echo -e "${BOLD}Validation Summary${NC}"
echo -e "${BOLD}=========================================${NC}"
echo ""

TOTAL_CHECKS=$((CHECKS_PASSED + CHECKS_FAILED))
echo "Checks Performed: $TOTAL_CHECKS"
echo -e "Checks Passed:    ${GREEN}$CHECKS_PASSED${NC}"
echo -e "Checks Failed:    ${RED}$CHECKS_FAILED${NC}"
echo -e "Warnings:         ${YELLOW}$WARNINGS${NC}"
echo ""

if [ "$VALIDATION_PASSED" = true ]; then
    echo -e "${GREEN}${BOLD}✓ DEPLOYMENT VALIDATION PASSED${NC}"
    
    if [ $WARNINGS -gt 0 ]; then
        echo ""
        echo -e "${YELLOW}Note: $WARNINGS warning(s) found (review above)${NC}"
    fi
    
    echo ""
    echo "Your application is deployed and healthy!"
    echo ""
    echo "Access your application:"
    echo -e "  ${BLUE}Application URL:${NC} http://$ALB_DNS"
    echo -e "  ${BLUE}API Docs:${NC}        http://$ALB_DNS/docs"
    echo -e "  ${BLUE}Health Check:${NC}    http://$ALB_DNS/health"
    echo ""
    echo "Next steps:"
    echo "  1. Configure custom domain and HTTPS"
    echo "  2. Subscribe to SNS alerts (if not done)"
    echo "  3. Test application functionality"
    echo "  4. Review CloudWatch dashboard"
    echo "  5. Run load tests"
    
    exit 0
else
    echo -e "${RED}${BOLD}✗ DEPLOYMENT VALIDATION FAILED${NC}"
    echo ""
    echo "Issues found:"
    echo "  - $CHECKS_FAILED critical checks failed"
    echo "  - $WARNINGS warnings"
    echo ""
    echo "Troubleshooting steps:"
    echo "  1. Check ECS service events:"
    echo "     aws ecs describe-services --cluster $CLUSTER_NAME \\"
    echo "       --services ohmycoins-$ENVIRONMENT-backend-service \\"
    echo "       --query 'services[0].events[:5]'"
    echo ""
    echo "  2. View recent logs:"
    echo "     aws logs tail /ecs/ohmycoins-$ENVIRONMENT-backend --follow"
    echo ""
    echo "  3. Check target health:"
    echo "     aws elbv2 describe-target-health --target-group-arn $BACKEND_TG_ARN"
    echo ""
    echo "  4. Review CloudWatch alarms:"
    echo "     aws cloudwatch describe-alarms --alarm-name-prefix ohmycoins-$ENVIRONMENT"
    echo ""
    echo "See TROUBLESHOOTING.md for more help."
    
    exit 1
fi
