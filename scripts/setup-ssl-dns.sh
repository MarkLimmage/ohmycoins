#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

# ================= CONFIGURATION =================
AWS_REGION="ap-southeast-2"
AWS_ACCOUNT_ID="220711411889"
ELB_NAME="ohmycoins-staging-alb"
ELB_DNS="ohmycoins-staging-alb-1628790289.ap-southeast-2.elb.amazonaws.com"
ELB_HOSTED_ZONE_ID="Z1GM3OXH4ZPM65"  # ALB canonical hosted zone for ap-southeast-2

# Domain Configuration
DOMAIN="ohmycoins.com"
STAGING_SUBDOMAIN="staging"         # Creates staging.ohmycoins.com
API_SUBDOMAIN="api.staging"         # Creates api.staging.ohmycoins.com
DASHBOARD_SUBDOMAIN="dashboard.staging"  # Creates dashboard.staging.ohmycoins.com

# Terraform Configuration Path
TERRAFORM_DIR="infrastructure/terraform/environments/staging"
# =================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}====================================================${NC}"
echo -e "${GREEN}SSL & DNS Automation for: ${DOMAIN} (Route 53)${NC}"
echo -e "${GREEN}====================================================${NC}"

# ========== STEP 0: Create/Get Route 53 Hosted Zone ==========
echo -e "\n${YELLOW}[0/7] Setting up Route 53 Hosted Zone...${NC}"

# Check if hosted zone exists
HOSTED_ZONE_ID=$(aws route53 list-hosted-zones-by-name \
    --dns-name "${DOMAIN}." \
    --query "HostedZones[?Name=='${DOMAIN}.'].Id" \
    --output text 2>/dev/null | cut -d'/' -f3)

if [ -z "$HOSTED_ZONE_ID" ]; then
    echo "   Creating new hosted zone for ${DOMAIN}..."
    HOSTED_ZONE_ID=$(aws route53 create-hosted-zone \
        --name "${DOMAIN}" \
        --caller-reference "ohmycoins-$(date +%s)" \
        --query 'HostedZone.Id' \
        --output text | cut -d'/' -f3)
    echo -e "${GREEN}   ✓ Created hosted zone: ${HOSTED_ZONE_ID}${NC}"
else
    echo -e "${GREEN}   ✓ Using existing hosted zone: ${HOSTED_ZONE_ID}${NC}"
fi

# Get nameservers
NAMESERVERS=$(aws route53 get-hosted-zone \
    --id "${HOSTED_ZONE_ID}" \
    --query 'DelegationSet.NameServers' \
    --output text)

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  IMPORTANT: Update GoDaddy Nameservers            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Go to GoDaddy and update nameservers for ${DOMAIN} to:"
echo ""
for NS in $NAMESERVERS; do
    echo "  → ${NS}"
done
echo ""
echo -e "${YELLOW}Press ENTER once you've updated the nameservers (or skip if already done)${NC}"
read -r

# ========== STEP 1: Request ACM Certificate ==========
echo -e "\n${YELLOW}[1/7] Requesting ACM Certificate...${NC}"
CERT_ARN=$(aws acm request-certificate \
    --domain-name "${STAGING_SUBDOMAIN}.${DOMAIN}" \
    --validation-method DNS \
    --subject-alternative-names "*.${STAGING_SUBDOMAIN}.${DOMAIN}" \
    --region "$AWS_REGION" \
    --output text \
    --query 'CertificateArn')

echo -e "${GREEN}   ✓ Certificate ARN: ${CERT_ARN}${NC}"

# ========== STEP 2: Get Validation Records ==========
echo -e "\n${YELLOW}[2/7] Waiting for validation records (AWS takes 10-30 seconds)...${NC}"

VALIDATION_RECORDS=""
ATTEMPT=0
MAX_ATTEMPTS=12

while [ -z "$VALIDATION_RECORDS" ] && [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    sleep 5
    ATTEMPT=$((ATTEMPT + 1))
    echo -n "."
    
    VALIDATION_RECORDS=$(aws acm describe-certificate \
        --certificate-arn "$CERT_ARN" \
        --region "$AWS_REGION" \
        --output json | jq -r '.Certificate.DomainValidationOptions[] | select(.ResourceRecord != null) | .ResourceRecord | "\(.Name)|\(.Value)"')
done

echo ""

if [ -z "$VALIDATION_RECORDS" ]; then
    echo -e "${RED}ERROR: Timeout waiting for validation records${NC}"
    exit 1
fi

echo -e "${GREEN}   ✓ Found validation records!${NC}"

# ========== STEP 3: Add Validation Records to Route 53 ==========
echo -e "\n${YELLOW}[3/7] Adding validation records to Route 53...${NC}"

# Process each validation record
echo "$VALIDATION_RECORDS" | while IFS='|' read -r CNAME_NAME CNAME_VALUE; do
    # Remove trailing dots
    CNAME_NAME_CLEAN=$(echo "$CNAME_NAME" | sed 's/\.$//')
    CNAME_VALUE_CLEAN=$(echo "$CNAME_VALUE" | sed 's/\.$//')
    
    echo "   → Adding: ${CNAME_NAME_CLEAN} → ${CNAME_VALUE_CLEAN}"
    
    # Create change batch JSON
    CHANGE_BATCH=$(cat <<EOF
{
  "Changes": [{
    "Action": "UPSERT",
    "ResourceRecordSet": {
      "Name": "${CNAME_NAME}",
      "Type": "CNAME",
      "TTL": 300,
      "ResourceRecords": [{"Value": "${CNAME_VALUE}"}]
    }
  }]
}
EOF
)
    
    # Apply change
    CHANGE_ID=$(aws route53 change-resource-record-sets \
        --hosted-zone-id "${HOSTED_ZONE_ID}" \
        --change-batch "${CHANGE_BATCH}" \
        --query 'ChangeInfo.Id' \
        --output text)
    
    if [ -n "$CHANGE_ID" ]; then
        echo -e "${GREEN}   ✓ Successfully added validation record${NC}"
    else
        echo -e "${RED}   ✗ Failed to add validation record${NC}"
        exit 1
    fi
done

# ========== STEP 4: Wait for Certificate Validation ==========
echo -e "\n${YELLOW}[4/7] Waiting for AWS to validate certificate (5-20 minutes)...${NC}"
echo "   This may take a while. AWS needs to verify DNS propagation."
echo "   You can check status at: https://console.aws.amazon.com/acm/home?region=${AWS_REGION}"

aws acm wait certificate-validated --certificate-arn "$CERT_ARN" --region "$AWS_REGION" 2>&1 | while read line; do
    echo "   $line"
done

echo -e "${GREEN}   ✓ Certificate VALIDATED and ISSUED!${NC}"

# ========== STEP 5: Add Application DNS Records to Route 53 ==========
echo -e "\n${YELLOW}[5/7] Adding application DNS records to Route 53...${NC}"

# Function to add/update ALIAS record pointing to ALB
add_alias_record() {
    local SUBDOMAIN_FULL=$1
    
    echo "   → Adding: ${SUBDOMAIN_FULL} → ${ELB_DNS} (ALIAS)"
    
    # Create change batch JSON for ALIAS record
    CHANGE_BATCH=$(cat <<EOF
{
  "Changes": [{
    "Action": "UPSERT",
    "ResourceRecordSet": {
      "Name": "${SUBDOMAIN_FULL}",
      "Type": "A",
      "AliasTarget": {
        "HostedZoneId": "${ELB_HOSTED_ZONE_ID}",
        "DNSName": "${ELB_DNS}",
        "EvaluateTargetHealth": true
      }
    }
  }]
}
EOF
)
    
    # Apply change
    CHANGE_ID=$(aws route53 change-resource-record-sets \
        --hosted-zone-id "${HOSTED_ZONE_ID}" \
        --change-batch "${CHANGE_BATCH}" \
        --query 'ChangeInfo.Id' \
        --output text)
    
    if [ -n "$CHANGE_ID" ]; then
        echo -e "${GREEN}   ✓ Successfully added ${SUBDOMAIN_FULL}${NC}"
    else
        echo -e "${RED}   ✗ Failed to add ${SUBDOMAIN_FULL}${NC}"
        return 1
    fi
}

# Add the three subdomains
add_alias_record "${STAGING_SUBDOMAIN}.${DOMAIN}"
add_alias_record "${API_SUBDOMAIN}.${DOMAIN}"
add_alias_record "${DASHBOARD_SUBDOMAIN}.${DOMAIN}"

# ========== STEP 6: Update Terraform Configuration ==========
echo -e "\n${YELLOW}[6/7] Updating Terraform configuration...${NC}"

TFVARS_FILE="${TERRAFORM_DIR}/terraform.tfvars"

if [ ! -f "$TFVARS_FILE" ]; then
    echo -e "${RED}ERROR: Terraform tfvars file not found at: ${TFVARS_FILE}${NC}"
    exit 1
fi

# Create backup
cp "$TFVARS_FILE" "${TFVARS_FILE}.backup.$(date +%Y%m%d-%H%M%S)"

# Update the terraform.tfvars file
cat > "$TFVARS_FILE" << EOF
# Staging Environment Configuration
# Updated by setup-ssl-dns.sh on $(date)

aws_region = "$AWS_REGION"

# Database password - RDS-compatible (no /, @, ", or space characters)
master_password = "8Zm2bz5rKnoex3Ybd15SfuC8T1R5pP3U"

# Domain configuration - Using custom domain with SSL
domain               = "${STAGING_SUBDOMAIN}.${DOMAIN}"
backend_domain       = "${API_SUBDOMAIN}.${DOMAIN}"
frontend_host        = "https://${DASHBOARD_SUBDOMAIN}.${DOMAIN}"
backend_cors_origins = "https://${DASHBOARD_SUBDOMAIN}.${DOMAIN},http://localhost:5173"

# ACM Certificate ARN for HTTPS
certificate_arn = "${CERT_ARN}"

# GitHub configuration
github_repo                 = "MarkLimmage/ohmycoins"
create_github_oidc_provider = true

# Container images
backend_image      = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/omc-backend"
backend_image_tag  = "latest"
frontend_image     = "ghcr.io/marklimmage/ohmycoins-frontend"
frontend_image_tag = "latest"
EOF

echo -e "${GREEN}   ✓ Updated terraform.tfvars${NC}"
echo "   Backup saved at: ${TFVARS_FILE}.backup.*"

# ========== Summary ==========
echo -e "\n${GREEN}====================================================${NC}"
echo -e "${GREEN}✓ SSL & DNS Setup Complete!${NC}"
echo -e "${GREEN}====================================================${NC}"
echo ""
echo "Route 53 Hosted Zone: ${HOSTED_ZONE_ID}"
echo "Certificate ARN: ${CERT_ARN}"
echo ""
echo "DNS Records Created (ALIAS to ALB):"
echo "  - ${STAGING_SUBDOMAIN}.${DOMAIN} → ${ELB_DNS}"
echo "  - ${API_SUBDOMAIN}.${DOMAIN} → ${ELB_DNS}"
echo "  - ${DASHBOARD_SUBDOMAIN}.${DOMAIN} → ${ELB_DNS}"
echo ""
echo -e "${BLUE}Nameservers (ensure these are set in GoDaddy):${NC}"
for NS in $NAMESERVERS; do
    echo "  - ${NS}"
done
echo ""
echo -e "${YELLOW}NEXT STEPS:${NC}"
echo ""
echo "1. Verify nameservers are updated in GoDaddy (if not done already)"
echo ""
echo "2. Wait 5-10 minutes for DNS propagation"
echo ""
echo "3. Apply Terraform changes to enable HTTPS:"
echo "   cd ${TERRAFORM_DIR}"
echo "   terraform plan"
echo "   terraform apply"
echo ""
echo "4. After Terraform apply completes, your application will be available at:"
echo "   https://${DASHBOARD_SUBDOMAIN}.${DOMAIN}"
echo "   https://${API_SUBDOMAIN}.${DOMAIN}/docs"
echo ""
echo "5. Test certificate:"
echo "   curl -I https://${STAGING_SUBDOMAIN}.${DOMAIN}"
echo ""
echo -e "${YELLOW}Note: DNS propagation can take 5-60 minutes depending on nameserver updates${NC}"
echo ""
