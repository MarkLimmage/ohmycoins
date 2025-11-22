#!/bin/bash
set -e

# Database Restore Utility for Oh My Coins
# Restores a PostgreSQL dump created with db-snapshot.sh

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if snapshot name provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: No snapshot name provided${NC}"
    echo ""
    echo "Usage: $0 <snapshot-name>"
    echo ""
    echo "Available snapshots:"
    ls -1 ./backups/*.sql.gz 2>/dev/null | sed 's|./backups/||' | sed 's|.sql.gz||' || echo "  (none found)"
    exit 1
fi

SNAPSHOT_NAME="$1"
SNAPSHOT_DIR="./backups"
SNAPSHOT_FILE="${SNAPSHOT_DIR}/${SNAPSHOT_NAME}.sql.gz"

# Check if snapshot exists
if [ ! -f "$SNAPSHOT_FILE" ]; then
    echo -e "${RED}Error: Snapshot not found: ${SNAPSHOT_FILE}${NC}"
    echo ""
    echo "Available snapshots:"
    ls -1 ./backups/*.sql.gz 2>/dev/null | sed 's|./backups/||' | sed 's|.sql.gz||' || echo "  (none found)"
    exit 1
fi

# Load environment variables
if [ -f .env ]; then
    set -a
    source <(cat .env | grep -v '^#' | grep -v '^$' | sed 's/#.*//')
    set +a
else
    echo -e "${RED}Error: .env file not found${NC}"
    exit 1
fi

# Check if database container is running
if ! docker compose ps db | grep -q "Up"; then
    echo -e "${RED}Error: Database container is not running${NC}"
    echo "Start it with: docker-compose up -d db"
    exit 1
fi

# Warning prompt
echo -e "${YELLOW}⚠️  WARNING: This will completely replace your current database!${NC}"
echo -e "Snapshot: ${SNAPSHOT_FILE}"
if [ -f "${SNAPSHOT_DIR}/${SNAPSHOT_NAME}.meta" ]; then
    echo ""
    echo "Snapshot metadata:"
    cat "${SNAPSHOT_DIR}/${SNAPSHOT_NAME}.meta" | grep -E '"(created_at|size|database)"' | sed 's/^/  /'
fi
echo ""
read -p "Are you sure you want to continue? (yes/no): " -r
echo
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo -e "${YELLOW}Restore cancelled.${NC}"
    exit 0
fi

echo -e "${YELLOW}Stopping dependent services...${NC}"
docker compose stop backend frontend playwright 2>/dev/null || true

echo -e "${YELLOW}Dropping existing database connections...${NC}"
docker compose exec -T db psql -U "${POSTGRES_USER}" -d postgres -c \
    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${POSTGRES_DB}' AND pid <> pg_backend_pid();" \
    2>/dev/null || true

echo -e "${YELLOW}Restoring database from ${SNAPSHOT_FILE}${NC}"
gunzip -c "$SNAPSHOT_FILE" | docker compose exec -T db psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}"

echo -e "${GREEN}✓ Database restored successfully!${NC}"
echo ""
echo -e "Next steps:"
echo -e "  1. Start services: ${YELLOW}docker-compose up -d${NC}"
echo -e "  2. Verify data: ${YELLOW}docker compose exec backend python -c 'from sqlmodel import Session, select, func; from app.core.db import engine; from app.models import User; print(f\"Users: {Session(engine).exec(select(func.count(User.id))).one()}\")'${NC}"
