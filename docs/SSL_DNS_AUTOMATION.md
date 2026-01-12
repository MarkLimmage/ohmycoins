# SSL & DNS Automation Setup Guide (Route 53)

This guide explains how to automate SSL certificate creation and DNS configuration for your OhMyCoins staging environment using AWS Route 53.

## Prerequisites

1. **Domain**: `ohmycoins.com` registered with GoDaddy (or any registrar)
2. **AWS CLI** configured with appropriate permissions
3. **Tools Required**: `jq`, `aws cli`

## What the Script Does

The automation script (`scripts/setup-ssl-dns.sh`) performs these steps:

1. **Create Route 53 Hosted Zone** - Sets up DNS hosting in AWS for your domain
2. **Request ACM Certificate** - Requests SSL cert for `staging.ohmycoins.com` and `*.staging.ohmycoins.com`
3. **Get Validation Records** - Retrieves CNAME records needed for domain validation
4. **Update Route 53 DNS** - Automatically adds validation records to Route 53
5. **Wait for Validation** - Monitors certificate status until AWS validates ownership
6. **Add Application Records** - Creates ALIAS records pointing subdomains to your ALB
7. **Update Terraform** - Automatically updates `terraform.tfvars` with certificate ARN and domains

## DNS Records Created

| Record Type | Name | Points To | Purpose |
|-------------|------|-----------|---------|
| CNAME | `_xxxxxx.staging.ohmycoins.com` | `_xxxxxx.acm-validations.aws.` | ACM validation |
| A (ALIAS) | `staging.ohmycoins.com` | ALB DNS | Main staging domain |
| A (ALIAS) | `api.staging.ohmycoins.com` | ALB DNS | Backend API |
| A (ALIAS) | `dashboard.staging.ohmycoins.com` | ALB DNS | Frontend dashboard |

**Note**: Uses Route 53 ALIAS records (not CNAME) for better performance and no additional cost.

## Usage

### Step 1: Run the Automation Script

```bash
cd /home/mark/omc/ohmycoins
./scripts/setup-ssl-dns.sh
```

The script will:
1. Create or use existing Route 53 hosted zone
2. Display nameservers that need to be set at GoDaddy
3. Wait for you to confirm nameserver update
4. Create certificate and DNS records automatically
5. Take 5-20 minutes (mostly waiting for AWS validation)

### Step 2: Update Nameservers at GoDaddy

When the script pauses and shows nameservers like:
```
ns-123.awsdns-12.com
ns-456.awsdns-45.net
ns-789.awsdns-78.org
ns-012.awsdns-01.co.uk
```

Go to GoDaddy:
1. Log in to GoDaddy account
2. Go to "My Products" → "Domains"
3. Click on `ohmycoins.com` → "Manage DNS"
4. Scroll to "Nameservers" section
5. Click "Change" → "Enter my own nameservers (advanced)"
6. Replace existing nameservers with the 4 AWS nameservers shown by script
7. Save changes

Press ENTER in the script to continue.

### Step 3: Apply Terraform Changes

After the script completes:

```bash
cd infrastructure/terraform/environments/staging
terraform plan  # Review changes
terraform apply # Apply to enable HTTPS
```

This will:
- Update ALB listeners to use HTTPS (port 443)
- Add HTTP→HTTPS redirect
- Configure backend and frontend with proper domains
- Update CORS settings

### Step 4: Verify

Wait 5-10 minutes for DNS propagation, then test:

```bash
# Test certificate
curl -I https://staging.ohmycoins.com

# Test backend API
curl https://api.staging.ohmycoins.com/api/v1/utils/health-check/

# Visit frontend
https://dashboard.staging.ohmycoins.com
```

## Nameserver Propagation Time

After updating nameservers at GoDaddy:
- **First validation**: 5-30 minutes (depending on TTL of old records)
- **Subsequent changes**: Instant (since Route 53 controls DNS)

You can check propagation status:
```bash
dig NS ohmycoins.com
```

Should show the 4 AWS nameservers once propagated.

## Configuration Details

The script is configured for:
- **Region**: ap-southeast-2 (Sydney)
- **Domain**: ohmycoins.com
- **Subdomains**:
  - `staging.ohmycoins.com` - Main domain
  - `api.staging.ohmycoins.com` - Backend API
  - `dashboard.staging.ohmycoins.com` - Frontend

To modify these, edit the configuration section in `scripts/setup-ssl-dns.sh`:
```bash
DOMAIN="ohmycoins.com"
STAGING_SUBDOMAIN="staging"
API_SUBDOMAIN="api.staging"
DASHBOARD_SUBDOMAIN="dashboard.staging"
```

## Terraform Changes

The script automatically updates `terraform.tfvars` with:

```hcl
domain               = "staging.ohmycoins.com"
backend_domain       = "api.staging.ohmycoins.com"
frontend_host        = "https://dashboard.staging.ohmycoins.com"
backend_cors_origins = "https://dashboard.staging.ohmycoins.com,http://localhost:5173"
certificate_arn      = "arn:aws:acm:ap-southeast-2:220711411889:certificate/xxx"
```

A backup is created before modification: `terraform.tfvars.backup.TIMESTAMP`

## Troubleshooting

### Issue: "Nameservers not updated yet"
**Solution**: Update nameservers at GoDaddy before continuing. The script will wait for you.

### Issue: Certificate validation timeout
**Causes**:
- Nameservers not propagated yet at GoDaddy
- DNS records not visible due to caching

**Check**:
```bash
# Verify nameserver propagation
dig NS ohmycoins.com

# Check validation record exists
dig _xxxxxx.staging.ohmycoins.com CNAME

# Check certificate status
aws acm describe-certificate --certificate-arn <ARN> --region ap-southeast-2
```

### Issue: "Hosted zone already exists"
**Solution**: Script will use existing hosted zone. No problem - it's idempotent.

### Issue: DNS records conflict
**Check existing records**:
```bash
aws route53 list-resource-record-sets --hosted-zone-id <ZONE_ID>
```

**Solution**: Script uses UPSERT so it will update existing records safely.

### Issue: Terraform apply fails after script
**Check**:
- Certificate is in "ISSUED" status
- DNS records have propagated (5-10 minutes)
- terraform.tfvars was updated correctly

## Manual Verification Steps

1. **Check Hosted Zone**:
```bash
aws route53 list-hosted-zones-by-name --dns-name ohmycoins.com
```

2. **Check Certificate Status**:
```bash
aws acm list-certificates --region ap-southeast-2
aws acm describe-certificate --certificate-arn <ARN> --region ap-southeast-2
```

3. **Verify DNS Records**:
```bash
aws route53 list-resource-record-sets --hosted-zone-id <ZONE_ID>
```

4. **Test DNS Resolution**:
```bash
dig staging.ohmycoins.com
dig api.staging.ohmycoins.com
dig dashboard.staging.ohmycoins.com
```

## Cost Impact

**Route 53 Hosted Zone**: $0.50/month
**Route 53 Queries**: $0.40 per million queries (first billion queries/month)
**ACM Certificate**: FREE
**ALIAS Records**: FREE (no query charges for ALIAS to AWS resources)

**Estimated monthly cost**: ~$0.50-1.00 for typical staging usage

## Advantages of Route 53 over GoDaddy DNS

1. **ALIAS Records**: Better performance, free queries to AWS resources
2. **Fast Propagation**: Changes take seconds, not minutes
3. **Programmatic Control**: Full API access without restrictions
4. **Health Checks**: Can route traffic based on endpoint health
5. **Integrated**: Works seamlessly with other AWS services
6. **No API Restrictions**: Unlike GoDaddy's account policies

## Rollback Procedure

If something goes wrong:

1. **Restore terraform.tfvars**:
```bash
cd infrastructure/terraform/environments/staging
cp terraform.tfvars.backup.TIMESTAMP terraform.tfvars
terraform apply
```

2. **Delete Certificate** (if needed):
```bash
aws acm delete-certificate --certificate-arn <ARN> --region ap-southeast-2
```

3. **Remove DNS Records** (via GoDaddy control panel or API)

## Next Steps After Setup

1. **Update Frontend Environment**: Rebuild frontend with correct API URL
2. **Test Login**: Verify superuser can log in via dashboard
3. **Configure Monitoring**: Set up CloudWatch alarms for HTTPS endpoints
4. **Update Documentation**: Record certificate ARN and domain setup
5. **Set Up Production**: Repeat process for production environment with `prod.ohmycoins.com`

## Security Notes

- **API Keys**: Never commit GoDaddy credentials to git
- **Certificate**: Automatically renews before expiration (AWS manages this)
- **DNS TTL**: Set to 600 seconds (10 minutes) for faster updates during setup
- **HTTPS Only**: After setup, configure ALB to reject HTTP traffic (optional)

## Support

If the automated script fails, you can perform these steps manually:
1. Request certificate via AWS Console
2. Add validation records to GoDaddy manually
3. Wait for validation
4. Add CNAME records for subdomains
5. Update terraform.tfvars manually
6. Run terraform apply

See `AWS_STAGING_DEPLOYMENT_COMPLETE.md` for manual DNS configuration instructions.
