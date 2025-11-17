#!/bin/bash
# AWS Cost Estimation Script
# Estimates monthly costs for Oh My Coins infrastructure

set -e

echo "========================================="
echo "Oh My Coins - AWS Cost Estimation"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Function to display cost breakdown
show_costs() {
    local env=$1
    
    echo -e "${CYAN}Environment: $env${NC}"
    echo "--------------------------------"
    
    if [ "$env" = "staging" ]; then
        echo "RDS PostgreSQL (db.t3.micro, single-AZ):     ~$15/month"
        echo "ElastiCache Redis (cache.t3.micro):          ~$15/month"
        echo "ECS Fargate (1 backend + 1 frontend):        ~$30/month"
        echo "Application Load Balancer:                   ~$20/month"
        echo "NAT Gateway (single AZ):                     ~$35/month"
        echo "Data Transfer:                               ~$10/month"
        echo "VPC Flow Logs:                               ~$5/month"
        echo "CloudWatch Logs:                             ~$5/month"
        echo "--------------------------------"
        echo -e "${GREEN}Total Estimated Cost: ~$135/month${NC}"
        echo ""
        echo "Note: Actual costs may vary based on usage patterns"
    else
        echo "RDS PostgreSQL (db.t3.small, Multi-AZ):      ~$60/month"
        echo "ElastiCache Redis (cache.t3.small, 2 nodes): ~$60/month"
        echo "ECS Fargate (2 backend + 2 frontend):        ~$120/month"
        echo "Application Load Balancer:                   ~$20/month"
        echo "NAT Gateway (Multi-AZ, 2 gateways):          ~$70/month"
        echo "Data Transfer:                               ~$30/month"
        echo "VPC Flow Logs:                               ~$10/month"
        echo "CloudWatch Logs (30-day retention):          ~$20/month"
        echo "--------------------------------"
        echo -e "${GREEN}Total Estimated Cost: ~$390/month${NC}"
        echo ""
        echo "Cost Optimization Opportunities:"
        echo "  - Savings Plans: 30-40% savings"
        echo "  - Reserved Instances: 20-30% savings"
        echo "  - Single NAT Gateway: ~$35/month savings"
        echo "  - Shorter log retention: ~$10/month savings"
    fi
}

# Parse command line arguments
if [ $# -eq 0 ]; then
    # Show both environments
    show_costs "staging"
    echo ""
    show_costs "production"
else
    show_costs "$1"
fi

echo ""
echo "========================================="
echo "Cost Comparison"
echo "========================================="
echo ""
echo "Monthly Costs:"
echo "  Staging:    ~$135/month"
echo "  Production: ~$390/month"
echo ""
echo "Annual Costs:"
echo "  Staging:    ~$1,620/year"
echo "  Production: ~$4,680/year"
echo ""
echo "With Savings Plans (40% off):"
echo "  Staging:    ~$972/year"
echo "  Production: ~$2,808/year"
echo ""
echo "========================================="
echo ""
echo -e "${YELLOW}Recommendation:${NC}"
echo "  - Start with staging for development/testing"
echo "  - Move to production once ready"
echo "  - Consider Savings Plans after 1-2 months"
echo "  - Monitor costs with AWS Cost Explorer"
echo ""
