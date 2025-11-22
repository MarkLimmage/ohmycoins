#!/bin/bash
set -e

# Database Snapshot Utility for Oh My Coins
# Creates a PostgreSQL dump that can be restored later

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get snapshot name from argument or generate timestamp-based name
SNAPSHOT_NAME="${1:-dev-snapshot-$(date +%Y%m%d-%H%M%S)}"
SNAPSHOT_DIR="./backups"
SNAPSHOT_FILE="${SNAPSHOT_DIR}/${SNAPSHOT_NAME}.sql"

# Ensure backups directory exists
mkdir -p "$SNAPSHOT_DIR"

echo -e "${YELLOW}Creating database snapshot: ${SNAPSHOT_NAME}${NC}"

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

# Create the snapshot using pg_dump
echo -e "${YELLOW}Dumping database to ${SNAPSHOT_FILE}${NC}"
docker compose exec -T db pg_dump \
    -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" \
    --clean \
    --if-exists \
    --no-owner \
    --no-acl \
    > "$SNAPSHOT_FILE"

# Compress the snapshot
echo -e "${YELLOW}Compressing snapshot...${NC}"
gzip -f "$SNAPSHOT_FILE"
SNAPSHOT_FILE="${SNAPSHOT_FILE}.gz"

# Get file size
FILE_SIZE=$(du -h "$SNAPSHOT_FILE" | cut -f1)

echo -e "${GREEN}✓ Snapshot created successfully!${NC}"
echo -e "  File: ${SNAPSHOT_FILE}"
echo -e "  Size: ${FILE_SIZE}"
echo ""
echo -e "To restore this snapshot, run:"
echo -e "  ${YELLOW}./scripts/db-restore.sh ${SNAPSHOT_NAME}${NC}"
echo ""
echo -e "To list all snapshots:"
echo -e "  ${YELLOW}ls -lh ${SNAPSHOT_DIR}/${NC}"

# Optional: Create a metadata file
cat > "${SNAPSHOT_DIR}/${SNAPSHOT_NAME}.meta" <<EOF
{
  "snapshot_name": "${SNAPSHOT_NAME}",
  "created_at": "$(date -Iseconds)",
  "database": "${POSTGRES_DB}",
  "size": "${FILE_SIZE}",
  "postgres_version": "$(docker compose exec -T db psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -t -c 'SELECT version();' | head -n1 | xargs)"
}
EOF

echo -e "${GREEN}Metadata saved to ${SNAPSHOT_DIR}/${SNAPSHOT_NAME}.meta${NC}"
