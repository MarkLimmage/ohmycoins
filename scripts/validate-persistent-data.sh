#!/bin/bash
# Quick validation test for persistent dev data store implementation

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}=== Persistent Dev Data Store - Validation Test ===${NC}\n"

# Test 1: Check if scripts exist and are executable
echo -e "${YELLOW}[1/6] Checking scripts...${NC}"
for script in db-snapshot.sh db-restore.sh db-reset.sh; do
    if [ -x "./scripts/$script" ]; then
        echo -e "  ${GREEN}✓${NC} scripts/$script is executable"
    else
        echo -e "  ${RED}✗${NC} scripts/$script is missing or not executable"
        exit 1
    fi
done

# Test 2: Check if backups directory exists
echo -e "\n${YELLOW}[2/6] Checking backups directory...${NC}"
if [ -d "./backups" ]; then
    echo -e "  ${GREEN}✓${NC} backups/ directory exists"
    if [ -f "./backups/README.md" ]; then
        echo -e "  ${GREEN}✓${NC} backups/README.md exists"
    else
        echo -e "  ${RED}✗${NC} backups/README.md is missing"
        exit 1
    fi
else
    echo -e "  ${RED}✗${NC} backups/ directory is missing"
    exit 1
fi

# Test 3: Check environment variables in .env
echo -e "\n${YELLOW}[3/6] Checking .env configuration...${NC}"
if [ -f ".env" ]; then
    for var in AUTO_SEED_DB SEED_USER_COUNT SEED_ALGORITHM_COUNT SEED_AGENT_SESSION_COUNT SEED_COLLECT_REAL_DATA; do
        if grep -q "^${var}=" .env; then
            echo -e "  ${GREEN}✓${NC} $var is configured"
        else
            echo -e "  ${RED}✗${NC} $var is missing from .env"
            exit 1
        fi
    done
else
    echo -e "  ${RED}✗${NC} .env file not found"
    exit 1
fi

# Test 4: Check docker-compose.override.yml for db-init service
echo -e "\n${YELLOW}[4/6] Checking docker-compose configuration...${NC}"
if [ -f "docker-compose.override.yml" ]; then
    if grep -q "db-init:" docker-compose.override.yml; then
        echo -e "  ${GREEN}✓${NC} db-init service is defined"
    else
        echo -e "  ${RED}✗${NC} db-init service is missing"
        exit 1
    fi
else
    echo -e "  ${RED}✗${NC} docker-compose.override.yml not found"
    exit 1
fi

# Test 5: Check documentation
echo -e "\n${YELLOW}[5/6] Checking documentation...${NC}"
for doc in PERSISTENT_DEV_DATA.md PERSISTENT_DEV_DATA_IMPLEMENTATION.md SYNTHETIC_DATA_QUICKSTART.md; do
    if [ -f "./$doc" ]; then
        echo -e "  ${GREEN}✓${NC} $doc exists"
    else
        echo -e "  ${RED}✗${NC} $doc is missing"
        exit 1
    fi
done

# Test 6: Check .gitignore
echo -e "\n${YELLOW}[6/6] Checking .gitignore...${NC}"
if grep -q "backups/\*.sql.gz" .gitignore; then
    echo -e "  ${GREEN}✓${NC} Snapshot files are excluded from git"
else
    echo -e "  ${RED}✗${NC} .gitignore not configured for snapshots"
    exit 1
fi

# All tests passed
echo -e "\n${GREEN}=== All validation tests passed! ===${NC}\n"
echo "Next steps:"
echo "  1. Start environment: ${YELLOW}docker-compose up -d${NC}"
echo "  2. Check logs: ${YELLOW}docker-compose logs db-init${NC}"
echo "  3. Test snapshot: ${YELLOW}./scripts/db-snapshot.sh test-snapshot${NC}"
echo ""
